from enum import IntEnum
from enum import auto


class TaskStatus(IntEnum):
    Pending = auto()
    Allocated = auto()
    Pipelined = auto()
    Binding = auto()
    Bound = auto()
    Running = auto()
    Releasing = auto()
    Succeeded = auto()
    Failed = auto()
    Unknown = auto()

    def is_allocated(self):
        return self in [
            TaskStatus.Bound,
            TaskStatus.Binding,
            TaskStatus.Running,
            TaskStatus.Allocated,
        ]
