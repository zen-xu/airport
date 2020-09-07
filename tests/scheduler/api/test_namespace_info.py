from airport.kube.api import ResourceQuantity
from airport.kube.api import ResourceQuota
from airport.scheduler.api.namespace_info import DefaultNamespaceWeight
from airport.scheduler.api.namespace_info import NamespaceCollection
from airport.scheduler.api.namespace_info import NamespaceWeightKey


def new_quota(name: str, weight: int) -> ResourceQuota:
    quota: ResourceQuota = ResourceQuota.parse_obj({"metadata": {"name": name}})

    if weight >= 0:
        quota.spec.hard[NamespaceWeightKey] = ResourceQuantity(weight)

    return quota


def test_namespace_collection():
    collection = NamespaceCollection("testCollection")
    collection.update(new_quota("abc", 123))
    collection.update(new_quota("abc", 456))
    collection.update(new_quota("def", -1))
    collection.update(new_quota("def", 16))
    collection.update(new_quota("ghi", 0))

    info = collection.snapshot()
    assert info.weight == 456

    collection.delete(new_quota("abc", 0))
    info = collection.snapshot()
    assert info.weight == 16

    collection.delete(new_quota("abc", 0))
    collection.delete(new_quota("def", 15))
    collection.delete(new_quota("ghi", -1))

    info = collection.snapshot()
    assert info.weight == DefaultNamespaceWeight


def test_empty_namespace_collection():
    collection = NamespaceCollection("testCollection")
    info = collection.snapshot()
    assert info.weight == DefaultNamespaceWeight

    # snapshot can be called anytime
    info = collection.snapshot()
    assert info.weight == DefaultNamespaceWeight

    collection.delete(new_quota("abc", 0))
    info = collection.snapshot()
    assert info.weight == DefaultNamespaceWeight

    collection.delete(new_quota("abc", 0))
    collection.delete(new_quota("def", 15))
    collection.delete(new_quota("ghi", -1))
    info = collection.snapshot()
    assert info.weight == DefaultNamespaceWeight
