from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional

from airport.kube.api import DefaultDatetime
from airport.kube.api import KubeEnum
from airport.kube.api import KubeModel
from airport.kube.api import ListMeta
from airport.kube.api import ObjectMeta
from airport.kube.api import PersistentVolumeClaimSpec
from airport.kube.api import PodTemplateSpec
from airport.kube.api import TypeMeta

from .bus import Action
from .bus import Event


TaskSpecKey = "volcano.sh/task-spec"
JobNameKey = "volcano.sh/job-name"
JobNamespaceKey = "volcano.sh/job-namespace"
DefaultTaskSpec = "default"
JobVersion = "volcano.sh/job-version"
JobTypeKey = "volcano.sh/job-type"
PodgroupNamePrefix = "podgroup-"


class VolumeSpec(KubeModel):
    mountPath: str = ""
    volumeClaimName: str = ""
    volumeClaim: Optional[PersistentVolumeClaimSpec]


class LifecyclePolicy(KubeModel):
    action: Optional[Action]
    event: Optional[Event]
    events: List[Event] = []
    exitCode: Optional[int]
    timeout: Optional[str]


class TaskSpec(KubeModel):
    name: str = ""
    replicas: int = 0
    template: PodTemplateSpec = PodTemplateSpec()
    policies: List[LifecyclePolicy] = []


class JobSpec(KubeModel):
    schedulerName: str = ""
    minAvailable: str = ""
    volumes: List[VolumeSpec] = []
    tasks: List[TaskSpec] = []
    policies: List[LifecyclePolicy] = []
    plugins: Dict[str, List[str]] = {}
    queue: str = ""
    maxRetry: int = 3
    ttlSecondsAfterFinished: Optional[int]
    priorityClassName: str = ""


class JobPhase(KubeEnum):
    Pending = "Pending"
    Aborting = "Aborting"
    Aborted = "Aborted"
    Running = "Running"
    Restarting = "Restarting"
    Completing = "Completing"
    Completed = "Completed"
    Terminating = "Terminating"
    Terminated = "Terminated"
    Failed = "Failed"


class JobState(KubeModel):
    phase: Optional[JobPhase]
    reason: str = ""
    message: str = ""
    lastTransitionTime: datetime = DefaultDatetime


class JobEvent(KubeEnum):
    CommandIssued = "CommandIssued"
    PluginError = "PluginError"
    PVCError = "PVCError"
    PodGroupError = "PodGroupError"
    ExecuteAction = "ExecuteAction"
    JobStatusError = "JobStatusError"


class JobStatus(KubeModel):
    state: Optional[JobState]
    minAvailable: int = 0
    pending: int = 0
    running: int = 0
    succeeded: int = 0
    failed: int = 0
    terminating: int = 0
    unknown: int = 0
    version: int = 0
    retryCount: int = 0
    controlledResources: Dict[str, str] = {}


class Job(TypeMeta, KubeModel):
    metadata: ObjectMeta = ObjectMeta()
    spec: JobSpec = JobSpec()
    status: JobStatus = JobStatus()


class JobList(TypeMeta):
    metadata: ListMeta = ListMeta()
    items: List[Job] = []
