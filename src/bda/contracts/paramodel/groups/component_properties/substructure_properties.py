from typing import List, Union, Annotated, Literal

from pydantic import Field, BaseModel

from bda.contracts.paramodel.groups.enums import (
    SupportTypeParaModel,
    FoundationTypeParaModel,
    ElementOrientationParaModel
)

from bda.contracts.shared import QuantityParaModel

from bda.contracts.paramodel.groups.component_properties.properties_base import PropertiesBaseParaModel, SegmentDetailsParaModel

# -------------------------
# Abstract base classes
# -------------------------

class AboveGroundDetailsBaseParaModel(BaseModel):
    support_type: SupportTypeParaModel


class FoundationDetailsBaseParaModel(BaseModel):
    foundation_type: FoundationTypeParaModel

# --------------------------------------------------
# Main Properties of the Substructure group
# --------------------------------------------------

class PropertiesSupportParaModel(PropertiesBaseParaModel):
    support_index: int
    skew_angle: QuantityParaModel # assumed to be a constant value for all supports at MVP stage
    bearing_underside_level: QuantityParaModel
    orientation: ElementOrientationParaModel


class PropertiesAboveGroundParaModel(PropertiesBaseParaModel):
    details: Annotated[Union[
        AboveGroundDetailsSolidTypeParaModel,
        AboveGroundDetailsColumnTypeParaModel
    ], Field(discriminator="support_type")]


class PropertiesPierParaModel(PropertiesBaseParaModel):
    transverse_offset: QuantityParaModel


class PropertiesWallParaModel(PropertiesBaseParaModel):
    element_thickness: QuantityParaModel


class PropertiesCrossbeamParaModel(PropertiesBaseParaModel):
    element_length: QuantityParaModel
    tapered_details: List[TaperedDetailsParaModel]


class PropertiesBelowGroundParaModel(PropertiesBaseParaModel):
    foundation_details: Annotated[Union[
        DeepFoundationDetailsParaModel,
        ShallowFoundationDetailsParaModel,
    ], Field(discriminator="foundation_type")]


class PropertiesPileParaModel(PropertiesBaseParaModel):
    pile_index: int
    pile_length: QuantityParaModel
    offset_along_support_line: QuantityParaModel
    offset_normal_to_support_line: QuantityParaModel
    spring_spacing: List[QuantityParaModel]


class PropertiesPileCapParaModel(PropertiesBaseParaModel):
    '''
    NOTE: The dimensions of the pile cap are represented by the dimensions of a rectangular cross-section assigned to the group
    '''
    top_of_pile_cap_level: QuantityParaModel
    element_length: QuantityParaModel

# --------------------------------------------------
# Other Properties
# --------------------------------------------------

class AboveGroundDetailsSolidTypeParaModel(AboveGroundDetailsBaseParaModel):
    support_type: Literal[SupportTypeParaModel.SOLID_TYPE]
    no_of_walls: int


class AboveGroundDetailsColumnTypeParaModel(AboveGroundDetailsBaseParaModel):
    support_type: Literal[SupportTypeParaModel.COLUMN_TYPE]
    no_of_piers: int


class TaperedDetailsParaModel(SegmentDetailsParaModel):
    x_end: QuantityParaModel
    section_id: str


class DeepFoundationDetailsParaModel(FoundationDetailsBaseParaModel):
    foundation_type: Literal[FoundationTypeParaModel.DEEP]
    no_of_piles: int


class ShallowFoundationDetailsParaModel(FoundationDetailsBaseParaModel):
    foundation_type: Literal[FoundationTypeParaModel.SHALLOW]
