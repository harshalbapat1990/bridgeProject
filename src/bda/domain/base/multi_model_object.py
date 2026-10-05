from dataclasses import dataclass
from abc import ABC

from bda.domain.units.validation import validate_pint_fields


@dataclass
class MultiModelObjectBase(ABC):
    """
    Base class for all domain objects.
    Automatically validates pint.Quantity fields.
    """

    def __post_init__(self) -> None:
        validate_pint_fields(self)
