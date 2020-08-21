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
