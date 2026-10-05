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

class SectionType_SolidRectangle(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.SOLID_RECTANGLE


class SolidRectangleSectionDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Solid Rectangle"
    ] = "Objects.Data.DataObject:BDA_Section:Standard_Shape:Solid Rectangle"


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class SolidRectangleHeight(LengthDimensionParameter):
    name: Literal["Height"] = "Height"
    symbol: Literal["H"] = "H"
    description: Literal["Height of the solid rectangular section"] = "Height of the solid rectangular section"

    provided_value: StrictFloat = Field(..., ge=0)


class SolidRectangleWidth(LengthDimensionParameter):
    name: Literal["Width"] = "Width"
    symbol: Literal["B"] = "B"
    description: Literal["Width of the solid rectangular section"] = "Width of the solid rectangular section"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class SolidRectangleDimensionGroupParameters(BaseModel):
    height: SolidRectangleHeight = Field(alias="Height")
    width: SolidRectangleWidth = Field(alias="Width")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_SolidRectangle(SectionDimensionParameterGroup):
    group_parameters: SolidRectangleDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class SolidRectangleDataObject_Properties(StandardShapeDataObject_Properties):
    bda_speckle_type: SolidRectangleSectionDataObjectSpeckleType

    section_type: SectionType_SolidRectangle = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_SolidRectangle = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_SolidRectangle(StandardShapeDataObject):
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Solid Rectangle"
    ]

    properties: SolidRectangleDataObject_Properties