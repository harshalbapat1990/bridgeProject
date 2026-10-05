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

class SectionType_Pipe(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.PIPE


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class PipeExternalDiameter(LengthDimensionParameter):
    name: Literal["External Diameter"] = "External Diameter"
    symbol: Literal["D"] = "D"
    description: Literal["External diameter of the pipe"] = "External diameter of the pipe"

    provided_value: StrictFloat = Field(..., ge=0)


class PipeWallThickness(LengthDimensionParameter):
    name: Literal["Wall Thickness"] = "Wall Thickness"
    symbol: Literal["tw"] = "tw"
    description: Literal["Wall thickness of the pipe"] = "Wall thickness of the pipe"

    provided_value: StrictFloat = Field(..., ge=0)


# ==========================================================
# DIMENSION GROUP
# ==========================================================

class PipeDimensionGroupParameters(BaseModel):
    external_diameter: PipeExternalDiameter = Field(alias="External Diameter")
    wall_thickness: PipeWallThickness = Field(alias="Wall Thickness")


# ==========================================================
# PARAMETER GROUP WRAPPER
# ==========================================================

class SectionDimensionParameterGroup_Pipe(SectionDimensionParameterGroup):
    group_parameters: PipeDimensionGroupParameters


# ==========================================================
# PROPERTIES
# ==========================================================

class PipeDataObject_Properties(StandardShapeDataObject_Properties):
    section_type: SectionType_Pipe = Field(alias="Section Type")

    section_dimensions: SectionDimensionParameterGroup_Pipe = Field(
        alias="Section Dimensions"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_Pipe(StandardShapeDataObject):
    APPLICATION_ID_PATTERN: ClassVar[str] = r"^SECT-[0-9]{4}-STANDARD-PIPE$"
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )

    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Pipe"
    ]

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Standard_Shape:Pipe"
    ] = Field(
        ...,
        frozen=True
    )

    properties: PipeDataObject_Properties


    @classmethod
    def create(
        cls,
        name: str,
        external_diameter: float,
        wall_thickness: float,
        description: str | None = None,
        unit: Literal["m", "in"] = "m",
        application_id: str = "pipe_1",
        isUser: bool = True,
    ) -> "SectionDataObject_Pipe":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Section:Standard_Shape:Pipe"
            ),
            bda_speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Section:Standard_Shape:Pipe"
            ),
            properties=(
                PipeDataObject_Properties(
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
                            SectionType_Pipe(
                                isUser=False
                            ),

                        "Section Dimensions":
                            SectionDimensionParameterGroup_Pipe(
                                isUser=isUser,
                                group_parameters=(
                                    PipeDimensionGroupParameters(
                                        **{
                                            "External Diameter":
                                                PipeExternalDiameter(
                                                    isUser=isUser,
                                                    provided_value=external_diameter,
                                                    provided_unit=unit,
                                                    base_value=external_diameter,
                                                ),

                                            "Wall Thickness":
                                                PipeWallThickness(
                                                    isUser=isUser,
                                                    provided_value=wall_thickness,
                                                    provided_unit=unit,
                                                    base_value=wall_thickness,
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

    pipe = SectionDataObject_Pipe.create(
        name="Example Pipe Section",
        application_id="SECT-0001-STANDARD-PIPE",
        external_diameter=0.508,
        wall_thickness=0.016,
        description="Steel CHS / Pipe section",
        unit="m",
    )

    print(
        pipe.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            SectionDataObject_Pipe.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )