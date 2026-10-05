from typing import List, Union, Annotated, Literal

from pydantic import Field, BaseModel, AliasChoices, AliasPath

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
    support_index: int = Field(validation_alias=AliasChoices("support_index", AliasPath("Support Index", "provided_value")))
    skew_angle: QuantityParaModel = Field(validation_alias=AliasChoices("skew_angle", AliasPath("Skew Angle")))
    bearing_underside_level: QuantityParaModel = Field(validation_alias=AliasChoices("bearing_underside_level", AliasPath("Bearing Underside Level")))
    orientation: ElementOrientationParaModel = Field(validation_alias=AliasChoices("orientation", AliasPath("Element Orientation", "provided_value")))


class PropertiesAboveGroundParaModel(PropertiesBaseParaModel):
    details: Annotated[Union[
        AboveGroundDetailsSolidTypeParaModel,
        AboveGroundDetailsColumnTypeParaModel
    ], Field(discriminator="support_type")] = Field(validation_alias=AliasChoices("details", AliasPath("Details", "group_parameters")))


class PropertiesPierParaModel(PropertiesBaseParaModel):
    transverse_offset: QuantityParaModel = Field(validation_alias=AliasChoices("transverse_offset", AliasPath("Transverse Offset")))


class PropertiesWallParaModel(PropertiesBaseParaModel):
    element_thickness: QuantityParaModel = Field(validation_alias=AliasChoices("element_thickness", AliasPath("Element Thickness")))


class PropertiesCrossbeamParaModel(PropertiesBaseParaModel):
    element_length: QuantityParaModel = Field(validation_alias=AliasChoices("element_length", AliasPath("Element Length")))
    tapered_details: List[TaperedDetailsParaModel] = Field(validation_alias=AliasChoices("tapered_details", AliasPath("Tapered Details", "group_parameters")))


class PropertiesBelowGroundParaModel(PropertiesBaseParaModel):
    foundation_details: Annotated[Union[
        DeepFoundationDetailsParaModel,
        ShallowFoundationDetailsParaModel,
    ], Field(discriminator="foundation_type")] = Field(validation_alias=AliasChoices("foundation_details", AliasPath("Foundation Details", "group_parameters")))


class PropertiesPileParaModel(PropertiesBaseParaModel):
    pile_index: int = Field(validation_alias=AliasChoices("pile_index", AliasPath("Pile Index", "provided_value")))
    pile_length: QuantityParaModel = Field(validation_alias=AliasChoices("pile_length", AliasPath("Pile Length")))
    offset_along_support_line: QuantityParaModel = Field(validation_alias=AliasChoices("offset_along_support_line", AliasPath("Offset Along Support Line")))
    offset_normal_to_support_line: QuantityParaModel = Field(validation_alias=AliasChoices("offset_normal_to_support_line", AliasPath("Offset Normal To Support Line")))
    spring_spacing: List[QuantityParaModel] = Field(validation_alias=AliasChoices("spring_spacing", AliasPath("Spring Spacing", "provided_value")))


class PropertiesPileCapParaModel(PropertiesBaseParaModel):
    '''
    NOTE: The dimensions of the pile cap are represented by the dimensions of a rectangular cross-section assigned to the group
    '''
    top_of_pile_cap_level: QuantityParaModel = Field(validation_alias=AliasChoices("top_of_pile_cap_level", AliasPath("Top Of Pile Cap Level")))
    element_length: QuantityParaModel = Field(validation_alias=AliasChoices("element_length", AliasPath("Element Length")))

# --------------------------------------------------
# Other Properties
# --------------------------------------------------

class AboveGroundDetailsSolidTypeParaModel(AboveGroundDetailsBaseParaModel):
    support_type: Literal[SupportTypeParaModel.SOLID_TYPE]
    no_of_walls: int = Field(validation_alias=AliasChoices("no_of_walls", AliasPath("Number Of Walls", "provided_value")))


class AboveGroundDetailsColumnTypeParaModel(AboveGroundDetailsBaseParaModel):
    support_type: Literal[SupportTypeParaModel.COLUMN_TYPE]
    no_of_piers: int = Field(validation_alias=AliasChoices("no_of_piers", AliasPath("Number Of Piers", "provided_value")))


class TaperedDetailsParaModel(SegmentDetailsParaModel):
    x_end: QuantityParaModel
    section_id: str


class DeepFoundationDetailsParaModel(FoundationDetailsBaseParaModel):
    foundation_type: Literal[FoundationTypeParaModel.DEEP]
    no_of_piles: int = Field(validation_alias=AliasChoices("no_of_piles", AliasPath("Number Of Piles", "provided_value")))


class ShallowFoundationDetailsParaModel(FoundationDetailsBaseParaModel):
    foundation_type: Literal[FoundationTypeParaModel.SHALLOW]
