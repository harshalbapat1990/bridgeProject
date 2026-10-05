from typing import List, Union, Annotated, Literal

from pydantic import Field, BaseModel

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
    total_deck_width: QuantityParaModel
    no_of_girders: int
    girder_spacing_type: SpacingTypeParaModel
    girder_spacing_values: List[QuantityParaModel]
    stringcourse_left_barrier_width: QuantityParaModel
    stringcourse_right_barrier_width: QuantityParaModel
    cantilever_left_width: QuantityParaModel
    cantilever_right_width: QuantityParaModel


class PropertiesSpanParaModel(PropertiesBaseParaModel):
    span_index: int
    span_length: QuantityParaModel
    top_deck_level_at_end: QuantityParaModel
    cracked_extents: List[CrackedExtentsDetailsParaModel] | None = Field(default_factory=list)
    tapered_details: List[TaperedDetailsParaModel] | None = Field(default_factory=list)
    splices: List[SpliceDetailsParaModel] | None = Field(default_factory=list)
    construction_sequence_details: ConstrSequenceDetailsParaModel | None = Field(default=None)


class PropertiesGirderParaModel(PropertiesBaseParaModel):
    girder_index: int # [0, 1, ... no_of_girders - 1]


class PropertiesDiaphragmParaModel(PropertiesBaseParaModel):
    support_index: int # [0, 1, ... no_of_spans + 1]
    geometry_details: Annotated[Union[
        DiaphragmConcreteNonModelled,
        DiaphragmSteelGirderParaModel,
        DiaphragmBracingEncasedParaModel
    ], Field(discriminator="diaphragm_type")]


class PropertiesTransverseBracingParaModel(PropertiesBaseParaModel):
    bracing_orientation: ElementOrientationParaModel
    x_position_at_start_girder: QuantityParaModel
    spacing_type: SpacingTypeParaModel
    spacing_values: List[QuantityParaModel]
    no_of_bracings: int
    left_girder_index: int
    right_girder_index: int
    bracing_details: TransverseBracingDetailsParaModel


class PropertiesBracingBraceParaModel(PropertiesBaseParaModel):
    geometry_details: Annotated[Union[
        BracingBraceXtypeDetailsParaModel,
        BracingBraceKtypeDetailsBraceParaModel,
    ], Field(discriminator="bracing_type")]


class BracingBraceDetailsBaseParaModel(PropertiesBaseParaModel):
    bracing_type: BracingTypeParaModel
    vertical_offset_left_top: QuantityParaModel
    vertical_offset_right_top: QuantityParaModel
    vertical_offset_left_btm: QuantityParaModel
    vertical_offset_right_btm: QuantityParaModel


class PropertiesBracingChordParaModel(PropertiesBaseParaModel):
    vertical_offset_at_left: QuantityParaModel
    vertical_offset_at_right: QuantityParaModel


class PropertiesPlanBracingParaModel(PropertiesBaseParaModel):
    plan_bracing_type: PlanBracingTypeParaModel
    left_girder_index: int
    right_girder_index: int

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
    horizontal_offset_at_left: QuantityParaModel # previously: vertical_offset_at_start
    horizontal_offset_at_right: QuantityParaModel #previously: vertical_offset_at_end


class BracingBraceXtypeDetailsParaModel(BracingBraceDetailsBaseParaModel):
    bracing_type: Literal[BracingTypeParaModel.X_TYPE] # = Field(default=BracingTypeParaModel.X_TYPE)


class BracingBraceKtypeDetailsBraceParaModel(BracingBraceDetailsBaseParaModel):
    bracing_type: Literal[BracingTypeParaModel.K_TYPE] #BracingTypeParaModel = Field(default=BracingTypeParaModel.K_TYPE)
    horizontal_offset_right_brace: QuantityParaModel
    horizontal_offset_left_brace: QuantityParaModel


class DiaphragmConcreteNonModelled(DiaphragmDetailsBaseParaModel):
    diaphragm_type: Literal[DiaphragmTypeParaModel.CONCRETE_NON_MODELLED]
    diaphragm_thickness: QuantityParaModel


class DiaphragmSteelGirderParaModel(DiaphragmDetailsBaseParaModel):
    diaphragm_type: Literal[DiaphragmTypeParaModel.STEEL_GIRDER]


class DiaphragmBracingEncasedParaModel(DiaphragmDetailsBaseParaModel):
    diaphragm_type: Literal[DiaphragmTypeParaModel.BRACING_ENCASED]
