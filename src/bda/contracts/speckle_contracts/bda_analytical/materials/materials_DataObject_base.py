from __future__ import annotations
from bda.contracts.speckle_contracts.base_objects import Parameter, BridgeDataObject, ParameterGroup, Geometry
from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_parameters import (
    GeneralMaterialDataObject_Properties
)

from typing import Annotated, Literal, Union, Optional, Any
from pydantic import Field, BaseModel
import json


class GeneralMaterialDataObject(BridgeDataObject):
    """
    Base for all material data objects.
    Material objects do not carry geometry.
    """

    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_General_Material"
    ] = Field(
        "Objects.Data.DataObject:BDA_General_Material",
        frozen=True,
    )

    properties: GeneralMaterialDataObject_Properties
    
    displayValue: list[Geometry] = Field(
        default_factory=list,
        frozen=True,
        description="Always empty for material objects.",
        json_schema_extra={"const": []},
    )