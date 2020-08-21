from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic.fields import Field


class KubeModel(BaseModel):
    pass


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
