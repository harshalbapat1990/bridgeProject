from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, StrictFloat

from bda.contracts.speckle_contracts.bda_analytical.sections.composite_family.composite_family_data_object import (
    CompositeDataObject,
    CompositeDataObject_Properties,
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

class SectionType_CompositeIAsymmetric(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.STEEL_I_ASYMMETRIC


class CompositeIAsymmetricDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Section:Composite:Composite I Asymmetric"
    ] = "Objects.Data.DataObject:BDA_Section:Composite:Composite I Asymmetric"


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class SlabDistance(LengthDimensionParameter):
    name: Literal["Slab Reference Offset"] = "Slab Reference Offset"
    symbol: Literal["Sg"] = "Sg"
    description: Literal["Reference offset of slab"] = "Reference offset of slab"

    provided_value: StrictFloat = Field(..., ge=0)


class TopFlangeReferenceOffset(LengthDimensionParameter):
    name: Literal["Top Flange Reference Offset"] = "Top Flange Reference Offset"
    symbol: Literal["Top"] = "Top"
    description: Literal["Reference offset to top flange"] = "Reference offset to top flange"

    provided_value: StrictFloat = Field(..., ge=0)


class BottomFlangeReferenceOffset(LengthDimensionParameter):
    name: Literal["Bottom Flange Reference Offset"] = "Bottom Flange Reference Offset"
    symbol: Literal["Bot"] = "Bot"
    description: Literal["Reference offset to bottom flange"] = "Reference offset to bottom flange"

    provided_value: StrictFloat = Field(..., ge=0)


class SlabWidth(LengthDimensionParameter):
    name: Literal["Slab Width"] = "Slab Width"
    symbol: Literal["Bc"] = "Bc"
    description: Literal["Concrete slab width"] = "Concrete slab width"

    provided_value: StrictFloat = Field(..., ge=0)


class SlabThickness(LengthDimensionParameter):
    name: Literal["Slab Thickness"] = "Slab Thickness"
    symbol: Literal["tc"] = "tc"
    description: Literal["Concrete slab thickness"] = "Concrete slab thickness"

    provided_value: StrictFloat = Field(..., ge=0)


class SlabGirderSpacing(LengthDimensionParameter):
    name: Literal["Girder Spacing"] = "Girder Spacing"
    symbol: Literal["Hh"] = "Hh"
    description: Literal["Spacing between girders"] = "Spacing between girders"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderTopFlangeLeftWidth(LengthDimensionParameter):
    name: Literal["Top Flange Left Width"] = "Top Flange Left Width"
    symbol: Literal["B1"] = "B1"
    description: Literal["Top flange left width"] = "Top flange left width"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderTopFlangeRightWidth(LengthDimensionParameter):
    name: Literal["Top Flange Right Width"] = "Top Flange Right Width"
    symbol: Literal["B2"] = "B2"
    description: Literal["Top flange right width"] = "Top flange right width"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderTopFlangeThickness(LengthDimensionParameter):
    name: Literal["Top Flange Thickness"] = "Top Flange Thickness"
    symbol: Literal["t1"] = "t1"
    description: Literal["Top flange thickness"] = "Top flange thickness"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderBottomFlangeLeftWidth(LengthDimensionParameter):
    name: Literal["Bottom Flange Left Width"] = "Bottom Flange Left Width"
    symbol: Literal["B3"] = "B3"
    description: Literal["Bottom flange left width"] = "Bottom flange left width"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderBottomFlangeRightWidth(LengthDimensionParameter):
    name: Literal["Bottom Flange Right Width"] = "Bottom Flange Right Width"
    symbol: Literal["B4"] = "B4"
    description: Literal["Bottom flange right width"] = "Bottom flange right width"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderBottomFlangeThickness(LengthDimensionParameter):
    name: Literal["Bottom Flange Thickness"] = "Bottom Flange Thickness"
    symbol: Literal["t2"] = "t2"
    description: Literal["Bottom flange thickness"] = "Bottom flange thickness"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderWebThickness(LengthDimensionParameter):
    name: Literal["Web Thickness"] = "Web Thickness"
    symbol: Literal["tw"] = "tw"
    description: Literal["Web thickness"] = "Web thickness"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderWebHeight(LengthDimensionParameter):
    name: Literal["Web Height"] = "Web Height"
    symbol: Literal["H"] = "H"
    description: Literal["Web height"] = "Web height"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class CompositeIAsymmetricDimensionGroupParameters(BaseModel):
    slab_reference_offset: SlabDistance = Field(alias="Slab Reference Offset")
    top_flange_reference_offset: TopFlangeReferenceOffset = Field(alias="Top Flange Reference Offset")
    bottom_flange_reference_offset: BottomFlangeReferenceOffset = Field(alias="Bottom Flange Reference Offset")
    slab_width: SlabWidth = Field(alias="Slab Width")
    slab_thickness: SlabThickness = Field(alias="Slab Thickness")
    slab_girder_spacing: SlabGirderSpacing = Field(alias="Girder Spacing")
    girder_top_flange_left_width: GirderTopFlangeLeftWidth = Field(alias="Top Flange Left Width")
    girder_top_flange_right_width: GirderTopFlangeRightWidth = Field(alias="Top Flange Right Width")
    girder_top_flange_thickness: GirderTopFlangeThickness = Field(alias="Top Flange Thickness")
    girder_bottom_flange_left_width: GirderBottomFlangeLeftWidth = Field(alias="Bottom Flange Left Width")
    girder_bottom_flange_right_width: GirderBottomFlangeRightWidth = Field(alias="Bottom Flange Right Width")
    girder_bottom_flange_thickness: GirderBottomFlangeThickness = Field(alias="Bottom Flange Thickness")
    girder_web_thickness: GirderWebThickness = Field(alias="Web Thickness")
    girder_web_height: GirderWebHeight = Field(alias="Web Height")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_CompositeIAsymmetric(SectionDimensionParameterGroup):
    group_parameters: CompositeIAsymmetricDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class CompositeIAsymmetricDataObject_Properties(CompositeDataObject_Properties):
    bda_speckle_type: CompositeIAsymmetricDataObjectSpeckleType

    section_type: SectionType_CompositeIAsymmetric = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_CompositeIAsymmetric = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_CompositeIAsymmetric(CompositeDataObject):
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Composite:Composite I Asymmetric"
    ]

    properties: CompositeIAsymmetricDataObject_Properties