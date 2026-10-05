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

class SectionType_ISection(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.I_SECTION


class ISectionDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:I-Section"
    ] = "Objects.Data.DataObject:BDA_Section:Standard_Shape:I-Section"


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class ISectionTotalHeight(LengthDimensionParameter):
    name: Literal["Total Height"] = "Total Height"
    symbol: Literal["H"] = "H"
    description: Literal["Total height of the section"] = "Total height of the section"

    provided_value: StrictFloat = Field(..., ge=0)


class ISectionTopFlangeWidth(LengthDimensionParameter):
    name: Literal["Top Flange Width"] = "Top Flange Width"
    symbol: Literal["B1"] = "B1"
    description: Literal["Top flange width"] = "Top flange width"

    provided_value: StrictFloat = Field(..., ge=0)


class ISectionBottomFlangeWidth(LengthDimensionParameter):
    name: Literal["Bottom Flange Width"] = "Bottom Flange Width"
    symbol: Literal["B2"] = "B2"
    description: Literal["Bottom flange width"] = "Bottom flange width"

    provided_value: StrictFloat = Field(..., ge=0)


class ISectionWebThickness(LengthDimensionParameter):
    name: Literal["Web Thickness"] = "Web Thickness"
    symbol: Literal["tw"] = "tw"
    description: Literal["Web thickness"] = "Web thickness"

    provided_value: StrictFloat = Field(..., ge=0)


class ISectionTopFlangeThickness(LengthDimensionParameter):
    name: Literal["Top Flange Thickness"] = "Top Flange Thickness"
    symbol: Literal["tf1"] = "tf1"
    description: Literal["Top flange thickness"] = "Top flange thickness"

    provided_value: StrictFloat = Field(..., ge=0)


class ISectionBottomFlangeThickness(LengthDimensionParameter):
    name: Literal["Bottom Flange Thickness"] = "Bottom Flange Thickness"
    symbol: Literal["tf2"] = "tf2"
    description: Literal["Bottom flange thickness"] = "Bottom flange thickness"

    provided_value: StrictFloat = Field(..., ge=0)


class ISectionWebInnerRadius(LengthDimensionParameter):
    name: Literal["Web Inner Radius"] = "Web Inner Radius"
    symbol: Literal["r1"] = "r1"
    description: Literal[
        "Inner radius between web and flange"
    ] = "Inner radius between web and flange"

    provided_value: StrictFloat = Field(..., ge=0)


class ISectionFlangeEndRadius(LengthDimensionParameter):
    name: Literal["Flange End Radius"] = "Flange End Radius"
    symbol: Literal["r2"] = "r2"
    description: Literal["Flange end radius"] = "Flange end radius"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class ISectionDimensionGroupParameters(BaseModel):
    total_height: ISectionTotalHeight = Field(alias="Total Height")
    top_flange_width: ISectionTopFlangeWidth = Field(alias="Top Flange Width")
    bottom_flange_width: ISectionBottomFlangeWidth = Field(alias="Bottom Flange Width")
    web_thickness: ISectionWebThickness = Field(alias="Web Thickness")
    top_flange_thickness: ISectionTopFlangeThickness = Field(alias="Top Flange Thickness")
    bottom_flange_thickness: ISectionBottomFlangeThickness = Field(alias="Bottom Flange Thickness")
    web_inner_radius: ISectionWebInnerRadius = Field(alias="Web Inner Radius")
    flange_end_radius: ISectionFlangeEndRadius = Field(alias="Flange End Radius")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_ISection(SectionDimensionParameterGroup):
    group_parameters: ISectionDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class ISectionDataObject_Properties(StandardShapeDataObject_Properties):
    bda_speckle_type: ISectionDataObjectSpeckleType

    section_type: SectionType_ISection = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_ISection = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_ISection(StandardShapeDataObject):
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:I-Section"
    ]

    properties: ISectionDataObject_Properties