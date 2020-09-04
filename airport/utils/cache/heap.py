from dataclasses import dataclass
from dataclasses import field
from threading import Condition
from threading import Lock
from threading import RLock
from typing import Callable
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar

from typing_extensions import Protocol


class HeapError(Exception):
    message: str = ""

    def __init__(self, msg=""):
        msg = msg or self.message
        super().__init__(msg)


class HeapClosed(HeapError):
    message = "heap is closed"


class HeapObjectNotFound(HeapError):
    message = "object not found"


class HeapObjectAlreadyRemoved(HeapError):
    message = "object was removed from heap data"


class HeapKeyFuncError(HeapError):
    ...


class HeapLessFuncError(HeapError):
    ...


T = TypeVar("T")


@dataclass
class HeapItem(Generic[T]):
    obj: T
    index: int


@dataclass
class ItemKeyValue(Generic[T]):
    key: str
    obj: T


KeyFunc = Callable[[T], str]
LessFunc = Callable[[T, T], bool]


@dataclass
class HeapData(Generic[T]):
    items: Dict[str, HeapItem[T]] = field(init=False)
    queue: List[str] = field(init=False)

    def __init__(self, key_func: KeyFunc, less_func: LessFunc):
        self._key_func = key_func
        self._less_func = less_func
        self.items = dict()
        self.queue = list()

    @property
    def key_func(self) -> KeyFunc:
        return self._key_func

    @property
    def less_func(self) -> LessFunc:
        return self._less_func

    def less(self, i: int, j: int) -> bool:
        """
        :raises HeapLessFuncError
        """

        if i > len(self.queue) or j > len(self.queue):
            return False

        if (item_i := self.items.get(self.queue[i])) is None:
            return False

        if (item_j := self.items.get(self.queue[j])) is None:
            return False

        return self.less_func(item_i.obj, item_j.obj)

    def swap(self, i: int, j: int):
        self.queue[i], self.queue[j] = self.queue[j], self.queue[i]
        item = self.items[self.queue[i]]
        item.index = i

        item = self.items[self.queue[j]]
        item.index = j

    def push(self, kv: ItemKeyValue[T]):
        queue_count = len(self.queue)
        self.items[kv.key] = HeapItem(obj=kv.obj, index=queue_count)
        self.queue.append(kv.key)

    def pop(self) -> Optional[T]:
        key = self.queue[-1]
        self.queue = self.queue[:-1]

        try:
            item = self.items.pop(key)
            return item.obj
        except KeyError:
            return None

    def __len__(self):
        return len(self.queue)


class HeapInterface(Protocol[T]):
    def __len__(self) -> int:
        ...

    def push(self, obj: T):
        ...

    def pop(self) -> Optional[T]:
        ...

    def less(self, i: int, j: int) -> bool:
        ...

    def swap(self, i: int, j: int):
        ...


def init(h: HeapInterface):
    n = len(h)

    for i in reversed(range(n // 2 - 1)):
        down(h, i, n)


def fix(h: HeapInterface, index: int):
    if not down(h, index, len(h)):
        up(h, index)


def down(h: HeapInterface, i0: int, n: int) -> bool:
    i = i0
    while True:
        j1 = 2 * i + 1
        if j1 >= n or j1 < 0:
            break
        j = j1
        if (j2 := j1 + 1) < n and h.less(j2, j1):
            j = j2

        if not h.less(j, i):
            break

        h.swap(i, j)
        i = j

    return i > i0


def up(h: HeapInterface, j: int):
    while True:
        i = (j - 1) // 2
        if i < 0:
            break

        if i == j or not h.less(j, i):
            break
        h.swap(i, j)
        j = i


def push(h: HeapInterface, x: T):
    h.push(x)
    up(h, len(h) - 1)


def pop(h: HeapInterface) -> Optional[T]:
    n = len(h) - 1
    h.swap(0, n)
    down(h, 0, n)
    return h.pop()


def remove(h: HeapInterface, i: int):
    n = len(h) - 1
    if n != i:
        h.swap(i, n)
        if not down(h, i, n):
            up(h, i)
    return h.pop()


@dataclass
class Heap(Generic[T]):
    lock: Lock
    rlock: RLock
    cond: Condition
    data: HeapData[T]
    closed: bool = False

    def __post_init__(self):
        self.lock = Lock()
        self.rlock = RLock()
        self.cond = Condition(self.lock)

    @classmethod
    def new(cls, key_fn: KeyFunc, less_fn: LessFunc) -> "Heap":
        heap_data: HeapData[T] = HeapData(key_func=key_fn, less_func=less_fn)
        lock = Lock()
        rlock = RLock()
        cond = Condition(lock)
        return Heap(lock=lock, rlock=rlock, cond=cond, data=heap_data)

    def close(self):
        """
        Close the Heap and signals condition variables that may be waiting to pop
        items from the heap.
        """

        with self.lock:
            self.closed = True
            self.cond.notify_all()

    def add(self, obj: T):
        """
        Inserts an item, and puts it in the queue. The item is updated if it
        already exists.

        :raises HeapClosed
        :raises HeapKeyFuncError
        """

        key = self.data.key_func(obj)
        with self.lock:
            if self.closed:
                raise HeapClosed

            if key in self.data.items:
                self.data.items[key].obj = obj
                fix(self.data, self.data.items[key].index)
            else:
                self.add_if_not_present_locked(key, obj)
            self.cond.notify_all()

    def bulk_add(self, objs: List[T]):
        """
        Adds all the items in the list to the queue and then signals the condition
        variable. It is useful when the caller would like to add all of the items
        to the queue before consumer starts processing them.

        :raises HeapClosed
        :raises HeapKeyFuncError
        """

        with self.lock:
            if self.closed:
                raise HeapClosed

            for obj in objs:
                key = self.data.key_func(obj)
                if key in self.data.items:
                    self.data.items[key].obj = obj
                    fix(self.data, self.data.items[key].index)
                else:
                    self.add_if_not_present_locked(key, obj)

            self.cond.notify_all()

    def add_if_not_present(self, obj: T):
        """
        Inserts an item, and puts it in the queue. If an item with
        the key is present in the map, no changes is made to the item.

        This is useful in a single producer/consumer scenario so that the consumer can
        safely retry items without contending with the producer and potentially enqueueing
        stale items.

        :raises HeapClosed
        :raises HeapKeyFuncError
        """

        key = self.data.key_func(obj)
        with self.lock:
            if self.closed:
                raise HeapClosed
            self.add_if_not_present_locked(key, obj)
            self.cond.notify_all()

    def add_if_not_present_locked(self, key: str, obj: T):
        """
        Assumes the lock is already held and adds the provided
        item to the queue if it does not already exist.
        """

        if key in self.data.items:
            return

        push(self.data, ItemKeyValue(key=key, obj=obj))

    def update(self, obj: T):
        """
        Update is the same as Add in this implementation. When the item does not
        exist, it is added.

        :raises HeapClosed
        :raises HeapKeyFuncError
        """

        self.add(obj)

    def delete(self, obj: T):
        """
        Removes an item.

        :raises HeapKeyFuncError
        :raises HeapObjectNotFound
        """
        key = self.data.key_func(obj)
        with self.lock:
            if (item := self.data.items.get(key)) is None:
                raise HeapObjectNotFound
            remove(self.data, item.index)

    def pop(self) -> T:
        """
        Pop waits until an item is ready. If multiple items are
        ready, they are returned in the order given by `Heap.data.less_func`.

        :raises HeapClosed
        :raises HeapObjectAlreadyRemoved
        """
        with self.lock:
            while len(self.data.queue) == 0:
                if self.closed:
                    raise HeapClosed
                self.cond.wait()

            obj: Optional[T] = pop(self.data)

            if obj is None:
                raise HeapObjectAlreadyRemoved
            else:
                return obj

    def list(self) -> List[T]:
        """
        :return: a list of all the items.
        """

        with self.rlock:
            return [item.obj for item in self.data.items.values()]

    def list_keys(self) -> List[str]:
        """
        :return: a list of all the keys of the objects currently in the Heap.
        """

        with self.rlock:
            return list(self.data.items.keys())

    def get(self, obj: T) -> Optional[T]:
        """
        :raises HeapKeyFuncError
        :return: the requested item.
        """

        key = self.data.key_func(obj)

        return self.get_by_key(key)

    def get_by_key(self, key: str) -> Optional[T]:
        """
        :return: the requested item
        """

        with self.rlock:
            if (item := self.data.items.get(key)) is not None:
                return item.obj
            return None

    def is_closed(self) -> bool:
        """
        :return:true if the queue is closed
        """

        with self.rlock:
            return self.closed
