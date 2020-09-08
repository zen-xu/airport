import pytest

from airport.kube.api import Node
from airport.kube.api import PodPhase
from airport.scheduler.api import NodeInfo
from airport.scheduler.api import Resource
from airport.scheduler.api import TaskInfo
from airport.scheduler.api import TaskStatus
from airport.scheduler.api.node_info import NodeNotReady
from airport.scheduler.api.node_info import NodeState

from .helper import build_node
from .helper import build_pod


parametrize = pytest.mark.parametrize


def test_add_non_owner_pod():
    node = build_node("n1", {"cpu": "8000m", "memory": "10G"})
    pod1 = build_pod(
        "c1", "p1", "n1", PodPhase.Running, {"cpu": "1000m", "memory": "1G"},
    )
    pod2 = build_pod(
        "c1", "p2", "n1", PodPhase.Running, {"cpu": "2000m", "memory": "2G"},
    )
    node_info = NodeInfo.new(node)
    for pod in [pod1, pod2]:
        task = TaskInfo.new(pod)
        node_info.add_task(task)

    assert node_info == NodeInfo(
        name="n1",
        node=node,
        idle=Resource.new({"cpu": "5000m", "memory": "7G"}),
        used=Resource.new({"cpu": "3000m", "memory": "3G"}),
        releasing=Resource(),
        pipelined=Resource(),
        allocatable=Resource.new({"cpu": "8000m", "memory": "10G"}),
        capability=Resource.new({"cpu": "8000m", "memory": "10G"}),
        state={"phase": "Ready"},
        tasks={"c1/p1": TaskInfo.new(pod1), "c1/p2": TaskInfo.new(pod2)},
    )


def test_add_unknown_pod():
    node = build_node("n1", {"cpu": "2000m", "memory": "1G"})
    pod = build_pod(
        "c1", "p1", "n1", PodPhase.Unknown, {"cpu": "1000m", "memory": "2G"}
    )
    node_info = NodeInfo.new(node)
    with pytest.raises(NodeNotReady):
        node_info.add_task(TaskInfo.new(pod))

    assert node_info == NodeInfo(
        name="n1",
        node=node,
        idle=Resource.new({"cpu": "2000m", "memory": "1G"}),
        used=Resource(),
        releasing=Resource(),
        pipelined=Resource(),
        allocatable=Resource.new({"cpu": "2000m", "memory": "1G"}),
        capability=Resource.new({"cpu": "2000m", "memory": "1G"}),
        state={"phase": "Ready"},
        tasks={},
    )


def test_add_releasing_pod():
    node = build_node("n1", {"cpu": "5000m", "memory": "8G"})
    pod = build_pod(
        "c1", "p1", "n1", PodPhase.Running, {"cpu": "1000m", "memory": "2G"}
    )
    pod.metadata.deletionTimestamp = "2020-01-01"
    node_info = NodeInfo.new(node)
    node_info.add_task(TaskInfo.new(pod))

    assert node_info == NodeInfo(
        name="n1",
        node=node,
        idle=Resource.new({"cpu": "4000m", "memory": "6G"}),
        used=Resource.new({"cpu": "1000m", "memory": "2G"}),
        releasing=Resource.new({"cpu": "1000m", "memory": "2G"}),
        pipelined=Resource(),
        allocatable=Resource.new({"cpu": "5000m", "memory": "8G"}),
        capability=Resource.new({"cpu": "5000m", "memory": "8G"}),
        state={"phase": "Ready"},
        tasks={"c1/p1": TaskInfo.new(pod)},
    )


def test_add_pipelined_pod():
    node = build_node("n1", {"cpu": "5000m", "memory": "8G"})
    pod = build_pod(
        "c1", "p1", "n1", PodPhase.Running, {"cpu": "1000m", "memory": "2G"}
    )
    pod.metadata.deletionTimestamp = "2020-01-01"
    node_info = NodeInfo.new(node)
    task = TaskInfo.new(pod)
    task.status = TaskStatus.Pipelined
    node_info.add_task(task)

    assert node_info == NodeInfo(
        name="n1",
        node=node,
        idle=Resource.new({"cpu": "5000m", "memory": "8G"}),
        used=Resource(),
        releasing=Resource(),
        pipelined=Resource.new({"cpu": "1000m", "memory": "2G"}),
        allocatable=Resource.new({"cpu": "5000m", "memory": "8G"}),
        capability=Resource.new({"cpu": "5000m", "memory": "8G"}),
        state={"phase": "Ready"},
        tasks={"c1/p1": task},
    )


def test_remove_pod():
    node = build_node("n1", {"cpu": "8000m", "memory": "10G"})
    pod1 = build_pod(
        "c1", "p1", "n1", PodPhase.Running, {"cpu": "1000m", "memory": "1G"}
    )
    pod2 = build_pod(
        "c1", "p2", "n1", PodPhase.Running, {"cpu": "2000m", "memory": "2G"}
    )
    pod3 = build_pod(
        "c1", "p3", "n1", PodPhase.Running, {"cpu": "3000m", "memory": "3G"}
    )

    node_info = NodeInfo.new(node)
    for pod in [pod1, pod2, pod3]:
        task = TaskInfo.new(pod)
        node_info.add_task(task)

    node_info.remove_task(TaskInfo.new(pod2))

    assert node_info == NodeInfo(
        name="n1",
        node=node,
        idle=Resource.new({"cpu": "4000m", "memory": "6G"}),
        used=Resource.new({"cpu": "4000m", "memory": "4G"}),
        releasing=Resource(),
        pipelined=Resource(),
        allocatable=Resource.new({"cpu": "8000m", "memory": "10G"}),
        capability=Resource.new({"cpu": "8000m", "memory": "10G"}),
        state={"phase": "Ready"},
        tasks={"c1/p1": TaskInfo.new(pod1), "c1/p3": TaskInfo.new(pod3),},
    )


@parametrize(
    "node_info,node,expected_state",
    [
        (NodeInfo(), None, NodeState(phase="NotReady", reason="UnInitialized"),),
        (
            NodeInfo(used=Resource.new({"cpu": "1000m", "memory": "2G"}),),
            Node(status={"allocatable": {"cpu": "500m", "memory": "1G"}}),
            NodeState(phase="NotReady", reason="OutOfSync"),
        ),
        (
            NodeInfo(),
            Node(status={"conditions": [{"type": "Ready", "status": "False"}]}),
            NodeState(phase="NotReady", reason="NotReady"),
        ),
    ],
)
def test_set_node_state(node_info: NodeInfo, node: Node, expected_state: NodeState):
    node_info.set_node_state(node)
    assert node_info.state == expected_state


def test_set_node():
    node = build_node("n1", {"cpu": "8000m", "memory": "10G"})
    pod1 = build_pod(
        "c1", "p1", "n1", PodPhase.Running, {"cpu": "1000m", "memory": "1G"},
    )
    pod2 = build_pod(
        "c1", "p2", "n1", PodPhase.Running, {"cpu": "2000m", "memory": "2G"},
    )
    node_info = NodeInfo.new(node)
    node_info.add_task(TaskInfo.new(pod1))
    node_info.add_task(TaskInfo.new(pod2))

    new_node = build_node("n2", {"cpu": "5000m", "memory": "5G"})
    node_info.set_node(new_node)

    assert node_info == NodeInfo(
        name="n2",
        node=new_node,
        allocatable=Resource.new({"cpu": "5000m", "memory": "5G"}),
        capability=Resource.new({"cpu": "5000m", "memory": "5G"}),
        idle=Resource.new({"cpu": "2000m", "memory": "2G"}),
        used=Resource.new({"cpu": "3000m", "memory": "3G"}),
        state={"phase": "Ready"},
        tasks={"c1/p1": TaskInfo.new(pod1), "c1/p2": TaskInfo.new(pod2)},
    )
