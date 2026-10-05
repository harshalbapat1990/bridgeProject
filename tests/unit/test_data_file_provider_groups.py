import pytest
from pathlib import Path

from bda.contracts.paramodel.groups import *
from bda.contracts.paramodel.groups import PropertiesBridgeParaModel
from bda.contracts.paramodel.groups.enums import (
    CurvatureTypeEnumParaModel,
)
from bda.contracts.paramodel.sections.sections_para_models import SectionOffsetParaModel
from bda.contracts.paramodel.groups.component_properties.properties_base import (
    PropertiesIndividualTendonParaModel,
    TendonGeometryCircularTypeParaModel,
    ControlPointParaModel,
    ControlPointWithRadiusParaModel,
)

from bda.infrastructure.data_providers.data_file_provider import DataFileProvider


def assert_quantity(q, value, unit):
    assert q.value == value
    assert q.unit == unit

class TestDataFileProvider_Groups:
    """Unit tests for DataFileProvider.get_groups_for_project."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    @pytest.fixture (scope="session")
    def fixtures_path(self):
        return Path(__file__).parent / "fixtures"

    @pytest.fixture (scope="session")
    def provider(self, fixtures_path):
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture (scope="session")
    def groups(self, provider):
        return provider.get_geometry_groups_for_project()

    # ------------------------------------------------------------------
    # Collection shape
    # ------------------------------------------------------------------

    def test_returns_list(self, groups):
        assert isinstance(groups, list)

    def test_returns_all_groups(self, groups):
        assert len(groups) == 26

    def test_all_items_are_GeometryGroupParaModel(self, groups):
        for g in groups:
            assert isinstance(g, GeometryGroupParaModel)

    # ------------------------------------------------------------------
    # Bridge group
    # ------------------------------------------------------------------

    def test_bridge_is_GeometryGroupParaModel(self, groups):
        assert isinstance(groups[0], GeometryGroupParaModel)

    def test_bridge_name(self, groups):
        assert groups[0].name == "Test Bridge"

    def test_bridge_structural_component_type(self, groups):
        assert groups[0].structural_component_type == "bridge"

    def test_bridge_material_id(self, groups):
        assert groups[0].material_id == "2"

    def test_bridge_section(self, groups):
        assert groups[0].section_id == "3"

    def test_bridge_type(self, groups):
        assert groups[0].properties.bridge_type == "Steel Composite"

    def test_bridge_idealisation(self, groups):
        assert groups[0].properties.bridge_idealisation == "grillage"

    def test_bridge_no_of_spans(self, groups):
        assert groups[0].properties.no_of_spans == 3

    def test_bridge_analysis_settings(self, groups):
        assert groups[0].properties.analysis_settings.mesh_divisor == 20

    def test_bridge_top_deck_level(self, groups):
        g = groups[0].properties
        assert_quantity(g.top_deck_level, 65.5, "m")

    def test_bridge_is_parameters_of_correct_type(self, groups):
        g = groups[0]
        assert isinstance(g.properties, PropertiesBridgeParaModel)

    def test_group_contains_nested_groups(self, groups):
        # The last group (nested_Bridge_group) is the one with nested groups
        g = groups[-1]
        assert len(g.nested_groups) > 0
        assert isinstance(g.nested_groups[0], GeometryGroupParaModel)

    # ------------------------------------------------------------------
    # Superstructure group
    # ------------------------------------------------------------------

    def test_superstructure__component_type(self, groups):
        assert groups[1].structural_component_type == "superstructure"

    def test_superstructure_properties_type(self, groups):
        assert isinstance(groups[1].properties, PropertiesSuperstructureParaModel)

    def test_superstructure_total_deck_width(self, groups):
        g = groups[1].properties
        assert_quantity(g.total_deck_width, 12, "m")

    def test_superstructure_no_of_girders(self, groups):
        assert groups[1].properties.no_of_girders == 5

    def test_superstructure_girder_spacing_type(self, groups):
        assert groups[1].properties.girder_spacing_type == "uniform"

    def test_superstructure_stringcourse_left_barrier_width(self, groups):
        g = groups[1].properties
        assert_quantity(g.stringcourse_left_barrier_width, 0.6, "m")

    def test_superstructure_stringcourse_right_barrier_width(self, groups):
        g = groups[1].properties
        assert_quantity(g.stringcourse_right_barrier_width, 0.6, "m")

    def test_superstructure_cantilever_left_width(self, groups):
        g = groups[1].properties
        assert_quantity(g.cantilever_left_width, 1.55, "m")

    def test_superstructure_cantilever_right_width(self, groups):
        g = groups[1].properties
        assert_quantity(g.cantilever_right_width, 1.45, "m")

    # ------------------------------------------------------------------
    # Span group
    # ------------------------------------------------------------------

    def test_span_groups_exist(self, groups):
        span_groups = [g for g in groups if g.structural_component_type == "span"]
        assert len(span_groups) == 1

    def test_span_properties(self, groups):
        g = groups[2]
        assert g.structural_component_type == "span"
        assert isinstance(g.properties, PropertiesSpanParaModel)
        assert g.properties.span_index == 0
        assert_quantity(g.properties.span_length, 40.0, "m")
        assert_quantity(g.properties.top_deck_level_at_end, 67.0, "m")

    # ------------------------------------------------------------------
    # Girder group
    # ------------------------------------------------------------------

    def test_girder_groups_exist(self, groups):
        girder_groups = [g for g in groups if g.structural_component_type == "girder"]
        assert len(girder_groups) == 1

    def test_girder_properties(self, groups):
        g = groups[3]
        assert g.structural_component_type == "girder"
        assert g.material_id == "3"
        assert g.section_id == "4"
        assert isinstance(g.properties, PropertiesGirderParaModel)
        assert g.properties.girder_index == 1
        assert g.parent_group == "group_span_1"


    # ------------------------------------------------------------------
    # Diaphragm group
    # ------------------------------------------------------------------

    def test_diaphragm_groups_exist(self, groups):
        diaphragm_groups = [g for g in groups if g.structural_component_type == "diaphragm"]
        assert len(diaphragm_groups) == 3

    def test_diaphragm_concrete_non_modelled_properties(self, groups):
        diaphragm_group = groups[4]
        assert diaphragm_group.structural_component_type == "diaphragm"
        assert isinstance(diaphragm_group.properties, PropertiesDiaphragmParaModel)
        assert diaphragm_group.properties.support_index == 0
        assert diaphragm_group.properties.geometry_details.diaphragm_type == "concrete-non-modelled"
        assert_quantity(diaphragm_group.properties.geometry_details.diaphragm_thickness, 0.6, "m")

    def test_diaphragm_steel_girder_properties(self, groups):
        diaphragm_group = groups[5]
        assert diaphragm_group.structural_component_type == "diaphragm"
        assert diaphragm_group.properties.geometry_details.diaphragm_type == "steel-girder"

    def test_diaphragm_bracing_encased_properties(self, groups):
        diaphragm_group = groups[6]
        assert diaphragm_group.structural_component_type == "diaphragm"
        assert diaphragm_group.properties.geometry_details.diaphragm_type == "bracing-encased"

    # ------------------------------------------------------------------
    # Transverse bracing
    # ------------------------------------------------------------------

    def test_transverse_bracing_properties(self, groups):
        g = groups[7]

        # --- basic checks ---
        assert g.structural_component_type == "transverse-bracing"
        assert isinstance(g.properties, PropertiesTransverseBracingParaModel)

        props = g.properties

        # --- simple fields ---
        assert props.bracing_orientation == "orthogonal"
        assert props.spacing_type == "uniform"
        assert props.no_of_bracings == 2
        assert props.left_girder_index == 0
        assert props.right_girder_index == 4

        # --- quantity: x_position_at_start_girder ---
        assert_quantity(props.x_position_at_start_girder, 5.0, "m")

        # --- list: spacing_values ---
        assert len(props.spacing_values) == 1
        assert_quantity(props.spacing_values[0], 10.0, "m")

        # --- nested object: bracing_details ---
        details = props.bracing_details
        assert details is not None

        assert_quantity(details.horizontal_offset_at_left, 0.0, "m")
        assert_quantity(details.horizontal_offset_at_right, 0.0, "m")

    # ------------------------------------------------------------------
    # Brace
    # ------------------------------------------------------------------

    def test_brace_properties(self, groups):
        g = groups[8]
        assert g.structural_component_type == "brace"
        assert isinstance(g.properties, PropertiesBracingBraceParaModel)
        assert g.properties.geometry_details.bracing_type == "k-type"
        assert_quantity(g.properties.geometry_details.vertical_offset_right_top, 0.1, "m")
        assert_quantity(g.properties.geometry_details.horizontal_offset_left_brace, 0.0, "m")

    def test_brace_x_type_properties(self, groups):
        x_type_braces = [
            g for g in groups
            if g.structural_component_type == "brace"
            and g.properties.geometry_details.bracing_type == "x-type"
        ]
        assert len(x_type_braces) == 1
        assert isinstance(x_type_braces[0].properties, PropertiesBracingBraceParaModel)

    # ------------------------------------------------------------------
    # Chord (index 15)
    # ------------------------------------------------------------------

    def test_chord_properties(self, groups):
        g = groups[9]
        assert g.structural_component_type == "chord"
        assert isinstance(g.properties, PropertiesBracingChordParaModel)
        assert_quantity(g.properties.vertical_offset_at_right, 0.1, "m")

    # ------------------------------------------------------------------
    # Plan bracing
    # ------------------------------------------------------------------

    def test_plan_bracing_properties(self, groups):
        g = groups[10]
        assert g.structural_component_type == "plan-bracing"
        assert isinstance(g.properties, PropertiesPlanBracingParaModel)
        assert g.properties.plan_bracing_type == "warren"
        assert g.properties.left_girder_index == 0
        assert g.properties.right_girder_index == 4

    # ------------------------------------------------------------------
    # Support groups
    # ------------------------------------------------------------------

    def test_support_groups_exist(self, groups):
        support_groups = [g for g in groups if g.structural_component_type == "support"]
        assert len(support_groups) == 1

    def test_support_properties(self, groups):
        g = groups[11]
        assert g.structural_component_type == "support"
        assert isinstance(g.properties, PropertiesSupportParaModel)
        assert g.properties.support_index == 0
        assert_quantity(g.properties.bearing_underside_level, -5.0, "m")
        assert_quantity(g.properties.skew_angle, 15.0, "degrees")
        assert g.properties.orientation == "orthogonal"

    # ------------------------------------------------------------------
    # Above-ground groups
    # ------------------------------------------------------------------

    def test_above_ground_groups_exist(self, groups):
        above_ground_groups = [g for g in groups if g.structural_component_type == "above-ground"]
        assert len(above_ground_groups) == 2

    def test_above_ground_properties(self, groups):
        g = groups[12]
        assert g.structural_component_type == "above-ground"
        assert isinstance(g.properties, PropertiesAboveGroundParaModel)
        assert g.properties.details.support_type == "solid-type"
        assert g.properties.details.no_of_walls == 1

    def test_above_ground_column_type_properties(self, groups):
        column_type_supports = [
            g for g in groups
            if g.structural_component_type == "above-ground"
            and g.properties.details.support_type == "column-type"
        ]
        assert len(column_type_supports) == 1
        assert column_type_supports[0].properties.details.no_of_piers == 2

    # ------------------------------------------------------------------
    # Pier
    # ------------------------------------------------------------------

    def test_pier_groups_exist(self, groups):
        pier_groups = [g for g in groups if g.structural_component_type == "pier"]
        assert len(pier_groups) == 1

    def test_pier_properties(self, groups):
        g = groups[13]
        assert g.structural_component_type == "pier"
        assert isinstance(g.properties, PropertiesPierParaModel)
        assert_quantity(g.properties.transverse_offset, 1.0, "m")

    # ------------------------------------------------------------------
    # Wall
    # ------------------------------------------------------------------

    def test_wall_properties(self, groups):
        wall_group = groups[14]
        assert wall_group.structural_component_type == "wall"
        assert isinstance(wall_group.properties, PropertiesWallParaModel)
        assert_quantity(wall_group.properties.element_thickness, 0.8, "m")

    # ------------------------------------------------------------------
    # Crossbeam
    # ------------------------------------------------------------------

    def test_crossbeam_properties(self, groups):
        crossbeam_group = groups[15]
        assert crossbeam_group.structural_component_type == "crossbeam"
        assert isinstance(crossbeam_group.properties, PropertiesCrossbeamParaModel)
        assert_quantity(crossbeam_group.properties.element_length, 10.0, "m")

    # ------------------------------------------------------------------
    # Below-ground
    # ------------------------------------------------------------------

    def test_below_ground_properties(self, groups):
        g = groups[16]
        assert g.structural_component_type == "below-ground"
        assert isinstance(g.properties, PropertiesBelowGroundParaModel)
        assert g.properties.foundation_details.foundation_type == "deep"
        assert g.properties.foundation_details.no_of_piles == 5

    def test_below_ground_shallow_properties(self, groups):
        shallow_foundations = [
            g for g in groups
            if g.structural_component_type == "below-ground"
            and g.properties.foundation_details.foundation_type == "shallow"
        ]
        assert len(shallow_foundations) == 1
        assert isinstance(shallow_foundations[0].properties, PropertiesBelowGroundParaModel)

    # ------------------------------------------------------------------
    # Pile
    # ------------------------------------------------------------------

    def test_pile_properties(self, groups):
        g = groups[17]
        assert g.structural_component_type == "pile"
        assert isinstance(g.properties, PropertiesPileParaModel)
        assert_quantity(g.properties.pile_length, 25.0, "m")
        assert_quantity(g.properties.offset_along_support_line, 0.0, "m")
        assert_quantity(g.properties.offset_normal_to_support_line, 0.0, "m")
        assert_quantity(g.properties.spring_spacing[0], 1.0, "m")

    # ------------------------------------------------------------------
    # Pile-cap
    # ------------------------------------------------------------------

    def test_pile_cap_properties(self, groups):
        pile_cap = groups[18]
        assert pile_cap.structural_component_type == "pile-cap"
        assert isinstance(pile_cap.properties, PropertiesPileCapParaModel)
        assert_quantity(pile_cap.properties.top_of_pile_cap_level, 10.0, "m")
        assert_quantity(pile_cap.properties.element_length, 2.0, "m")

    # ------------------------------------------------------------------
    # Linkage groups
    # ------------------------------------------------------------------

    def test_linkage_groups_exist(self, groups):
        linkage_groups = [
            g for g in groups
            if g.structural_component_type == "superstructure-to-substructure-connections"
        ]
        assert len(linkage_groups) == 2

    def test_linkage_single_properties(self, groups):
        linkage = groups[19]
        assert (
            linkage.structural_component_type
            == "superstructure-to-substructure-connections"
        )
        assert isinstance(
            linkage.properties, PropertiesLinkageSupToSubParaModel
        )
        assert linkage.properties.support_index == 1
        assert (
                linkage
                .properties
                .bearing_configuration_details
                .bearing_configuration_type == "singular"
        )
        assert (
                linkage
                .properties
                .bearing_configuration_details
                .no_of_bearings == 1
        )

    def test_linkage_multiple_properties(self, groups):
        linkage = groups[20]
        assert (
            linkage.structural_component_type
            == "superstructure-to-substructure-connections"
        )
        assert isinstance(
            linkage.properties, PropertiesLinkageSupToSubParaModel
        )
        assert linkage.properties.support_index == 3
        assert (
                linkage
                .properties
                .bearing_configuration_details
                .bearing_configuration_type == "multiple"
        )
        assert (
                linkage
                .properties
                .bearing_configuration_details
                .bearing_spacing_type == "uniform"
        )
        assert_quantity(
            linkage
            .properties
            .bearing_configuration_details
            .bearing_spacing[0],
            value= 0.5,
            unit= "m"
        )
        assert (
            linkage
            .properties
            .bearing_configuration_details
            .no_of_bearings == 5)


    # ------------------------------------------------------------------
    # Individual tendon
    # ------------------------------------------------------------------

    def _individual_tendon(self, groups):
        return next(
            g for g in groups
            if g.structural_component_type == "individual-tendon"
        )

    def test_individual_tendon_groups_exist(self, groups):
        tendon_groups = [
            g for g in groups
            if g.structural_component_type == "individual-tendon"
        ]
        assert len(tendon_groups) == 1

    def test_individual_tendon_is_GeometryGroupParaModel(self, groups):
        assert isinstance(self._individual_tendon(groups), GeometryGroupParaModel)

    def test_individual_tendon_name(self, groups):
        assert self._individual_tendon(groups).name == "Individual Tendon 1"

    def test_individual_tendon_parent_group(self, groups):
        assert self._individual_tendon(groups).parent_group == "girder_1"

    def test_individual_tendon_properties_type(self, groups):
        g = self._individual_tendon(groups)
        assert isinstance(g.properties, PropertiesIndividualTendonParaModel)

    def test_individual_tendon_index(self, groups):
        assert self._individual_tendon(groups).properties.tendon_index == 0

    def test_individual_tendon_geometry_type(self, groups):
        g = self._individual_tendon(groups)
        assert isinstance(g.properties.tendon_geometry, TendonGeometryCircularTypeParaModel)

    def test_individual_tendon_geometry_curvature_type(self, groups):
        g = self._individual_tendon(groups)
        assert g.properties.tendon_geometry.curvature_type == CurvatureTypeEnumParaModel.CIRCULAR

    def test_individual_tendon_geometry_datum_point(self, groups):
        g = self._individual_tendon(groups)
        assert g.properties.tendon_geometry.datum_point == SectionOffsetParaModel.CENTER_TOP

    def test_individual_tendon_control_points_length(self, groups):
        g = self._individual_tendon(groups)
        assert len(g.properties.tendon_geometry.control_points) == 2

    def test_individual_tendon_control_points_type(self, groups):
        g = self._individual_tendon(groups)
        assert all(
            isinstance(cp, ControlPointWithRadiusParaModel)
            for cp in g.properties.tendon_geometry.control_points
        )

    def test_individual_tendon_first_control_point_point_type(self, groups):
        g = self._individual_tendon(groups)
        cp = g.properties.tendon_geometry.control_points[0]
        assert isinstance(cp.point, ControlPointParaModel)

    def test_individual_tendon_first_control_point_values(self, groups):
        g = self._individual_tendon(groups)
        cp = g.properties.tendon_geometry.control_points[0]
        assert_quantity(cp.point.longitudinal_x, 0.0, "m")
        assert_quantity(cp.point.transverse_offset_y, 0.1, "m")
        assert_quantity(cp.point.vertical_offset_z, -0.5, "m")
        assert_quantity(cp.radius, 50.0, "m")

    def test_individual_tendon_second_control_point_values(self, groups):
        g = self._individual_tendon(groups)
        cp = g.properties.tendon_geometry.control_points[1]
        assert_quantity(cp.point.longitudinal_x, 20.0, "m")
        assert_quantity(cp.point.transverse_offset_y, 0.0, "m")
        assert_quantity(cp.point.vertical_offset_z, -1.2, "m")
        assert_quantity(cp.radius, 75.0, "m")


    # ------------------------------------------------------------------
    # Properties tests
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "component_type,expected_cls",
        [
            ("bridge", PropertiesBridgeParaModel),
            ("superstructure", PropertiesSuperstructureParaModel),
            ("span", PropertiesSpanParaModel),
            ("girder", PropertiesGirderParaModel),
            ("diaphragm", PropertiesDiaphragmParaModel),
            ("transverse-bracing", PropertiesTransverseBracingParaModel),
            ("brace", PropertiesBracingBraceParaModel),
            ("chord", PropertiesBracingChordParaModel),
            ("plan-bracing", PropertiesPlanBracingParaModel),
            ("support", PropertiesSupportParaModel),
            ("above-ground", PropertiesAboveGroundParaModel),
            ("pier", PropertiesPierParaModel),
            ("wall", PropertiesWallParaModel),
            ("crossbeam", PropertiesCrossbeamParaModel),
            ("below-ground", PropertiesBelowGroundParaModel),
            ("pile", PropertiesPileParaModel),
            ("pile-cap", PropertiesPileCapParaModel),
            ("superstructure-to-substructure-connections", PropertiesLinkageSupToSubParaModel),
            ("individual-tendon", PropertiesIndividualTendonParaModel),
        ],
    )
    def test_group_properties_type_mapping(self, groups, component_type, expected_cls):
        matches = [
            g for g in groups
            if g.structural_component_type.value == component_type
        ]
        assert matches, f"Missing group with structural_component_type={component_type}"

        g = matches[0]
        assert isinstance(g.properties, expected_cls)


    # ====================================================================
    # NESTED DETAILS TYPE VERIFICATION
    # ====================================================================

    # Bridge Analysis Settings
    def test_bridge_analysis_settings_type(self, groups):
        """Bridge analysis_settings must be AnalysisSettingsParaModel."""
        from bda.contracts.paramodel.groups.component_properties.bridge_properties import (
            AnalysisSettingsParaModel,
        )
        bridge = groups[0]
        assert isinstance(bridge.properties.analysis_settings, AnalysisSettingsParaModel)

    # Diaphragm geometry_details types
    def test_diaphragm_concrete_non_modelled_details_type(self, groups):
        """Diaphragm concrete-non-modelled must have DiaphragmConcreteNonModelled type."""
        from bda.contracts.paramodel.groups.component_properties.superstructure_properties import (
            DiaphragmConcreteNonModelled,
        )
        diaphragm_group = groups[4]
        assert isinstance(diaphragm_group.properties.geometry_details, DiaphragmConcreteNonModelled)

    def test_diaphragm_steel_girder_details_type(self, groups):
        """Diaphragm steel-girder must have DiaphragmSteelGirderParaModel type."""
        from bda.contracts.paramodel.groups.component_properties.superstructure_properties import (
            DiaphragmSteelGirderParaModel,
        )
        diaphragm_group = groups[5]
        assert isinstance(diaphragm_group.properties.geometry_details, DiaphragmSteelGirderParaModel)

    def test_diaphragm_bracing_encased_details_type(self, groups):
        """Diaphragm bracing-encased must have DiaphragmBracingEncasedParaModel type."""
        from bda.contracts.paramodel.groups.component_properties.superstructure_properties import (
            DiaphragmBracingEncasedParaModel,
        )
        diaphragm_group = groups[6]
        assert isinstance(diaphragm_group.properties.geometry_details, DiaphragmBracingEncasedParaModel)

    # Transverse Bracing Details
    def test_transverse_bracing_details_type(self, groups):
        """Transverse-bracing details must be TransverseBracingDetailsParaModel."""
        from bda.contracts.paramodel.groups.component_properties.superstructure_properties import (
            TransverseBracingDetailsParaModel,
        )
        g = groups[7]
        assert isinstance(g.properties.bracing_details, TransverseBracingDetailsParaModel)

    # Brace (Bracing Brace) geometry_details types
    def test_brace_k_type_details_type(self, groups):
        """Brace with k-type must have BracingBraceKtypeDetailsBraceParaModel type."""
        from bda.contracts.paramodel.groups.component_properties.superstructure_properties import (
            BracingBraceKtypeDetailsBraceParaModel,
        )
        g = groups[8]
        assert isinstance(g.properties.geometry_details, BracingBraceKtypeDetailsBraceParaModel)

    def test_brace_x_type_details_type(self, groups):
        """Brace with x-type must have BracingBraceXtypeDetailsParaModel type."""
        from bda.contracts.paramodel.groups.component_properties.superstructure_properties import (
            BracingBraceXtypeDetailsParaModel,
        )
        x_type_brace = next(
            g for g in groups
            if g.structural_component_type == "brace"
            and g.properties.geometry_details.bracing_type == "x-type"
        )
        assert isinstance(x_type_brace.properties.geometry_details, BracingBraceXtypeDetailsParaModel)

    # Above-ground Details types
    def test_above_ground_solid_type_details_type(self, groups):
        """Above-ground solid-type must have AboveGroundDetailsSolidTypeParaModel type."""
        from bda.contracts.paramodel.groups.component_properties.substructure_properties import (
            AboveGroundDetailsSolidTypeParaModel,
        )
        g = groups[12]
        assert isinstance(g.properties.details, AboveGroundDetailsSolidTypeParaModel)

    def test_above_ground_column_type_details_type(self, groups):
        """Above-ground column-type must have AboveGroundDetailsColumnTypeParaModel type."""
        from bda.contracts.paramodel.groups.component_properties.substructure_properties import (
            AboveGroundDetailsColumnTypeParaModel,
        )
        column_type_support = next(
            g for g in groups
            if g.structural_component_type == "above-ground"
            and g.properties.details.support_type == "column-type"
        )
        assert isinstance(column_type_support.properties.details, AboveGroundDetailsColumnTypeParaModel)

    # Below-ground Foundation Details types
    def test_below_ground_deep_foundation_details_type(self, groups):
        """Below-ground with deep foundation must have DeepFoundationDetailsParaModel type."""
        from bda.contracts.paramodel.groups.component_properties.substructure_properties import (
            DeepFoundationDetailsParaModel,
        )
        g = groups[16]
        assert isinstance(g.properties.foundation_details, DeepFoundationDetailsParaModel)

    def test_below_ground_shallow_foundation_details_type(self, groups):
        """Below-ground with shallow foundation must have ShallowFoundationDetailsParaModel type."""
        from bda.contracts.paramodel.groups.component_properties.substructure_properties import (
            ShallowFoundationDetailsParaModel,
        )
        shallow_foundation = next(
            g for g in groups
            if g.structural_component_type == "below-ground"
            and g.properties.foundation_details.foundation_type == "shallow"
        )
        assert isinstance(shallow_foundation.properties.foundation_details, ShallowFoundationDetailsParaModel)

    # Linkage Bearing Configuration Details types
    def test_linkage_single_bearing_configuration_details_type(self, groups):
        """Linkage with single bearing must have SingleBearingConfigurationDetailsParaModel type."""
        from bda.contracts.paramodel.groups.component_properties.linkage_properties import (
            SingleBearingConfigurationDetailsParaModel,
        )
        linkage = groups[19]
        assert isinstance(linkage.properties.bearing_configuration_details, SingleBearingConfigurationDetailsParaModel)

    def test_linkage_multiple_bearing_configuration_details_type(self, groups):
        """Linkage with multiple bearings must have MultipleBearingConfigurationDetailsParaModel type."""
        from bda.contracts.paramodel.groups.component_properties.linkage_properties import (
            MultipleBearingConfigurationDetailsParaModel,
        )
        linkage = groups[20]
        assert isinstance(linkage.properties.bearing_configuration_details, MultipleBearingConfigurationDetailsParaModel)



