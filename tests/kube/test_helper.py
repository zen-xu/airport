import pytest

from airport.kube import helper


parametrize = pytest.mark.parametrize


@parametrize(
    "name",
    [
        "kubernetes.io/",
        "kubernetes.io/a",
        pytest.param("kubernetes.io", marks=pytest.mark.xfail),
    ],
)
def test_is_prefixed_native_resource_name(name):
    assert helper.is_prefixed_native_resource_name(name)


@parametrize(
    "name",
    [
        "kubernetes.io/",
        "kubernetes.io/a",
        "kubernetes.io",
        pytest.param("docker/abc", marks=pytest.mark.xfail),
    ],
)
def test_is_native_resource_name(name):
    assert helper.is_native_resource_name(name)


@parametrize(
    "name",
    [
        "hugepages-",
        "hugepages-3Mi",
        pytest.param("hugepages", marks=pytest.mark.xfail),
    ],
)
def test_is_huge_page_resource_name(name):
    assert helper.is_huge_page_resource_name(name)


@parametrize(
    "name",
    [
        "app",
        "00099",
        "apple.ff",
        "apple-.ff",
        "Apple-.ff",
        "app/apple",
        "0" * 63,
        pytest.param("Apple-", marks=pytest.mark.xfail),
        pytest.param("000-", marks=pytest.mark.xfail),
        pytest.param("/apple", marks=pytest.mark.xfail),
        pytest.param("0" * 64, marks=pytest.mark.xfail),
        pytest.param("a/b/c", marks=pytest.mark.xfail),
    ],
)
def test_is_qualified_name(name):
    assert helper.is_qualified_name(name)


@parametrize(
    "name",
    [
        "example.com/dongle",
        "nvidia.com/gpu",
        pytest.param("kubernetes.io/a", marks=pytest.mark.xfail),
        pytest.param("requests.cpu", marks=pytest.mark.xfail),
    ],
)
def test_is_extended_resource_name(name):
    assert helper.is_extended_resource_name(name)


@parametrize(
    "name",
    [
        "attachable-volumes-",
        "attachable-volumes-volume1",
        pytest.param("attachable", marks=pytest.mark.xfail),
    ],
)
def test_is_attachable_volume_resource_name(name):
    assert helper.is_attachable_volume_resource_name(name)


@parametrize(
    "name",
    [
        "kubernetes.io/a",
        "hugepages-3Mi",
        "nvidia.com/gpu",
        "attachable-volumes-volume1",
    ],
)
def test_is_scalar_resource_name(name):
    assert helper.is_scalar_resource_name(name)
