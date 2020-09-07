from datetime import datetime

import pytest

from airport.api.scheduling import KubeGroupNameAnnotationKey
from airport.kube.api import Pod
from airport.scheduler.api import JobInfo
from airport.scheduler.api import PodGroup
from airport.scheduler.api import Resource
from airport.scheduler.api import TaskInfo
from airport.scheduler.api import job_info
from airport.scheduler.api.enums import TaskStatus


parametrize = pytest.mark.parametrize


@pytest.fixture
def pod():
    return Pod.parse_obj(
        {
            "metadata": {
                "name": "demo",
                "namespace": "default",
                "uid": "05196752-598e-4d10-bf50-a9226d14c514",
                "annotations": {KubeGroupNameAnnotationKey: "demo-job"},
            },
            "spec": {
                "containers": [
                    {
                        "name": "worker1",
                        "resources": {"requests": {"cpu": "10m", "memory": "100Mi"}},
                    },
                    {
                        "name": "worker2",
                        "resources": {"requests": {"cpu": "20m", "memory": "200Mi"}},
                    },
                ],
                "initContainers": [
                    {
                        "name": "init",
                        "resources": {"requests": {"cpu": "1", "memory": "200Mi"}},
                    },
                ],
            },
        }
    )


@pytest.fixture
def empty_pod():
    return Pod()


class TestTaskInfo:
    def test_get_job_id(self, pod: Pod):
        assert job_info.get_job_id(pod) == "default/demo-job"

    def test_get_job_id_from_empty_pod(self, empty_pod: Pod):
        assert job_info.get_job_id(empty_pod) == ""

    def test_get_job_id_no_annotation(self, pod: Pod):
        pod.metadata.annotations = {}
        assert job_info.get_job_id(pod) == ""

        pod.metadata.annotations = {KubeGroupNameAnnotationKey: ""}
        assert job_info.get_job_id(pod) == ""

    def test_get_job_id_no_namespace(self, pod: Pod):
        pod.metadata.namespace = ""
        assert job_info.get_job_id(pod) == ""

    def test_get_pod_resource_without_init_container(self, pod: Pod, empty_pod: Pod):
        assert job_info.get_pod_resource_without_init_container(pod) == Resource.new(
            {"cpu": "30m", "memory": "300Mi"}
        )

        assert job_info.get_pod_resource_without_init_container(empty_pod) == Resource()

    def test_get_pod_resource_request(self, pod: Pod, empty_pod: Pod):
        assert job_info.get_pod_resource_request(pod) == Resource.new(
            {"cpu": "1", "memory": "300Mi"}
        )

        assert job_info.get_pod_resource_request(empty_pod) == Resource()

    @parametrize(
        "pod,task_status",
        [
            ({"status": {"phase": "Running"}}, TaskStatus.Running,),
            (
                {
                    "metadata": {"deletionTimestamp": datetime.now()},
                    "status": {"phase": "Running"},
                },
                TaskStatus.Releasing,
            ),
            (
                {
                    "metadata": {"deletionTimestamp": datetime.now()},
                    "status": {"phase": "Pending"},
                },
                TaskStatus.Releasing,
            ),
            ({"status": {"phase": "Pending"}}, TaskStatus.Pending,),
            (
                {"status": {"phase": "Pending"}, "spec": {"nodeName": "node1"}},
                TaskStatus.Bound,
            ),
            ({"status": {"phase": "Unknown"}}, TaskStatus.Unknown,),
            ({"status": {"phase": "Succeeded"}}, TaskStatus.Succeeded,),
            ({"status": {"phase": "Failed"}}, TaskStatus.Failed,),
        ],
    )
    def test_get_task_status(
        self, pod: dict, task_status: TaskStatus,
    ):
        pod = Pod.parse_obj(pod)
        assert job_info.get_task_status(pod) == task_status

    def test_new_task_info(self, pod: Pod):
        task_info = job_info.TaskInfo.new(pod)
        assert task_info == job_info.TaskInfo.parse_obj(
            {
                "uid": "05196752-598e-4d10-bf50-a9226d14c514",
                "job": "default/demo-job",
                "name": "demo",
                "namespace": "default",
                "resource_requests": Resource.new({"cpu": "30m", "memory": "300Mi"}),
                "init_resource_requests": Resource.new({"cpu": "1", "memory": "300Mi"}),
                "node_name": "",
                "status": TaskStatus.Unknown,
                "priority": 1,
                "volume_ready": False,
                "pod": pod,
            }
        )


def build_pod(namespace, name, node_name, pod_phase, resource_list):
    return Pod.parse_obj(
        {
            "metadata": {
                "uid": f"{namespace}-{name}",
                "name": name,
                "namespace": namespace,
            },
            "spec": {
                "nodeName": node_name,
                "containers": [{"resources": {"requests": resource_list}}],
            },
            "status": {"phase": pod_phase},
        }
    )


class TestJobInfo:
    def test_add_task_info(self):
        pod1 = build_pod("ns", "p1", "", "Pending", {"cpu": "1000m", "memory": "1G"})
        task1 = TaskInfo.new(pod1)

        pod2 = build_pod("ns", "p2", "n1", "Running", {"cpu": "2000m", "memory": "2G"})
        task2 = TaskInfo.new(pod2)

        pod3 = build_pod("ns", "p3", "n1", "Pending", {"cpu": "1000m", "memory": "1G"})
        task3 = TaskInfo.new(pod3)

        pod4 = build_pod("ns", "p4", "n1", "Pending", {"cpu": "1000m", "memory": "1G"})
        task4 = TaskInfo.new(pod4)

        job = job_info.JobInfo(uid="job1")

        for task in [task1, task2, task3, task4]:
            job.add_task_info(task)

        assert job == JobInfo(
            uid="job1",
            allocated=Resource.new({"cpu": "4000m", "memory": "4G"}),
            total_request=Resource.new({"cpu": "5000m", "memory": "5G"}),
            tasks={
                task1.uid: task1,
                task2.uid: task2,
                task3.uid: task3,
                task4.uid: task4,
            },
            task_status_index={
                TaskStatus.Pending: {task1.uid: task1},
                TaskStatus.Running: {task2.uid: task2},
                TaskStatus.Bound: {task3.uid: task3, task4.uid: task4},
            },
        )

    def test_add_task_index(self):
        job = JobInfo()
        task_info = TaskInfo(
            uid="6a4254f0-c299-401a-ab0a-20dd9f27506b",
            resource_requests=Resource.new({"cpu": "30m", "memory": "300Mi"}),
            status=TaskStatus.Bound,
        )
        job.add_task_index(task_info)
        assert (
            job.task_status_index[TaskStatus.Bound][
                "6a4254f0-c299-401a-ab0a-20dd9f27506b"
            ]
            == task_info
        )

    def test_set_pod_group(self):
        job = JobInfo()
        create_timestamp = datetime(2020, 1, 1)
        pod_group = PodGroup(
            metadata={
                "name": "demo",
                "namespace": "default",
                "creationTimestamp": create_timestamp,
            },
            spec={"minMember": 20, "queue": "big_queue"},
        )
        job.set_pod_group(pod_group)
        assert job.name == "demo"
        assert job.namespace == "default"
        assert job.min_available == 20
        assert job.queue == "big_queue"
        assert job.create_timestamp == create_timestamp
        assert job.pod_group == pod_group

    def test_delete_task_info(self):
        pod1 = build_pod("ns", "p1", "", "Pending", {"cpu": "1000m", "memory": "1G"})
        task1 = TaskInfo.new(pod1)

        pod2 = build_pod("ns", "p2", "n1", "Running", {"cpu": "2000m", "memory": "2G"})
        task2 = TaskInfo.new(pod2)

        pod3 = build_pod("ns", "p3", "n1", "Running", {"cpu": "3000m", "memory": "3G"})
        task3 = TaskInfo.new(pod3)

        job = JobInfo(uid="job")

        for task in [task1, task2, task3]:
            job.add_task_info(task)

        job.delete_task_info(task2)

        assert job == JobInfo(
            uid="job",
            allocated=Resource.new({"cpu": "3000m", "memory": "3G"}),
            total_request=Resource.new({"cpu": "4000m", "memory": "4G"}),
            tasks={task1.uid: task1, task3.uid: task3},
            task_status_index={
                TaskStatus.Pending: {task1.uid: task1},
                TaskStatus.Running: {task3.uid: task3},
            },
        )

        with pytest.raises(job_info.FailedToFindTask):
            job.delete_task_info(task2)
