from __future__ import annotations

from typing import Literal, ClassVar
from pydantic import BaseModel, Field, StrictFloat

from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_family_data_object import (
    StandardShapeDataObject,
    StandardShapeDataObject_Properties,
    SectionFamily_StandardShape,
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

class SectionType_Channel(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.CHANNEL


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
    section_type: SectionType_Channel = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_Channel = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_Channel(StandardShapeDataObject):
    APPLICATION_ID_PATTERN: ClassVar[str] = r"^SECT-[0-9]{4}-STANDARD-CHANNEL$"
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Channel"
    ]

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Channel"
    ] = Field(
        ...,
        frozen=True
    )

    properties: ChannelDataObject_Properties

    @classmethod
    def create(
        cls,
        name: str,
        height: float,
        top_flange_width: float,
        bottom_flange_width: float,
        web_thickness: float,
        top_flange_thickness: float,
        bottom_flange_thickness: float,
        web_inner_radius: float,
        flange_end_radius: float,
        description: str | None = None,
        unit: Literal["m", "in"] = "m",
        application_id: str = "channel_1",
        isUser: bool = True,
    ) -> "SectionDataObject_Channel":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Section:Standard_Shape:Channel"
            ),
            bda_speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Section:Standard_Shape:Channel"
            ),
            properties=(
                ChannelDataObject_Properties(
                    **{
                        "Section Description":
                            SectionDescription(
                                isUser=isUser,
                                provided_value=description,
                            ),

                        "Section Family":
                            SectionFamily_StandardShape(
                                isUser=False
                            ),

                        "Section Type":
                            SectionType_Channel(
                                isUser=False
                            ),

                        "Section Dimensions":
                            SectionDimensionParameterGroup_Channel(
                                isUser=isUser,
                                group_parameters=(
                                    ChannelDimensionGroupParameters(
                                        **{
                                            "Height":
                                                ChannelHeight(
                                                    isUser=isUser,
                                                    provided_value=height,
                                                    provided_unit=unit,
                                                    base_value=height,
                                                ),

                                            "Top Flange Width":
                                                ChannelTopFlangeWidth(
                                                    isUser=isUser,
                                                    provided_value=top_flange_width,
                                                    provided_unit=unit,
                                                    base_value=top_flange_width,
                                                ),

                                            "Bottom Flange Width":
                                                ChannelBottomFlangeWidth(
                                                    isUser=isUser,
                                                    provided_value=bottom_flange_width,
                                                    provided_unit=unit,
                                                    base_value=bottom_flange_width,
                                                ),

                                            "Web Thickness":
                                                ChannelWebThickness(
                                                    isUser=isUser,
                                                    provided_value=web_thickness,
                                                    provided_unit=unit,
                                                    base_value=web_thickness,
                                                ),

                                            "Top Flange Thickness":
                                                ChannelTopFlangeThickness(
                                                    isUser=isUser,
                                                    provided_value=top_flange_thickness,
                                                    provided_unit=unit,
                                                    base_value=top_flange_thickness,
                                                ),

                                            "Bottom Flange Thickness":
                                                ChannelBottomFlangeThickness(
                                                    isUser=isUser,
                                                    provided_value=bottom_flange_thickness,
                                                    provided_unit=unit,
                                                    base_value=bottom_flange_thickness,
                                                ),

                                            "Web Inner Radius":
                                                ChannelWebInnerRadius(
                                                    isUser=isUser,
                                                    provided_value=web_inner_radius,
                                                    provided_unit=unit,
                                                    base_value=web_inner_radius,
                                                ),

                                            "Flange End Radius":
                                                ChannelFlangeEndRadius(
                                                    isUser=isUser,
                                                    provided_value=flange_end_radius,
                                                    provided_unit=unit,
                                                    base_value=flange_end_radius,
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

    channel = SectionDataObject_Channel.create(
        name="Example Channel Section",
        application_id="SECT-0001-STANDARD-CHANNEL",
        height=0.600,
        top_flange_width=0.250,
        bottom_flange_width=0.250,
        web_thickness=0.012,
        top_flange_thickness=0.020,
        bottom_flange_thickness=0.020,
        web_inner_radius=0.015,
        flange_end_radius=0.010,
        description="Steel channel section",
        unit="m",
    )

    print(
        channel.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )
        
    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            SectionDataObject_Channel.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )