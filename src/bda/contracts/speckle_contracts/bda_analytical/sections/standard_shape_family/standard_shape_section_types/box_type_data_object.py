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

class SectionType_Box(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.BOX


class BoxSectionDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Box"
    ] = "Objects.Data.DataObject:BDA_Section:Standard_Shape:Box"


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class BoxHeight(LengthDimensionParameter):
    name: Literal["Height"] = "Height"
    symbol: Literal["H"] = "H"
    description: Literal["Overall height of the box section"] = "Overall height of the box section"

    provided_value: StrictFloat = Field(..., ge=0)


class BoxFlangeWidth(LengthDimensionParameter):
    name: Literal["Flange Width"] = "Flange Width"
    symbol: Literal["B"] = "B"
    description: Literal["Flange width of the box section"] = "Flange width of the box section"

    provided_value: StrictFloat = Field(..., ge=0)


class BoxWebThickness(LengthDimensionParameter):
    name: Literal["Web Thickness"] = "Web Thickness"
    symbol: Literal["tw"] = "tw"
    description: Literal["Web thickness of the box section"] = "Web thickness of the box section"

    provided_value: StrictFloat = Field(..., ge=0)


class BoxFlangeThickness(LengthDimensionParameter):
    name: Literal["Flange Thickness"] = "Flange Thickness"
    symbol: Literal["tf"] = "tf"
    description: Literal["Flange thickness of the box section"] = "Flange thickness of the box section"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class BoxDimensionGroupParameters(BaseModel):
    height: BoxHeight = Field(alias="Height")
    flange_width: BoxFlangeWidth = Field(alias="Flange Width")
    web_thickness: BoxWebThickness = Field(alias="Web Thickness")
    flange_thickness: BoxFlangeThickness = Field(alias="Flange Thickness")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_Box(SectionDimensionParameterGroup):
    group_parameters: BoxDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class BoxDataObject_Properties(StandardShapeDataObject_Properties):
    bda_speckle_type: BoxSectionDataObjectSpeckleType

    section_type: SectionType_Box = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_Box = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_Box(StandardShapeDataObject):
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Box"
    ]

    properties: BoxDataObject_Properties