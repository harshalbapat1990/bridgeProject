from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, StrictFloat

from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_family_data_object import (
    StandardShapeDataObject,
    StandardShapeDataObject_Properties,
)

from bda.contracts.speckle_contracts.bda_analytical.sections.general_section_data_object_parameters import (
    SectionDimensionParameterGroup,
    SectionType,
    LengthDimensionParameter,
)

from bda.contracts.speckle_contracts.base_objects import DataObjectSpeckleType
from bda.contracts.paramodel.sections.sections_para_models import (
    SectionTypeParaModel,
)


# ==========================================================
# SECTION TYPE + SPECKLE TYPE
# ==========================================================

class SectionType_Pipe(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.PIPE


class PipeSectionDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Pipe"
    ] = "Objects.Data.DataObject:BDA_Section:Standard_Shape:Pipe"


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class PipeExternalDiameter(LengthDimensionParameter):
    name: Literal["External Diameter"] = "External Diameter"
    symbol: Literal["D"] = "D"
    description: Literal["External diameter of the pipe"] = "External diameter of the pipe"

    provided_value: StrictFloat = Field(..., ge=0)


class PipeWallThickness(LengthDimensionParameter):
    name: Literal["Wall Thickness"] = "Wall Thickness"
    symbol: Literal["tw"] = "tw"
    description: Literal["Wall thickness of the pipe"] = "Wall thickness of the pipe"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class PipeDimensionGroupParameters(BaseModel):
    external_diameter: PipeExternalDiameter = Field(alias="External Diameter")
    wall_thickness: PipeWallThickness = Field(alias="Wall Thickness")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_Pipe(SectionDimensionParameterGroup):
    group_parameters: PipeDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class PipeDataObject_Properties(StandardShapeDataObject_Properties):
    bda_speckle_type: PipeSectionDataObjectSpeckleType

    section_type: SectionType_Pipe = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_Pipe = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_Pipe(StandardShapeDataObject):
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Pipe"
    ]

    properties: PipeDataObject_Properties