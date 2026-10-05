from __future__ import annotations

from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes

from typing import Literal, ClassVar
from pydantic import BaseModel, Field, StrictFloat

from bda.contracts.speckle_contracts.bda_analytical.sections.composite_family.composite_family_data_object import (
    CompositeDataObject,
    CompositeDataObject_Properties,
    SectionFamily_Composite,
)

from bda.contracts.speckle_contracts.bda_analytical.sections.general_section_data_object_parameters import (
    SectionDimensionParameterGroup,
    SectionType,
    LengthDimensionParameter,
    SectionDescription,
)

from bda.contracts.paramodel.sections.sections_para_models import (
    SectionTypeParaModel,
)


# ==========================================================
# SECTION TYPE + SPECKLE TYPE
# ==========================================================

class SectionType_CompositeIAsymmetric(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.STEEL_I_ASYMMETRIC


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
    section_type: SectionType_CompositeIAsymmetric = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_CompositeIAsymmetric = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_CompositeIAsymmetric(CompositeDataObject):
    APPLICATION_ID_PATTERN: ClassVar[str] = r"^SECT-[0-9]{4}-COMPOSITE-I-ASYMMETRIC$"
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )
    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_SECTION_COMPOSITE_COMPOSITE_I_ASYMMETRIC
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_SECTION_COMPOSITE_COMPOSITE_I_ASYMMETRIC.value, frozen=True)

    properties: CompositeIAsymmetricDataObject_Properties

    @classmethod
    def create(
        cls,
        name: str,
        slab_reference_offset: float,
        top_flange_reference_offset: float,
        bottom_flange_reference_offset: float,
        slab_width: float,
        slab_thickness: float,
        slab_girder_spacing: float,
        girder_top_flange_left_width: float,
        girder_top_flange_right_width: float,
        girder_top_flange_thickness: float,
        girder_bottom_flange_left_width: float,
        girder_bottom_flange_right_width: float,
        girder_bottom_flange_thickness: float,
        girder_web_thickness: float,
        girder_web_height: float,
        description: str | None = None,
        unit: Literal["m", "in"] = "m",
        application_id: str = "composite_i_asymmetric_1",
        isUser: bool = True,
    ) -> "SectionDataObject_CompositeIAsymmetric":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            properties=(
                CompositeIAsymmetricDataObject_Properties(
                    **{
                        "Section Description":
                            SectionDescription(
                                isUser=isUser,
                                provided_value=description,
                            ),

                        "Section Family":
                            SectionFamily_Composite(
                                isUser=False,
                            ),

                        "Section Type":
                            SectionType_CompositeIAsymmetric(
                                isUser=False,
                            ),

                        "Section Dimensions":
                            SectionDimensionParameterGroup_CompositeIAsymmetric(
                                isUser=isUser,
                                group_parameters=(
                                    CompositeIAsymmetricDimensionGroupParameters(
                                        **{
                                            "Slab Reference Offset":
                                                SlabDistance(
                                                    isUser=isUser,
                                                    provided_value=slab_reference_offset,
                                                    provided_unit=unit,
                                                    base_value=slab_reference_offset,
                                                ),

                                            "Top Flange Reference Offset":
                                                TopFlangeReferenceOffset(
                                                    isUser=isUser,
                                                    provided_value=top_flange_reference_offset,
                                                    provided_unit=unit,
                                                    base_value=top_flange_reference_offset,
                                                ),

                                            "Bottom Flange Reference Offset":
                                                BottomFlangeReferenceOffset(
                                                    isUser=isUser,
                                                    provided_value=bottom_flange_reference_offset,
                                                    provided_unit=unit,
                                                    base_value=bottom_flange_reference_offset,
                                                ),

                                            "Slab Width":
                                                SlabWidth(
                                                    isUser=isUser,
                                                    provided_value=slab_width,
                                                    provided_unit=unit,
                                                    base_value=slab_width,
                                                ),

                                            "Slab Thickness":
                                                SlabThickness(
                                                    isUser=isUser,
                                                    provided_value=slab_thickness,
                                                    provided_unit=unit,
                                                    base_value=slab_thickness,
                                                ),

                                            "Girder Spacing":
                                                SlabGirderSpacing(
                                                    isUser=isUser,
                                                    provided_value=slab_girder_spacing,
                                                    provided_unit=unit,
                                                    base_value=slab_girder_spacing,
                                                ),

                                            "Top Flange Left Width":
                                                GirderTopFlangeLeftWidth(
                                                    isUser=isUser,
                                                    provided_value=girder_top_flange_left_width,
                                                    provided_unit=unit,
                                                    base_value=girder_top_flange_left_width,
                                                ),

                                            "Top Flange Right Width":
                                                GirderTopFlangeRightWidth(
                                                    isUser=isUser,
                                                    provided_value=girder_top_flange_right_width,
                                                    provided_unit=unit,
                                                    base_value=girder_top_flange_right_width,
                                                ),

                                            "Top Flange Thickness":
                                                GirderTopFlangeThickness(
                                                    isUser=isUser,
                                                    provided_value=girder_top_flange_thickness,
                                                    provided_unit=unit,
                                                    base_value=girder_top_flange_thickness,
                                                ),

                                            "Bottom Flange Left Width":
                                                GirderBottomFlangeLeftWidth(
                                                    isUser=isUser,
                                                    provided_value=girder_bottom_flange_left_width,
                                                    provided_unit=unit,
                                                    base_value=girder_bottom_flange_left_width,
                                                ),

                                            "Bottom Flange Right Width":
                                                GirderBottomFlangeRightWidth(
                                                    isUser=isUser,
                                                    provided_value=girder_bottom_flange_right_width,
                                                    provided_unit=unit,
                                                    base_value=girder_bottom_flange_right_width,
                                                ),

                                            "Bottom Flange Thickness":
                                                GirderBottomFlangeThickness(
                                                    isUser=isUser,
                                                    provided_value=girder_bottom_flange_thickness,
                                                    provided_unit=unit,
                                                    base_value=girder_bottom_flange_thickness,
                                                ),

                                            "Web Thickness":
                                                GirderWebThickness(
                                                    isUser=isUser,
                                                    provided_value=girder_web_thickness,
                                                    provided_unit=unit,
                                                    base_value=girder_web_thickness,
                                                ),

                                            "Web Height":
                                                GirderWebHeight(
                                                    isUser=isUser,
                                                    provided_value=girder_web_height,
                                                    provided_unit=unit,
                                                    base_value=girder_web_height,
                                                ),
                                        }
                                    )
                                ),
                            ),
                    }
                )
            ),
        )

if __name__ == "__main__":

    composite_i_asymmetric = (
        SectionDataObject_CompositeIAsymmetric.create(
            name="Example Composite I Asymmetric",
            application_id="SECT-0001-COMPOSITE-I-ASYMMETRIC",

            slab_reference_offset=0.000,
            top_flange_reference_offset=0.100,
            bottom_flange_reference_offset=1.500,

            slab_width=3.500,
            slab_thickness=0.250,
            slab_girder_spacing=3.000,

            girder_top_flange_left_width=0.300,
            girder_top_flange_right_width=0.450,
            girder_top_flange_thickness=0.030,

            girder_bottom_flange_left_width=0.450,
            girder_bottom_flange_right_width=0.600,
            girder_bottom_flange_thickness=0.040,

            girder_web_thickness=0.020,
            girder_web_height=1.400,

            description="Composite asymmetrical steel I girder with concrete slab",
            unit="m",
        )
    )

    print(
        composite_i_asymmetric.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            SectionDataObject_CompositeIAsymmetric.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )