from __future__ import annotations

from pydantic import BaseModel

from bda.contracts.shared import QuantityParaModel

# -------------------------
# Abstract base classes
# -------------------------

class PropertiesBaseParaModel(BaseModel):
    """
    Abstract base class for properties.

    Implementation depends on StructuralComponentType.
    Discriminator is defined in ParaModelGeometryGroup.
    """

class SegmentDetailsParaModel(BaseModel):
    x_start: QuantityParaModel