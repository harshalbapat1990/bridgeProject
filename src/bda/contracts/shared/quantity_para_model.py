from __future__ import annotations

from typing import Optional

from pydantic import Field, AliasChoices

from bda.contracts.paramodel.shared.base_model_para_model import BaseModelParaModel


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------


class QuantityParaModel(BaseModelParaModel):
    """Represents a physical quantity as stored in the JSON: value + unit."""

    value: float= Field(validation_alias=AliasChoices("value", "provided_value"))
    unit: Optional[str] = Field(validation_alias=AliasChoices("unit", "provided_unit"),
                                default=None)


