from pathlib import Path
from uuid import UUID

import pytest

from bda.application.mapping.base import to_uuid
from bda.application.mapping.geometry_groups.group_mapper import GeometryGroupMapper
from bda.domain.models.submodels.geometry_group_props.bridge_properties import GroupPropertiesBridge

# --- Domain group classes ---
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    GroupPropertiesSuperstructure,
    GroupPropertiesSpan,
    GroupPropertiesGirder,
    GroupPropertiesDiaphragm,
    GroupPropertiesTransverseBracing,
    GroupPropertiesBrace,
    GroupPropertiesChord,
    GroupPropertiesPlanBracing,
    DiaphragmConcreteNonModelledDetails,
    DiaphragmSteelGirderDetails,
    DiaphragmBracingEncasedDetails,
    BracingBraceKtypeDetails,
    TransverseBracingDetails,
    ConstrSequenceDetails,
    CrackedExtentsDetails,
    TaperedDetails,
)
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
    DeepFoundationDetails,
)
from bda.domain.models.submodels.geometry_group_props.linkage_properties import (
    GroupPropertiesLinkageSupToSub,
    SingleBearingConfigurationDetails,
    MultipleBearingConfigurationDetails,
)
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import (
    SpacingType,
    ElementOrientation,
    PlanBracingType,
)

from bda.infrastructure.data_providers import DataFileProvider


# ---------------------------------------------------------------------------
# Index map (matches order in geometry_groups.json)
# ---------------------------------------------------------------------------
# 0  Bridge
# 1  Superstructure
# 2  Span
# 3  Girder
# 4  Diaphragm – concrete-non-modelled
# 5  Diaphragm – steel-girder
# 6  Diaphragm – bracing-encased
# 7  Transverse bracing
# 8  Brace (k-type)
# 9  Chord
# 10 Plan bracing
# 11 Support
# 12 Above-ground (solid-type)
# 13 Pier
# 14 Wall
# 15 Crossbeam
# 16 Below-ground (deep)
# 17 Pile
# 18 Pile-cap
# 19 Linkage – singular
# 20 Linkage – multiple
# 21 Nested bridge (bridge → superstructure → span → girder)


class TestGeometryGroupMapper:
    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    @pytest.fixture(scope="session")
    def fixtures_path(self):
        return Path(__file__).parent / "fixtures"

    @pytest.fixture(scope="session")
    def provider(self, fixtures_path):
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture(scope="session")
    def groups(self, provider):
        return provider.get_geometry_groups_for_project()

    # ------------------------------------------------------------------
    # Bridge (index 0)
    # ------------------------------------------------------------------

    def test_bridge_group_mapping(self, groups):
        result = GeometryGroupMapper.map_group(groups[0])
        assert isinstance(result.properties, GroupPropertiesBridge)

    def test_bridge_group_id_is_uuid(self, groups):
        result = GeometryGroupMapper.map_group(groups[0])
        assert isinstance(result.guid, UUID)

    def test_bridge_group_name(self, groups):
        result = GeometryGroupMapper.map_group(groups[0])
        assert result.name == "Test Bridge"

    def test_bridge_properties_no_of_spans(self, groups):
        result = GeometryGroupMapper.map_group(groups[0])
        assert result.properties.no_of_spans == 3

    def test_bridge_properties_analysis_settings(self, groups):
        result = GeometryGroupMapper.map_group(groups[0])
        assert result.properties.analysis_settings.girder_mesh_divisor == 20

    # ------------------------------------------------------------------
    # Superstructure (index 1)
    # ------------------------------------------------------------------

    def test_superstructure_properties_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[1])
        assert isinstance(result.properties, GroupPropertiesSuperstructure)

    def test_superstructure_properties_no_of_girders(self, groups):
        result = GeometryGroupMapper.map_group(groups[1])
        assert result.properties.no_of_girders == 5

    def test_superstructure_properties_spacing_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[1])
        assert result.properties.girder_spacing_type == SpacingType.UNIFORM

    def test_superstructure_properties_spacing_values_length(self, groups):
        result = GeometryGroupMapper.map_group(groups[1])
        assert len(result.properties.girder_spacing_values) == 1

    def test_superstructure_properties_total_deck_width(self, groups):
        result = GeometryGroupMapper.map_group(groups[1])
        assert result.properties.total_deck_width.magnitude == 12.0

    # ------------------------------------------------------------------
    # Span (index 2)
    # ------------------------------------------------------------------


    def test_span_properties_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[2])
        assert isinstance(result.properties, GroupPropertiesSpan)

    def test_span_properties_span_index(self, groups):
        result = GeometryGroupMapper.map_group(groups[2])
        assert result.properties.span_index == 0

    def test_span_properties_span_length(self, groups):
        result = GeometryGroupMapper.map_group(groups[2])
        assert result.properties.span_length.magnitude == 40.0

    def test_span_properties_cracked_extends(self, groups):
        result = GeometryGroupMapper.map_group(groups[2])
        assert len(result.properties.cracked_extends) == 2
        assert isinstance(result.properties.cracked_extends[0], CrackedExtentsDetails)

    def test_span_properties_tapered_details(self, groups):
        result = GeometryGroupMapper.map_group(groups[2])
        assert len(result.properties.tapered_details) == 1
        assert isinstance(result.properties.tapered_details[0], TaperedDetails)
        assert result.properties.tapered_details[0].section_id == to_uuid("tapered_section_1")

    def test_span_properties_splices(self, groups):
        result = GeometryGroupMapper.map_group(groups[2])
        assert len(result.properties.splices) == 2

    def test_span_properties_construction_sequence(self, groups):
        result = GeometryGroupMapper.map_group(groups[2])
        cs = result.properties.construction_sequence_details
        assert isinstance(cs, ConstrSequenceDetails)
        assert cs.pouring_orientation == ElementOrientation.SKEWED
        assert len(cs.segments) == 2

    # ------------------------------------------------------------------
    # Girder (index 3)
    # ------------------------------------------------------------------


    def test_girder_properties_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[3])
        assert isinstance(result.properties, GroupPropertiesGirder)

    def test_girder_properties_girder_index(self, groups):
        result = GeometryGroupMapper.map_group(groups[3])
        assert result.properties.girder_index == 1

    # ------------------------------------------------------------------
    # Diaphragm – concrete non-modelled (index 4)
    # ------------------------------------------------------------------


    def test_diaphragm_concrete_properties_support_index(self, groups):
        result = GeometryGroupMapper.map_group(groups[4])
        assert result.properties.support_index == 0

    def test_diaphragm_concrete_geometry_details_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[4])
        assert isinstance(result.properties.geometry_details, DiaphragmConcreteNonModelledDetails)

    def test_diaphragm_concrete_thickness(self, groups):
        result = GeometryGroupMapper.map_group(groups[4])
        assert result.properties.geometry_details.diaphragm_thickness.magnitude == 0.6

    # ------------------------------------------------------------------
    # Diaphragm – steel girder (index 5)
    # ------------------------------------------------------------------


    def test_diaphragm_steel_geometry_details_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[5])
        assert isinstance(result.properties.geometry_details, DiaphragmSteelGirderDetails)

    # ------------------------------------------------------------------
    # Diaphragm – bracing encased (index 6)
    # ------------------------------------------------------------------


    def test_diaphragm_bracing_geometry_details_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[6])
        assert isinstance(result.properties.geometry_details, DiaphragmBracingEncasedDetails)

    # ------------------------------------------------------------------
    # Transverse bracing (index 7)
    # ------------------------------------------------------------------


    def test_transverse_bracing_properties_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[7])
        assert isinstance(result.properties, GroupPropertiesTransverseBracing)

    def test_transverse_bracing_orientation(self, groups):
        result = GeometryGroupMapper.map_group(groups[7])
        assert result.properties.bracing_orientation == ElementOrientation.ORTHOGONAL

    def test_transverse_bracing_no_of_bracings(self, groups):
        result = GeometryGroupMapper.map_group(groups[7])
        assert result.properties.no_of_bracings == 2

    def test_transverse_bracing_details_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[7])
        assert isinstance(result.properties.bracing_details, TransverseBracingDetails)

    # ------------------------------------------------------------------
    # Brace – k-type (index 8)
    # ------------------------------------------------------------------


    def test_brace_properties_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[8])
        assert isinstance(result.properties, GroupPropertiesBrace)

    def test_brace_details_ktype(self, groups):
        result = GeometryGroupMapper.map_group(groups[8])
        assert isinstance(result.properties.geometry_details, BracingBraceKtypeDetails)

    def test_brace_details_horizontal_offset(self, groups):
        result = GeometryGroupMapper.map_group(groups[8])
        assert result.properties.geometry_details.horizontal_offset_right_brace.magnitude == 0.1

    # ------------------------------------------------------------------
    # Chord (index 9)
    # ------------------------------------------------------------------


    def test_chord_properties_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[9])
        assert isinstance(result.properties, GroupPropertiesChord)

    def test_chord_vertical_offset_at_right(self, groups):
        result = GeometryGroupMapper.map_group(groups[9])
        assert result.properties.vertical_offset_at_right.magnitude == 0.1

    # ------------------------------------------------------------------
    # Plan bracing (index 10)
    # ------------------------------------------------------------------


    def test_plan_bracing_properties_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[10])
        assert isinstance(result.properties, GroupPropertiesPlanBracing)

    def test_plan_bracing_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[10])
        assert result.properties.plan_bracing_type == PlanBracingType.WARREN

    def test_plan_bracing_girder_indices(self, groups):
        result = GeometryGroupMapper.map_group(groups[10])
        assert result.properties.left_girder_index == 0
        assert result.properties.right_girder_index == 4

    # ------------------------------------------------------------------
    # Support (index 11)
    # ------------------------------------------------------------------


    def test_support_properties_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[11])
        assert isinstance(result.properties, GroupPropertiesSupport)

    def test_support_index(self, groups):
        result = GeometryGroupMapper.map_group(groups[11])
        assert result.properties.support_index == 0

    def test_support_skew_angle(self, groups):
        result = GeometryGroupMapper.map_group(groups[11])
        assert result.properties.skew_angle.magnitude == 15.0

    def test_support_orientation(self, groups):
        result = GeometryGroupMapper.map_group(groups[11])
        assert result.properties.orientation == ElementOrientation.ORTHOGONAL

    # ------------------------------------------------------------------
    # Above-ground – solid type (index 12)
    # ------------------------------------------------------------------


    def test_above_ground_properties_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[12])
        assert isinstance(result.properties, GroupPropertiesAboveGround)

    def test_above_ground_details_solid_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[12])
        assert isinstance(result.properties.details, AboveGroundDetailsSolid)

    def test_above_ground_no_of_walls(self, groups):
        result = GeometryGroupMapper.map_group(groups[12])
        assert result.properties.details.no_of_walls == 1

    # ------------------------------------------------------------------
    # Pier (index 13)
    # ------------------------------------------------------------------


    def test_pier_transverse_offset(self, groups):
        result = GeometryGroupMapper.map_group(groups[13])
        assert result.properties.transverse_offset.magnitude == 1.0

    # ------------------------------------------------------------------
    # Wall (index 14)
    # ------------------------------------------------------------------


    def test_wall_element_thickness(self, groups):
        result = GeometryGroupMapper.map_group(groups[14])
        assert result.properties.element_thickness.magnitude == 0.8

    # ------------------------------------------------------------------
    # Crossbeam (index 15)
    # ------------------------------------------------------------------


    def test_crossbeam_element_length(self, groups):
        result = GeometryGroupMapper.map_group(groups[15])
        assert result.properties.element_length.magnitude == 10.0

    def test_crossbeam_tapered_details_empty(self, groups):
        result = GeometryGroupMapper.map_group(groups[15])
        assert result.properties.tapered_details == []

    # ------------------------------------------------------------------
    # Below-ground – deep foundation (index 16)
    # ------------------------------------------------------------------


    def test_below_ground_foundation_details_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[16])
        assert isinstance(result.properties.foundation_details, DeepFoundationDetails)

    def test_below_ground_no_of_piles(self, groups):
        result = GeometryGroupMapper.map_group(groups[16])
        assert result.properties.foundation_details.no_of_piles == 5

    # ------------------------------------------------------------------
    # Pile (index 17)
    # ------------------------------------------------------------------


    def test_pile_length(self, groups):
        result = GeometryGroupMapper.map_group(groups[17])
        assert result.properties.pile_length.magnitude == 25.0

    def test_pile_spring_spacing(self, groups):
        result = GeometryGroupMapper.map_group(groups[17])
        assert len(result.properties.spring_spacing) == 1
        assert result.properties.spring_spacing[0].magnitude == 1.0

    # ------------------------------------------------------------------
    # Pile-cap (index 18)
    # ------------------------------------------------------------------


    def test_pile_cap_top_level(self, groups):
        result = GeometryGroupMapper.map_group(groups[18])
        assert result.properties.top_of_pile_cap_level.magnitude == 10.0

    def test_pile_cap_element_length(self, groups):
        result = GeometryGroupMapper.map_group(groups[18])
        assert result.properties.element_length.magnitude == 2.0

    # ------------------------------------------------------------------
    # Linkage – singular bearing (index 19)
    # ------------------------------------------------------------------


    def test_linkage_singular_properties_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[19])
        assert isinstance(result.properties, GroupPropertiesLinkageSupToSub)

    def test_linkage_singular_support_index(self, groups):
        result = GeometryGroupMapper.map_group(groups[19])
        assert result.properties.support_index == 1

    def test_linkage_singular_bearing_details_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[19])
        assert isinstance(result.properties.bearing_configuration_details, SingleBearingConfigurationDetails)

    def test_linkage_singular_no_of_bearings(self, groups):
        result = GeometryGroupMapper.map_group(groups[19])
        assert result.properties.bearing_configuration_details.no_of_bearings == 1

    # ------------------------------------------------------------------
    # Linkage – multiple bearings (index 20)
    # ------------------------------------------------------------------

    def test_linkage_multiple_bearing_details_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[20])
        assert isinstance(result.properties.bearing_configuration_details, MultipleBearingConfigurationDetails)

    def test_linkage_multiple_no_of_bearings(self, groups):
        result = GeometryGroupMapper.map_group(groups[20])
        assert result.properties.bearing_configuration_details.no_of_bearings == 5

    def test_linkage_multiple_spacing_type(self, groups):
        result = GeometryGroupMapper.map_group(groups[20])
        assert result.properties.bearing_configuration_details.bearing_spacing_type == SpacingType.UNIFORM

    def test_linkage_multiple_spacing_values(self, groups):
        result = GeometryGroupMapper.map_group(groups[20])
        spacing = result.properties.bearing_configuration_details.bearing_spacing
        assert len(spacing) == 1
        assert spacing[0].magnitude == 0.5

    # ------------------------------------------------------------------
    # Nested group hierarchy (last entry – nested bridge)
    # ------------------------------------------------------------------

    def test_nested_bridge_group_mapping(self, groups):
        result = GeometryGroupMapper.map_group(groups[-1])
        assert isinstance(result.properties, GroupPropertiesBridge)

    def test_nested_bridge_has_superstructure_child(self, groups):
        result = GeometryGroupMapper.map_group(groups[-1])
        assert len(result.nested_groups) == 1
        assert isinstance(result.nested_groups[0].properties, GroupPropertiesSuperstructure)

    def test_nested_superstructure_has_span_child(self, groups):
        result = GeometryGroupMapper.map_group(groups[-1])
        superstructure = result.nested_groups[0]
        assert len(superstructure.nested_groups) == 1
        assert isinstance(superstructure.nested_groups[0].properties, GroupPropertiesSpan)

    def test_nested_span_has_girder_child(self, groups):
        result = GeometryGroupMapper.map_group(groups[-1])
        span = result.nested_groups[0].nested_groups[0]
        assert len(span.nested_groups) == 1
        assert isinstance(span.nested_groups[0].properties, GroupPropertiesGirder)

    def test_nested_parent_references_are_set(self, groups):
        result = GeometryGroupMapper.map_group(groups[-1])
        superstructure = result.nested_groups[0]
        span = superstructure.nested_groups[0]
        girder = span.nested_groups[0]
        assert superstructure.parent_group is result
        assert span.parent_group is superstructure
        assert girder.parent_group is span

