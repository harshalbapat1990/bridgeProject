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

class SectionType_SolidRectangle(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.SOLID_RECTANGLE


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class SolidRectangleHeight(LengthDimensionParameter):
    name: Literal["Height"] = "Height"
    symbol: Literal["H"] = "H"
    description: Literal["Height of the solid rectangular section"] = "Height of the solid rectangular section"

    provided_value: StrictFloat = Field(..., ge=0)


class SolidRectangleWidth(LengthDimensionParameter):
    name: Literal["Width"] = "Width"
    symbol: Literal["B"] = "B"
    description: Literal["Width of the solid rectangular section"] = "Width of the solid rectangular section"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class SolidRectangleDimensionGroupParameters(BaseModel):
    height: SolidRectangleHeight = Field(alias="Height")
    width: SolidRectangleWidth = Field(alias="Width")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_SolidRectangle(SectionDimensionParameterGroup):
    group_parameters: SolidRectangleDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class SolidRectangleDataObject_Properties(StandardShapeDataObject_Properties):
    section_type: SectionType_SolidRectangle = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_SolidRectangle = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_SolidRectangle(StandardShapeDataObject):
    APPLICATION_ID_PATTERN: ClassVar[str] = r"^SECT-[0-9]{4}-STANDARD-SOLID-RECTANGLE$"
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Solid Rectangle"
    ] = "Objects.Data.DataObject:BDA_Section:Standard_Shape:Solid Rectangle"

    properties: SolidRectangleDataObject_Properties

    @classmethod
    def create(
        cls,
        name: str,
        height: float,
        width: float,
        description: str | None = None,
        unit: Literal["m", "in"] = "m",
        application_id: str = "solid_rectangle_1",
        isUser: bool = True,
    ) -> "SectionDataObject_SolidRectangle":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            properties=(
                SolidRectangleDataObject_Properties(
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
                            SectionType_SolidRectangle(
                                isUser=False
                            ),

                        "Section Dimensions":
                            SectionDimensionParameterGroup_SolidRectangle(
                                isUser=isUser,
                                group_parameters=(
                                    SolidRectangleDimensionGroupParameters(
                                        **{
                                            "Height":
                                                SolidRectangleHeight(
                                                    isUser=isUser,
                                                    provided_value=height,
                                                    provided_unit=unit,
                                                    base_value=height,
                                                ),

                                            "Width":
                                                SolidRectangleWidth(
                                                    isUser=isUser,
                                                    provided_value=width,
                                                    provided_unit=unit,
                                                    base_value=width,
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

    solid_rectangle = SectionDataObject_SolidRectangle.create(
        name="Example Solid Rectangle Section",
        application_id="SECT-0001-STANDARD-SOLID-RECTANGLE",
        height=0.600,
        width=0.300,
        description="Solid rectangular concrete section",
        unit="m",
    )

    print(
        solid_rectangle.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            SectionDataObject_SolidRectangle.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )