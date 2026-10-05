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

class SectionType_Angle(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.ANGLE


class AngleSectionDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Angle"
    ] = "Objects.Data.DataObject:BDA_Section:Standard_Shape:Angle"


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class AngleHeight(LengthDimensionParameter):
    name: Literal["Height"] = "Height"
    symbol: Literal["H"] = "H"
    description: Literal["Height of the angle section"] = "Height of the angle section"

    provided_value: StrictFloat = Field(..., ge=0)


class AngleWidth(LengthDimensionParameter):
    name: Literal["Width"] = "Width"
    symbol: Literal["B"] = "B"
    description: Literal["Width of the angle section"] = "Width of the angle section"

    provided_value: StrictFloat = Field(..., ge=0)


class AngleWebThickness(LengthDimensionParameter):
    name: Literal["Web Thickness"] = "Web Thickness"
    symbol: Literal["t_w"] = "t_w"
    description: Literal["Web thickness of the angle section"] = "Web thickness of the angle section"

    provided_value: StrictFloat = Field(..., ge=0)


class AngleFlangeThickness(LengthDimensionParameter):
    name: Literal["Flange Thickness"] = "Flange Thickness"
    symbol: Literal["t_f"] = "t_f"
    description: Literal["Flange thickness of the angle section"] = "Flange thickness of the angle section"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class AngleDimensionGroupParameters(BaseModel):
    height: AngleHeight = Field(alias="Height")
    width: AngleWidth = Field(alias="Width")
    web_thickness: AngleWebThickness = Field(alias="Web Thickness")
    flange_thickness: AngleFlangeThickness = Field(alias="Flange Thickness")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_Angle(SectionDimensionParameterGroup):
    group_parameters: AngleDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class AngleDataObject_Properties(StandardShapeDataObject_Properties):
    bda_speckle_type: AngleSectionDataObjectSpeckleType

    section_type: SectionType_Angle = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_Angle = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_Angle(StandardShapeDataObject):
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Angle"
    ]

    properties: AngleDataObject_Properties