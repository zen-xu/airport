from typing import List
from typing import Optional

from airport.kube.api import KubeEnum
from airport.kube.api import ObjectMeta
from airport.kube.api import OwnerReference
from airport.kube.api import TypeMeta


class Action(KubeEnum):
    AbortJob = "AbortJob"
    RestartJob = "RestartJob"
    RestartTask = "RestartTask"
    TerminateJob = "TerminateJob"
    CompleteJob = "CompleteJob"
    ResumeJob = "ResumeJob"
    SyncJob = "SyncJob"
    EnqueueJob = "EnqueueJob"
    SyncQueue = "SyncQueue"
    OpenQueue = "OpenQueue"
    CloseQueue = "CloseQueue"


class Event(KubeEnum):
    Any = "*"
    PodFailed = "PodFailed"
    PodEvicted = "PodEvicted"
    Unknown = "Unknown"
    TaskCompleted = "TaskCompleted"
    OutOfSync = "OutOfSync"
    CommandIssued = "CommandIssued"


class Command(TypeMeta, ObjectMeta):
    action: str
    target: OwnerReference
    reason: Optional[str]
    message: Optional[str]


class CommandList(TypeMeta, ObjectMeta):
    items: List[Command]
