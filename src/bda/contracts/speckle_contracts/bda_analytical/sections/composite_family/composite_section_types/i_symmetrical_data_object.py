from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
from __future__ import annotations

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

class SectionType_CompositeISymmetric(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.STEEL_I_SYMMETRIC


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
    section_type: SectionType_CompositeISymmetric = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_CompositeISymmetric = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_CompositeISymmetric(CompositeDataObject):
    APPLICATION_ID_PATTERN: ClassVar[str] = r"^SECT-[0-9]{4}-COMPOSITE-I-SYMMETRIC$"
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Composite:Composite I Symmetric"
    ]

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_SECTION_COMPOSITE_COMPOSITE_I_SYMMETRIC
    ] = Field(
        ...,
        frozen=True
    )

    properties: CompositeISymmetricDataObject_Properties

    @classmethod
    def create(
        cls,
        name: str,
        slab_width: float,
        slab_thickness: float,
        slab_girder_spacing: float,
        girder_top_flange_width: float,
        girder_top_flange_thickness: float,
        girder_bottom_flange_width: float,
        girder_bottom_flange_thickness: float,
        girder_web_thickness: float,
        girder_web_height: float,
        description: str | None = None,
        unit: Literal["m", "in"] = "m",
        application_id: str = "composite_i_symmetric_1",
        isUser: bool = True,
    ) -> "SectionDataObject_CompositeISymmetric":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Section:Composite:Composite I Symmetric"
            ),
            bda_speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Section:Composite:Composite I Symmetric"
            ),
            properties=(
                CompositeISymmetricDataObject_Properties(
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
                            SectionType_CompositeISymmetric(
                                isUser=False,
                            ),

                        "Section Dimensions":
                            SectionDimensionParameterGroup_CompositeISymmetric(
                                isUser=isUser,
                                group_parameters=(
                                    CompositeISymmetricDimensionGroupParameters(
                                        **{
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

                                            "Top Flange Width":
                                                GirderTopFlangeWidth(
                                                    isUser=isUser,
                                                    provided_value=girder_top_flange_width,
                                                    provided_unit=unit,
                                                    base_value=girder_top_flange_width,
                                                ),

                                            "Top Flange Thickness":
                                                GirderTopFlangeThickness(
                                                    isUser=isUser,
                                                    provided_value=girder_top_flange_thickness,
                                                    provided_unit=unit,
                                                    base_value=girder_top_flange_thickness,
                                                ),

                                            "Bottom Flange Width":
                                                GirderBottomFlangeWidth(
                                                    isUser=isUser,
                                                    provided_value=girder_bottom_flange_width,
                                                    provided_unit=unit,
                                                    base_value=girder_bottom_flange_width,
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

    composite_i_symmetric = (
        SectionDataObject_CompositeISymmetric.create(
            name="Example Composite I Symmetric",
            application_id="SECT-0001-COMPOSITE-I-SYMMETRIC",

            slab_width=3.500,
            slab_thickness=0.250,
            slab_girder_spacing=0.100,

            girder_top_flange_width=0.500,
            girder_top_flange_thickness=0.030,

            girder_bottom_flange_width=0.600,
            girder_bottom_flange_thickness=0.040,

            girder_web_thickness=0.020,
            girder_web_height=1.400,

            description="Composite symmetric steel I girder with concrete slab",
            unit="m",
        )
    )

    print(
        composite_i_symmetric.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            SectionDataObject_CompositeISymmetric.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )