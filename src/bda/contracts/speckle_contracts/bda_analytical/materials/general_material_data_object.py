from __future__ import annotations

from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
import re
from bda.contracts.speckle_contracts.base_objects import Parameter, BridgeDataObject, ParameterGroup, Geometry
from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_parameters import (
    GeneralMaterialDataObject_Properties
)

from typing import Annotated, ClassVar, Literal, Union, Optional, Any
from pydantic import Field, BaseModel, field_validator
import json


class GeneralMaterialDataObject(BridgeDataObject):
    """
    Base for all material data objects.
    Material objects do not carry geometry.
    """

    """Ensures material IDs follow the format: MAT-<number>-<type>-<code>."""
    MATERIAL_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^MAT-\d+-[A-Z]+-[A-Z0-9]+$"
    )

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GENERAL_MATERIAL
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GENERAL_MATERIAL.value, frozen=True)

    properties: GeneralMaterialDataObject_Properties
    
    displayValue: list[Geometry] = Field(
        default_factory=list,
        frozen=True,
        description="Always empty for material objects.",
        json_schema_extra={"const": []},
    )

    @field_validator("applicationId")
    @classmethod
    def validate_material_application_id(
        cls,
        value: str,
    ):

        if not cls.MATERIAL_ID_PATTERN.match(value):
            raise ValueError(
                "Material applicationId must match MAT-<index>-<TYPE>-<CODE>"
            )

        return value