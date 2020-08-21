from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional

from pydantic.fields import Field

from airport.kube.api import KubeEnum
from airport.kube.api import KubeModel
from airport.kube.api import ObjectMeta
from airport.kube.api import PersistentVolumeClaimSpec
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
    mountPath: str
    volumeClaimName: Optional[str]
    volumeClaim: Optional[PersistentVolumeClaimSpec]


class TaskSpec(KubeModel):
    name: Optional[str]
    replicas: Optional[int]
    # template: Optional[PodTemplateSpec]


class LifecyclePolicy(KubeModel):
    action: Optional[Action]
    event: Optional[Event]
    events: List[Event]
    exitCode: Optional[int]
    timeout: Optional[str]


class JobSpec(KubeModel):
    schedulerName: Optional[str]
    minAvailable: Optional[int]
    volumes: List[VolumeSpec] = Field(default_factory=list)
    tasks: List[TaskSpec] = Field(default_factory=list)
    policies: List[LifecyclePolicy] = Field(default_factory=list)
    plugins: Dict[str, List[str]] = Field(default=dict)
    queue: Optional[str]
    maxRetry: int = 3
    ttlSecondsAfterFinished: Optional[int]
    priorityClassName: Optional[str]


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
    reason: Optional[str]
    message: Optional[str]
    lastTransitionTime: Optional[datetime]


class JobEvent(KubeEnum):
    CommandIssued = "CommandIssued"
    PluginError = "PluginError"
    PVCError = "PVCError"
    PodGroupError = "PodGroupError"
    ExecuteAction = "ExecuteAction"
    JobStatusError = "JobStatusError"


class JobStatus(KubeModel):
    state: Optional[JobState]
    minAvailable: Optional[int]
    pending: Optional[int]
    running: Optional[int]
    succeeded: Optional[int]
    failed: Optional[int]
    terminating: Optional[int]
    unknown: Optional[int]
    version: Optional[int]
    retryCount: Optional[int]
    controlledResources: Dict[str, str]


class Job(TypeMeta, ObjectMeta):
    spec: JobSpec
    status: JobStatus
