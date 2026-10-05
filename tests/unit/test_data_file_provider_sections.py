import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from bda.contracts.paramodel.sections.dimensions_para_models import Point2DParaModel, \
    DimensionsTendonUserParaModel
from bda.contracts.paramodel.sections.sections_para_models import SectionFamilyParaModel, SectionTypeParaModel, \
    SectionStandardPipeParaModel, SectionTendonUserParaModel, \
    TendonPropertiesInternalPostParaModel, TendonTypeEnumParaModel, BondTypeEnumParaModel, \
    RelaxationParamsCEBFIP1990ParaModel, RelaxationCodeEnumParaModel, \
    RelaxationClassCEBFIP1990EnumParaModel
from bda.infrastructure.data_providers.data_file_provider import DataFileProvider
from bda.contracts.paramodel.sections import (
    SectionBaseParaModel,
    SectionStandardAngleParaModel,
    SectionStandardISectionParaModel,
    SectionStandardBoxParaModel,
    SectionStandardChannelParaModel,
    SectionStandardSolidRectangleParaModel,
    SectionStandardSolidRoundParaModel,
    SectionCompositeSteelISymmetricParaModel,
    SectionCompositeSteelIAsymmetricParaModel,
    SectionPSCValueParaModel,
    SectionPSC1CellParaModel,
    SectionPSC2CellParaModel,
    SectionTaperedParaModel,
)
from bda.contracts.shared import QuantityParaModel


class TestDataFileProvider_Sections:
    """Unit tests for DataFileProvider.get_sections_for_project."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    @pytest.fixture
    def fixtures_path(self):
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def provider(self, fixtures_path):
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture
    def sections(self, provider):
        return provider.get_sections_for_project()

    # Shorthand indices for fixture sections
    #  0  standard_angle
    #  1  standard_angle
    #  2  standard_angle
    #  3  standard_I_section
    #  4  standard_box
    #  5  standard_channel
    #  6  standard_solid_rectangle
    #  7  standard_solid_round
    #  8  composite_steel_i_symmetric
    #  9  composite_steel_i_asymmetric
    # 10  psc_value_section
    # 11  psc_1cell
    # 12  psc_2cell
    # 13  tapered_example_1
    # 14  standard_pipe
    # 15  tendon_user_example

    # ------------------------------------------------------------------
    # Collection shape
    # ------------------------------------------------------------------

    def test_sections_json_exists(self, fixtures_path):
        assert (fixtures_path / "sections.json").exists()

    def test_returns_list(self, sections):
        assert isinstance(sections, list)

    def test_returns_16_sections(self, sections):
        assert len(sections) == 16

    def test_all_items_are_section_base_para_model(self, sections):
        for s in sections:
            assert isinstance(s, SectionBaseParaModel)

    # ------------------------------------------------------------------
    # User (idx= 0..5)
    # ------------------------------------------------------------------

    def test_s0_name(self, sections):
        assert sections[0].name == "standard_angle"

    def test_s0_section_family(self, sections):
        assert sections[0].section_family == SectionFamilyParaModel.STANDARD_SHAPE

    def test_s0_section_type(self, sections):
        assert sections[0].section_type == SectionTypeParaModel.ANGLE

    # removed from MVP implementation, but leaving here for future development
    #
    # def test_s0_offset(self, sections):
    #     assert sections[0].offset == SectionOffsetParaModel.LEFT_TOP

    def test_s0_id_is_str(self, sections):
        assert isinstance(sections[0].section_id, str)
        assert sections[0].section_id == "331ffcb4-4aa8-4d67-9b72-e7428ac99bdf"

    def test_s0_dim_height_is_quantity(self, sections):
        assert isinstance(sections[0].dimensions.height_h, QuantityParaModel)

    def test_s0_dim_height_value(self, sections):
        assert sections[0].dimensions.height_h.value == pytest.approx(0.203)

    def test_s0_dim_height_unit(self, sections):
        assert sections[0].dimensions.height_h.unit == "m"

    def test_s0_dim_width_value(self, sections):
        assert sections[0].dimensions.width_b.value == pytest.approx(0.203)

    def test_s0_dim_thickness_web_value(self, sections):
        assert sections[0].dimensions.thickness_web_tw.value == pytest.approx(0.022)

    def test_s0_dim_thickness_flange_value(self, sections):
        assert sections[0].dimensions.thickness_flange_tf.value == pytest.approx(0.022)

    def test_s3_section_type(self, sections):
        assert sections[3].section_type == SectionTypeParaModel.I_SECTION

    def test_s3_name(self, sections):
        assert sections[3].name == "standard_I_section"

    def test_s3_type(self, sections):
        assert isinstance(sections[3], SectionStandardISectionParaModel)

    def test_s3_section_family(self, sections):
        assert sections[3].section_family == SectionFamilyParaModel.STANDARD_SHAPE

    # removed from MVP implementation, but leaving here for future development
    #
    # def test_s3_offset(self, sections):
    #     assert sections[3].offset == SectionOffsetParaModel.LEFT_TOP

    # ------------------------------------------------------------------
    # User – i-section (idx 3)
    # ------------------------------------------------------------------

    def test_s3_dim_total_height_value(self, sections):
        assert sections[3].dimensions.total_height_h.value == pytest.approx(1.01)

    def test_s3_dim_total_height_unit(self, sections):
        assert sections[3].dimensions.total_height_h.unit == "m"

    def test_s3_dim_web_thickness_value(self, sections):
        assert sections[3].dimensions.web_thickness_tw.value == pytest.approx(0.015)

    def test_s3_dim_top_flange_width_value(self, sections):
        assert sections[3].dimensions.top_flange_width_b1.value == pytest.approx(0.41)

    def test_s3_dim_radius_r1_value(self, sections):
        assert sections[3].dimensions.web_inner_radius_r1.value == pytest.approx(0.01)

    # ------------------------------------------------------------------
    # User – Box (idx 4)
    # ------------------------------------------------------------------

    def test_s4_type(self, sections):
        assert isinstance(sections[4], SectionStandardBoxParaModel)

    def test_s4_dim_height_value(self, sections):
        assert sections[4].dimensions.height_h.value == pytest.approx(0.50)

    def test_s4_dim_web_thickness_value(self, sections):
        assert sections[4].dimensions.web_thickness_tw.value == pytest.approx(0.015)

    def test_s4_dim_all_units_are_metres(self, sections):
        d = sections[4].dimensions
        for field in (d.height_h, d.flange_width_b,
                      d.web_thickness_tw, d.flange_thickness_tf):
            assert field.unit == "m"

    # ------------------------------------------------------------------
    # User – Channel (idx 5)
    # ------------------------------------------------------------------

    def test_s5_type(self, sections):
        assert isinstance(sections[5], SectionStandardChannelParaModel)

    def test_s5_dim_height_value(self, sections):
        assert sections[5].dimensions.height_h.value == pytest.approx(0.55)

    def test_s5_dim_flange_end_radius_value(self, sections):
        assert sections[5].dimensions.flange_end_radius_r2.value == pytest.approx(0.008)

    # ------------------------------------------------------------------
    # User – SolidRectangle (idx 6)
    # ------------------------------------------------------------------

    def test_s6_type(self, sections):
        assert isinstance(sections[6], SectionStandardSolidRectangleParaModel)

    def test_s6_dim_height_value(self, sections):
        assert sections[6].dimensions.height_h.value == pytest.approx(0.40)

    def test_s6_dim_width_value(self, sections):
        assert sections[6].dimensions.width_b.value == pytest.approx(0.25)

    # ------------------------------------------------------------------
    # User – SolidRound (idx 7)
    # ------------------------------------------------------------------

    def test_s7_type(self, sections):
        assert isinstance(sections[7], SectionStandardSolidRoundParaModel)

    def test_s7_dim_diameter_value(self, sections):
        assert sections[7].dimensions.diameter_d.value == pytest.approx(0.18)

    def test_s7_dim_diameter_unit(self, sections):
        assert sections[7].dimensions.diameter_d.unit == "m"

    # ------------------------------------------------------------------
    # Composite – SteelItype1 (idx 8)
    # ------------------------------------------------------------------

    def test_s8_type(self, sections):
        assert isinstance(sections[8], SectionCompositeSteelISymmetricParaModel)

    def test_s8_section_family(self, sections):
        assert sections[8].section_family == SectionFamilyParaModel.COMPOSITE

    def test_s8_dim_slab_width_value(self, sections):
        assert sections[8].dimensions.slab_width_bc.value == pytest.approx(3.00)

    def test_s8_dim_girder_web_height_value(self, sections):
        assert sections[8].dimensions.girder_web_height_hw.value == pytest.approx(1.20)

    def test_s8_dim_all_units_are_metres(self, sections):
        d = sections[8].dimensions
        for field in (d.slab_width_bc, d.slab_thickness_tc, d.slab_girder_spacing_hh,
                      d.girder_top_flange_width_b1, d.girder_top_flange_thickness_tf1,
                      d.girder_bottom_flange_width_b2, d.girder_bottom_flange_thickness_tf2,
                      d.girder_web_thickness_tw, d.girder_web_height_hw):
            assert field.unit == "m"

    # ------------------------------------------------------------------
    # Composite – SteelItype2 (idx 9)
    # ------------------------------------------------------------------

    def test_s9_type(self, sections):
        assert isinstance(sections[9], SectionCompositeSteelIAsymmetricParaModel)

    def test_s9_section_type(self, sections):
        assert sections[9].section_type == SectionTypeParaModel.STEEL_I_ASYMMETRIC

    def test_s9_dim_slab_distance_value(self, sections):
        assert sections[9].dimensions.slab_distance_rf_sg.value == pytest.approx(0.15)

    def test_s9_dim_girder_web_height_value(self, sections):
        assert sections[9].dimensions.girder_web_height_h.value == pytest.approx(1.25)

    # ------------------------------------------------------------------
    # PSC – Value (idx 10)
    # ------------------------------------------------------------------

    def test_s10_type(self, sections):
        assert isinstance(sections[10], SectionPSCValueParaModel)

    def test_s10_outer_outline_has_four_points(self, sections):
        assert len(sections[10].dimensions.outer_outline.vertices) == 4

    def test_s10_outer_outline_point_is_paramodelpoint(self, sections):
        point = sections[10].dimensions.outer_outline.vertices[0]
        assert isinstance(point, Point2DParaModel)

    def test_s10_outer_outline_coords_are_quantity(self, sections):
        p = sections[10].dimensions.outer_outline.vertices[0]
        assert isinstance(p.x, QuantityParaModel)
        assert isinstance(p.y, QuantityParaModel)

    def test_s10_outer_outline_first_point_values(self, sections):
        p = sections[10].dimensions.outer_outline.vertices[0]
        assert p.x.value == pytest.approx(0.0)
        assert p.y.value == pytest.approx(0.0)

    def test_s10_outer_outline_second_point_x(self, sections):
        p = sections[10].dimensions.outer_outline.vertices[1]
        assert p.x.value == pytest.approx(1.2)

    def test_s10_outer_outline_all_units_metres(self, sections):
        for point in sections[10].dimensions.outer_outline.vertices:
            assert point.x.unit == "m"
            assert point.y.unit == "m"

    def test_s10_inner_outlines_has_one_outline(self, sections):
        assert len(sections[10].dimensions.inner_outlines) == 1

    def test_s10_inner_outline_has_four_points(self, sections):
        assert len(sections[10].dimensions.inner_outlines[0].vertices) == 4

    def test_s10_inner_outline_first_point_values(self, sections):
        p = sections[10].dimensions.inner_outlines[0].vertices[0]
        assert p.x.value == pytest.approx(0.2)
        assert p.y.value == pytest.approx(0.4)

    # ------------------------------------------------------------------
    # PSC – 1Cell (idx 11)
    # ------------------------------------------------------------------

    def test_s11_type(self, sections):
        assert isinstance(sections[11], SectionPSC1CellParaModel)

    def test_s11_joints_is_list_of_bool(self, sections):
        joints = sections[11].dimensions.joints
        assert isinstance(joints, list)
        assert all(isinstance(j, bool) for j in joints)

    def test_s11_joints_values(self, sections):
        assert sections[11].dimensions.joints == [True, False, True, False, True, False, True, False]

    def test_s11_outer_height_ho_length(self, sections):
        assert len(sections[11].dimensions.outer_height_ho) == 6

    def test_s11_outer_height_ho_first_value(self, sections):
        assert sections[11].dimensions.outer_height_ho[0].value == pytest.approx(2.5)

    def test_s11_outer_height_ho_first_unit(self, sections):
        assert sections[11].dimensions.outer_height_ho[0].unit == "m"

    def test_s11_outer_breadth_bo_length(self, sections):
        assert len(sections[11].dimensions.outer_breadth_bo) == 6

    def test_s11_inner_height_hi_length(self, sections):
        assert len(sections[11].dimensions.inner_height_hi) == 10

    def test_s11_inner_breadth_bi_length(self, sections):
        assert len(sections[11].dimensions.inner_breadth_bi) == 7

    def test_s11_all_ho_units_are_metres(self, sections):
        for q in sections[11].dimensions.outer_height_ho:
            assert q.unit == "m"

    # ------------------------------------------------------------------
    # PSC – 2Cell (idx 12)
    # ------------------------------------------------------------------

    def test_s12_type(self, sections):
        assert isinstance(sections[12], SectionPSC2CellParaModel)

    def test_s12_section_type(self, sections):
        assert sections[12].section_type == SectionTypeParaModel.PSC_2CELLS

    def test_s12_dimensions_same_structure_as_1cell(self, sections):
        """psc-2cell shares DimensionsPSC12CellParaModel with psc-1cell."""
        assert sections[12].dimensions.joints == sections[11].dimensions.joints

    # ------------------------------------------------------------------
    # Tapered (idx 13)
    # ------------------------------------------------------------------

    def test_s13_type(self, sections):
        assert isinstance(sections[13], SectionTaperedParaModel)

    def test_s13_section_family(self, sections):
        assert sections[13].section_family == "tapered"

    def test_s13_name(self, sections):
        assert sections[13].name == "tapered_example_1"

    def test_s13_section_start_id(self, sections):
        assert sections[13].section_start_id == "331ffcb4-4aa8-4d67-9b72-e7428ac99bdf"

    def test_s13_section_end_id(self, sections):
        assert sections[13].section_end_id == "331ffcb4-4aa8-4d67-9b71-e7428ac99bdf"

    def test_s13_taper_y_variation(self, sections):
        assert sections[13].taper_y_variation == "linear"

    def test_s13_taper_z_variation(self, sections):
        assert sections[13].taper_z_variation == "linear"

    def test_s13_offset(self, sections):
        assert sections[13].offset == "center-center"

    # ------------------------------------------------------------------
    # User - pipe (idx 14)
    # ------------------------------------------------------------------

    def test_s14_type(self, sections):
        assert isinstance(sections[14], SectionStandardPipeParaModel)

    def test_s14_dim_height_value(self, sections):
        assert sections[14].dimensions.external_diameter_d.value == pytest.approx(0.40)

    def test_s14_dim_web_thickness_value(self, sections):
        assert sections[14].dimensions.wall_thickness_tw.value == pytest.approx(0.02)

    def test_s14_dim_all_units_are_metres(self, sections):
        d = sections[14].dimensions
        for field in (d.external_diameter_d, d.wall_thickness_tw):
            assert field.unit == "m"


    # ------------------------------------------------------------------
    # Tendon – user (idx 15)
    # ------------------------------------------------------------------

    def test_s15_type(self, sections):
        assert isinstance(sections[15], SectionTendonUserParaModel)

    def test_s15_name(self, sections):
        assert sections[15].name == "tendon_user_example"

    def test_s15_section_id(self, sections):
        assert sections[15].section_id == "7d2f1e64-3a6b-4c58-9f21-0b6e5d4c8a12"

    def test_s15_section_family(self, sections):
        assert sections[15].section_family == SectionFamilyParaModel.TENDON

    def test_s15_section_type(self, sections):
        assert sections[15].section_type == SectionTypeParaModel.TENDON_USER

    # removed from MVP implementation, but leaving here for future development
    #
    # def test_s15_offset(self, sections):
    #     assert sections[15].offset == SectionOffsetParaModel.CENTER_CENTER

    # Dimensions
    def test_s15_dimensions_type(self, sections):
        assert isinstance(sections[15].dimensions, DimensionsTendonUserParaModel)

    def test_s15_dim_number_of_strands_is_quantity(self, sections):
        assert isinstance(sections[15].dimensions.number_of_strands, int)

    def test_s15_dim_number_of_strands_value(self, sections):
        assert sections[15].dimensions.number_of_strands == 19

    def test_s15_dim_typical_strand_area_value(self, sections):
        assert sections[15].dimensions.typical_strand_area.value == pytest.approx(140.0)

    def test_s15_dim_typical_strand_area_unit(self, sections):
        assert sections[15].dimensions.typical_strand_area.unit == "mm2"

    # General properties (Internal Post-Tension)
    def test_s15_general_properties_type(self, sections):
        assert isinstance(sections[15].general_properties, TendonPropertiesInternalPostParaModel)

    def test_s15_general_properties_tendon_type(self, sections):
        assert sections[15].general_properties.tendon_type == TendonTypeEnumParaModel.INTERNAL_POST_TENSION

    def test_s15_general_properties_duct_diameter_value(self, sections):
        assert sections[15].general_properties.duct_diameter.value == pytest.approx(0.09)

    def test_s15_general_properties_duct_diameter_unit(self, sections):
        assert sections[15].general_properties.duct_diameter.unit == "m"

    def test_s15_general_properties_bond_type(self, sections):
        assert sections[15].general_properties.bond_type == BondTypeEnumParaModel.BONDED

    def test_s15_general_properties_anchorage_set_slip_value(self, sections):
        assert sections[15].general_properties.anchorage_set_slip.value == pytest.approx(6.0)

    def test_s15_general_properties_anchorage_set_slip_unit(self, sections):
        assert sections[15].general_properties.anchorage_set_slip.unit == "mm"

    def test_s15_general_properties_curvature_coefficient(self, sections):
        assert sections[15].general_properties.curvature_coefficient == pytest.approx(0.25)

    def test_s15_general_properties_wobble_coefficient_value(self, sections):
        assert sections[15].general_properties.wobble_coefficient.value == pytest.approx(0.0066)

    def test_s15_general_properties_wobble_coefficient_unit(self, sections):
        assert sections[15].general_properties.wobble_coefficient.unit == "1/m"

    # Relaxation parameters (CEB-FIP-1990)
    def test_s15_relaxation_parameters_type(self, sections):
        assert isinstance(sections[15].relaxation_parameters, RelaxationParamsCEBFIP1990ParaModel)

    def test_s15_relaxation_parameters_code(self, sections):
        assert sections[15].relaxation_parameters.relaxation_code == RelaxationCodeEnumParaModel.CEB_FIP_1990

    def test_s15_relaxation_parameters_class(self, sections):
        assert sections[15].relaxation_parameters.relaxation_class == RelaxationClassCEBFIP1990EnumParaModel.CLASS_2_LOW

    def test_s15_relaxation_parameters_relaxation_1000_hours_value(self, sections):
        assert sections[15].relaxation_parameters.relaxation_1000_hours_value == pytest.approx(0.05)

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def test_file_not_found(self):
        provider = DataFileProvider(folder="/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            provider.get_sections_for_project()

    def test_invalid_json_raises_decode_error(self):
        with patch("builtins.open", mock_open(read_data="{ invalid json }")):
            with pytest.raises(json.JSONDecodeError):
                DataFileProvider(folder=".").get_sections_for_project()

    def test_none_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder=None).get_sections_for_project()

    def test_empty_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder="").get_sections_for_project()

    def test_missing_sections_key_returns_empty_list(self):
        with patch("builtins.open", mock_open(read_data=json.dumps({"other_key": []}))):
            result = DataFileProvider(folder=".").get_sections_for_project()
            assert result == []

    def test_unknown_section_family_raises_value_error(self):
        bad = json.dumps({"sections": [
            {"guid": "abc", "name": "x", "section_family": "unknown_family",
             "section_type": "unknown_type", "offset": "center-top"}
        ]})
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValueError, match="Unknown section"):
                DataFileProvider(folder=".").get_sections_for_project()

    # ------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------

    def test_consistent_results_across_calls(self, provider):
        first  = provider.get_sections_for_project()
        second = provider.get_sections_for_project()
        assert len(first) == len(second)
        for a, b in zip(first, second):
            assert a.name == b.name
            assert a.section_family == b.section_family

    def test_provider_stores_folder_path(self, fixtures_path):
        provider = DataFileProvider(folder=str(fixtures_path))
        assert provider.Folder == str(fixtures_path)

