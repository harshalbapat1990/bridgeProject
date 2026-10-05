from __future__ import annotations

from typing import Literal, ClassVar
from pydantic import BaseModel, Field, StrictFloat

from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_family_data_object import (
    StandardShapeDataObject,
    StandardShapeDataObject_Properties,
    SectionFamily_StandardShape
)

from bda.contracts.speckle_contracts.bda_analytical.sections.general_section_data_object_parameters import (
    SectionDimensionParameterGroup,
    SectionType,
    LengthDimensionParameter,
    SectionDescription
)

from bda.contracts.paramodel.sections.sections_para_models import (
    SectionTypeParaModel,
)


# ==========================================================
# SECTION TYPE + SPECKLE TYPE
# ==========================================================

class SectionType_Angle(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.ANGLE


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class AngleHeight(LengthDimensionParameter):
    name: Literal["Height"] = "Height"
    symbol: Literal["H"] = "H"
    description: Literal["Height of the angle section"] = "Height of the angle section"

    provided_value: StrictFloat = Field(..., ge=0)


class AngleWidth(LengthDimensionParameter):
    name: Literal["Width"] = "Width"
    symbol: Literal["B"] = "B"
    description: Literal["Width of the angle section"] = "Width of the angle section"

    provided_value: StrictFloat = Field(..., ge=0)


class AngleWebThickness(LengthDimensionParameter):
    name: Literal["Web Thickness"] = "Web Thickness"
    symbol: Literal["t_w"] = "t_w"
    description: Literal["Web thickness of the angle section"] = "Web thickness of the angle section"

    provided_value: StrictFloat = Field(..., ge=0)


class AngleFlangeThickness(LengthDimensionParameter):
    name: Literal["Flange Thickness"] = "Flange Thickness"
    symbol: Literal["t_f"] = "t_f"
    description: Literal["Flange thickness of the angle section"] = "Flange thickness of the angle section"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class AngleDimensionGroupParameters(BaseModel):
    height: AngleHeight = Field(alias="Height")
    width: AngleWidth = Field(alias="Width")
    web_thickness: AngleWebThickness = Field(alias="Web Thickness")
    flange_thickness: AngleFlangeThickness = Field(alias="Flange Thickness")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_Angle(SectionDimensionParameterGroup):
    group_parameters: AngleDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class AngleDataObject_Properties(StandardShapeDataObject_Properties):
    section_type: SectionType_Angle = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_Angle = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_Angle(StandardShapeDataObject):
    APPLICATION_ID_PATTERN: ClassVar[str] = r"^SECT-[0-9]{4}-STANDARD-ANGLE$"
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )
    
    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Angle"
    ] = "Objects.Data.DataObject:BDA_Section:Standard_Shape:Angle"

    properties: AngleDataObject_Properties

    @classmethod
    def create(
        cls,
        name:str,
        height: float,
        width: float,
        web_thickness: float,
        flange_thickness: float,
        description: str | None = None,
        unit: Literal["m", "in"] = "m",
        application_id: str = "angle_1",
        isUser: bool = True,
    ) -> "SectionDataObject_Angle":

        return cls(
            id=None,
            name = name,
            applicationId=application_id,
            properties=(
                AngleDataObject_Properties(
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
                            SectionType_Angle(
                                isUser=False
                            ),

                        "Section Dimensions":
                            SectionDimensionParameterGroup_Angle(
                                isUser=isUser,
                                group_parameters=(
                                    AngleDimensionGroupParameters(
                                        **{
                                            "Height":
                                                AngleHeight(
                                                    isUser=isUser,
                                                    provided_value=height,
                                                    provided_unit=unit,
                                                    base_value=height,
                                                ),

                                            "Width":
                                                AngleWidth(
                                                    isUser=isUser,
                                                    provided_value=width,
                                                    provided_unit=unit,
                                                    base_value=width,
                                                ),

                                            "Web Thickness":
                                                AngleWebThickness(
                                                    isUser=isUser,
                                                    provided_value=web_thickness,
                                                    provided_unit=unit,
                                                    base_value=web_thickness,
                                                ),

                                            "Flange Thickness":
                                                AngleFlangeThickness(
                                                    isUser=isUser,
                                                    provided_value=flange_thickness,
                                                    provided_unit=unit,
                                                    base_value=flange_thickness,
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

    angle = SectionDataObject_Angle.create(
        name="Example Angle Section",
        application_id="SECT-0001-STANDARD-ANGLE",
        height=0.300,
        width=0.150,
        web_thickness=0.012,
        flange_thickness=0.015,
        description="UK Equal Angle",
        unit="m"
    )

    print(
        angle.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            SectionDataObject_Angle.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )
    