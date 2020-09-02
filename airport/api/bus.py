from typing import List

from airport.kube.api import KubeEnum
from airport.kube.api import KubeModel
from airport.kube.api import ListMeta
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


class Command(TypeMeta, KubeModel):
    metadata: ObjectMeta = ObjectMeta()
    action: str = ""
    target: OwnerReference = OwnerReference()
    reason: str = ""
    message: str = ""


class CommandList(TypeMeta, KubeModel):
    metadata: ListMeta = ListMeta()
    items: List[Command] = []
