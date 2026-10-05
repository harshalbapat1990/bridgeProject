from __future__ import annotations

from typing import Literal
from pydantic import Field, StrictFloat, BaseModel

from bda.contracts.speckle_contracts.bda_analytical.sections.psc_family.psc_family_data_object import (
    PSCDataObject,
    PSCDataObject_Properties,
)

from bda.contracts.speckle_contracts.bda_analytical.sections.general_section_data_object_parameters import (
    SectionType,
    LengthDimensionParameter,
)

from bda.contracts.speckle_contracts.base_objects import (
    DataObjectSpeckleType,
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


class PSCValueDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Section:PSC:PSC Value"
    ] = "Objects.Data.DataObject:BDA_Section:PSC:PSC Value"


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
    description: Literal["internal defined voids within the PSC Value section"]

    group_parameters: dict[str,PolygonParameterGroup] = Field(...,min_length=1)


# ==========================================================
# Section Dimesnions
# ==========================================================

class PSCValueDimensionGroupParameters(BaseModel):
    external_polygon: PSCValueExternalPolygon = Field(alias="External Section Polygon")
    internal_voids:PSCValueInternalPolygonsGroup = Field(alias="Internal Section Polygons")


class SectionDimensionParameterGroup_PSCValue(ParameterGroup):
    group_parameters: PSCValueDimensionGroupParameters

# ==========================================================
# PROPERTIES
# ==========================================================

class PSCValueDataObject_Properties(PSCDataObject_Properties):
    bda_speckle_type: PSCValueDataObjectSpeckleType

    section_type: SectionType_PSCValue = Field(alias="Section Type")
    section_dimensions: SectionDimensionParameterGroup_PSCValue = Field(
        alias="Section Dimensions"
    )
    


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_PSCValue(PSCDataObject):
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:PSC:PSC Value"
    ]

    properties: PSCValueDataObject_Properties