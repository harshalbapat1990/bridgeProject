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

class SectionType_SolidCircle(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.SOLID_ROUND


class SolidCircleSectionDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Solid Circle"
    ] = "Objects.Data.DataObject:BDA_Section:Standard_Shape:Solid Circle"


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class SolidCircleDiameter(LengthDimensionParameter):
    name: Literal["Diameter"] = "Diameter"
    symbol: Literal["D"] = "D"
    description: Literal["Diameter of the solid circular section"] = "Diameter of the solid circular section"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class SolidCircleDimensionGroupParameters(BaseModel):
    diameter: SolidCircleDiameter = Field(alias="Diameter")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_SolidCircle(SectionDimensionParameterGroup):
    group_parameters: SolidCircleDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class SolidCircleDataObject_Properties(StandardShapeDataObject_Properties):
    bda_speckle_type: SolidCircleSectionDataObjectSpeckleType

    section_type: SectionType_SolidCircle = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_SolidCircle = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_SolidCircle(StandardShapeDataObject):
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Solid Circle"
    ]

    properties: SolidCircleDataObject_Properties