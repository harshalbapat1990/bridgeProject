from bda.application.mapping.base import to_pint, to_pint_optional, to_uuid
from bda.application.mapping.geometry_groups.registry import register_properties_mapper, PROPERTIES_MAPPERS

# --- ParaModel contracts ---
from bda.contracts.paramodel.groups import (
    PropertiesBridgeParaModel,
    AnalysisSettingsParaModel,
    PropertiesBaseParaModel,
    # superstructure
    PropertiesSuperstructureParaModel,
    PropertiesSpanParaModel,
    PropertiesGirderParaModel,
    PropertiesDiaphragmParaModel,
    PropertiesTransverseBracingParaModel,
    PropertiesBracingBraceParaModel,
    PropertiesBracingChordParaModel,
    PropertiesPlanBracingParaModel,
    CrackedExtentsDetailsParaModel,
    ConstrSequenceDetailsParaModel,
    TransverseBracingDetailsParaModel,
    BracingBraceXtypeDetailsParaModel,
    BracingBraceKtypeDetailsBraceParaModel,
    DiaphragmConcreteNonModelled,
    DiaphragmSteelGirderParaModel,
    DiaphragmBracingEncasedParaModel,
    # substructure
    PropertiesSupportParaModel,
    PropertiesAboveGroundParaModel,
    PropertiesPierParaModel,
    PropertiesWallParaModel,
    PropertiesCrossbeamParaModel,
    PropertiesBelowGroundParaModel,
    PropertiesPileParaModel,
    PropertiesPileCapParaModel,
    AboveGroundDetailsSolidTypeParaModel,
    AboveGroundDetailsColumnTypeParaModel,
    DeepFoundationDetailsParaModel,
    ShallowFoundationDetailsParaModel,
    # linkage
    PropertiesLinkageSupToSubParaModel,
    SingleBearingConfigurationDetailsParaModel,
    MultipleBearingConfigurationDetailsParaModel,
)
from bda.contracts.paramodel.groups.component_properties.superstructure_properties import (
    TaperedDetailsParaModel as TaperedDetailsSpanParaModel,
    SegmentDetailsParaModel, SpliceDetailsParaModel,
)
from bda.contracts.paramodel.groups.component_properties.substructure_properties import (
    TaperedDetailsParaModel as TaperedDetailsSubParaModel,
)
from bda.contracts.paramodel.groups.enums import StructuralComponentTypeParaModel

# --- Domain enums ---
from bda.domain.enums import BridgeType
from bda.domain.models.submodels import GroupProperties
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import (
    SpacingType,
    ElementOrientation,
    DiaphragmType,
    BracingType,
    PlanBracingType,
)

# --- Domain models: bridge ---
from bda.domain.models.submodels.geometry_group_props.bridge_properties import (
    GroupPropertiesBridge,
    BridgeIdealisation,
    AnalysisSettings,
)

# --- Domain models: superstructure ---
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    GroupPropertiesSuperstructure,
    GroupPropertiesSpan,
    GroupPropertiesGirder,
    GroupPropertiesDiaphragm,
    GroupPropertiesTransverseBracing,
    GroupPropertiesBrace,
    GroupPropertiesChord,
    GroupPropertiesPlanBracing,
    SegmentDetails,
    CrackedExtentsDetails,
    TaperedDetails,
    ConstrSequenceDetails,
    TransverseBracingDetails,
    DiaphragmConcreteNonModelledDetails,
    DiaphragmSteelGirderDetails,
    DiaphragmBracingEncasedDetails,
    BracingBraceXtypeDetails,
    BracingBraceKtypeDetails, SpliceDetails,
)

# --- Domain models: substructure ---
from bda.domain.models.submodels.geometry_group_props.substructure_properties import (
    GroupPropertiesSupport,
    GroupPropertiesAboveGround,
    GroupPropertiesPier,
    GroupPropertiesWall,
    GroupPropertiesCrossbeam,
    GroupPropertiesBelowGround,
    GroupPropertiesPile,
    GroupPropertiesPileCap,
    AboveGroundDetailsSolid,
    AboveGroundDetailsColumn,
    DeepFoundationDetails,
    ShallowFoundationDetails,
)

# --- Domain models: linkage ---
from bda.domain.models.submodels.geometry_group_props.linkage_properties import (
    GroupPropertiesLinkageSupToSub,
    SingleBearingConfigurationDetails,
    MultipleBearingConfigurationDetails,
)


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def map_properties(
        component_type: StructuralComponentTypeParaModel,
        dto: PropertiesBaseParaModel | None) -> GroupProperties | None:
    if dto is None:
        return None

    mapper = PROPERTIES_MAPPERS.get(component_type)
    if mapper is None:
        raise ValueError(f"No mapper for {component_type.value}")

    return mapper(dto)


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------

def map_analysis_settings(dto: AnalysisSettingsParaModel) -> AnalysisSettings:
    return AnalysisSettings(girder_mesh_divisor=dto.mesh_divisor)


@register_properties_mapper(StructuralComponentTypeParaModel.BRIDGE)
def map_bridge_properties(dto: PropertiesBridgeParaModel) -> GroupPropertiesBridge:
    return GroupPropertiesBridge(
        type=BridgeType(dto.bridge_type.value),
        idealisation=BridgeIdealisation(dto.bridge_idealisation.value),
        no_of_spans=dto.no_of_spans,
        analysis_settings=map_analysis_settings(dto.analysis_settings),
        top_deck_level=to_pint(dto.top_deck_level),
    )


# ---------------------------------------------------------------------------
# Superstructure
# ---------------------------------------------------------------------------

def _map_segment_details(dto: SegmentDetailsParaModel) -> SegmentDetails:
    return SegmentDetails(x_start=to_pint(dto.x_start))


def _map_cracked_extends(dto: CrackedExtentsDetailsParaModel) -> CrackedExtentsDetails:
    return CrackedExtentsDetails(
        x_start=to_pint(dto.x_start),
        x_end=to_pint(dto.x_end),
    )


def _map_tapered_details_span(dto: TaperedDetailsSpanParaModel) -> TaperedDetails:
    return TaperedDetails(
        x_start=to_pint(dto.x_start),
        x_end=to_pint(dto.x_end),
        section_id=to_uuid(dto.section_id),
    )


def _map_splice_details(dto: SpliceDetailsParaModel) -> SpliceDetails:
    return SpliceDetails(
        x_start=to_pint(dto.x_start),
        section_id=to_uuid(dto.section_id),
    )


def _map_constr_sequence_details(dto: ConstrSequenceDetailsParaModel) -> ConstrSequenceDetails:
    return ConstrSequenceDetails(
        segments=[_map_segment_details(s) for s in dto.segments],
        pouring_orientation=ElementOrientation(dto.pouring_orientation.value),
    )


def _map_transverse_bracing_details(dto: TransverseBracingDetailsParaModel) -> TransverseBracingDetails:
    return TransverseBracingDetails(
        horizontal_offset_at_left=to_pint(dto.horizontal_offset_at_left),
        horizontal_offset_at_right=to_pint(dto.horizontal_offset_at_right),
    )


@register_properties_mapper(StructuralComponentTypeParaModel.SUPERSTRUCTURE)
def map_superstructure_properties(dto: PropertiesSuperstructureParaModel) -> GroupPropertiesSuperstructure:
    return GroupPropertiesSuperstructure(
        total_deck_width=to_pint(dto.total_deck_width),
        no_of_girders=dto.no_of_girders,
        girder_spacing_type=SpacingType(dto.girder_spacing_type.value),
        girder_spacing_values=[to_pint(v) for v in dto.girder_spacing_values],
        stringcourse_left_barrier_width=to_pint(dto.stringcourse_left_barrier_width),
        stringcourse_right_barrier_width=to_pint(dto.stringcourse_right_barrier_width),
        cantilever_left_width=to_pint(dto.cantilever_left_width),
        cantilever_right_width=to_pint(dto.cantilever_right_width),
    )


@register_properties_mapper(StructuralComponentTypeParaModel.SPAN)
def map_span_properties(dto: PropertiesSpanParaModel) -> GroupPropertiesSpan:
    return GroupPropertiesSpan(
        span_index=dto.span_index,
        span_length=to_pint(dto.span_length),
        top_deck_level_at_end=to_pint(dto.top_deck_level_at_end),
        cracked_extends=[_map_cracked_extends(c) for c in (dto.cracked_extents or [])],
        tapered_details=[_map_tapered_details_span(t) for t in (dto.tapered_details or [])],
        splices=[_map_splice_details(s) for s in (dto.splices or [])],
        construction_sequence_details=(
            _map_constr_sequence_details(dto.construction_sequence_details)
            if dto.construction_sequence_details else None
        ),
    )


@register_properties_mapper(StructuralComponentTypeParaModel.GIRDER)
def map_girder_properties(dto: PropertiesGirderParaModel) -> GroupPropertiesGirder:
    return GroupPropertiesGirder(girder_index=dto.girder_index)


def _map_diaphragm_details(dto):
    if isinstance(dto, DiaphragmConcreteNonModelled):
        return DiaphragmConcreteNonModelledDetails(
            diaphragm_thickness=to_pint(dto.diaphragm_thickness)
        )
    if isinstance(dto, DiaphragmSteelGirderParaModel):
        return DiaphragmSteelGirderDetails()
    if isinstance(dto, DiaphragmBracingEncasedParaModel):
        return DiaphragmBracingEncasedDetails()
    raise ValueError(f"Unknown diaphragm detail type: {type(dto)}")


@register_properties_mapper(StructuralComponentTypeParaModel.DIAPHRAGM)
def map_diaphragm_properties(dto: PropertiesDiaphragmParaModel) -> GroupPropertiesDiaphragm:
    return GroupPropertiesDiaphragm(
        support_index=dto.support_index,
        geometry_details=_map_diaphragm_details(dto.geometry_details),
    )


@register_properties_mapper(StructuralComponentTypeParaModel.TRANSVERSE_BRACING)
def map_transverse_bracing_properties(dto: PropertiesTransverseBracingParaModel) -> GroupPropertiesTransverseBracing:
    return GroupPropertiesTransverseBracing(
        bracing_orientation=ElementOrientation(dto.bracing_orientation.value),
        x_position_at_start_girder=to_pint(dto.x_position_at_start_girder),
        spacing_type=SpacingType(dto.spacing_type.value),
        spacing_values=[to_pint(v) for v in dto.spacing_values],
        no_of_bracings=dto.no_of_bracings,
        left_girder_index=dto.left_girder_index,
        right_girder_index=dto.right_girder_index,
        bracing_details=_map_transverse_bracing_details(dto.bracing_details),
    )


def _map_brace_details(dto):
    if isinstance(dto, BracingBraceXtypeDetailsParaModel):
        return BracingBraceXtypeDetails(
            vertical_offset_left_top=to_pint(dto.vertical_offset_left_top),
            vertical_offset_right_top=to_pint(dto.vertical_offset_right_top),
            vertical_offset_left_bottom=to_pint(dto.vertical_offset_left_btm),
            vertical_offset_right_bottom=to_pint(dto.vertical_offset_right_btm)
        )
    if isinstance(dto, BracingBraceKtypeDetailsBraceParaModel):
        return BracingBraceKtypeDetails(
            vertical_offset_left_top=to_pint(dto.vertical_offset_left_top),
            vertical_offset_right_top=to_pint(dto.vertical_offset_right_top),
            vertical_offset_left_bottom=to_pint(dto.vertical_offset_left_btm),
            vertical_offset_right_bottom=to_pint(dto.vertical_offset_right_btm),
            horizontal_offset_right_brace=to_pint(dto.horizontal_offset_right_brace),
            horizontal_offset_left_brace=to_pint(dto.horizontal_offset_left_brace),
        )
    raise ValueError(f"Unknown brace detail type: {type(dto)}")


@register_properties_mapper(StructuralComponentTypeParaModel.BRACE)
def map_brace_properties(dto: PropertiesBracingBraceParaModel) -> GroupPropertiesBrace:
    return GroupPropertiesBrace(geometry_details=_map_brace_details(dto.geometry_details))


@register_properties_mapper(StructuralComponentTypeParaModel.CHORD)
def map_chord_properties(dto: PropertiesBracingChordParaModel) -> GroupPropertiesChord:
    return GroupPropertiesChord(
        vertical_offset_at_left=to_pint(dto.vertical_offset_at_left),
        vertical_offset_at_right=to_pint(dto.vertical_offset_at_right),
    )


@register_properties_mapper(StructuralComponentTypeParaModel.PLAN_BRACING)
def map_plan_bracing_properties(dto: PropertiesPlanBracingParaModel) -> GroupPropertiesPlanBracing:
    return GroupPropertiesPlanBracing(
        plan_bracing_type=PlanBracingType(dto.plan_bracing_type.value),
        left_girder_index=dto.left_girder_index,
        right_girder_index=dto.right_girder_index,
    )


# ---------------------------------------------------------------------------
# Substructure
# ---------------------------------------------------------------------------

def _map_above_ground_details(dto):
    if isinstance(dto, AboveGroundDetailsSolidTypeParaModel):
        return AboveGroundDetailsSolid(no_of_walls=dto.no_of_walls)
    if isinstance(dto, AboveGroundDetailsColumnTypeParaModel):
        return AboveGroundDetailsColumn(no_of_piers=dto.no_of_piers)
    raise ValueError(f"Unknown above-ground detail type: {type(dto)}")


def _map_foundation_details(dto):
    if isinstance(dto, DeepFoundationDetailsParaModel):
        return DeepFoundationDetails(no_of_piles=dto.no_of_piles)
    if isinstance(dto, ShallowFoundationDetailsParaModel):
        return ShallowFoundationDetails()
    raise ValueError(f"Unknown foundation detail type: {type(dto)}")


def _map_tapered_details_substructure(dto: TaperedDetailsSubParaModel) -> TaperedDetails:
    return TaperedDetails(
        x_start=to_pint(dto.x_start),
        x_end=to_pint(dto.x_end),
        section_id=to_uuid(dto.section_id),
    )


@register_properties_mapper(StructuralComponentTypeParaModel.SUPPORT)
def map_support_properties(dto: PropertiesSupportParaModel) -> GroupPropertiesSupport:
    return GroupPropertiesSupport(
        support_index=dto.support_index,
        skew_angle=to_pint(dto.skew_angle),
        bearing_underside_level=to_pint(dto.bearing_underside_level),
        orientation=ElementOrientation(dto.orientation.value),
    )


@register_properties_mapper(StructuralComponentTypeParaModel.ABOVE_GROUND)
def map_above_ground_properties(dto: PropertiesAboveGroundParaModel) -> GroupPropertiesAboveGround:
    return GroupPropertiesAboveGround(details=_map_above_ground_details(dto.details))


@register_properties_mapper(StructuralComponentTypeParaModel.PIER)
def map_pier_properties(dto: PropertiesPierParaModel) -> GroupPropertiesPier:
    return GroupPropertiesPier(transverse_offset=to_pint(dto.transverse_offset))


@register_properties_mapper(StructuralComponentTypeParaModel.WALL)
def map_wall_properties(dto: PropertiesWallParaModel) -> GroupPropertiesWall:
    return GroupPropertiesWall(element_thickness=to_pint(dto.element_thickness))


@register_properties_mapper(StructuralComponentTypeParaModel.CROSSBEAM)
def map_crossbeam_properties(dto: PropertiesCrossbeamParaModel) -> GroupPropertiesCrossbeam:
    return GroupPropertiesCrossbeam(
        element_length=to_pint(dto.element_length),
        tapered_details=[_map_tapered_details_substructure(t) for t in dto.tapered_details],
    )


@register_properties_mapper(StructuralComponentTypeParaModel.BELOW_GROUND)
def map_below_ground_properties(dto: PropertiesBelowGroundParaModel) -> GroupPropertiesBelowGround:
    return GroupPropertiesBelowGround(
        foundation_details=_map_foundation_details(dto.foundation_details)
    )


@register_properties_mapper(StructuralComponentTypeParaModel.PILE)
def map_pile_properties(dto: PropertiesPileParaModel) -> GroupPropertiesPile:
    return GroupPropertiesPile(
        pile_index=dto.pile_index,
        pile_length=to_pint(dto.pile_length),
        offset_along_support_line=to_pint(dto.offset_along_support_line),
        offset_normal_to_support_line=to_pint(dto.offset_normal_to_support_line),
        spring_spacing=[to_pint(s) for s in dto.spring_spacing],
    )


@register_properties_mapper(StructuralComponentTypeParaModel.PILE_CAP)
def map_pile_cap_properties(dto: PropertiesPileCapParaModel) -> GroupPropertiesPileCap:
    return GroupPropertiesPileCap(
        top_of_pile_cap_level=to_pint(dto.top_of_pile_cap_level),
        element_length=to_pint(dto.element_length),
    )


# ---------------------------------------------------------------------------
# Linkage
# ---------------------------------------------------------------------------

def _map_bearing_alignment_details(dto):
    if isinstance(dto, SingleBearingConfigurationDetailsParaModel):
        return SingleBearingConfigurationDetails(no_of_bearings=dto.no_of_bearings)
    if isinstance(dto, MultipleBearingConfigurationDetailsParaModel):
        return MultipleBearingConfigurationDetails(
            no_of_bearings=dto.no_of_bearings,
            bearing_spacing_type=SpacingType(dto.bearing_spacing_type.value),
            bearing_spacing=[to_pint(s) for s in dto.bearing_spacing],
        )
    raise ValueError(f"Unknown bearing alignment detail type: {type(dto)}")


@register_properties_mapper(StructuralComponentTypeParaModel.SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS)
def map_linkage_sup_to_sub_properties(dto: PropertiesLinkageSupToSubParaModel) -> GroupPropertiesLinkageSupToSub:
    return GroupPropertiesLinkageSupToSub(
        support_index=dto.support_index,
        bearing_configuration_details=_map_bearing_alignment_details(dto.bearing_configuration_details),
    )

