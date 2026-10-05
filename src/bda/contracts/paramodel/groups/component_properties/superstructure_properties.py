from typing import List, Union, Annotated, Literal

from pydantic import Field, BaseModel, AliasChoices, AliasPath

from bda.contracts.paramodel.groups.component_properties.properties_base import PropertiesBaseParaModel, SegmentDetailsParaModel
from bda.contracts.paramodel.groups.enums import DiaphragmTypeParaModel, SpacingTypeParaModel, \
    ElementOrientationParaModel, BracingTypeParaModel, PlanBracingTypeParaModel

from bda.contracts.shared import QuantityParaModel

# -------------------------
# Abstract base classes
# -------------------------

class DiaphragmDetailsBaseParaModel(BaseModel):
    """
    Abstract base class for diaphragm properties.
    """
    diaphragm_type: DiaphragmTypeParaModel

# --------------------------------------------------
# Main Properties of the Superstructure group
# --------------------------------------------------

class PropertiesSuperstructureParaModel(PropertiesBaseParaModel):
    total_deck_width: QuantityParaModel = Field(validation_alias=AliasChoices("total_deck_width", AliasPath("Total Deck Width")))
    no_of_girders: int = Field(validation_alias=AliasChoices("no_of_girders", AliasPath("Number of Girders", "provided_value")))
    girder_spacing_type: SpacingTypeParaModel = Field(validation_alias=AliasChoices("girder_spacing_type", AliasPath("Girder Spacing Type", "provided_value")))
    girder_spacing_values: List[QuantityParaModel] = Field(validation_alias=AliasChoices("girder_spacing_values", AliasPath("Girder Spacing Values", "provided_value")))
    stringcourse_left_barrier_width: QuantityParaModel = Field(validation_alias=AliasChoices("stringcourse_left_barrier_width", AliasPath("Stringcourse Left Barrier Width")))
    stringcourse_right_barrier_width: QuantityParaModel = Field(validation_alias=AliasChoices("stringcourse_right_barrier_width", AliasPath("Stringcourse Right Barrier Width")))
    cantilever_left_width: QuantityParaModel = Field(validation_alias=AliasChoices("cantilever_left_width", AliasPath("Cantilever Left Width")))
    cantilever_right_width: QuantityParaModel = Field(validation_alias=AliasChoices("cantilever_right_width", AliasPath("Cantilever Right Width")))


class PropertiesSpanParaModel(PropertiesBaseParaModel):
    span_index: int = Field(validation_alias=AliasChoices("span_index", AliasPath("Span Index", "provided_value")))
    span_length: QuantityParaModel = Field(validation_alias=AliasChoices("span_length", AliasPath("Span Length")))
    top_deck_level_at_end: QuantityParaModel = Field(validation_alias=AliasChoices("top_deck_level_at_end", AliasPath("Top Deck Level At End")))
    cracked_extents: List[CrackedExtentsDetailsParaModel] | None = Field(default_factory=list, validation_alias=AliasChoices("cracked_extents", AliasPath("Cracked Extents", "group_parameters")))
    tapered_details: List[TaperedDetailsParaModel] | None = Field(default_factory=list, validation_alias=AliasChoices("tapered_details", AliasPath("Tapered Details", "group_parameters")))
    splices: List[SpliceDetailsParaModel] | None = Field(default_factory=list, validation_alias=AliasChoices("splices", AliasPath("Splices", "group_parameters")))
    construction_sequence_details: ConstrSequenceDetailsParaModel | None = Field(default=None, validation_alias=AliasChoices("construction_sequence_details", AliasPath("Construction Sequence Details", "group_parameters")))


class PropertiesGirderParaModel(PropertiesBaseParaModel):
    girder_index: int = Field(validation_alias=AliasChoices("girder_index", AliasPath("Girder Index", "provided_value"))) # [0, 1, ... no_of_girders - 1]


class PropertiesDiaphragmParaModel(PropertiesBaseParaModel):
    support_index: int = Field(validation_alias=AliasChoices("support_index", AliasPath("Support Index", "provided_value"))) # [0, 1, ... no_of_spans + 1]
    geometry_details: Annotated[Union[
        DiaphragmConcreteNonModelled,
        DiaphragmSteelGirderParaModel,
        DiaphragmBracingEncasedParaModel
    ], Field(discriminator="diaphragm_type")] = Field(validation_alias=AliasChoices("geometry_details", AliasPath("Geometry Details", "group_parameters")))


class PropertiesTransverseBracingParaModel(PropertiesBaseParaModel):
    bracing_orientation: ElementOrientationParaModel = Field(validation_alias=AliasChoices("bracing_orientation", AliasPath("Bracing Orientation", "provided_value")))
    x_position_at_start_girder: QuantityParaModel = Field(validation_alias=AliasChoices("x_position_at_start_girder", AliasPath("Start Position of First Bracing")))
    spacing_type: SpacingTypeParaModel = Field(validation_alias=AliasChoices("spacing_type", AliasPath("Bracing Spacing", "provided_value")))
    spacing_values: List[QuantityParaModel] = Field(validation_alias=AliasChoices("spacing_values", AliasPath("Bracing Spacing Distances", "provided_value")))
    no_of_bracings: int = Field(validation_alias=AliasChoices("no_of_bracings", AliasPath("Number of Bracings", "provided_value")))
    left_girder_index: int = Field(validation_alias=AliasChoices("left_girder_index", AliasPath("Left Girder Index", "provided_value")))
    right_girder_index: int = Field(validation_alias=AliasChoices("right_girder_index", AliasPath("Right Girder Index", "provided_value")))
    bracing_details: TransverseBracingDetailsParaModel = Field(validation_alias=AliasChoices("bracing_details", AliasPath("Bracing Details", "group_parameters")))


class PropertiesBracingBraceParaModel(PropertiesBaseParaModel):
    geometry_details: Annotated[Union[
        BracingBraceXtypeDetailsParaModel,
        BracingBraceKtypeDetailsBraceParaModel,
    ], Field(discriminator="bracing_type")] = Field(validation_alias=AliasChoices("geometry_details", AliasPath("Geometry Details", "group_parameters")))


class BracingBraceDetailsBaseParaModel(PropertiesBaseParaModel):
    bracing_type: BracingTypeParaModel
    vertical_offset_left_top: QuantityParaModel = Field(validation_alias=AliasChoices("vertical_offset_left_top", AliasPath("Vertical Offset at Left Top")))
    vertical_offset_right_top: QuantityParaModel = Field(validation_alias=AliasChoices("vertical_offset_right_top", AliasPath("Vertical Offset at Right Top")))
    vertical_offset_left_btm: QuantityParaModel = Field(validation_alias=AliasChoices("vertical_offset_left_btm", AliasPath("Vertical Offset at Left Bottom")))
    vertical_offset_right_btm: QuantityParaModel = Field(validation_alias=AliasChoices("vertical_offset_right_btm", AliasPath("Vertical Offset at Right Bottom")))


class PropertiesBracingChordParaModel(PropertiesBaseParaModel):
    vertical_offset_at_left: QuantityParaModel = Field(validation_alias=AliasChoices("vertical_offset_at_left", AliasPath("Vertical Offset at Left")))
    vertical_offset_at_right: QuantityParaModel = Field(validation_alias=AliasChoices("vertical_offset_at_right", AliasPath("Vertical Offset at Right")))


class PropertiesPlanBracingParaModel(PropertiesBaseParaModel):
    plan_bracing_type: PlanBracingTypeParaModel = Field(validation_alias=AliasChoices("plan_bracing_type", AliasPath("Plan Bracing Type", "provided_value")))
    left_girder_index: int = Field(validation_alias=AliasChoices("left_girder_index", AliasPath("Left Girder Index", "provided_value")))
    right_girder_index: int = Field(validation_alias=AliasChoices("right_girder_index", AliasPath("Right Girder Index", "provided_value")))

# --------------------------------------------------
# Other Properties
# --------------------------------------------------

class CrackedExtentsDetailsParaModel(SegmentDetailsParaModel):
    x_end: QuantityParaModel


class TaperedDetailsParaModel(SegmentDetailsParaModel):
    x_end: QuantityParaModel
    section_id: str


class SpliceDetailsParaModel(SegmentDetailsParaModel):
    section_id: str

class ConstrSequenceDetailsParaModel(BaseModel):
    segments: List[SegmentDetailsParaModel]
    pouring_orientation: ElementOrientationParaModel


class TransverseBracingDetailsParaModel(BaseModel):
    horizontal_offset_at_left: QuantityParaModel = Field(validation_alias=AliasChoices("horizontal_offset_at_left", AliasPath("Horizontal Offset to Left Girder"))) # previously: vertical_offset_at_start
    horizontal_offset_at_right: QuantityParaModel = Field(validation_alias=AliasChoices("horizontal_offset_at_right", AliasPath("Horizontal Offset to Right Girder"))) #previously: vertical_offset_at_end


class BracingBraceXtypeDetailsParaModel(BracingBraceDetailsBaseParaModel):
    bracing_type: Literal[BracingTypeParaModel.X_TYPE] # = Field(default=BracingTypeParaModel.X_TYPE)


class BracingBraceKtypeDetailsBraceParaModel(BracingBraceDetailsBaseParaModel):
    bracing_type: Literal[BracingTypeParaModel.K_TYPE] #BracingTypeParaModel = Field(default=BracingTypeParaModel.K_TYPE)
    horizontal_offset_right_brace: QuantityParaModel = Field(validation_alias=AliasChoices("horizontal_offset_right_brace", AliasPath("Horizontal Offset at Right")))
    horizontal_offset_left_brace: QuantityParaModel = Field(validation_alias=AliasChoices("horizontal_offset_left_brace", AliasPath("Horizontal Offset at Left")))


class DiaphragmConcreteNonModelled(DiaphragmDetailsBaseParaModel):
    diaphragm_type: Literal[DiaphragmTypeParaModel.CONCRETE_NON_MODELLED]
    diaphragm_thickness: QuantityParaModel = Field(validation_alias=AliasChoices("diaphragm_thickness", AliasPath("Diaphragm Thickness")))


class DiaphragmSteelGirderParaModel(DiaphragmDetailsBaseParaModel):
    diaphragm_type: Literal[DiaphragmTypeParaModel.STEEL_GIRDER]


class DiaphragmBracingEncasedParaModel(DiaphragmDetailsBaseParaModel):
    diaphragm_type: Literal[DiaphragmTypeParaModel.BRACING_ENCASED]
