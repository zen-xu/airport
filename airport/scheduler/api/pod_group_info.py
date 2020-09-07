from airport.api.scheduling import PodGroup as _PodGroup


PodGroupVersionV1Beta1 = "v1beta1"


class PodGroup(_PodGroup):
    version: str = PodGroupVersionV1Beta1
