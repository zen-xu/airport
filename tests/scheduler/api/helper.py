from typing import Dict
from typing import List

from airport.kube.api import Node
from airport.kube.api import OwnerReference
from airport.kube.api import Pod
from airport.kube.api import PodPhase
from airport.kube.api import ResourceList


def build_node(name: str, alloc: ResourceList) -> Node:
    return Node.parse_obj(
        {
            "metadata": {"name": name},
            "status": {"capacity": alloc, "allocatable": alloc},
        }
    )


def build_pod(
    namespace: str,
    name: str,
    node: str,
    phase: PodPhase,
    req: ResourceList,
    owner: List[OwnerReference] = None,
    labels: Dict[str, str] = None,
) -> Pod:
    return Pod.parse_obj(
        {
            "metadata": {
                "uid": f"{namespace}/{name}",
                "name": name,
                "namespace": namespace,
                "ownerReferences": owner or [],
                "labels": labels or {},
            },
            "status": {"phase": phase, "qosClass": "Guaranteed"},
            "spec": {
                "nodeName": node,
                "containers": [{"resources": {"requests": req}}],
            },
        }
    )
