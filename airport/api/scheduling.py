from datetime import datetime
from typing import List
from typing import Optional

from airport.kube.api import ConditionStatus
from airport.kube.api import KubeEnum
from airport.kube.api import KubeModel
from airport.kube.api import ListMeta
from airport.kube.api import ObjectMeta
from airport.kube.api import ResourceList
from airport.kube.api import TypeMeta


GroupName = "scheduling.volcano.sh"
GroupVersion = "v1beta1"
KubeGroupNameAnnotationKey = "scheduling.k8s.io/group-name"
VolcanoGroupNameAnnotationKey = f"{GroupName}/group-name"
QueueNameAnnotationKey = f"{GroupName}/queue-name"


class QueueEvent(KubeEnum):
    OutOfSync = "OutOfSync"
    CommandIssued = "CommandIssued"


class QueueAction(KubeEnum):
    SyncQueue = "SyncQueue"
    OpenQueue = "OpenQueue"
    CloseQueue = "CloseQueue"


class PodGroupSpec(KubeModel):
    minMember: int
    queue: Optional[str]
    priorityClassName: Optional[str]
    minResources: ResourceList


class PodGroupPhase(KubeEnum):
    Pending = "Pending"
    Running = "Running"
    Unknown = "Unknown"
    Inqueue = "Inqueue"


class PodGroupConditionType(KubeEnum):
    Scheduled = "Scheduled"
    Unschedulable = "Unschedulable"


class PodGroupCondition(KubeModel):
    type: PodGroupConditionType
    status: ConditionStatus
    transitionID: str
    lastTransitionTime: Optional[datetime]
    reason: Optional[str]
    message: Optional[str]


class PodGroupStatus(KubeModel):
    phase: PodGroupPhase
    conditions: PodGroupCondition
    running: Optional[int]
    succeeded: Optional[int]
    failed: Optional[int]


class PodGroup(TypeMeta, ObjectMeta):
    spec: Optional[PodGroupSpec]
    status: Optional[PodGroupStatus]


class PodGroupList(TypeMeta, ListMeta):
    items: List[PodGroup] = []


class QueueSpec(KubeModel):
    weight: int
    capability: ResourceList
    reclaimable: bool


class QueueState(KubeEnum):
    Open = "Open"
    Closed = "Closed"
    Closing = "Closing"
    Unknown = "Unknown"


class QueueStatus(KubeModel):
    state: QueueState
    unknown: int
    pending: int
    running: int
    inqueue: int


class Queue(TypeMeta, ObjectMeta):
    spec: Optional[QueueSpec]
    status: Optional[QueueStatus]


class QueueList(TypeMeta, ListMeta):
    items: List[Queue]
