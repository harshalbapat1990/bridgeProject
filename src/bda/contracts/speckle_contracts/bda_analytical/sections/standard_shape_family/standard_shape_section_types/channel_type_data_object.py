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

class SectionType_Channel(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.CHANNEL


class ChannelSectionDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Channel"
    ] = "Objects.Data.DataObject:BDA_Section:Standard_Shape:Channel"


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class ChannelHeight(LengthDimensionParameter):
    name: Literal["Height"] = "Height"
    symbol: Literal["H"] = "H"
    description: Literal["Overall height of the channel section"] = "Overall height of the channel section"

    provided_value: StrictFloat = Field(..., ge=0)


class ChannelTopFlangeWidth(LengthDimensionParameter):
    name: Literal["Top Flange Width"] = "Top Flange Width"
    symbol: Literal["B1"] = "B1"
    description: Literal["Top flange width"] = "Top flange width"

    provided_value: StrictFloat = Field(..., ge=0)


class ChannelBottomFlangeWidth(LengthDimensionParameter):
    name: Literal["Bottom Flange Width"] = "Bottom Flange Width"
    symbol: Literal["B2"] = "B2"
    description: Literal["Bottom flange width"] = "Bottom flange width"

    provided_value: StrictFloat = Field(..., ge=0)


class ChannelWebThickness(LengthDimensionParameter):
    name: Literal["Web Thickness"] = "Web Thickness"
    symbol: Literal["tw"] = "tw"
    description: Literal["Web thickness"] = "Web thickness"

    provided_value: StrictFloat = Field(..., ge=0)


class ChannelTopFlangeThickness(LengthDimensionParameter):
    name: Literal["Top Flange Thickness"] = "Top Flange Thickness"
    symbol: Literal["tf1"] = "tf1"
    description: Literal["Top flange thickness"] = "Top flange thickness"

    provided_value: StrictFloat = Field(..., ge=0)


class ChannelBottomFlangeThickness(LengthDimensionParameter):
    name: Literal["Bottom Flange Thickness"] = "Bottom Flange Thickness"
    symbol: Literal["tf2"] = "tf2"
    description: Literal["Bottom flange thickness"] = "Bottom flange thickness"

    provided_value: StrictFloat = Field(..., ge=0)


class ChannelWebInnerRadius(LengthDimensionParameter):
    name: Literal["Web Inner Radius"] = "Web Inner Radius"
    symbol: Literal["r1"] = "r1"
    description: Literal[
        "Inner radius between web and flange"
    ] = "Inner radius between web and flange"

    provided_value: StrictFloat = Field(..., ge=0)


class ChannelFlangeEndRadius(LengthDimensionParameter):
    name: Literal["Flange End Radius"] = "Flange End Radius"
    symbol: Literal["r2"] = "r2"
    description: Literal["Flange end radius"] = "Flange end radius"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class ChannelDimensionGroupParameters(BaseModel):
    height: ChannelHeight = Field(alias="Height")
    top_flange_width: ChannelTopFlangeWidth = Field(alias="Top Flange Width")
    bottom_flange_width: ChannelBottomFlangeWidth = Field(alias="Bottom Flange Width")
    web_thickness: ChannelWebThickness = Field(alias="Web Thickness")
    top_flange_thickness: ChannelTopFlangeThickness = Field(alias="Top Flange Thickness")
    bottom_flange_thickness: ChannelBottomFlangeThickness = Field(alias="Bottom Flange Thickness")
    web_inner_radius: ChannelWebInnerRadius = Field(alias="Web Inner Radius")
    flange_end_radius: ChannelFlangeEndRadius = Field(alias="Flange End Radius")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_Channel(SectionDimensionParameterGroup):
    group_parameters: ChannelDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class ChannelDataObject_Properties(StandardShapeDataObject_Properties):
    bda_speckle_type: ChannelSectionDataObjectSpeckleType

    section_type: SectionType_Channel = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_Channel = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_Channel(StandardShapeDataObject):
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Channel"
    ]

    properties: ChannelDataObject_Properties