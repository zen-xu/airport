import time

from threading import Thread

import pytest

from pydantic import BaseModel

from airport.utils.cache.heap import Heap
from airport.utils.cache.heap import HeapClosed
from airport.utils.cache.heap import HeapObjectNotFound


class HeapTestObject(BaseModel):
    name: str
    value: int


def make_heap_obj(name: str, value: int) -> HeapTestObject:
    return HeapTestObject(name=name, value=value)


def heap_key_func(obj: HeapTestObject):
    return obj.name


def compare_ints(value1: HeapTestObject, value2: HeapTestObject) -> bool:
    return value1.value < value2.value


@pytest.fixture
def heap() -> Heap[HeapTestObject]:
    return Heap.new(heap_key_func, compare_ints)


def test_heap_basic(heap: Heap[HeapTestObject]):

    amount = 500

    def task1():
        for i in reversed(range(amount)):
            heap.add(make_heap_obj(f"a{i}", i))

    thread1 = Thread(target=task1)

    def task2():
        for i in range(amount):
            heap.add(make_heap_obj(f"b{i}", i))

    thread2 = Thread(target=task2)

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    prev_num = 0
    for i in range(amount * 2):
        obj = heap.pop()
        num = obj.value
        if prev_num > num:
            pytest.fail(f"got {obj} out of order, last was {prev_num}")

        prev_num = num


def test_heap_add(heap: Heap[HeapTestObject]):
    heap.add(make_heap_obj("foo", 10))
    heap.add(make_heap_obj("bar", 1))
    heap.add(make_heap_obj("baz", 11))
    heap.add(make_heap_obj("zab", 30))
    heap.add(make_heap_obj("foo", 13))

    assert heap.pop().value == 1
    assert heap.pop().value == 11

    with pytest.raises(HeapObjectNotFound):
        # baz already pop
        heap.delete(make_heap_obj("baz", 11))
    heap.add(make_heap_obj("foo", 14))  # update foo

    assert heap.pop().value == 14
    assert heap.pop().value == 30


def test_heap_bulk_add(heap: Heap[HeapTestObject]):
    amount = 500

    def task():
        datas = [make_heap_obj(f"a{i}", i) for i in reversed(range(amount))]
        heap.bulk_add(datas)

    Thread(target=task).start()

    prev_num = -1
    for i in range(amount):
        obj = heap.pop()
        if prev_num >= obj.value:
            pytest.fail(f"got {obj} out of order, last was {prev_num}")


def test_heap_empty_pop(heap: Heap[HeapTestObject]):
    def task():
        time.sleep(1)
        heap.close()

    Thread(target=task).start()

    with pytest.raises(HeapClosed):
        heap.pop()


def test_heap_add_if_not_present(heap: Heap[HeapTestObject]):
    heap.add_if_not_present(make_heap_obj("foo", 10))
    heap.add_if_not_present(make_heap_obj("bar", 1))
    heap.add_if_not_present(make_heap_obj("baz", 11))
    heap.add_if_not_present(make_heap_obj("zab", 30))
    heap.add_if_not_present(make_heap_obj("foo", 13))  # update

    assert len(heap.data.items) == 4
    assert heap.data.items["foo"].obj.value == 10

    assert heap.pop().value == 1
    assert heap.pop().value == 10

    heap.add_if_not_present(make_heap_obj("bar", 14))
    assert heap.pop().value == 11
    assert heap.pop().value == 14


def test_heap_delete(heap: Heap[HeapTestObject]):
    heap.add(make_heap_obj("foo", 10))
    heap.add(make_heap_obj("bar", 1))
    heap.add(make_heap_obj("bal", 31))
    heap.add(make_heap_obj("baz", 11))

    heap.delete(make_heap_obj("bar", 200))
    assert heap.pop().value == 10

    heap.add(make_heap_obj("zab", 30))
    heap.add(make_heap_obj("faz", 30))
    data_len = len(heap.data)

    with pytest.raises(HeapObjectNotFound):
        heap.delete(make_heap_obj("non-existent", 10))
    assert len(heap.data) == data_len

    heap.delete(make_heap_obj("bal", 31))
    heap.delete(make_heap_obj("zab", 30))

    assert heap.pop().value == 11
    assert heap.pop().value == 30

    assert len(heap.data) == 0


def test_heap_update(heap: Heap[HeapTestObject]):
    heap.add(make_heap_obj("foo", 10))
    heap.add(make_heap_obj("bar", 1))
    heap.add(make_heap_obj("bal", 31))
    heap.add(make_heap_obj("baz", 11))

    heap.update(make_heap_obj("baz", 0))

    assert heap.data.queue[0] == "baz" and heap.data.items["baz"].index == 0
    assert heap.pop().value == 0

    heap.update(make_heap_obj("bar", 100))
    assert heap.data.queue[0] == "foo" and heap.data.items["foo"].index == 0


def test_heap_get(heap: Heap[HeapTestObject]):
    heap.add(make_heap_obj("foo", 10))
    heap.add(make_heap_obj("bar", 1))
    heap.add(make_heap_obj("bal", 31))
    heap.add(make_heap_obj("baz", 11))

    obj = heap.get(make_heap_obj("baz", 0))
    assert obj is not None and obj.value == 11

    obj = heap.get(make_heap_obj("non-existing", 0))
    assert obj is None


def test_heap_get_by_key(heap: Heap[HeapTestObject]):
    heap.add(make_heap_obj("foo", 10))
    heap.add(make_heap_obj("bar", 1))
    heap.add(make_heap_obj("bal", 31))
    heap.add(make_heap_obj("baz", 11))

    obj = heap.get_by_key("baz")
    assert obj is not None and obj.value == 11

    obj = heap.get_by_key("non-existing")
    assert obj is None


def test_heap_close(heap: Heap[HeapTestObject]):
    heap.add(make_heap_obj("foo", 10))
    heap.add(make_heap_obj("bar", 1))

    assert not heap.closed, "didn't expect heap to be closed"

    heap.close()
    assert heap.closed, "expect heap to be closed"


def test_heap_list(heap: Heap[HeapTestObject]):
    heap_list = heap.list()
    assert len(heap_list) == 0

    items = {"foo": 10, "bar": 1, "bal": 31, "baz": 11, "faz": 30}

    for k, v in items.items():
        heap.add(make_heap_obj(k, v))

    assert len(heap.list()) == len(items)

    for obj in heap.list():
        assert items[obj.name] == obj.value


def test_heap_list_keys(heap: Heap[HeapTestObject]):
    list_keys = heap.list_keys()
    assert len(list_keys) == 0

    items = {"foo": 10, "bar": 1, "bal": 31, "baz": 11, "faz": 30}
    for k, v in items.items():
        heap.add(make_heap_obj(k, v))

    assert len(heap.list_keys()) == len(items)

    for key in heap.list_keys():
        assert items.get(key)


def test_heap_after_close(heap: Heap[HeapTestObject]):
    heap.close()

    with pytest.raises(HeapClosed):
        heap.add(make_heap_obj("test", 1))

    with pytest.raises(HeapClosed):
        heap.add_if_not_present(make_heap_obj("test", 1))

    with pytest.raises(HeapClosed):
        heap.bulk_add([make_heap_obj("test", 1)])
