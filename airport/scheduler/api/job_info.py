from collections import defaultdict
from datetime import datetime
from typing import Dict
from typing import Optional
from typing import Union

from pydantic import BaseModel

from airport.api.scheduling import KubeGroupNameAnnotationKey
from airport.kube.api import DefaultDatetime
from airport.kube.api import Pod
from airport.kube.api import PodPhase

from .enums import TaskStatus
from .pod_group_info import PodGroup
from .resource_info import Resource


class FailedToFindTask(Exception):
    def __init__(self, task: "TaskInfo", job: "JobInfo"):
        self.message = f"failed to find task <{task.namespace}/{task.name}> in job <{job.namespace}/{job.name}>"


class FitError(Exception):
    ...


class TaskInfo(BaseModel):
    uid: str = ""
    job: str = ""
    name: str = ""
    namespace: str = ""
    resource_requests: Resource = Resource()
    init_resource_requests: Resource = Resource()
    node_name: str = ""
    status: TaskStatus
    priority: int = 0
    volume_ready: bool = False
    pod: Pod = Pod()

    @classmethod
    def new(cls, pod: Pod) -> "TaskInfo":
        request = get_pod_resource_without_init_container(pod)
        init_request = get_pod_resource_request(pod)
        job_id = get_job_id(pod)
        status = get_task_status(pod)

        return cls(
            uid=pod.metadata.uid,
            job=job_id,
            name=pod.metadata.name,
            namespace=pod.metadata.namespace,
            node_name=pod.spec.nodeName,
            status=status,
            priority=1,
            pod=pod,
            resource_requests=request,
            init_resource_requests=init_request,
        )


class JobInfo(BaseModel):
    uid: str = ""
    name: str = ""
    namespace: str = ""
    queue: str = ""
    priority: int = 0
    min_available: int = 0
    nodes_fit_delta: Dict[str, Resource] = {}
    job_fit_errors: str = ""
    nodes_fit_errors: Dict[str, str] = {}
    task_status_index: Dict[TaskStatus, Dict[str, TaskInfo]] = {}
    tasks: Dict[str, TaskInfo] = {}
    allocated: Resource = Resource()
    total_request: Resource = Resource()
    create_timestamp: datetime = DefaultDatetime
    pod_group: Optional[PodGroup]

    @classmethod
    def new(cls, uid: str, *tasks: TaskInfo) -> "JobInfo":
        job = JobInfo(uid=uid)

        for task in tasks:
            job.add_task_info(task)

        return job

    def add_task_info(self, task: TaskInfo):
        self.tasks[task.uid] = task
        self.add_task_index(task)

        self.total_request += task.resource_requests

        if task.status.is_allocated():
            self.allocated += task.resource_requests

    def add_task_index(self, task: TaskInfo):
        if task.status not in self.task_status_index:
            self.task_status_index[task.status] = {}

        self.task_status_index[task.status][task.uid] = task

    def unset_pod_group(self):
        self.pod_group = None

    def set_pod_group(self, pg: PodGroup):
        self.name = pg.metadata.name
        self.namespace = pg.metadata.namespace
        if pg.spec is not None:
            self.min_available = pg.spec.minMember
            self.queue = pg.spec.queue
        self.create_timestamp = pg.metadata.creationTimestamp

        self.pod_group = pg

    def update_task_status(self, task: TaskInfo, status: TaskStatus):
        if task.uid in self.tasks:
            self.delete_task_info(task)

        task.status = status
        self.add_task_info(task)

    def delete_task_info(self, task: TaskInfo):
        try:
            job_task = self.tasks[task.uid]
        except KeyError:
            raise FailedToFindTask(task, self)

        self.total_request -= job_task.resource_requests

        if job_task.status.is_allocated():
            self.allocated -= job_task.resource_requests

        self.tasks.pop(job_task.uid)
        self.delete_task_index(job_task)

    def delete_task_index(self, task: TaskInfo):
        try:
            job_tasks = self.task_status_index[task.status]
        except KeyError:
            return

        job_tasks.pop(task.uid)

        if not job_tasks:
            self.task_status_index.pop(task.status)

    def fit_error(self) -> FitError:
        reasons: Dict[Union[str, TaskStatus], int] = defaultdict(int)
        for status, task_map in self.task_status_index.items():
            reasons[status] += len(task_map)
        reasons["minAvailable"] = self.min_available

        reason_strings = []
        for status, count in reasons.items():
            reason_strings.append(f"{status} {count}")
        reason = ", ".join(sorted(reason_strings))
        reason_message = f"pod group is not ready, {reason}"
        return FitError(reason_message)

    @property
    def ready_task_num(self) -> int:
        occupied = 0

        for status, tasks in self.task_status_index.items():
            if status.is_allocated() or status == TaskStatus.Succeeded:
                occupied += len(tasks)
                continue

            if status == TaskStatus.Pending:
                for task in tasks.values():
                    if task.init_resource_requests.is_empty():
                        occupied += 1

        return occupied

    @property
    def waiting_task_num(self) -> int:
        occupied = 0
        for status, tasks in self.task_status_index.items():
            if status == TaskStatus.Pipelined:
                occupied += len(tasks)

        return occupied

    @property
    def valid_task_num(self) -> int:
        occupied = 0
        for status, tasks in self.task_status_index.items():
            if status.is_allocated() or status in [
                TaskStatus.Succeeded,
                TaskStatus.Pipelined,
                TaskStatus.Pending,
            ]:
                occupied += len(tasks)

        return occupied

    @property
    def ready(self) -> bool:
        return self.ready_task_num >= self.min_available

    @property
    def pipelined(self) -> bool:
        return self.waiting_task_num + self.ready_task_num >= self.min_available


def get_job_id(pod: Pod) -> str:
    try:
        pod_group_name = pod.metadata.annotations[KubeGroupNameAnnotationKey]
    except KeyError:
        return ""

    if pod.metadata.namespace and pod_group_name:
        return f"{pod.metadata.namespace}/{pod_group_name}"
    else:
        return ""


def get_pod_resource_request(pod: Pod) -> Resource:
    result = get_pod_resource_without_init_container(pod)
    for container in pod.spec.initContainers:
        result.set_max_resource(Resource.new(container.resources.requests))

    return result


def get_pod_resource_without_init_container(pod: Pod) -> Resource:
    result = Resource()
    for container in pod.spec.containers:
        result += Resource.new(container.resources.requests)
    return result


def get_task_status(pod: Pod) -> TaskStatus:
    if pod.status is None:
        return TaskStatus.Unknown

    if pod.status.phase == PodPhase.Running:
        if pod.metadata.deletionTimestamp is not None:
            return TaskStatus.Releasing
        else:
            return TaskStatus.Running
    elif pod.status.phase == PodPhase.Pending:
        if pod.metadata.deletionTimestamp is not None:
            return TaskStatus.Releasing
        else:
            if not pod.spec.nodeName:
                return TaskStatus.Pending
            else:
                return TaskStatus.Bound
    elif pod.status.phase == PodPhase.Unknown:
        return TaskStatus.Unknown
    elif pod.status.phase == PodPhase.Succeeded:
        return TaskStatus.Succeeded
    elif pod.status.phase == PodPhase.Failed:
        return TaskStatus.Failed
    else:
        return TaskStatus.Unknown
