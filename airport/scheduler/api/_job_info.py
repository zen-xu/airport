from pydantic import BaseModel
from returns.maybe import Maybe

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

        uid = (
            Maybe.from_value(pod.metadata)
            .map(lambda metadata: metadata.uid)
            .value_or("")
        )
        name = (
            Maybe.from_value(pod.metadata)
            .map(lambda metadata: metadata.name)
            .value_or("")
        )
        namespace = (
            Maybe.from_value(pod.metadata)
            .map(lambda metadata: metadata.namespace)
            .value_or("")
        )
        node_name = (
            Maybe.from_value(pod.spec).map(lambda spec: spec.nodeName).value_or("")
        )
        status = get_task_status(pod)

        return cls(
            uid=uid,
            job=job_id,
            name=name,
            namespace=namespace,
            node_name=node_name,
            status=status,
            priority=1,
            pod=pod,
            resource_requests=request,
            init_resource_requests=init_request,
        )


def get_job_id(pod: Pod) -> str:
    if pod.metadata is None:
        return ""

    annotations = pod.metadata.annotations
    try:
        pod_group_name = annotations[KubeGroupNameAnnotationKey]
    except KeyError:
        return ""

    if not pod_group_name:
        return ""

    namespace = pod.metadata.namespace or ""

    return f"{namespace}/{pod_group_name}"


def get_pod_resource_request(pod: Pod) -> Resource:
    if pod.spec is None:
        return Resource()

    result = get_pod_resource_without_init_container(pod)
    for container in pod.spec.initContainers:
        if container.resources is None:
            continue
        result.set_max_resource(Resource.new(container.resources.requests))

    return result


def get_pod_resource_without_init_container(pod: Pod) -> Resource:
    if pod.spec is None:
        return Resource()

    result = Resource()
    for container in pod.spec.containers:
        if container.resources is None:
            continue
        result += Resource.new(container.resources.requests)
    return result


def get_task_status(pod: Pod) -> TaskStatus:
    if pod.status is None:
        return TaskStatus.Unknown

    if pod.status.phase == PodPhase.Running:
        return TaskStatus.Running
    elif pod.status.phase == PodPhase.Pending:
        return (
            Maybe.from_value(pod.metadata)
            .map(lambda metadata: metadata.deletionTimestamp)
            .map(lambda _: TaskStatus.Releasing)
            .value_or(TaskStatus.Running)
        )
    elif pod.status.phase == PodPhase.Unknown:
        return TaskStatus.Unknown
    elif pod.status.phase == PodPhase.Succeeded:
        return TaskStatus.Succeeded
    elif pod.status.phase == PodPhase.Failed:
        return TaskStatus.Failed
    else:
        return TaskStatus.Unknown
