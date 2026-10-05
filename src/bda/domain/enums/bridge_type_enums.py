from enum import Enum

__all__ = ["BridgeType"]


class BridgeType(str, Enum):
    STEEL_COMPOSITE = "Steel Composite"
    PSC_BOX = "PSC Box"

