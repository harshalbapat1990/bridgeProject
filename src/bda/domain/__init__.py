"""Domain layer - contains business models and enumerations.

This layer is independent and does not depend on application or infrastructure layers.
"""

from .models.analytical_multi_model import AnalyticalMultiModel

__all__ = ["AnalyticalMultiModel"]

