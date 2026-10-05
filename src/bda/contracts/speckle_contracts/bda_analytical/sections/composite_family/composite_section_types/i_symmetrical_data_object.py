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

class SectionType_CompositeISymmetric(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.STEEL_I_SYMMETRIC


class CompositeISymmetricDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Section:Composite:Composite I Symmetric"
    ] = "Objects.Data.DataObject:BDA_Section:Composite:Composite I Symmetric"


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

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
    symbol: Literal["hh"] = "hh"
    description: Literal["Spacing between girder top and slab base"] = "Spacing between girder top and slab base"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderTopFlangeWidth(LengthDimensionParameter):
    name: Literal["Top Flange Width"] = "Top Flange Width"
    symbol: Literal["B1"] = "B1"
    description: Literal["Top flange width of girder"] = "Top flange width of girder"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderTopFlangeThickness(LengthDimensionParameter):
    name: Literal["Top Flange Thickness"] = "Top Flange Thickness"
    symbol: Literal["tf1"] = "tf1"
    description: Literal["Top flange thickness of girder"] = "Top flange thickness of girder"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderBottomFlangeWidth(LengthDimensionParameter):
    name: Literal["Bottom Flange Width"] = "Bottom Flange Width"
    symbol: Literal["B2"] = "B2"
    description: Literal["Bottom flange width of girder"] = "Bottom flange width of girder"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderBottomFlangeThickness(LengthDimensionParameter):
    name: Literal["Bottom Flange Thickness"] = "Bottom Flange Thickness"
    symbol: Literal["tf2"] = "tf2"
    description: Literal["Bottom flange thickness of girder"] = "Bottom flange thickness of girder"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderWebThickness(LengthDimensionParameter):
    name: Literal["Web Thickness"] = "Web Thickness"
    symbol: Literal["tw"] = "tw"
    description: Literal["Web thickness of girder"] = "Web thickness of girder"

    provided_value: StrictFloat = Field(..., ge=0)


class GirderWebHeight(LengthDimensionParameter):
    name: Literal["Web Height"] = "Web Height"
    symbol: Literal["hw"] = "hw"
    description: Literal["Web height of girder"] = "Web height of girder"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class CompositeISymmetricDimensionGroupParameters(BaseModel):
    slab_width: SlabWidth = Field(alias="Slab Width")
    slab_thickness: SlabThickness = Field(alias="Slab Thickness")
    slab_girder_spacing: SlabGirderSpacing = Field(alias="Girder Spacing")
    girder_top_flange_width: GirderTopFlangeWidth = Field(alias="Top Flange Width")
    girder_top_flange_thickness: GirderTopFlangeThickness = Field(alias="Top Flange Thickness")
    girder_bottom_flange_width: GirderBottomFlangeWidth = Field(alias="Bottom Flange Width")
    girder_bottom_flange_thickness: GirderBottomFlangeThickness = Field(alias="Bottom Flange Thickness")
    girder_web_thickness: GirderWebThickness = Field(alias="Web Thickness")
    girder_web_height: GirderWebHeight = Field(alias="Web Height")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_CompositeISymmetric(SectionDimensionParameterGroup):
    group_parameters: CompositeISymmetricDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class CompositeISymmetricDataObject_Properties(CompositeDataObject_Properties):
    bda_speckle_type: CompositeISymmetricDataObjectSpeckleType

    section_type: SectionType_CompositeISymmetric = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_CompositeISymmetric = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_CompositeISymmetric(CompositeDataObject):
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Composite:Composite I Symmetric"
    ]

    properties: CompositeISymmetricDataObject_Properties