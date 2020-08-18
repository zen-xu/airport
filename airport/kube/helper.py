import re


DefaultResourceRequestsPrefix: str = "requests."
ResourceDefaultNamespacePrefix: str = "kubernetes.io/"
ResourceHugePagesPrefix: str = "hugepages-"
ResourceAttachableVolumesPrefix: str = "attachable-volumes-"

QualifiedNameMaxLength: int = 63
QnameCharFmt: str = r"[A-Za-z0-9]"
QnameExtCharFmt: str = r"[-A-Za-z0-9_.]"
QualifiedNameFmt: str = f"({QnameCharFmt}{QnameExtCharFmt}*)?{QnameCharFmt}"
QualifiedNameRegexp = re.compile(f"^{QualifiedNameFmt}$")


def is_prefixed_native_resource_name(name: str) -> bool:
    """
    Returns true if the `name` contains `kubernetes.io/`
    """

    return ResourceDefaultNamespacePrefix in name


def is_native_resource_name(name: str) -> bool:
    """
    Returns true if the `name` contains `kubernetes.io/` or `name`
    does not contain `/`
    """

    return "/" not in name or is_prefixed_native_resource_name(name)


def is_huge_page_resource_name(name: str) -> bool:
    """
    Returns true if the resource name has the huge page resource prefix
    """
    return name.startswith(ResourceHugePagesPrefix)


def is_qualified_name(name: str) -> bool:
    parts = name.split("/")
    parts_len = len(parts)

    if parts_len == 1:
        name = parts[0]
    elif parts_len == 2:
        prefix, name = parts
        if len(prefix) == 0:
            return False
    else:
        return False

    if (
        not name
        or len(name) > QualifiedNameMaxLength
        or not QualifiedNameRegexp.match(name)
    ):
        return False

    return True


def is_extended_resource_name(name: str) -> bool:
    if is_native_resource_name(name) or name.startswith(DefaultResourceRequestsPrefix):
        return False

    name_for_quota = f"{DefaultResourceRequestsPrefix}{name}"
    return is_qualified_name(name_for_quota)


def is_attachable_volume_resource_name(name: str) -> bool:
    return name.startswith(ResourceAttachableVolumesPrefix)


def is_scalar_resource_name(name: str) -> bool:
    return (
        is_extended_resource_name(name)
        or is_huge_page_resource_name(name)
        or is_prefixed_native_resource_name(name)
        or is_attachable_volume_resource_name(name)
    )
