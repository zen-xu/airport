from pydantic import BaseModel

from airport.api.scheduling import KubeGroupNameAnnotationKey
from airport.kube.api import Pod
from airport.kube.api import PodPhase

from ._enums import TaskStatus
from ._resource_info import Resource


class TaskInfo(BaseModel):
    uid: str
    job: str
    name: str
    namespace: str
    resource_requests: Resource
    init_resource_requests: Resource
    node_name: str
    status: TaskStatus
    priority: int
    volume_ready: bool = False
    pod: Pod

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
    if pod.status.phase == PodPhase.Running:
        if pod.metadata.deletionTimestamp is not None:
            return TaskStatus.Releasing
        else:
            return TaskStatus.Running
    elif pod.status.phase == PodPhase.Pending:
        if pod.metadata.deletionTimestamp is not None:
            return TaskStatus.Releasing
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
