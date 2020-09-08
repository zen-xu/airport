from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel

from airport.kube.api import ConditionStatus
from airport.kube.api import Node
from airport.kube.api import NodeConditionType
from airport.kube.api import Pod
from airport.logger import logger

from .enums import NodePhase
from .enums import TaskStatus
from .job_info import TaskInfo
from .resource_info import Resource


class NodeState(BaseModel):
    phase: NodePhase
    reason: str = ""


class NodeException(Exception):
    ...


class NodeNotReady(NodeException):
    ...


class AddTaskFailed(NodeException):
    ...


class RemoveTaskFailed(NodeException):
    ...


class NodeInfo(BaseModel):
    name: str = ""
    node: Optional[Node]
    state: NodeState = NodeState(phase=NodePhase.NotReady)
    releasing: Resource = Resource()
    pipelined: Resource = Resource()
    idle: Resource = Resource()
    used: Resource = Resource()
    allocatable: Resource = Resource()
    capability: Resource = Resource()
    tasks: Dict[str, TaskInfo] = {}
    others: Dict[str, Any] = {}

    @property
    def ready(self) -> bool:
        return self.state.phase == NodePhase.Ready

    @property
    def pods(self) -> List[Pod]:
        return [task.pod for task in self.tasks.values()]

    @classmethod
    def new(cls, node: Optional[Node] = None) -> "NodeInfo":
        if node is None:
            node_info = NodeInfo()
        else:
            node_info = NodeInfo(
                name=node.metadata.name,
                node=node,
                idle=Resource.new(node.status.allocatable),
                allocatable=Resource.new(node.status.allocatable),
                capability=Resource.new(node.status.capacity),
            )

        node_info.set_node_state(node)
        return node_info

    def set_node_state(self, node: Optional[Node]):
        if node is None:
            self.state = NodeState(phase=NodePhase.NotReady, reason="UnInitialized")
            return

        if self.used > Resource.new(node.status.allocatable):
            self.state = NodeState(phase=NodePhase.NotReady, reason="OutOfSync")
            return

        for cond in node.status.conditions:
            if (
                cond.type == NodeConditionType.Ready
                and cond.status != ConditionStatus.ConditionTrue
            ):
                self.state = NodeState(phase=NodePhase.NotReady, reason="NotReady")
                return

        self.state = NodeState(phase=NodePhase.Ready)

    def set_node(self, node: Optional[Node]):
        self.set_node_state(node)

        if not self.ready or node is None:
            logger.warn(
                f"failed to set node info, phase: {self.state.phase}, reason {self.state.reason}"
            )
            return

        self.name = node.metadata.name
        self.node = node

        self.allocatable = Resource.new(node.status.allocatable)
        self.capability = Resource.new(node.status.capacity)
        self.releasing = Resource()
        self.pipelined = Resource()
        self.idle = Resource.new(node.status.allocatable)
        self.used = Resource()

        for task in self.tasks.values():
            if task.status == TaskStatus.Releasing:
                self.idle -= task.resource_requests
                self.releasing += task.resource_requests
                self.used += task.resource_requests
            elif task.status == TaskStatus.Pipelined:
                self.pipelined += task.resource_requests
            else:
                # default
                self.idle -= task.resource_requests
                self.used += task.resource_requests

    def allocate_idle_resource(self, task: TaskInfo):
        """
        :except NodeNotReady
        """
        if task.resource_requests <= self.idle:
            self.idle -= task.resource_requests
        else:
            raise NodeNotReady(f"selected node <{self.name}> NotReady")

    def add_task(self, task: TaskInfo):
        """
        :except AddTaskFailed
        :except NodeNotReady
        """
        if task.node_name and self.name and self.name != task.node_name:
            raise AddTaskFailed(
                f"task <{task.namespace}/{task.name}> already on different node <{task.node_name}>"
            )

        key = gen_pod_key(task.pod)
        if key in self.tasks:
            raise AddTaskFailed(
                f"task <{task.namespace}/{task.name}> already on node <{self.name}>"
            )

        if self.node is not None:
            if task.status == TaskStatus.Releasing:
                self.allocate_idle_resource(task)
                self.releasing += task.resource_requests
                self.used += task.resource_requests
            elif task.status == TaskStatus.Pipelined:
                self.pipelined += task.resource_requests
            else:
                # default
                self.allocate_idle_resource(task)
                self.used += task.resource_requests

        # Node will hold a copy of task to make sure the status
        # change will not impact resource in node.
        task_copy: TaskInfo = task.copy(deep=True)
        task.node_name = task_copy.node_name = self.name
        self.tasks[key] = task_copy

    def remove_task(self, task: TaskInfo):
        """
        :except RemoveTaskFailed
        """
        key = gen_pod_key(task.pod)
        if key not in self.tasks:
            raise RemoveTaskFailed(
                f"failed to find task <{task.namespace}/{task.name}> on host <{self.name}>"
            )

        if self.node is not None:
            if task.status == TaskStatus.Releasing:
                self.releasing -= task.resource_requests
                self.idle += task.resource_requests
                self.used -= task.resource_requests
            elif task.status == TaskStatus.Pipelined:
                self.pipelined -= task.resource_requests
            else:
                # default
                self.idle += task.resource_requests
                self.used -= task.resource_requests

        self.tasks.pop(key)

    def update_task(self, task: TaskInfo):
        """
        :except RemoveTaskFailed
        """
        self.remove_task(task)

        try:
            self.add_task(task)
        except NodeException as e:
            logger.fatal(
                f"failed to add task <{task.namespace}/{task.name}> to node <{self.name}> during task update: {e}"
            )

    def __str__(self):
        if self.node:
            return f"Node ({self.name}): idle <{self.idle}>, used <{self.used}>, releasing <{self.releasing}>, state <phase {self.state.phase}, reason '{self.state.reason}'>, taints <{self.node.spec.taint}>"
        else:
            return "EmptyNode"


def gen_pod_key(pod: Pod) -> str:
    return f"{pod.metadata.namespace}/{pod.metadata.name}"
