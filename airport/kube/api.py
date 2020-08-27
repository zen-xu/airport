from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from uuid import UUID

from kubernetes.utils.quantity import parse_quantity
from pydantic import BaseModel
from pydantic.fields import Field


class KubeModel(BaseModel):
    ...


class KubeEnum(str, Enum):
    ...


class _ResourceQuantityMeta(type):
    def __new__(mcs, name, bases, attrs):
        def wrap(op):  # noqa
            method_name = f"__{op}__"

            def method(self, *args, **kwargs):
                result = getattr(Decimal, method_name)(self, *args, **kwargs)
                return self.__class__(result)

            method.__name__ = method_name
            return method

        for op in [
            "add",
            "sub",
            "mul",
            "truediv",
            "floordiv",
            "mod",
            "pow",
            "neg",
            "abs",
        ]:
            attrs[f"__{op}__"] = wrap(op)

        def __divmod__(self, v):
            quotient, remainder = Decimal.__divmod__(self, v)
            return self.__class__(quotient), self.__class__(remainder)

        attrs["__divmod__"] = __divmod__
        return super().__new__(mcs, name, bases, attrs)


class ResourceQuantity(Decimal, metaclass=_ResourceQuantityMeta):
    def __new__(cls, quantity: Union[str, float, Decimal]):
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


class TypeMeta(KubeModel):
    kind: Optional[str]
    apiVersion: Optional[str]


class OwnerReference(KubeModel):
    apiVersion: str
    kind: str
    name: str
    uid: UUID
    controller: Optional[bool]
    blockOwnerDeletion: bool = False


class ListMeta(KubeModel):
    selfLink: Optional[str]
    resourceVersion: Optional[str]
    continue_value: str = Field(..., alias="continue")
    remainingItemCount: Optional[int]


class LocalObjectReference(KubeModel):
    name: Optional[str]


class ObjectMeta(KubeModel):
    name: Optional[str]
    generateName: Optional[str]
    namespace: Optional[str]
    selfLink: Optional[str]
    uid: Optional[UUID]
    resourceVersion: Optional[str]
    generation: Optional[int]
    creationTimestamp: Optional[datetime]
    deletionTimestamp: Optional[datetime]
    deletionGracePeriodSeconds: Optional[int]
    labels: Dict[str, str] = {}
    annotations: Dict[str, str] = {}
    ownerReferences: List[OwnerReference] = []
    finalizers: List[str] = []
    clusterName: Optional[str]
    # managedFields not needed


class LabelSelectorOperator(KubeEnum):
    In = "In"
    NotIn = "NotIn"
    Exists = "Exists"
    DoesNotExist = "DoesNotExist"


class LabelSelectorRequirement(KubeModel):
    key: str
    operator: LabelSelectorOperator
    values: List[str] = []


class LabelSelector(KubeModel):
    matchLabels: Dict[str, str] = {}
    matchExpressions: List[LabelSelectorRequirement] = []


class ResourceName(KubeEnum):
    CPU = "cpu"
    Memory = "memory"
    Storage = "storage"
    EphemeralStorage = "ephemeral-storage"


ResourceList = Dict[ResourceName, ResourceQuantity]


class ResourceRequirements(KubeModel):
    limits: ResourceList = {}
    requests: ResourceList = {}


class TypedLocalObjectReference(KubeModel):
    kind: str
    name: str
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
    resources: Optional[ResourceRequirements]
    volumeName: Optional[str]
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


class PersistentVolumeClaim(TypeMeta):
    metadata: ObjectMeta
    spec: Optional[PersistentVolumeClaimSpec]
    status: Optional[PersistentVolumeClaimStatus]


class KeyToPath(KubeModel):
    key: str
    path: str
    mode: Optional[int] = Field(..., ge=0, le=0o777)


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
    path: str
    type: HostPathType = HostPathType.Unset


class StorageMedium(KubeEnum):
    Default = ""
    Memory = "Memory"
    HugePages = "HugePages"


class EmptyDirVolumeSource(KubeModel):
    medium: StorageMedium = StorageMedium.Default
    sizeLimit: Optional[ResourceQuantity]


class SecretVolumeSource(KubeModel):
    secretName: Optional[str]
    items: List[KeyToPath] = []
    defaultMode: Optional[int] = 0o0644
    optional: Optional[bool]


class ConfigMapVolumeSource(LocalObjectReference):
    items: List[KeyToPath]
    defaultMode: Optional[int] = 0o0644
    optional: Optional[bool]


class CSIVolumeSource(KubeModel):
    driver: str
    readOnly: bool = False
    fsType: Optional[str]
    volumeAttributes: Dict[str, str] = {}
    nodePublishSecretRef: Optional[LocalObjectReference]


class VolumeSource(KubeModel):
    hostPath: Optional[HostPathVolumeSource]
    emptyDIr: Optional[EmptyDirVolumeSource]
    secret: Optional[SecretVolumeSource]
    persistentVolumeClaim: Optional[PersistentVolumeClaim]
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
    name: str


class Protocol(KubeEnum):
    TCP = "TCP"
    UDP = "UDP"
    SCTP = "SCTP"


class ContainerPort(KubeModel):
    name: Optional[str]
    hostPort: Optional[int] = Field(..., gt=0, lt=65536)
    containerPort: Optional[int] = Field(..., gt=0, lt=65536)
    protocol: Protocol = Protocol.TCP
    hostIP: Optional[str]


class ConfigMapEnvSource(LocalObjectReference):
    optional: Optional[bool]


class SecretEnvSource(LocalObjectReference):
    optional: Optional[bool]


class EnvFromSource(KubeModel):
    prefix: str
    configMapRef: Optional[ConfigMapEnvSource]
    secretRef: Optional[SecretEnvSource]


class ObjectFieldSelector(KubeModel):
    apiVersion: Optional[str]
    fieldPath: str


class ResourceFieldSelector(KubeModel):
    containerName: Optional[str]
    resource: str
    divisor: ResourceQuantity


class ConfigMapKeySelector(LocalObjectReference):
    key: str
    optional: Optional[bool]


class SecretKeySelector(LocalObjectReference):
    key: str
    optional: Optional[bool]


class EnvVarSource(KubeModel):
    fieldRef: Optional[ObjectFieldSelector]
    resourceFieldRef: Optional[ResourceFieldSelector]
    configMapKeyRef: Optional[ConfigMapKeySelector]
    secretKeyRef: Optional[SecretKeySelector]


class EnvVar(KubeModel):
    name: str
    value: str = ""
    valueFrom: Optional[EnvVarSource]


class MountPropagationMode(KubeEnum):
    NoneMode = "None"
    HostToContainer = "HostToContainer"
    Bidirectional = "Bidirectional"


class VolumeMount(KubeModel):
    name: str
    mountPath: str
    subPath: str = ""
    readOnly: bool = False
    mountPropagation: MountPropagationMode = MountPropagationMode.NoneMode
    subPathExpr: str = ""


class VolumeDevice(KubeModel):
    name: str
    devicePath: str


class ExecAction(KubeModel):
    command: List[str] = []


class HttpHeader(KubeModel):
    name: str
    value: str


class URIScheme(KubeEnum):
    HTTP = "HTTP"
    HTTPS = "HTTPS"


class HTTPGetAction(KubeModel):
    path: Optional[str]
    port: Union[int, str]
    host: Optional[str]
    uriSchema: URIScheme = Field(URIScheme.HTTP, alias="schema")
    httpHeaders: List[HttpHeader] = []


class TCPSocketAction(KubeModel):
    port: Union[str, int]
    host: Optional[str]


class Handler(KubeModel):
    exec: Optional[ExecAction]
    httpGet: Optional[HTTPGetAction]
    tcpSocket: Optional[TCPSocketAction]


class Probe(Handler):
    initialDelaySeconds: Optional[int]
    timeoutSeconds: int = 1
    periodSeconds: int = 10
    successThreshold: int = 1
    failureThreshold: int = 3


Capability = str


class Capabilities(KubeModel):
    add: List[Capability] = []
    drop: List[Capability] = []


class SELinuxOptions(KubeModel):
    user: Optional[str]
    role: Optional[str]
    type: Optional[str]
    level: Optional[str]


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
    name: str
    image: str
    command: List[str] = []
    args: List[str] = []
    workingDir: Optional[str]
    ports: List[ContainerPort] = []
    envFrom: List[EnvFromSource] = []
    env: List[EnvVar] = []
    resources: ResourceRequirements
    volumeMounts: List[VolumeMount] = []
    volumeDevices: List[VolumeDevice] = []
    livenessProbe: Optional[Probe]
    readinessProbe: Optional[Probe]
    startupProbe: Optional[Probe]
    lifecycle: Optional[Lifecycle]
    terminationMessagePath: Optional[str]
    terminationMessagePolicy: TerminationMessagePolicy = TerminationMessagePolicy.File
    imagePullPolicy: PullPolicy = PullPolicy.Always
    securityContext: Optional[SecurityContext]
    stdin: bool = False
    stdinOnce: bool = False
    tty: bool = False


class EphemeralContainer(EphemeralContainerCommon):
    targetContainerName: Optional[str]


class Container(KubeModel):
    name: str
    image: Optional[str]
    command: List[str] = []
    args: List[str] = []
    workingDir: Optional[str]
    ports: List[ContainerPort] = []
    envFrom: List[EnvFromSource] = []
    env: List[EnvVar] = []
    resources: Optional[ResourceRequirements]
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
    name: str
    value: str


class PodSecurityContext(KubeModel):
    seLinuxOptions: Optional[SELinuxOptions]
    windowsOptions: Optional[WindowsSecurityContextOptions]
    runAsUser: Optional[int]
    runAsGroup: Optional[int]
    runAsRoot: Optional[bool]
    supplementalGroups: List[int] = []
    fsGroup: Optional[int]
    sysctls: List[Sysctl]


class NodeSelectorOperator(KubeEnum):
    In = "In"
    NotIn = "NotIN"
    Exists = "Exists"
    DoesNotExist = "DoesNotExist"
    Gt = "Gt"
    Lt = "Lt"


class NodeSelectorRequirement(KubeModel):
    key: str
    operator: NodeSelectorOperator
    values: List[str] = []


class NodeSelectorTerm(KubeModel):
    matchExpressions: List[NodeSelectorRequirement] = []
    matchFields: List[NodeSelectorRequirement] = []


class NodeSelector(KubeModel):
    nodeSelectorTerms: List[NodeSelectorTerm] = []


class PreferredSchedulingTerm(KubeModel):
    weight: int = Field(..., ge=1, le=100)
    preference: NodeSelectorTerm


class NodeAffinity(KubeModel):
    requiredDuringSchedulingIgnoredDuringExecution: Optional[NodeSelector]
    preferredDuringSchedulingIgnoredDuringExecution: List[PreferredSchedulingTerm] = []


class PodAffinityTerm(KubeModel):
    labelSelector: Optional[LabelSelector]
    namespaces: List[str] = []
    topologyKey: str


class WeightedPodAffinityTerm(KubeModel):
    weight: int = Field(..., ge=1, le=100)
    podAffinityTerm: PodAffinityTerm


class PodAffinity(KubeModel):
    requiredDuringSchedulingIgnoredDuringExecution: Optional[PodAffinityTerm]
    preferredDuringSchedulingIgnoredDuringExecution: Optional[WeightedPodAffinityTerm]


class PodAntiAffinity(KubeModel):
    requiredDuringSchedulingIgnoredDuringExecution: Optional[PodAffinityTerm]
    preferredDuringSchedulingIgnoredDuringExecution: Optional[WeightedPodAffinityTerm]


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
    key: Optional[str]
    operator: Optional[TolerationOperator]
    value: Optional[str]
    effect: Optional[TaintEffect]
    tolerationSeconds: Optional[int]


class HostAlias(KubeModel):
    ip: str
    hostnames: List[str] = []


class PodDNSConfigOption(KubeModel):
    name: str
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
    type: PodConditionType
    status: ConditionStatus
    lastProbeTime: Optional[datetime]
    lastTransitionTime: Optional[datetime]
    reason: Optional[str]
    message: Optional[str]


class PodReadinessGate(KubeModel):
    conditionType: PodConditionType


class UnsatisfiableConstraintAction(KubeEnum):
    DoNotSchedule = "DoNotSchedule"
    ScheduleAnyway = "ScheduleAnyway"


class TopologySpreadConstraint(KubeModel):
    maxSkew: int
    topologyKey: str
    whenUnsatisfiable: UnsatisfiableConstraintAction
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
    serviceAccountName: Optional[str]
    serviceAccount: Optional[str]
    automountServiceAccountToken: Optional[bool]
    nodeName: Optional[str]
    hostNetwork: Optional[bool]
    hostPID: Optional[bool]
    hostIPC: Optional[bool]
    shareProcessNamespace: Optional[bool]
    securityContext: Optional[PodSecurityContext]
    imagePullSecrets: List[LocalObjectReference] = []
    hostname: Optional[str]
    subdomain: Optional[str]
    affinity: Optional[Affinity]
    schedulerName: Optional[str]
    tolerations: List[Toleration] = []
    hostAliases: List[HostAlias] = []
    priorityClassName: Optional[str]
    priority: Optional[int]
    dnsConfig: Optional[PodDNSConfig]
    readinessGates: List[PodReadinessGate] = []
    runtimeClassName: Optional[str]
    enableServiceLinks: Optional[bool]
    preemptionPolicy: Optional[PreemptionPolicy]
    overhead: Optional[ResourceList]
    topologySpreadConstraints: List[TopologySpreadConstraint]


class PodTemplateSpec(KubeModel):
    metadata: ObjectMeta
    spec: Optional[PodSpec]


class PodPhase(KubeEnum):
    Pending = "Pending"
    Running = "Running"
    Succeeded = "Succeeded"
    Failed = "Failed"
    Unknown = "Unknown"


class PodIP(KubeModel):
    ip: str


class ContainerStateWaiting(KubeModel):
    reason: Optional[str]
    message: Optional[str]


class ContainerStateRunning(KubeModel):
    startedAt: Optional[datetime]


class ContainerStateTerminated(KubeModel):
    exitCode: int
    signal: Optional[int]
    reason: Optional[str]
    message: Optional[str]
    startedAt: Optional[datetime]
    finishedAt: Optional[datetime]
    containerID: Optional[str]


class ContainerState(KubeModel):
    waiting: Optional[ContainerStateWaiting]
    running: Optional[ContainerStateRunning]
    terminated: Optional[ContainerStateTerminated]


class ContainerStatus(KubeModel):
    name: str
    state: Optional[ContainerState]
    lastState: Optional[ContainerState]
    ready: bool
    restartCount: int
    image: str
    imageID: str
    containerID: Optional[str]
    started: Optional[bool]


class PodQOSClass(KubeEnum):
    Guaranteed = "Guaranteed"
    Burstable = "Burstable"
    BestEffort = "BestEffort"


class PodStatus(KubeModel):
    phase: Optional[PodPhase]
    conditions: List[PodCondition] = []
    message: Optional[str]
    reason: Optional[str]
    nominatedNodeName: Optional[str]
    hostIP: Optional[str]
    podIP: Optional[str]
    podIPs: List[PodIP] = []
    startTime: Optional[datetime]
    initContainerStatuses: List[ContainerStatus] = []
    containerStatuses: List[ContainerStatus] = []
    qosClass: Optional[PodQOSClass]
    ephemeralContainerStatuses: List[ContainerStatus] = []


class Pod(TypeMeta):
    metadata: Optional[ObjectMeta]
    spec: Optional[PodSpec]
    status: Optional[PodStatus]


class PodList(TypeMeta):
    metadata: Optional[ListMeta]
    items: List[Pod] = []
