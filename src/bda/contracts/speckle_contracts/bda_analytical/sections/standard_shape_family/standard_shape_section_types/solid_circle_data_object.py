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

class SectionType_SolidCircle(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.SOLID_ROUND


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class SolidCircleDiameter(LengthDimensionParameter):
    name: Literal["Diameter"] = "Diameter"
    symbol: Literal["D"] = "D"
    description: Literal["Diameter of the solid circular section"] = "Diameter of the solid circular section"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class SolidCircleDimensionGroupParameters(BaseModel):
    diameter: SolidCircleDiameter = Field(alias="Diameter")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_SolidCircle(SectionDimensionParameterGroup):
    group_parameters: SolidCircleDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class SolidCircleDataObject_Properties(StandardShapeDataObject_Properties):
    section_type: SectionType_SolidCircle = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_SolidCircle = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_SolidCircle(StandardShapeDataObject):
    APPLICATION_ID_PATTERN: ClassVar[str] = r"^SECT-[0-9]{4}-STANDARD-SOLID-CIRCLE$"
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Solid Circle"
    ]

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Solid Circle"
    ] = Field(
        ...,
        frozen=True
    )

    properties: SolidCircleDataObject_Properties

    @classmethod
    def create(
        cls,
        name: str,
        diameter: float,
        description: str | None = None,
        unit: Literal["m", "in"] = "m",
        application_id: str = "solid_circle_1",
        isUser: bool = True,
    ) -> "SectionDataObject_SolidCircle":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Section:Standard_Shape:Solid Circle"
            ),
            bda_speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Section:Standard_Shape:Solid Circle"
            ),
            properties=(
                SolidCircleDataObject_Properties(
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
                            SectionType_SolidCircle(
                                isUser=False
                            ),

                        "Section Dimensions":
                            SectionDimensionParameterGroup_SolidCircle(
                                isUser=isUser,
                                group_parameters=(
                                    SolidCircleDimensionGroupParameters(
                                        **{
                                            "Diameter":
                                                SolidCircleDiameter(
                                                    isUser=isUser,
                                                    provided_value=diameter,
                                                    provided_unit=unit,
                                                    base_value=diameter,
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

    solid_circle = SectionDataObject_SolidCircle.create(
        name="Example Solid Circle Section",
        application_id="SECT-0001-STANDARD-SOLID-CIRCLE",
        diameter=0.400,
        description="Solid circular steel section",
        unit="m",
    )

    print(
        solid_circle.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            SectionDataObject_SolidCircle.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )