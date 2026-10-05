from __future__ import annotations

from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes

from typing import Literal, ClassVar
from pydantic import Field, StrictFloat, BaseModel

from bda.contracts.speckle_contracts.bda_analytical.sections.psc_family.psc_family_data_object import (
    PSCDataObject,
    PSCDataObject_Properties,
    SectionFamily_PSC,
)

from bda.contracts.speckle_contracts.bda_analytical.sections.general_section_data_object_parameters import (
    SectionType,
    LengthDimensionParameter,
    SectionDescription,
    SectionDimensionParameterGroup
)

from bda.contracts.speckle_contracts.base_objects import (
    ParameterGroup,
    Parameter
)

from bda.contracts.paramodel.sections.sections_para_models import (
    SectionTypeParaModel,
)


# ==========================================================
# SECTION TYPE + SPECKLE TYPE
# ==========================================================

class SectionType_PSCValue(SectionType):
    provided_value: SectionTypeParaModel = SectionTypeParaModel.PSC_VALUE


# ==========================================================
# POINT 2D PARAMETER GROUP
# ==========================================================

class CoordinateListParameter(Parameter[list[tuple[float, float]]]):
    name: Literal["2D Coordinates"] = "2D Coordinates"
    description: Literal["Ordered list of XY coordinate pairs defining a polygon"] = \
        "Ordered list of XY coordinate pairs defining a polygon"

    provided_value: list[tuple[StrictFloat, StrictFloat]] = Field(...,min_length=3)
    provided_unit: Literal["m","in"]
    base_unit: Literal["m"]
    symbol: str | None = None


# ==========================================================
# POLYGON PARAMETER GROUP
# ==========================================================

class PolygonParameterGroup_Parameters(BaseModel):
    co_ordinates: CoordinateListParameter = Field(...,alias="2D Coordinates")

class PolygonParameterGroup(ParameterGroup):
    description: Literal[
        "Polygon defined by ordered coordinate pairs"
    ] = "Polygon defined by ordered coordinate pairs"

    group_parameters: dict[
        Literal["2D Coordinates"],
        CoordinateListParameter
    ]


# ==========================================================
# DIMENSION PARAMETERS
# ==========================================================

class PSCHeight(LengthDimensionParameter):
    name: Literal["Height"] = "Height"
    symbol: Literal["H"] = "H"
    description: Literal["Overall section height"] = "Overall section height"
    provided_value: StrictFloat = Field(..., ge=0)


class PSCWidth(LengthDimensionParameter):
    name: Literal["Width"] = "Width"
    symbol: Literal["B"] = "B"
    description: Literal["Overall section width"] = "Overall section width"
    provided_value: StrictFloat = Field(..., ge=0)


class PSCTopSlabThickness(LengthDimensionParameter):
    name: Literal["Top Slab Thickness"] = "Top Slab Thickness"
    symbol: Literal["t1"] = "t1"
    description: Literal["Top slab thickness"] = "Top slab thickness"
    provided_value: StrictFloat = Field(..., ge=0)


class PSCBottomSlabThickness(LengthDimensionParameter):
    name: Literal["Bottom Slab Thickness"] = "Bottom Slab Thickness"
    symbol: Literal["t2"] = "t2"
    description: Literal["Bottom slab thickness"] = "Bottom slab thickness"
    provided_value: StrictFloat = Field(..., ge=0)

# ==========================================================
# DIMENSION GROUP (FULL PARAMETER TREE)
# ==========================================================

class SectionDimensionParameterGroup_PSCValue(ParameterGroup):
    name: Literal["Section Dimensions"] = "Section Dimensions"
    isUser: bool = False
    description: Literal["Dimensions of the PSC value section"] = "Dimensions of the PSC value section"

    group_parameters: None = None


# ==========================================================
# External Polygon (FULL PARAMETER TREE)
# ==========================================================

class PSCValueExternalPolygon(PolygonParameterGroup):
    name: Literal["External Section Polygon"] = "External Section Polygon"

class PSCValueInternalPolygonsGroup(ParameterGroup):
    name: Literal["Internal Section Polygons"] = "Internal Section Polygons"
    description: Literal["internal defined voids within the PSC Value section"]="internal defined voids within the PSC Value section"

    group_parameters: dict[str,PolygonParameterGroup] = Field(...,min_length=1)


# ==========================================================
# Section Dimesnions
# ==========================================================

class PSCValueDimensionGroupParameters(BaseModel):
    external_polygon: PSCValueExternalPolygon = Field(alias="External Section Polygon")
    internal_voids:PSCValueInternalPolygonsGroup = Field(alias="Internal Section Polygons")


class SectionDimensionParameterGroup_PSCValue(SectionDimensionParameterGroup):
    group_parameters: PSCValueDimensionGroupParameters

# ==========================================================
# PROPERTIES
# ==========================================================

class PSCValueDataObject_Properties(PSCDataObject_Properties):
    section_type: SectionType_PSCValue = Field(alias="Section Type")
    section_dimensions: SectionDimensionParameterGroup_PSCValue = Field(
        alias="Section Dimensions"
    )
    


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_PSCValue(PSCDataObject):
    APPLICATION_ID_PATTERN: ClassVar[str] = r"^SECT-[0-9]{4}-PSC-VALUE$"
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_SECTION_PSC_PSC_VALUE
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_SECTION_PSC_PSC_VALUE.value, frozen=True)

    properties: PSCValueDataObject_Properties

    @classmethod
    def create(
        cls,
        name: str,
        external_polygon: list[tuple[float, float]],
        internal_polygons: dict[str, list[tuple[float, float]]],
        description: str | None = None,
        unit: Literal["m", "in"] = "m",
        application_id: str = "psc_value_1",
        isUser: bool = True,
    ) -> "SectionDataObject_PSCValue":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            properties=(
                PSCValueDataObject_Properties(
                    **{
                        "Section Description":
                            SectionDescription(
                                isUser=isUser,
                                provided_value=description,
                            ),

                        "Section Family":
                            SectionFamily_PSC(
                                isUser=False,
                            ),

                        "Section Type":
                            SectionType_PSCValue(
                                isUser=False,
                            ),

                        "Section Dimensions":
                            SectionDimensionParameterGroup_PSCValue(
                                isUser=isUser,
                                group_parameters=(
                                    PSCValueDimensionGroupParameters(
                                        **{
                                            "External Section Polygon":
                                                PSCValueExternalPolygon(
                                                    isUser=isUser,
                                                    group_parameters={
                                                        "2D Coordinates":
                                                            CoordinateListParameter(
                                                                isUser=isUser,
                                                                provided_value=external_polygon,
                                                                base_value=external_polygon,
                                                                provided_unit=unit,
                                                                base_unit="m",
                                                            )
                                                    },
                                                ),

                                            "Internal Section Polygons":
                                                PSCValueInternalPolygonsGroup(
                                                    isUser=isUser,
                                                    group_parameters={
                                                        polygon_name:
                                                            PolygonParameterGroup(
                                                                name=polygon_name,
                                                                isUser=isUser,
                                                                group_parameters={
                                                                    "2D Coordinates":
                                                                        CoordinateListParameter(
                                                                            isUser=isUser,
                                                                            provided_value=polygon_points,
                                                                            base_value=polygon_points,
                                                                            provided_unit=unit,
                                                                            base_unit="m",
                                                                        )
                                                                },
                                                            )
                                                        for polygon_name, polygon_points
                                                        in internal_polygons.items()
                                                    },
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

    psc_section = SectionDataObject_PSCValue.create(
        name="PSC Box Example",
        application_id="SECT-0001-PSC-VALUE",
        external_polygon=[
            (-6.0, 2.5),
            (6.0, 2.5),
            (6.0, 2.35),
            (2.75, 0.0),
            (-2.75, 0.0),
            (-6.0, 2.35),
        ],

        internal_polygons={
            "Void 1": [
                (-0.25, 2.2),
                (-1.8323, 2.2),
                (-2.8323, 2.1),
                (-2.3510, 0.6155),
                (-0.25, 0.3),
            ],

            "Void 2": [
                (0.25, 2.2),
                (1.8323, 2.2),
                (2.8323, 2.1),
                (2.3510, 0.6155),
                (0.25, 0.3),
            ],
        },

        description="PSC box girder section",
        unit="m",
    )

    print(
        psc_section.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    import json                             #can be commented out after testing
    print("\n=== JSON SCHEMA ===\n")        #can be commented out after testing
    print(
        json.dumps(
            SectionDataObject_PSCValue.model_json_schema(),
            indent=4,
        )                                   #can be commented out after testing
    )