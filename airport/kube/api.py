from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Union
from uuid import UUID

from pydantic import BaseModel
from pydantic.fields import Field


class KubeModel(BaseModel):
    ...


class KubeEnum(str, Enum):
    ...


ResourceQuantity = Decimal


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


class PersistentVolumeAccessMode(KubeEnum):
    ReadWriteOnce = "ReadWriteOnce"
    ReadOnlyMany = "ReadOnlyMany"
    ReadWriteMany = "ReadWriteMany"


class PersistentVolumeMode(KubeEnum):
    Block = "Block"
    Filesystem = "Filesystem"


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
    limits: Optional[ResourceList] = {}
    requests: Optional[ResourceList] = {}


class TypedLocalObjectReference(KubeModel):
    kind: str
    name: str
    apiGroup: Optional[str]


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


class PersistentVolumeClaim(TypeMeta, ObjectMeta):
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
    medium: Optional[StorageMedium]
    sizeLimit: Optional[Decimal]


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


class ContainerPort(KubeModel):
    name: Optional[str]
    hostPort: Optional[int] = Field(..., gt=0, lt=65536)
    containerPort: Optional[int] = Field(..., gt=0, lt=65536)
    protocol: Literal["TCP", "UDP", "SCTP"] = "TCP"
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


class VolumeMount(KubeModel):
    name: str
    mountPath: str
    subPath: str = ""
    readOnly: bool = False
    mountPropagation: Literal["None", "HostToContainer", "Bidirectional"] = "None"
    subPathExpr: str = ""


class VolumeDevice(KubeModel):
    name: str
    devicePath: str


class ExecAction(KubeModel):
    command: List[str] = []


class HttpHeader(KubeModel):
    name: str
    value: str


class HTTPGetAction(KubeModel):
    path: Optional[str]
    port: Union[int, str]
    host: Optional[str]
    httpSchema: Literal["HTTP", "HTTPS"] = Field("HTTP", alias="schema")
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
    procMount: Literal["Default", "Unmasked"] = "Default"


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


class RestartPolicy(KubeEnum):
    Always = "Always"
    OnFailure = "OnFailure"
    Never = "Never"


class DNSPolicy(KubeEnum):
    ClusterFirstWithHostNet = "ClusterFirstWithHostNet"
    ClusterFirst = "ClusterFirst"
    Default = "Default"
    DnsNone = "None"


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


class PodSpec(KubeModel):
    volumes: List[Volume] = []
    initContainers: List[Container] = []
    ephemeralContainers: List[EphemeralContainer] = []
    restartPolicy: Optional[RestartPolicy]
    terminationGracePeriodSeconds: int = 30
    activeDeadlineSeconds: Optional[int]
    dnsPolicy: DNSPolicy


class PodTemplateSpec(ObjectMeta):
    spec: Optional[PodSpec]
