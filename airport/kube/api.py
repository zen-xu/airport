from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from kubernetes.utils.quantity import parse_quantity
from pydantic import BaseModel
from pydantic.fields import Field


DefaultDatetime = datetime.fromtimestamp(0)


class KubeModel(BaseModel):
    ...


class KubeEnum(str, Enum):
    ...


class ResourceQuantity(Decimal):
    def __new__(cls, quantity: Union[str, float, Decimal] = 0) -> "ResourceQuantity":
        quantity = parse_quantity(quantity)
        return super().__new__(cls, quantity)  # noqa

    def __repr__(self):
        return f"{self.__class__.__name__}('{self}')"

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, float]):
        quantity = parse_quantity(v)
        return cls(quantity)  # noqa

    def __add__(self, value) -> "ResourceQuantity":
        return self.__class__(super().__add__(value))  # noqa

    def __sub__(self, value) -> "ResourceQuantity":
        return self.__class__(super().__sub__(value))  # noqa

    def __mul__(self, value) -> "ResourceQuantity":
        return self.__class__(super().__mul__(value))  # noqa

    def __truediv__(self, value) -> "ResourceQuantity":
        return self.__class__(super().__truediv__(value))  # noqa

    def __floordiv__(self, value) -> "ResourceQuantity":
        return self.__class__(super().__floordiv__(value))  # noqa

    def __mod__(self, value) -> "ResourceQuantity":
        return self.__class__(super().__mod__(value))  # noqa

    def __pow__(self, value, mod=None, /) -> "ResourceQuantity":
        return self.__class__(super().__pow__(value, mod))  # noqa

    def __neg__(self) -> "ResourceQuantity":
        return self.__class__(super().__neg__())  # noqa

    def __abs__(self) -> "ResourceQuantity":
        return self.__class__(super().__abs__())  # noqa

    def __divmod__(self, value) -> Tuple["ResourceQuantity", "ResourceQuantity"]:
        quotient, remainder = super().__divmod__(value)
        return self.__class__(quotient), self.__class__(remainder)  # noqa


class TypeMeta(KubeModel):
    kind: str = ""
    apiVersion: str = ""


class OwnerReference(KubeModel):
    apiVersion: str = ""
    kind: str = ""
    name: str = ""
    uid: str = ""
    controller: bool = False
    blockOwnerDeletion: bool = False


class ListMeta(KubeModel):
    selfLink: str = ""
    resourceVersion: str = ""
    continue_value: str = Field("", alias="continue")
    remainingItemCount: Optional[int]


class LocalObjectReference(KubeModel):
    name: str = ""


class ObjectMeta(KubeModel):
    name: str = ""
    generateName: str = ""
    namespace: str = ""
    selfLink: str = ""
    uid: str = ""
    resourceVersion: str = ""
    generation: str = ""
    creationTimestamp: datetime = DefaultDatetime
    deletionTimestamp: Optional[datetime]
    deletionGracePeriodSeconds: Optional[int]
    labels: Dict[str, str] = {}
    annotations: Dict[str, str] = {}
    ownerReferences: List[OwnerReference] = []
    finalizers: List[str] = []
    clusterName: str = ""
    # managedFields not needed


class LabelSelectorOperator(KubeEnum):
    In = "In"
    NotIn = "NotIn"
    Exists = "Exists"
    DoesNotExist = "DoesNotExist"


class LabelSelectorRequirement(KubeModel):
    key: str = ""
    operator: Optional[LabelSelectorOperator]
    values: List[str] = []


class LabelSelector(KubeModel):
    matchLabels: Dict[str, str] = {}
    matchExpressions: List[LabelSelectorRequirement] = []


class ResourceName(KubeEnum):
    CPU = "cpu"
    Memory = "memory"
    Storage = "storage"
    EphemeralStorage = "ephemeral-storage"


ResourceList = Dict[Union[ResourceName, str], ResourceQuantity]


class ResourceRequirements(KubeModel):
    limits: ResourceList = {}
    requests: ResourceList = {}


class TypedLocalObjectReference(KubeModel):
    kind: str = ""
    name: str = ""
    apiGroup: Optional[str]


class PersistentVolumeAccessMode(KubeEnum):
    ReadWriteOnce = "ReadWriteOnce"
    ReadOnlyMany = "ReadOnlyMany"
    ReadWriteMany = "ReadWriteMany"


class PersistentVolumeMode(KubeEnum):
    Block = "Block"
    Filesystem = "Filesystem"


class PersistentVolumeClaimSpec(KubeModel):
    accessModes: List[PersistentVolumeAccessMode] = []
    selector: Optional[LabelSelector]
    resources: ResourceRequirements = ResourceRequirements()
    volumeName: str = ""
    storageClassName: Optional[str]
    volumeMode: Optional[PersistentVolumeMode]
    dataSource: Optional[TypedLocalObjectReference]


class PersistentVolumeClaimPhase(KubeEnum):
    Pending = "Pending"
    Bound = "Bound"
    Lost = "Lost"


class PersistentVolumeClaimCondition(KubeEnum):
    Resizing = "Resizing"
    FileSystemResizePending = "FileSystemResizePending"


class PersistentVolumeClaimStatus(KubeModel):
    phase: Optional[PersistentVolumeClaimPhase]
    accessModes: List[PersistentVolumeAccessMode] = []
    capacity: ResourceList = {}
    conditions: List[PersistentVolumeClaimCondition] = []


class KeyToPath(KubeModel):
    key: str = ""
    path: str = ""
    mode: Optional[int] = Field(None, ge=0, le=0o777)


class HostPathType(KubeEnum):
    Unset = ""
    DirectoryOrCreate = "DirectoryOrCreate"
    Directory = "Directory"
    FileOrCreate = "FileOrCreate"
    File = "File"
    Socket = "Socket"
    CharDevice = "CharDevice"
    BlockDevice = "BlockDevice"


class HostPathVolumeSource(KubeModel):
    path: str = ""
    type: HostPathType = HostPathType.Unset


class StorageMedium(KubeEnum):
    Default = ""
    Memory = "Memory"
    HugePages = "HugePages"


class EmptyDirVolumeSource(KubeModel):
    medium: StorageMedium = StorageMedium.Default
    sizeLimit: Optional[ResourceQuantity]


class SecretVolumeSource(KubeModel):
    secretName: str = ""
    items: List[KeyToPath] = []
    defaultMode: int = 0o0644
    optional: Optional[bool]


class PersistentVolumeClaimVolumeSource(KubeModel):
    claimName: str = ""
    readOnly: bool = False


class ConfigMapVolumeSource(LocalObjectReference):
    items: List[KeyToPath] = []
    defaultMode: int = 0o0644
    optional: Optional[bool]


class CSIVolumeSource(KubeModel):
    driver: str = ""
    readOnly: bool = False
    fsType: Optional[str]
    volumeAttributes: Dict[str, str] = {}
    nodePublishSecretRef: Optional[LocalObjectReference]


class VolumeSource(KubeModel):
    hostPath: Optional[HostPathVolumeSource]
    emptyDIr: Optional[EmptyDirVolumeSource]
    secret: Optional[SecretVolumeSource]
    persistentVolumeClaim: Optional[PersistentVolumeClaimVolumeSource]
    configMap: Optional[ConfigMapVolumeSource]
    csi: Optional[CSIVolumeSource]
    # Unsupported
    # --------------------
    # GCEPersistentDisk
    # AWSElasticBlockStore
    # GitRepo
    # NFS
    # ISCSI
    # Glusterfs
    # RBD
    # FlexVolume
    # Cinder
    # CephFS
    # Flocker
    # DownwardAPI
    # FC
    # AzureFile
    # VsphereVolume
    # Quobyte
    # AzureDisk
    # PhotonPersistentDisk
    # Projected
    # PortworxVolume
    # ScaleIO


class Volume(VolumeSource):
    name: str = ""


class Protocol(KubeEnum):
    TCP = "TCP"
    UDP = "UDP"
    SCTP = "SCTP"


class ContainerPort(KubeModel):
    name: str = ""
    hostPort: Optional[int] = Field(None, gt=0, lt=65536)
    containerPort: Optional[int] = Field(None, gt=0, lt=65536)
    protocol: Protocol = Protocol.TCP
    hostIP: str = ""


class ConfigMapEnvSource(LocalObjectReference):
    optional: Optional[bool]


class SecretEnvSource(LocalObjectReference):
    optional: Optional[bool]


class EnvFromSource(KubeModel):
    prefix: str = ""
    configMapRef: Optional[ConfigMapEnvSource]
    secretRef: Optional[SecretEnvSource]


class ObjectFieldSelector(KubeModel):
    apiVersion: str = ""
    fieldPath: str = ""


class ResourceFieldSelector(KubeModel):
    containerName: str = ""
    resource: str = ""
    divisor: ResourceQuantity = ResourceQuantity()


class ConfigMapKeySelector(LocalObjectReference):
    key: str = ""
    optional: Optional[bool]


class SecretKeySelector(LocalObjectReference):
    key: str = ""
    optional: Optional[bool]


class EnvVarSource(KubeModel):
    fieldRef: Optional[ObjectFieldSelector]
    resourceFieldRef: Optional[ResourceFieldSelector]
    configMapKeyRef: Optional[ConfigMapKeySelector]
    secretKeyRef: Optional[SecretKeySelector]


class EnvVar(KubeModel):
    name: str = ""
    value: str = ""
    valueFrom: Optional[EnvVarSource]


class MountPropagationMode(KubeEnum):
    NoneMode = "None"
    HostToContainer = "HostToContainer"
    Bidirectional = "Bidirectional"


class VolumeMount(KubeModel):
    name: str = ""
    readOnly: bool = False
    mountPath: str = ""
    subPath: str = ""
    mountPropagation: MountPropagationMode = MountPropagationMode.NoneMode
    subPathExpr: str = ""


class VolumeDevice(KubeModel):
    name: str = ""
    devicePath: str = ""


class ExecAction(KubeModel):
    command: List[str] = []


class HttpHeader(KubeModel):
    name: str = ""
    value: str = ""


class URIScheme(KubeEnum):
    HTTP = "HTTP"
    HTTPS = "HTTPS"


class HTTPGetAction(KubeModel):
    path: str = ""
    port: Union[int, str] = ""
    host: str = ""
    uriSchema: URIScheme = Field(URIScheme.HTTP, alias="schema")
    httpHeaders: List[HttpHeader] = []


class TCPSocketAction(KubeModel):
    port: Union[str, int] = ""
    host: str = ""


class Handler(KubeModel):
    exec: Optional[ExecAction]
    httpGet: Optional[HTTPGetAction]
    tcpSocket: Optional[TCPSocketAction]


class Probe(Handler):
    initialDelaySeconds: int = 0
    timeoutSeconds: int = 1
    periodSeconds: int = 10
    successThreshold: int = 1
    failureThreshold: int = 3


Capability = str


class Capabilities(KubeModel):
    add: List[Capability] = []
    drop: List[Capability] = []


class SELinuxOptions(KubeModel):
    user: str = ""
    role: str = ""
    type: str = ""
    level: str = ""


class WindowsSecurityContextOptions(KubeModel):
    gmsaCredentialSpecName: Optional[str]
    gmsaCredentialSpec: Optional[str]
    runAsUserName: Optional[str]


class ProcMountType(KubeEnum):
    Default = "Default"
    Unmasked = "Unmasked"


class SecurityContext(KubeModel):
    capabilities: Optional[Capabilities]
    privileged: bool = False
    seLinuxOptions: Optional[SELinuxOptions]
    windowsOptions: Optional[WindowsSecurityContextOptions]
    runAsUser: Optional[int]
    runAsGroup: Optional[int]
    runAsNonRoot: Optional[bool]
    readOnlyRootFilesystem: bool = False
    allowPrivilegeEscalation: Optional[bool]
    procMount: ProcMountType = ProcMountType.Default


class Lifecycle(KubeModel):
    postStart: Optional[Handler]
    preStop: Optional[Handler]


class TerminationMessagePolicy(KubeEnum):
    File = "File"
    FallbackToLogsOnError = "FallbackToLogsOnError"


class PullPolicy(KubeEnum):
    Always = "Always"
    Never = "Never"
    IfNotPresent = "IfNotPresent"


class EphemeralContainerCommon(KubeModel):
    name: str = ""
    image: str = ""
    command: List[str] = []
    args: List[str] = []
    workingDir: str = ""
    ports: List[ContainerPort] = []
    envFrom: List[EnvFromSource] = []
    env: List[EnvVar] = []
    resources: ResourceRequirements = ResourceRequirements()
    volumeMounts: List[VolumeMount] = []
    volumeDevices: List[VolumeDevice] = []
    livenessProbe: Optional[Probe]
    readinessProbe: Optional[Probe]
    startupProbe: Optional[Probe]
    lifecycle: Optional[Lifecycle]
    terminationMessagePath: str = ""
    terminationMessagePolicy: TerminationMessagePolicy = TerminationMessagePolicy.File
    imagePullPolicy: PullPolicy = PullPolicy.Always
    securityContext: Optional[SecurityContext]
    stdin: bool = False
    stdinOnce: bool = False
    tty: bool = False


class EphemeralContainer(EphemeralContainerCommon):
    targetContainerName: str = ""


class Container(KubeModel):
    name: str = ""
    image: str = ""
    command: List[str] = []
    args: List[str] = []
    workingDir: str = ""
    ports: List[ContainerPort] = []
    envFrom: List[EnvFromSource] = []
    env: List[EnvVar] = []
    resources: ResourceRequirements = ResourceRequirements()
    volumeMounts: List[VolumeMount] = []
    volumeDevices: List[VolumeDevice] = []
    livenessProbe: Optional[Probe]
    readinessProbe: Optional[Probe]
    startupProbe: Optional[Probe]
    lifecycle: Optional[Lifecycle]
    terminationMessagePath: str = "/dev/termination-log"
    terminationMessagePolicy: TerminationMessagePolicy = TerminationMessagePolicy.File
    imagePullPolicy: PullPolicy = PullPolicy.Always
    securityContext: Optional[SecurityContext]
    stdin: bool = False
    stdinOnce: bool = False
    tty: bool = False


class Sysctl(KubeModel):
    name: str = ""
    value: str = ""


class PodSecurityContext(KubeModel):
    seLinuxOptions: Optional[SELinuxOptions]
    windowsOptions: Optional[WindowsSecurityContextOptions]
    runAsUser: Optional[int]
    runAsGroup: Optional[int]
    runAsRoot: Optional[bool]
    supplementalGroups: List[int] = []
    fsGroup: Optional[int]
    sysctls: List[Sysctl] = []


class NodeSelectorOperator(KubeEnum):
    In = "In"
    NotIn = "NotIN"
    Exists = "Exists"
    DoesNotExist = "DoesNotExist"
    Gt = "Gt"
    Lt = "Lt"


class NodeSelectorRequirement(KubeModel):
    key: str = ""
    operator: Optional[NodeSelectorOperator]
    values: List[str] = []


class NodeSelectorTerm(KubeModel):
    matchExpressions: List[NodeSelectorRequirement] = []
    matchFields: List[NodeSelectorRequirement] = []


class NodeSelector(KubeModel):
    nodeSelectorTerms: List[NodeSelectorTerm] = []


class PreferredSchedulingTerm(KubeModel):
    weight: int = Field(None, ge=1, le=100)
    preference: NodeSelectorTerm = NodeSelectorTerm()


class NodeAffinity(KubeModel):
    requiredDuringSchedulingIgnoredDuringExecution: Optional[NodeSelector]
    preferredDuringSchedulingIgnoredDuringExecution: List[PreferredSchedulingTerm] = []


class PodAffinityTerm(KubeModel):
    labelSelector: Optional[LabelSelector]
    namespaces: List[str] = []
    topologyKey: str = ""


class WeightedPodAffinityTerm(KubeModel):
    weight: int = Field(None, ge=1, le=100)
    podAffinityTerm: PodAffinityTerm = PodAffinityTerm()


class PodAffinity(KubeModel):
    requiredDuringSchedulingIgnoredDuringExecution: List[PodAffinityTerm] = []
    preferredDuringSchedulingIgnoredDuringExecution: List[WeightedPodAffinityTerm] = []


class PodAntiAffinity(KubeModel):
    requiredDuringSchedulingIgnoredDuringExecution: List[PodAffinityTerm] = []
    preferredDuringSchedulingIgnoredDuringExecution: List[WeightedPodAffinityTerm] = []


class Affinity(KubeModel):
    nodeAffinity: Optional[NodeAffinity]
    podAffinity: Optional[PodAffinity]
    podAntiAffinity: Optional[PodAntiAffinity]


class TolerationOperator(KubeEnum):
    Exists = "Exists"
    Equal = "Equal"


class TaintEffect(KubeEnum):
    NoSchedule = "NoSchedule"
    PreferNoSchedule = "PreferNoSchedule"
    NoExecute = "NoExecute"


class Toleration(KubeModel):
    key: str = ""
    operator: TolerationOperator = TolerationOperator.Equal
    value: str = ""
    effect: Optional[TaintEffect]
    tolerationSeconds: Optional[int]


class HostAlias(KubeModel):
    ip: str = ""
    hostnames: List[str] = []


class PodDNSConfigOption(KubeModel):
    name: str = ""
    value: Optional[str]


class PodDNSConfig(KubeModel):
    nameservers: List[str] = []
    searches: List[str] = []
    options: List[PodDNSConfigOption] = []


class PodConditionType(KubeEnum):
    ContainersReady = "ContainersReady"
    Initialized = "Initialized"
    Ready = "Ready"
    PodScheduled = "PodScheduled"


class ConditionStatus(KubeEnum):
    ConditionTrue = "True"
    ConditionFalse = "False"
    ConditionUnknown = "Unknown"


class PodCondition(KubeModel):
    type: Optional[PodConditionType]
    status: Optional[ConditionStatus]
    lastProbeTime: datetime = DefaultDatetime
    lastTransitionTime: datetime = DefaultDatetime
    reason: str = ""
    message: str = ""


class PodReadinessGate(KubeModel):
    conditionType: Optional[PodConditionType]


class UnsatisfiableConstraintAction(KubeEnum):
    DoNotSchedule = "DoNotSchedule"
    ScheduleAnyway = "ScheduleAnyway"


class TopologySpreadConstraint(KubeModel):
    maxSkew: int = 1
    topologyKey: str = ""
    whenUnsatisfiable: Optional[UnsatisfiableConstraintAction]
    labelSelector: Optional[LabelSelector]


class RestartPolicy(KubeEnum):
    Always = "Always"
    OnFailure = "OnFailure"
    Never = "Never"


class DNSPolicy(KubeEnum):
    ClusterFirstWithHostNet = "ClusterFirstWithHostNet"
    ClusterFirst = "ClusterFirst"
    Default = "Default"
    NonePolicy = "None"


class PreemptionPolicy(KubeEnum):
    PreemptLowerPriority = "PreemptLowerPriority"
    Never = "Never"


class PodSpec(KubeModel):
    volumes: List[Volume] = []
    initContainers: List[Container] = []
    containers: List[Container] = []
    ephemeralContainers: List[EphemeralContainer] = []
    restartPolicy: Optional[RestartPolicy]
    terminationGracePeriodSeconds: int = 30
    activeDeadlineSeconds: Optional[int]
    dnsPolicy: Optional[DNSPolicy]
    serviceAccountName: str = ""
    serviceAccount: str = ""
    automountServiceAccountToken: Optional[bool]
    nodeName: str = ""
    hostNetwork: bool = False
    hostPID: bool = False
    hostIPC: bool = False
    shareProcessNamespace: bool = False
    securityContext: Optional[PodSecurityContext]
    imagePullSecrets: List[LocalObjectReference] = []
    hostname: str = ""
    subdomain: str = ""
    affinity: Optional[Affinity]
    schedulerName: str = ""
    tolerations: List[Toleration] = []
    hostAliases: List[HostAlias] = []
    priorityClassName: str = ""
    priority: Optional[int]
    dnsConfig: Optional[PodDNSConfig]
    readinessGates: List[PodReadinessGate] = []
    runtimeClassName: Optional[str]
    enableServiceLinks: Optional[bool]
    preemptionPolicy: Optional[PreemptionPolicy]
    overhead: ResourceList = {}
    topologySpreadConstraints: List[TopologySpreadConstraint] = []


class PodTemplateSpec(KubeModel):
    metadata: ObjectMeta = ObjectMeta()
    spec: PodSpec = PodSpec()


class PodPhase(KubeEnum):
    Pending = "Pending"
    Running = "Running"
    Succeeded = "Succeeded"
    Failed = "Failed"
    Unknown = "Unknown"


class PodIP(KubeModel):
    ip: str = ""


class ContainerStateWaiting(KubeModel):
    reason: str = ""
    message: str = ""


class ContainerStateRunning(KubeModel):
    startedAt: datetime = DefaultDatetime


class ContainerStateTerminated(KubeModel):
    exitCode: int = 0
    signal: int = 0
    reason: str = ""
    message: str = ""
    startedAt: datetime = DefaultDatetime
    finishedAt: datetime = DefaultDatetime
    containerID: str = ""


class ContainerState(KubeModel):
    waiting: Optional[ContainerStateWaiting]
    running: Optional[ContainerStateRunning]
    terminated: Optional[ContainerStateTerminated]


class ContainerStatus(KubeModel):
    name: str = ""
    state: ContainerState = ContainerState()
    lastState: ContainerState = ContainerState()
    ready: bool = False
    restartCount: int = 0
    image: str = ""
    imageID: str = ""
    containerID: str = ""
    started: Optional[bool]


class PodQOSClass(KubeEnum):
    Guaranteed = "Guaranteed"
    Burstable = "Burstable"
    BestEffort = "BestEffort"


class PodStatus(KubeModel):
    phase: Optional[PodPhase]
    conditions: List[PodCondition] = []
    message: str = ""
    reason: str = ""
    nominatedNodeName: str = ""
    hostIP: str = ""
    podIP: str = ""
    podIPs: List[PodIP] = []
    startTime: Optional[datetime]
    initContainerStatuses: List[ContainerStatus] = []
    containerStatuses: List[ContainerStatus] = []
    qosClass: Optional[PodQOSClass]
    ephemeralContainerStatuses: List[ContainerStatus] = []


class Pod(TypeMeta, KubeModel):
    metadata: ObjectMeta = ObjectMeta()
    spec: PodSpec = PodSpec()
    status: PodStatus = PodStatus()


class PodList(TypeMeta, KubeModel):
    metadata: Optional[ListMeta]
    items: List[Pod] = []


class ResourceQuotaScope(KubeEnum):
    Terminating = "Terminating"
    NotTerminating = "NotTerminating"
    BestEffort = "BestEffort"
    NotBestEffort = "NotBestEffort"
    PriorityClass = "PriorityClass"


class ScopeSelectorOperator(KubeEnum):
    In = "In"
    NotIn = "NotIn"
    Exists = "Exists"
    DoesNotExist = "DoesNotExist"


class ScopedResourceSelectorRequirement(KubeModel):
    scopeName: Optional[ResourceQuotaScope]
    operator: Optional[ScopeSelectorOperator]
    values: List[str] = []


class ScopeSelector(KubeModel):
    matchExpressions: List[ScopedResourceSelectorRequirement] = []


class ResourceQuotaSpec(KubeModel):
    hard: ResourceList = {}
    scopes: List[ResourceQuotaScope] = []
    scopeSelector: Optional[ScopeSelector]


class ResourceQuotaStatus(KubeModel):
    hard: ResourceList = {}
    used: ResourceList = {}


class ResourceQuota(TypeMeta, KubeModel):
    metadata: Optional[ObjectMeta] = ObjectMeta()
    spec: ResourceQuotaSpec = ResourceQuotaSpec()
    status: ResourceQuotaStatus = ResourceQuotaStatus()
