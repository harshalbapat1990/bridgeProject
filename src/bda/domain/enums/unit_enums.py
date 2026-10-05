from enum import Enum

__all__ = ["UnitSystem"]

class UnitSystem(str, Enum):
    SI = "Metric"
    IM = "US Customary"