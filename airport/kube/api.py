from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class KubeModel(BaseModel):
    ...


class KubeEnum(str, Enum):
    ...


class TypeMeta(KubeModel):
    kind: Optional[str]
    apiVersion: Optional[str]


class OwnerReference(KubeModel):
    apiVersion: str
    kind: str
    name: str
    uid: Optional[UUID]
    controller: Optional[bool]
    blockOwnerDeletion: Optional[bool]


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


ResourceList = Dict[ResourceName, Decimal]


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
    pass


class HostPathType(KubeModel):
    pass


class HostPathVolumeSource(KubeModel):
    path: str
    type: Optional[HostPathType]


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


class Container(KubeModel):
    pass


class ContainerPort(KubeModel):
    pass


class EnvFromSource(KubeModel):
    pass


class EnvVar(KubeModel):
    pass


class VolumeMount(KubeModel):
    pass


class VolumeDevice(KubeModel):
    pass


class Probe(KubeModel):
    pass


class TerminationMessagePolicy(KubeEnum):
    pass


class PullPolicy(KubeEnum):
    pass


class SecurityContext(KubeModel):
    pass


class Lifecycle(KubeModel):
    pass


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
    volumeDevice: List[VolumeDevice] = []
    livenessProbe: Optional[Probe]
    readinessProbe: Optional[Probe]
    startupProbe: Optional[Probe]
    lifecycle: Optional[Lifecycle]
    terminationMessagePath: Optional[str]
    terminationMessagePolicy: Optional[TerminationMessagePolicy]
    imagePullPolicy: Optional[PullPolicy]
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
