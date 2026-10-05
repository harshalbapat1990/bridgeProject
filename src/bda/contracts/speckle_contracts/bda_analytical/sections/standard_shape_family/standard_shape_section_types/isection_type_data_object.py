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

class SectionType_ISection(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.I_SECTION


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
    section_type: SectionType_ISection = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_ISection = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_ISection(StandardShapeDataObject):
    APPLICATION_ID_PATTERN: ClassVar[str] = r"^SECT-[0-9]{4}-STANDARD-ISECTION$"
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )
    
    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:I-Section"
    ] = "Objects.Data.DataObject:BDA_Section:Standard_Shape:I-Section"

    properties: ISectionDataObject_Properties

    @classmethod
    def create(
        cls,
        name: str,
        total_height: float,
        top_flange_width: float,
        bottom_flange_width: float,
        web_thickness: float,
        top_flange_thickness: float,
        bottom_flange_thickness: float,
        web_inner_radius: float,
        flange_end_radius: float,
        description: str | None = None,
        unit: Literal["m", "in"] = "m",
        application_id: str = "isection_1",
        isUser: bool = True,
    ) -> "SectionDataObject_ISection":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            properties=(
                ISectionDataObject_Properties(
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
                            SectionType_ISection(
                                isUser=False
                            ),

                        "Section Dimensions":
                            SectionDimensionParameterGroup_ISection(
                                isUser=isUser,
                                group_parameters=(
                                    ISectionDimensionGroupParameters(
                                        **{
                                            "Total Height":
                                                ISectionTotalHeight(
                                                    isUser=isUser,
                                                    provided_value=total_height,
                                                    provided_unit=unit,
                                                    base_value=total_height,
                                                ),

                                            "Top Flange Width":
                                                ISectionTopFlangeWidth(
                                                    isUser=isUser,
                                                    provided_value=top_flange_width,
                                                    provided_unit=unit,
                                                    base_value=top_flange_width,
                                                ),

                                            "Bottom Flange Width":
                                                ISectionBottomFlangeWidth(
                                                    isUser=isUser,
                                                    provided_value=bottom_flange_width,
                                                    provided_unit=unit,
                                                    base_value=bottom_flange_width,
                                                ),

                                            "Web Thickness":
                                                ISectionWebThickness(
                                                    isUser=isUser,
                                                    provided_value=web_thickness,
                                                    provided_unit=unit,
                                                    base_value=web_thickness,
                                                ),

                                            "Top Flange Thickness":
                                                ISectionTopFlangeThickness(
                                                    isUser=isUser,
                                                    provided_value=top_flange_thickness,
                                                    provided_unit=unit,
                                                    base_value=top_flange_thickness,
                                                ),

                                            "Bottom Flange Thickness":
                                                ISectionBottomFlangeThickness(
                                                    isUser=isUser,
                                                    provided_value=bottom_flange_thickness,
                                                    provided_unit=unit,
                                                    base_value=bottom_flange_thickness,
                                                ),

                                            "Web Inner Radius":
                                                ISectionWebInnerRadius(
                                                    isUser=isUser,
                                                    provided_value=web_inner_radius,
                                                    provided_unit=unit,
                                                    base_value=web_inner_radius,
                                                ),

                                            "Flange End Radius":
                                                ISectionFlangeEndRadius(
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

    i_section = SectionDataObject_ISection.create(
        name="Example I Section",
        application_id="SECT-0001-STANDARD-ISECTION",
        total_height=1.200,
        top_flange_width=0.500,
        bottom_flange_width=0.500,
        web_thickness=0.020,
        top_flange_thickness=0.035,
        bottom_flange_thickness=0.035,
        web_inner_radius=0.020,
        flange_end_radius=0.012,
        description="Steel plate girder I-section",
        unit="m",
    )

    print(
        i_section.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            SectionDataObject_ISection.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )