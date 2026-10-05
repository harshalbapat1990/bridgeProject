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

class SectionType_Box(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.BOX


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class BoxHeight(LengthDimensionParameter):
    name: Literal["Height"] = "Height"
    symbol: Literal["H"] = "H"
    description: Literal["Overall height of the box section"] = "Overall height of the box section"

    provided_value: StrictFloat = Field(..., ge=0)


class BoxFlangeWidth(LengthDimensionParameter):
    name: Literal["Flange Width"] = "Flange Width"
    symbol: Literal["B"] = "B"
    description: Literal["Flange width of the box section"] = "Flange width of the box section"

    provided_value: StrictFloat = Field(..., ge=0)


class BoxWebThickness(LengthDimensionParameter):
    name: Literal["Web Thickness"] = "Web Thickness"
    symbol: Literal["tw"] = "tw"
    description: Literal["Web thickness of the box section"] = "Web thickness of the box section"

    provided_value: StrictFloat = Field(..., ge=0)


class BoxFlangeThickness(LengthDimensionParameter):
    name: Literal["Flange Thickness"] = "Flange Thickness"
    symbol: Literal["tf"] = "tf"
    description: Literal["Flange thickness of the box section"] = "Flange thickness of the box section"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class BoxDimensionGroupParameters(BaseModel):
    height: BoxHeight = Field(alias="Height")
    flange_width: BoxFlangeWidth = Field(alias="Flange Width")
    web_thickness: BoxWebThickness = Field(alias="Web Thickness")
    flange_thickness: BoxFlangeThickness = Field(alias="Flange Thickness")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_Box(SectionDimensionParameterGroup):
    group_parameters: BoxDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class BoxDataObject_Properties(StandardShapeDataObject_Properties):
    section_type: SectionType_Box = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_Box = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_Box(StandardShapeDataObject):
    APPLICATION_ID_PATTERN: ClassVar[str] = r"^SECT-[0-9]{4}-STANDARD-BOX$"
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Box"
    ] = "Objects.Data.DataObject:BDA_Section:Standard_Shape:Box"

    properties: BoxDataObject_Properties

    @classmethod
    def create(
        cls,
        name: str,
        height: float,
        flange_width: float,
        web_thickness: float,
        flange_thickness: float,
        description: str | None = None,
        unit: Literal["m", "in"] = "m",
        application_id: str = "box_1",
        isUser: bool = True,
    ) -> "SectionDataObject_Box":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            properties=(
                BoxDataObject_Properties(
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
                            SectionType_Box(
                                isUser=False
                            ),

                        "Section Dimensions":
                            SectionDimensionParameterGroup_Box(
                                isUser=isUser,
                                group_parameters=(
                                    BoxDimensionGroupParameters(
                                        **{
                                            "Height":
                                                BoxHeight(
                                                    isUser=isUser,
                                                    provided_value=height,
                                                    provided_unit=unit,
                                                    base_value=height,
                                                ),

                                            "Flange Width":
                                                BoxFlangeWidth(
                                                    isUser=isUser,
                                                    provided_value=flange_width,
                                                    provided_unit=unit,
                                                    base_value=flange_width,
                                                ),

                                            "Web Thickness":
                                                BoxWebThickness(
                                                    isUser=isUser,
                                                    provided_value=web_thickness,
                                                    provided_unit=unit,
                                                    base_value=web_thickness,
                                                ),

                                            "Flange Thickness":
                                                BoxFlangeThickness(
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

    box = SectionDataObject_Box.create(
        name="Example Box Section",
        application_id="SECT-0001-STANDARD-BOX",
        height=1.500,
        flange_width=0.800,
        web_thickness=0.025,
        flange_thickness=0.030,
        description="Steel box girder section",
        unit="m",
    )

    print(
        box.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            SectionDataObject_Box.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )