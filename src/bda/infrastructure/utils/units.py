"""Canonical units and quantity helpers shared by importers and tests."""

from bda.domain.units import ureg

Q_ = ureg.Quantity

CANONICAL_LENGTH = ureg.meter
CANONICAL_FORCE = ureg.kilonewton
CANONICAL_MOMENT = ureg.kilonewton * ureg.meter
CANONICAL_STRESS = ureg.megapascal

# CSI OAPI present-units code for kN, m, C.
CSI_UNIT_CODE_KN_M_C = 6

# Canonical unit system identifier written into every ...ResultModel DTO.
# Fetchers MUST set this value; mappers ASSERT it before applying Q_().
# Changing this string is a breaking change that requires updating every
# fetcher, mapper, and test that references it.
CANONICAL_UNIT_SYSTEM = "kN-m-C"

__all__ = [
    "ureg",
    "Q_",
    "CANONICAL_LENGTH",
    "CANONICAL_FORCE",
    "CANONICAL_MOMENT",
    "CANONICAL_STRESS",
    "CSI_UNIT_CODE_KN_M_C",
    "CANONICAL_UNIT_SYSTEM",
]

