from enum import Enum

__all__ = ["MaterialCode", "MaterialModelType", "MaterialType"]


class MaterialCode(str, Enum):
    """Material standard/code discriminator for standard materials."""

    GENERIC = "generic"

class MaterialModelType(str, Enum):
    ISOTROPIC = "isotropic"
    ORTHOTROPIC = "orthotropic"

class MaterialType(str, Enum):
    CONCRETE = "concrete"
    STEEL = "steel"
    REINFORCEMENT = "steel reinforcement"
    TENDON = "tendon"

