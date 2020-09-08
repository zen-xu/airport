from enum import Enum


class StrEnum(str, Enum):
    ...


class TaskStatus(StrEnum):
    Pending = "Pending"
    Allocated = "Allocated"
    Pipelined = "Pipelined"
    Binding = "Binding"
    Bound = "Bound"
    Running = "Running"
    Releasing = "Releasing"
    Succeeded = "Succeeded"
    Failed = "Failed"
    Unknown = "Unknown"

    def is_allocated(self):
        return self in [
            TaskStatus.Bound,
            TaskStatus.Binding,
            TaskStatus.Running,
            TaskStatus.Allocated,
        ]


class NodePhase(StrEnum):
    Ready = "Ready"
    NotReady = "NotReady"
