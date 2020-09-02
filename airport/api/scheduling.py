from datetime import datetime
from typing import List
from typing import Optional

from airport.kube.api import ConditionStatus
from airport.kube.api import DefaultDatetime
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
    minMember: int = 0
    queue: str = ""
    priorityClassName: str = ""
    minResources: ResourceList = {}


class PodGroupPhase(KubeEnum):
    Pending = "Pending"
    Running = "Running"
    Unknown = "Unknown"
    Inqueue = "Inqueue"


class PodGroupConditionType(KubeEnum):
    Scheduled = "Scheduled"
    Unschedulable = "Unschedulable"


class PodGroupCondition(KubeModel):
    type: Optional[PodGroupConditionType]
    status: Optional[ConditionStatus]
    transitionID: str = ""
    lastTransitionTime: datetime = DefaultDatetime
    reason: str = ""
    message: str = ""


class PodGroupStatus(KubeModel):
    phase: Optional[PodGroupPhase]
    conditions: List[PodGroupCondition] = []
    running: int = 0
    succeeded: int = 0
    failed: int = 0


class PodGroup(TypeMeta, KubeModel):
    metadata: ObjectMeta = ObjectMeta()
    spec: PodGroupSpec = PodGroupSpec()
    status: PodGroupStatus = PodGroupStatus()


class PodGroupList(TypeMeta, KubeModel):
    metadata: ListMeta = ListMeta()
    items: List[PodGroup] = []


class QueueSpec(KubeModel):
    weight: int = 0
    capability: ResourceList = {}
    reclaimable: Optional[bool]


class QueueState(KubeEnum):
    Open = "Open"
    Closed = "Closed"
    Closing = "Closing"
    Unknown = "Unknown"


class QueueStatus(KubeModel):
    state: Optional[QueueState]
    unknown: int = 0
    pending: int = 0
    running: int = 0
    inqueue: int = 0


class Queue(TypeMeta, KubeModel):
    metadata: ObjectMeta = ObjectMeta()
    spec: QueueSpec = QueueSpec()
    status: QueueStatus = QueueStatus()


class QueueList(TypeMeta, KubeModel):
    metadata: ListMeta = ListMeta()
    items: List[Queue] = []
