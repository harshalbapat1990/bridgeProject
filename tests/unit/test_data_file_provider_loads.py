import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from pydantic import ValidationError

from bda.contracts.paramodel.groups.enums import StructuralComponentTypeParaModel
from bda.contracts.paramodel.loadings import LoadApplicationDomainEnum, LoadContextEnum, \
    MainCodeEnum, SecondaryCodeEnum, LoadServiceStateEnum
from bda.contracts.paramodel.loadings.design.aashto.construction_loads import \
    ExecutionLoad
from bda.contracts.paramodel.loadings.design.aashto.structural_loads import StructuralInServiceDeadLoad, \
    NonStructuralInServiceDeadLoad, DeadLoadingByDensityEnhancement, StructuralLoadApplicationByGroup, \
    DeadLoadingByDirectValue, StructuralLoadApplicationByComponentType, \
    NonStructuralDeadLoadApplicationByDeckAppurtenance, PrestressingInServiceLoad, \
    PrestressLoadByStress, PrestressApplicationTypeEnum, TendonJackingTypeEnum, \
    StructuralLoadApplicationBase
from bda.contracts.paramodel.loadings.design.aashto.enums import AashtoLoadNatureEnum, \
    PrimaryTrafficTypeEnum,  WindExposureCategoryEnum, \
    GradientDefinitionTypeEnum, DeckOverlayEnum, GradientZoneEnum, TrafficLoadModelEnum
from bda.contracts.paramodel.loadings.design.aashto.environment_loads import \
    WindInServiceLoad, GradientTemperatureLoad, UniformTemperatureLoad, \
    WindInConstructionLoad, UniformTemperatureParameters, \
    GradientTempParamsCustom, GradientTempParamsByZone, \
    EarthquakeLoad, ResponseSpectrumParameters, ResponseSpectrumPoint, \
    ModalAnalysisParameters, IncludedLoad, SettlementLoad, EarthquakeLoad, SettlementLoad
from bda.contracts.paramodel.loadings.design.aashto.live_loads import HL93ModelBrakingLoad, HL93ModelVerticalDirectLoad, \
    PedestrianStandardLoad, StandardLaneParameters, CustomLaneParameters
from bda.contracts.paramodel.loadings.enums import DeadLoadingMethodEnum, \
    StructuralApplicationTypeEnum, LoadApplicationTypeEnum, TrafficLoadTypeEnum, \
    EnvironmentLoadTypeEnum, DefinitionTypeEnum, StructuralLoadTypeEnum, \
    ModalAnalysisTypeEnum
from bda.contracts.paramodel.loadings.load_model_base_para_models import LoadModelBaseParaModel
from bda.contracts.shared import QuantityParaModel
from bda.infrastructure.data_providers.data_file_provider import DataFileProvider


def assert_quantity(q: QuantityParaModel, value: float, unit: str) -> None:
    assert isinstance(q, QuantityParaModel)
    assert q.value == pytest.approx(value)
    assert q.unit == unit


class TestDataFileProvider_Loads:
    """Unit tests for DataFileProvider.get_loads_for_project."""

    @pytest.fixture
    def fixtures_path(self) -> Path:
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def provider(self, fixtures_path: Path) -> DataFileProvider:
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture
    def loads(self, provider: DataFileProvider):
        return provider.get_loads_for_project()

    @pytest.fixture
    def structural_dead_by_group(self, loads):
        return loads[0]

    @pytest.fixture
    def structural_dead_by_component(self, loads):
        return loads[1]

    @pytest.fixture
    def non_structural_dead(self, loads):
        return loads[2]

    @pytest.fixture
    def braking_load(self, loads):
        return loads[3]

    @pytest.fixture
    def execution_load_full(self, loads):
        return loads[4]

    @pytest.fixture
    def execution_load_partial(self, loads):
        return loads[5]

    @pytest.fixture
    def wind_in_service(self, loads):
        return loads[6]

    @pytest.fixture
    def wind_in_construction(self, loads):
        return loads[7]

    @pytest.fixture
    def temperature_custom_gradient(self, loads):
        return loads[8]

    @pytest.fixture
    def temperature_zone_gradient(self, loads):
        return loads[9]

    @pytest.fixture
    def temperature_uniform(self, loads):
        return loads[10]

    @pytest.fixture
    def standard_Hl93_load_with_standard_lane(self, loads):
        return loads[11]

    @pytest.fixture
    def standard_Hl93_load_with_custom_lane(self, loads):
        return loads[12]

    @pytest.fixture
    def pedestrian_standard_load(self, loads):
        return loads[13]

    @pytest.fixture
    def prestressing_load(self, loads):
        return loads[14]

    @pytest.fixture
    def earthquake_without_vertical_rs(self, loads):
        return loads[15]

    @pytest.fixture
    def earthquake_with_vertical_rs(self, loads):
        return loads[16]

    @pytest.fixture
    def settlement_load(self, loads):
        return loads[17]
    # ------------------------------------------------------------------
    # Collection shape
    # ------------------------------------------------------------------

    def test_static_loads_json_exists(self, fixtures_path: Path):
        assert (fixtures_path / "loads.json").exists()

    def test_returns_list(self, loads):
        assert isinstance(loads, list)

    def test_returns_all_loads(self, loads):
        assert len(loads) == 18

    def test_all_items_are_load_model_base(self, loads):
        assert all(isinstance(item, LoadModelBaseParaModel) for item in loads)

    def test_type_discrimination_covers_all_concrete_types(self, loads):
        types = {type(load) for load in loads}
        assert StructuralInServiceDeadLoad in types
        assert NonStructuralInServiceDeadLoad in types
        assert HL93ModelVerticalDirectLoad in types
        assert PedestrianStandardLoad in types
        assert HL93ModelBrakingLoad in types
        assert ExecutionLoad in types
        assert WindInServiceLoad in types
        assert WindInConstructionLoad in types
        assert GradientTemperatureLoad in types
        assert UniformTemperatureLoad in types
        assert PrestressingInServiceLoad in types
        assert EarthquakeLoad in types
        assert SettlementLoad in types
    # ------------------------------------------------------------------
    # Structural dead load — by group (index 0)
    # ------------------------------------------------------------------

    def test_structural_dead_by_group_concrete_type(self, structural_dead_by_group):
        assert isinstance(structural_dead_by_group, StructuralInServiceDeadLoad)

    def test_structural_dead_by_group_static_load_type(self, structural_dead_by_group):
        assert structural_dead_by_group.load_application_domain == LoadApplicationDomainEnum.STRUCTURE

    def test_structural_dead_by_group_load_context(self, structural_dead_by_group):
        assert structural_dead_by_group.load_context == LoadContextEnum.DESIGN

    def test_structural_dead_by_group_main_code(self, structural_dead_by_group):
        assert structural_dead_by_group.main_code == MainCodeEnum.AASHTO

    def test_structural_dead_by_group_secondary_code_is_none(self, structural_dead_by_group):
        assert structural_dead_by_group.secondary_code == SecondaryCodeEnum.NONE

    def test_structural_dead_by_group_load_nature(self, structural_dead_by_group):
        assert structural_dead_by_group.load_nature == AashtoLoadNatureEnum.DC

    def test_structural_dead_by_group_load_application_domain(self, structural_dead_by_group):
        assert structural_dead_by_group.load_application_domain == LoadApplicationDomainEnum.STRUCTURE

    def test_structural_dead_by_group_load_service_state(self, structural_dead_by_group):
        assert structural_dead_by_group.load_service_state == LoadServiceStateEnum.IN_SERVICE

    def test_structural_dead_by_group_loading_concrete_type(self, structural_dead_by_group):
        assert isinstance(structural_dead_by_group.loading, DeadLoadingByDensityEnhancement)

    def test_structural_dead_by_group_loading_method(self, structural_dead_by_group):
        assert structural_dead_by_group.loading.method == DeadLoadingMethodEnum.DENSITY_ENHANCEMENT

    def test_structural_dead_by_group_loading_enhancement_factor(self, structural_dead_by_group):
        assert structural_dead_by_group.loading.enhancement_factor == pytest.approx(0.0)

    def test_structural_dead_by_group_application_concrete_type(self, structural_dead_by_group):
        assert isinstance(structural_dead_by_group.load_application, StructuralLoadApplicationByGroup)

    def test_structural_dead_by_group_application_type(self, structural_dead_by_group):
        assert structural_dead_by_group.load_application.application_type == StructuralApplicationTypeEnum.STRUCTURAL_GROUP_ID

    def test_structural_dead_by_group_application_group_id(self, structural_dead_by_group):
        assert structural_dead_by_group.load_application.group_id == "superstructure-group-01"

    # ------------------------------------------------------------------
    # Structural dead load — by component type (index 1)
    # ------------------------------------------------------------------

    def test_structural_dead_by_component_concrete_type(self, structural_dead_by_component):
        assert isinstance(structural_dead_by_component, StructuralInServiceDeadLoad)

    def test_structural_dead_by_component_secondary_code(self, structural_dead_by_component):
        assert structural_dead_by_component.secondary_code == SecondaryCodeEnum.UAE

    def test_structural_dead_by_component_load_nature(self, structural_dead_by_component):
        assert structural_dead_by_component.load_nature == AashtoLoadNatureEnum.DW

    def test_structural_dead_by_component_loading_concrete_type(self, structural_dead_by_component):
        assert isinstance(structural_dead_by_component.loading, DeadLoadingByDirectValue)

    def test_structural_dead_by_component_loading_method(self, structural_dead_by_component):
        assert structural_dead_by_component.loading.method == DeadLoadingMethodEnum.DIRECT_VALUE

    def test_structural_dead_by_component_loading_linear_load_value(self, structural_dead_by_component):
        assert_quantity(structural_dead_by_component.loading.linear_load_value, 12.5, "kN/m")

    def test_structural_dead_by_component_loading_pressure_load_value_is_none(self, structural_dead_by_component):
        assert structural_dead_by_component.loading.pressure_load_value is None

    def test_structural_dead_by_component_application_concrete_type(self, structural_dead_by_component):
        assert isinstance(structural_dead_by_component.load_application, StructuralLoadApplicationByComponentType)

    def test_structural_dead_by_component_application_type(self, structural_dead_by_component):
        assert structural_dead_by_component.load_application.application_type == StructuralApplicationTypeEnum.STRUCTURAL_COMPONENT_TYPE

    def test_structural_dead_by_component_component_type(self, structural_dead_by_component):
        assert structural_dead_by_component.load_application.component_type == StructuralComponentTypeParaModel.DECK_SLAB

    # ------------------------------------------------------------------
    # Non-structural dead load (index 2)
    # ------------------------------------------------------------------

    def test_non_structural_dead_concrete_type(self, non_structural_dead):
        assert isinstance(non_structural_dead, NonStructuralInServiceDeadLoad)

    def test_non_structural_dead_load_application_domain(self, non_structural_dead):
        assert non_structural_dead.load_application_domain == LoadApplicationDomainEnum.ANCILLARY_WORKS

    def test_non_structural_dead_load_service_state(self, non_structural_dead):
        assert non_structural_dead.load_service_state == LoadServiceStateEnum.IN_SERVICE

    def test_non_structural_dead_load_nature(self, non_structural_dead):
        assert non_structural_dead.load_nature == AashtoLoadNatureEnum.DW

    def test_non_structural_dead_loading_concrete_type(self, non_structural_dead):
        assert isinstance(non_structural_dead.loading, DeadLoadingByDensityEnhancement)

    def test_non_structural_dead_loading_enhancement_factor(self, non_structural_dead):
        assert non_structural_dead.loading.enhancement_factor == pytest.approx(0.10)

    def test_non_structural_dead_application_concrete_type(self, non_structural_dead):
        assert isinstance(non_structural_dead.load_application, NonStructuralDeadLoadApplicationByDeckAppurtenance)

    def test_non_structural_dead_application_type(self, non_structural_dead):
        assert non_structural_dead.load_application.application_type == LoadApplicationTypeEnum.DECK_APPURTENANCE_ID

    def test_non_structural_dead_appurtenance_id(self, non_structural_dead):
        assert non_structural_dead.load_application.appurtenance_id == "barrier-left-01"

    # ------------------------------------------------------------------
    # Braking load (index 3)
    # ------------------------------------------------------------------

    def test_braking_concrete_type(self, braking_load):
        assert isinstance(braking_load, HL93ModelBrakingLoad)

    def test_braking_load_application_domain(self, braking_load):
        assert braking_load.load_application_domain == LoadApplicationDomainEnum.LIVE_LOAD

    def test_braking_load_service_state(self, braking_load):
        assert braking_load.load_service_state == LoadServiceStateEnum.IN_SERVICE

    def test_braking_load_nature(self, braking_load):
        assert braking_load.load_nature == AashtoLoadNatureEnum.BR

    def test_braking_primary_traffic_type(self, braking_load):
        assert braking_load.primary_traffic_type == PrimaryTrafficTypeEnum.ROAD

    def test_braking_vehicle_def_type(self, braking_load):
        assert braking_load.vehicle_def_type == DefinitionTypeEnum.STANDARD

    def test_braking_traffic_load_type(self, braking_load):
        assert braking_load.traffic_load_type == TrafficLoadTypeEnum.BRAKING

    def test_braking_max_traffic_lanes_in_one_direction(self, braking_load):
        assert braking_load.max_traffic_lanes_in_one_direction == 3


    # ------------------------------------------------------------------
    # Execution load — all three UDLs defined (index 4)
    # ------------------------------------------------------------------

    def test_execution_full_concrete_type(self, execution_load_full):
        assert isinstance(execution_load_full, ExecutionLoad)

    def test_execution_full_load_application_domain(self, execution_load_full):
        assert execution_load_full.load_application_domain == LoadApplicationDomainEnum.CONSTRUCTION

    def test_execution_full_load_service_state(self, execution_load_full):
        assert execution_load_full.load_service_state == LoadServiceStateEnum.CONSTRUCTION

    def test_execution_full_load_nature(self, execution_load_full):
        assert execution_load_full.load_nature == AashtoLoadNatureEnum.CS

    def test_execution_full_fixed_material_udl(self, execution_load_full):
        assert_quantity(execution_load_full.load_fixed_material_udl, 1.0, "kN/m2")

    def test_execution_full_variable_material_udl(self, execution_load_full):
        assert_quantity(execution_load_full.load_variable_material_udl, 1.5, "kN/m2")

    def test_execution_full_personnel_and_eqp_udl(self, execution_load_full):
        assert_quantity(execution_load_full.load_personnel_and_eqp_udl, 2.4, "kN/m2")

    # ------------------------------------------------------------------
    # Execution load — only fixed UDL defined (index 5)
    # ------------------------------------------------------------------

    def test_execution_partial_concrete_type(self, execution_load_partial):
        assert isinstance(execution_load_partial, ExecutionLoad)

    def test_execution_partial_fixed_material_udl(self, execution_load_partial):
        assert_quantity(execution_load_partial.load_fixed_material_udl, 0.5, "kN/m2")

    def test_execution_partial_variable_material_udl_is_none(self, execution_load_partial):
        assert execution_load_partial.load_variable_material_udl is None

    def test_execution_partial_personnel_and_eqp_udl_is_none(self, execution_load_partial):
        assert execution_load_partial.load_personnel_and_eqp_udl is None

    # ------------------------------------------------------------------
    # Wind in-service load (index 6)
    # ------------------------------------------------------------------

    def test_wind_in_service_concrete_type(self, wind_in_service):
        assert isinstance(wind_in_service, WindInServiceLoad)

    def test_wind_in_service_load_application_domain(self, wind_in_service):
        assert wind_in_service.load_application_domain == LoadApplicationDomainEnum.ENVIRONMENT

    def test_wind_in_service_load_service_state(self, wind_in_service):
        assert wind_in_service.load_service_state == LoadServiceStateEnum.IN_SERVICE

    def test_wind_in_service_env_load_type(self, wind_in_service):
        assert wind_in_service.env_load_type == EnvironmentLoadTypeEnum.WIND

    def test_wind_in_service_load_nature(self, wind_in_service):
        assert wind_in_service.load_nature == AashtoLoadNatureEnum.WS

    def test_wind_in_service_exposure_category(self, wind_in_service):
        assert wind_in_service.exposure_category == WindExposureCategoryEnum.CATEGORY_B

    def test_wind_in_service_reference_superstructure_height(self, wind_in_service):
        assert_quantity(wind_in_service.reference_superstructure_height, 6.5, "m")

    def test_wind_in_service_reference_substructure_height(self, wind_in_service):
        assert_quantity(wind_in_service.reference_substructure_height, 4.0, "m")

    def test_wind_in_service_gust_strength_iii(self, wind_in_service):
        assert_quantity(wind_in_service.wind_speed_3s_gust_strength_iii, 45.0, "m/s")

    def test_wind_in_service_gust_service_iv(self, wind_in_service):
        assert_quantity(wind_in_service.wind_speed_3s_gust_service_iv, 38.0, "m/s")

    def test_wind_in_service_gust_service_i(self, wind_in_service):
        assert_quantity(wind_in_service.wind_speed_3s_gust_service_i, 35.0, "m/s")

    def test_wind_in_service_gust_strength_v(self, wind_in_service):
        assert_quantity(wind_in_service.wind_speed_3s_gust_strength_v, 50.0, "m/s")

    # ------------------------------------------------------------------
    # Wind in-construction load (index 7)
    # ------------------------------------------------------------------

    def test_wind_in_construction_concrete_type(self, wind_in_construction):
        assert isinstance(wind_in_construction, WindInConstructionLoad)

    def test_wind_in_construction_load_service_state(self, wind_in_construction):
        assert wind_in_construction.load_service_state == LoadServiceStateEnum.CONSTRUCTION

    def test_wind_in_construction_env_load_type(self, wind_in_construction):
        assert wind_in_construction.env_load_type == EnvironmentLoadTypeEnum.WIND

    def test_wind_in_construction_exposure_category(self, wind_in_construction):
        assert wind_in_construction.exposure_category == WindExposureCategoryEnum.CATEGORY_C

    def test_wind_in_construction_gust_active_work_zone(self, wind_in_construction):
        assert_quantity(wind_in_construction.wind_speed_3s_gust_active_work_zone, 40.0, "m/s")

    def test_wind_in_construction_gust_inactive_work_zone(self, wind_in_construction):
        assert_quantity(wind_in_construction.wind_speed_3s_gust_inactive_work_zone, 45.0, "m/s")

    def test_wind_in_construction_reduction_factor_active(self, wind_in_construction):
        assert wind_in_construction.wind_speed_reduction_factor_active_work_zone == pytest.approx(0.75)

    def test_wind_in_construction_reduction_factor_inactive(self, wind_in_construction):
        assert wind_in_construction.wind_speed_reduction_factor_inactive_work_zone == pytest.approx(1.0)

    def test_wind_in_construction_avg_height_active(self, wind_in_construction):
        assert_quantity(wind_in_construction.avg_height_of_superstructure_for_active_work_zone, 8.0, "m")

    def test_wind_in_construction_avg_height_inactive(self, wind_in_construction):
        assert_quantity(wind_in_construction.avg_height_of_superstructure_for_inactive_work_zone, 10.0, "m")

    def test_wind_in_construction_duration_days(self, wind_in_construction):
        assert wind_in_construction.superstructure_constr_duration_days == 180

    # ------------------------------------------------------------------
    # Temperature load — custom gradient (index 8)
    # ------------------------------------------------------------------

    def test_temperature_custom_concrete_type(self, temperature_custom_gradient):
        assert isinstance(temperature_custom_gradient, GradientTemperatureLoad)

    def test_temperature_custom_env_load_type(self, temperature_custom_gradient):
        assert temperature_custom_gradient.env_load_type == EnvironmentLoadTypeEnum.TEMPERATURE

    def test_temperature_custom_load_nature(self, temperature_custom_gradient):
        assert temperature_custom_gradient.load_nature == AashtoLoadNatureEnum.TG

    def test_temperature_custom_gradient_concrete_type(self, temperature_custom_gradient):
        assert isinstance(temperature_custom_gradient.gradient_temperature_params, GradientTempParamsCustom)

    def test_temperature_custom_gradient_definition_type(self, temperature_custom_gradient):
        assert temperature_custom_gradient.gradient_temperature_params.definition_type == GradientDefinitionTypeEnum.CUSTOM

    def test_temperature_custom_gradient_deck_overlay(self, temperature_custom_gradient):
        assert temperature_custom_gradient.gradient_temperature_params.deck_overlay == DeckOverlayEnum.ASPHALT

    def test_temperature_custom_gradient_cooling_t1(self, temperature_custom_gradient):
        assert_quantity(temperature_custom_gradient.gradient_temperature_params.cooling_t1, -5.0, "degC")

    def test_temperature_custom_gradient_cooling_t2(self, temperature_custom_gradient):
        assert_quantity(temperature_custom_gradient.gradient_temperature_params.cooling_t2, -3.5, "degC")

    def test_temperature_custom_gradient_cooling_t3(self, temperature_custom_gradient):
        assert_quantity(temperature_custom_gradient.gradient_temperature_params.cooling_t3, 0.0, "degC")

    def test_temperature_custom_gradient_heating_t1(self, temperature_custom_gradient):
        assert_quantity(temperature_custom_gradient.gradient_temperature_params.heating_t1, 12.0, "degC")

    def test_temperature_custom_gradient_heating_t2(self, temperature_custom_gradient):
        assert_quantity(temperature_custom_gradient.gradient_temperature_params.heating_t2, 6.7, "degC")

    def test_temperature_custom_gradient_heating_t3(self, temperature_custom_gradient):
        assert_quantity(temperature_custom_gradient.gradient_temperature_params.heating_t3, 3.0, "degC")

    # ------------------------------------------------------------------
    # Temperature load — by zone gradient (index 9)
    # ------------------------------------------------------------------

    def test_temperature_zone_concrete_type(self, temperature_zone_gradient):
        assert isinstance(temperature_zone_gradient, GradientTemperatureLoad)

    def test_temperature_zone_load_nature(self, temperature_zone_gradient):
        assert temperature_zone_gradient.load_nature == AashtoLoadNatureEnum.TG

    def test_temperature_zone_gradient_concrete_type(self, temperature_zone_gradient):
        assert isinstance(temperature_zone_gradient.gradient_temperature_params, GradientTempParamsByZone)

    def test_temperature_zone_gradient_definition_type(self, temperature_zone_gradient):
        assert temperature_zone_gradient.gradient_temperature_params.definition_type == GradientDefinitionTypeEnum.BY_ZONE

    def test_temperature_zone_gradient_deck_overlay(self, temperature_zone_gradient):
        assert temperature_zone_gradient.gradient_temperature_params.deck_overlay == DeckOverlayEnum.PLAIN

    def test_temperature_zone_gradient_zone(self, temperature_zone_gradient):
        assert temperature_zone_gradient.gradient_temperature_params.zone == GradientZoneEnum.ZONE_1

    # ------------------------------------------------------------------
    # Temperature load — uniform (index 10)
    # ------------------------------------------------------------------

    def test_temperature_uniform_concrete_type(self, temperature_uniform):
        assert isinstance(temperature_uniform, UniformTemperatureLoad)

    def test_temperature_uniform_env_load_type(self, temperature_uniform):
        assert temperature_uniform.env_load_type == EnvironmentLoadTypeEnum.TEMPERATURE

    def test_temperature_uniform_load_nature(self, temperature_uniform):
        assert temperature_uniform.load_nature == AashtoLoadNatureEnum.TU

    def test_temperature_uniform_params_type(self, temperature_uniform):
        assert isinstance(temperature_uniform.uniform_temperature_params, UniformTemperatureParameters)

    def test_temperature_uniform_min_design(self, temperature_uniform):
        assert_quantity(temperature_uniform.uniform_temperature_params.temperature_min_design, -10.0, "degC")

    def test_temperature_uniform_max_design(self, temperature_uniform):
        assert_quantity(temperature_uniform.uniform_temperature_params.temperature_max_design, 50.0, "degC")

    def test_temperature_uniform_ref_expansion(self, temperature_uniform):
        assert_quantity(temperature_uniform.uniform_temperature_params.temperature_ref_expansion, 20.0, "degC")

    def test_temperature_uniform_ref_contraction(self, temperature_uniform):
        assert_quantity(temperature_uniform.uniform_temperature_params.temperature_ref_contraction, 20.0, "degC")

    # ------------------------------------------------------------------
    # Live load — HL-93 vertical direct with standard lane definition (index 11)
    # ------------------------------------------------------------------

    def test_standard_HL93_load_with_standard_lane_concrete_type(self, standard_Hl93_load_with_standard_lane):
        assert isinstance(standard_Hl93_load_with_standard_lane, HL93ModelVerticalDirectLoad)

    def test_standard_HL93_load_with_standard_lane_load_application_domain(self, standard_Hl93_load_with_standard_lane):
        assert standard_Hl93_load_with_standard_lane.load_application_domain == LoadApplicationDomainEnum.LIVE_LOAD

    def test_standard_HL93_load_with_standard_lane_load_service_state(self, standard_Hl93_load_with_standard_lane):
        assert standard_Hl93_load_with_standard_lane.load_service_state == LoadServiceStateEnum.IN_SERVICE

    def test_standard_HL93_load_with_standard_lane_load_nature(self, standard_Hl93_load_with_standard_lane):
        assert standard_Hl93_load_with_standard_lane.load_nature == AashtoLoadNatureEnum.LL

    def test_standard_HL93_load_with_standard_lane_primary_traffic_type(self, standard_Hl93_load_with_standard_lane):
        assert standard_Hl93_load_with_standard_lane.primary_traffic_type == PrimaryTrafficTypeEnum.ROAD

    def test_standard_HL93_load_with_standard_lane_vehicle_def_type(self, standard_Hl93_load_with_standard_lane):
        assert standard_Hl93_load_with_standard_lane.vehicle_def_type == DefinitionTypeEnum.STANDARD

    def test_standard_HL93_load_with_standard_lane_traffic_load_model(self, standard_Hl93_load_with_standard_lane):
        assert standard_Hl93_load_with_standard_lane.traffic_load_model == TrafficLoadModelEnum.HL93

    def test_standard_HL93_load_with_standard_lane_traffic_load_type(self, standard_Hl93_load_with_standard_lane):
        assert standard_Hl93_load_with_standard_lane.traffic_load_type == TrafficLoadTypeEnum.VERTICAL_TRAFFIC_DIRECT

    def test_standard_HL93_load_with_standard_lane_include_truck_model(self, standard_Hl93_load_with_standard_lane):
        assert standard_Hl93_load_with_standard_lane.include_truck_model is False

    def test_standard_HL93_load_with_standard_lane_include_tandem_model(self, standard_Hl93_load_with_standard_lane):
        assert standard_Hl93_load_with_standard_lane.include_tandem_model is False

    def test_standard_HL93_load_with_standard_lane_include_fatigue_model(self, standard_Hl93_load_with_standard_lane):
        assert standard_Hl93_load_with_standard_lane.include_fatigue_model is False

    def test_standard_HL93_load_with_standard_lane_lane_parameters_concrete_type(self, standard_Hl93_load_with_standard_lane):
        assert isinstance(standard_Hl93_load_with_standard_lane.lane_parameters, StandardLaneParameters)

    def test_standard_HL93_load_with_standard_lane_lane_definition_type(self, standard_Hl93_load_with_standard_lane):
        assert standard_Hl93_load_with_standard_lane.lane_parameters.lane_definition_type == DefinitionTypeEnum.STANDARD

    # ------------------------------------------------------------------
    # Live load — HL-93 vertical direct with custom lane definition (index 12)
    # ------------------------------------------------------------------

    def test_standard_HL93_load_with_custom_lane_concrete_type(self, standard_Hl93_load_with_custom_lane):
        assert isinstance(standard_Hl93_load_with_custom_lane, HL93ModelVerticalDirectLoad)

    def test_standard_HL93_load_with_custom_lane_load_application_domain(self, standard_Hl93_load_with_custom_lane):
        assert standard_Hl93_load_with_custom_lane.load_application_domain == LoadApplicationDomainEnum.LIVE_LOAD

    def test_standard_HL93_load_with_custom_lane_load_service_state(self, standard_Hl93_load_with_custom_lane):
        assert standard_Hl93_load_with_custom_lane.load_service_state == LoadServiceStateEnum.IN_SERVICE

    def test_standard_HL93_load_with_custom_lane_load_nature(self, standard_Hl93_load_with_custom_lane):
        assert standard_Hl93_load_with_custom_lane.load_nature == AashtoLoadNatureEnum.LL

    def test_standard_HL93_load_with_custom_lane_primary_traffic_type(self, standard_Hl93_load_with_custom_lane):
        assert standard_Hl93_load_with_custom_lane.primary_traffic_type == PrimaryTrafficTypeEnum.ROAD

    def test_standard_HL93_load_with_custom_lane_vehicle_def_type(self, standard_Hl93_load_with_custom_lane):
        assert standard_Hl93_load_with_custom_lane.vehicle_def_type == DefinitionTypeEnum.STANDARD

    def test_standard_HL93_load_with_custom_lane_traffic_load_model(self, standard_Hl93_load_with_custom_lane):
        assert standard_Hl93_load_with_custom_lane.traffic_load_model == TrafficLoadModelEnum.HL93

    def test_standard_HL93_load_with_custom_lane_traffic_load_type(self, standard_Hl93_load_with_custom_lane):
        assert standard_Hl93_load_with_custom_lane.traffic_load_type == TrafficLoadTypeEnum.VERTICAL_TRAFFIC_DIRECT

    def test_standard_HL93_load_with_custom_lane_include_truck_model(self, standard_Hl93_load_with_custom_lane):
        assert standard_Hl93_load_with_custom_lane.include_truck_model is True

    def test_standard_HL93_load_with_custom_lane_include_tandem_model(self, standard_Hl93_load_with_custom_lane):
        assert standard_Hl93_load_with_custom_lane.include_tandem_model is True

    def test_standard_HL93_load_with_custom_lane_include_fatigue_model(self, standard_Hl93_load_with_custom_lane):
        assert standard_Hl93_load_with_custom_lane.include_fatigue_model is True

    def test_standard_HL93_load_with_custom_lane_lane_parameters_concrete_type(self, standard_Hl93_load_with_custom_lane):
        assert isinstance(standard_Hl93_load_with_custom_lane.lane_parameters, CustomLaneParameters)

    def test_standard_HL93_load_with_custom_lane_lane_definition_type(self, standard_Hl93_load_with_custom_lane):
        assert standard_Hl93_load_with_custom_lane.lane_parameters.lane_definition_type == DefinitionTypeEnum.CUSTOM

    def test_standard_HL93_load_with_custom_lane_lane_width(self, standard_Hl93_load_with_custom_lane):
        assert_quantity(standard_Hl93_load_with_custom_lane.lane_parameters.lane_width, 3.5, "m")

    # ------------------------------------------------------------------
    # Live load — Pedestrian standard load (index 13)
    # ------------------------------------------------------------------

    def test_pedestrian_standard_load_concrete_type(self, pedestrian_standard_load):
        assert isinstance(pedestrian_standard_load, PedestrianStandardLoad)

    def test_pedestrian_standard_load_load_application_domain(self, pedestrian_standard_load):
        assert pedestrian_standard_load.load_application_domain == LoadApplicationDomainEnum.LIVE_LOAD

    def test_pedestrian_standard_load_load_service_state(self, pedestrian_standard_load):
        assert pedestrian_standard_load.load_service_state == LoadServiceStateEnum.IN_SERVICE

    def test_pedestrian_standard_load_load_nature(self, pedestrian_standard_load):
        assert pedestrian_standard_load.load_nature == AashtoLoadNatureEnum.PL

    def test_pedestrian_standard_load_primary_traffic_type(self, pedestrian_standard_load):
        assert pedestrian_standard_load.primary_traffic_type == PrimaryTrafficTypeEnum.ROAD

    def test_pedestrian_standard_load_vehicle_def_type(self, pedestrian_standard_load):
        assert pedestrian_standard_load.vehicle_def_type == DefinitionTypeEnum.STANDARD

    def test_pedestrian_standard_load_traffic_load_model(self, pedestrian_standard_load):
        assert pedestrian_standard_load.traffic_load_model == TrafficLoadModelEnum.Pedestrian

    # ------------------------------------------------------------------
    # Prestressing load — Prestressing load with application by stress (index 14)
    # ------------------------------------------------------------------

    def test_prestressing_concrete_type(self, prestressing_load):
        assert isinstance(prestressing_load, PrestressingInServiceLoad)

    def test_prestressing_load_context(self, prestressing_load):
        assert prestressing_load.load_context == LoadContextEnum.DESIGN

    def test_prestressing_main_code(self, prestressing_load):
        assert prestressing_load.main_code == MainCodeEnum.AASHTO

    def test_prestressing_secondary_code_is_none(self, prestressing_load):
        assert prestressing_load.secondary_code == SecondaryCodeEnum.NONE

    def test_prestressing_load_application_domain(self, prestressing_load):
        assert prestressing_load.load_application_domain == LoadApplicationDomainEnum.STRUCTURE

    def test_prestressing_load_service_state(self, prestressing_load):
        assert prestressing_load.load_service_state == LoadServiceStateEnum.IN_SERVICE

    def test_prestressing_load_nature(self, prestressing_load):
        assert prestressing_load.load_nature == AashtoLoadNatureEnum.PS

    def test_prestressing_structural_load_type(self, prestressing_load):
        assert prestressing_load.structural_load_type == StructuralLoadTypeEnum.PRESTRESSING

    def test_prestressing_loading_concrete_type(self, prestressing_load):
        assert isinstance(prestressing_load.loading, PrestressLoadByStress)

    def test_prestressing_loading_application_type(self, prestressing_load):
        assert prestressing_load.loading.prestress_application_type == PrestressApplicationTypeEnum.BY_STRESS

    def test_prestressing_loading_tendon_jacking_type(self, prestressing_load):
        assert prestressing_load.loading.tendon_jacking_type == TendonJackingTypeEnum.BOTH_ENDS

    def test_prestressing_loading_tendon_stress(self, prestressing_load):
        assert_quantity(prestressing_load.loading.tendon_stress, 1200.0, "MPa")

    def test_prestressing_load_application_is_list(self, prestressing_load):
        assert isinstance(prestressing_load.load_application, list)

    def test_prestressing_load_application_length(self, prestressing_load):
        assert len(prestressing_load.load_application) == 1

    def test_prestressing_load_application_concrete_type(self, prestressing_load):
        assert isinstance(prestressing_load.load_application[0], StructuralLoadApplicationBase)

    def test_prestressing_load_application_by_component_type(self, prestressing_load):
        assert isinstance(prestressing_load.load_application[0], StructuralLoadApplicationByComponentType)

    def test_prestressing_load_application_application_type(self, prestressing_load):
        assert prestressing_load.load_application[0].application_type == StructuralApplicationTypeEnum.STRUCTURAL_COMPONENT_TYPE

    # ------------------------------------------------------------------
    # Earthquake load — without vertical response spectrum (index 15)
    # ------------------------------------------------------------------

    def test_earthquake_without_vertical_rs_concrete_type(self, earthquake_without_vertical_rs):
        assert isinstance(earthquake_without_vertical_rs, EarthquakeLoad)

    def test_earthquake_without_vertical_rs_load_context(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.load_context == LoadContextEnum.DESIGN

    def test_earthquake_without_vertical_rs_main_code(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.main_code == MainCodeEnum.AASHTO

    def test_earthquake_without_vertical_rs_secondary_code_is_none(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.secondary_code == SecondaryCodeEnum.NONE

    def test_earthquake_without_vertical_rs_load_application_domain(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.load_application_domain == LoadApplicationDomainEnum.ENVIRONMENT

    def test_earthquake_without_vertical_rs_load_service_state(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.load_service_state == LoadServiceStateEnum.IN_SERVICE

    def test_earthquake_without_vertical_rs_env_load_type(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.env_load_type == EnvironmentLoadTypeEnum.EARTHQUAKE

    def test_earthquake_without_vertical_rs_load_nature(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.load_nature == AashtoLoadNatureEnum.EQ

    def test_earthquake_without_vertical_rs_response_spectrum_params_type(self, earthquake_without_vertical_rs):
        assert isinstance(earthquake_without_vertical_rs.response_spectrum_params, ResponseSpectrumParameters)

    def test_earthquake_without_vertical_rs_damping_ratio(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.response_spectrum_params.damping_ratio == pytest.approx(0.05)

    def test_earthquake_without_vertical_rs_horizontal_rs_length(self, earthquake_without_vertical_rs):
        assert len(earthquake_without_vertical_rs.response_spectrum_params.horizontal_response_spectrum) == 6

    def test_earthquake_without_vertical_rs_horizontal_rs_point_type(self, earthquake_without_vertical_rs):
        assert all(
            isinstance(point, ResponseSpectrumPoint)
            for point in earthquake_without_vertical_rs.response_spectrum_params.horizontal_response_spectrum
        )

    def test_earthquake_without_vertical_rs_horizontal_rs_first_point(self, earthquake_without_vertical_rs):
        first = earthquake_without_vertical_rs.response_spectrum_params.horizontal_response_spectrum[0]
        assert_quantity(first.period, 0.0, "s")
        assert_quantity(first.acceleration, 0.0, "m/s^2")

    def test_earthquake_without_vertical_rs_horizontal_rs_last_point(self, earthquake_without_vertical_rs):
        last = earthquake_without_vertical_rs.response_spectrum_params.horizontal_response_spectrum[-1]
        assert_quantity(last.period, 5.0, "s")
        assert_quantity(last.acceleration, 25.0, "m/s^2")

    def test_earthquake_without_vertical_rs_consider_vertical_rs(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.response_spectrum_params.consider_vertical_rs is False

    def test_earthquake_without_vertical_rs_use_horizontal_as_vertical_is_none(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.response_spectrum_params.use_horizontal_rs_as_vertical is None

    def test_earthquake_without_vertical_rs_vertical_rs_is_none(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.response_spectrum_params.vertical_response_spectrum is None

    def test_earthquake_without_vertical_rs_modal_params_type(self, earthquake_without_vertical_rs):
        assert isinstance(earthquake_without_vertical_rs.modal_analysis_params, ModalAnalysisParameters)

    def test_earthquake_without_vertical_rs_modal_analysis_type(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.modal_analysis_params.modal_analysis_type == ModalAnalysisTypeEnum.EIGEN_VECTORS_LANCZOS

    def test_earthquake_without_vertical_rs_number_of_modes(self, earthquake_without_vertical_rs):
        assert earthquake_without_vertical_rs.modal_analysis_params.number_of_modes == 10

    def test_earthquake_without_vertical_rs_included_load_types_length(self, earthquake_without_vertical_rs):
        assert len(earthquake_without_vertical_rs.modal_analysis_params.included_load_types) == 2

    def test_earthquake_without_vertical_rs_included_load_types_type(self, earthquake_without_vertical_rs):
        assert all(
            isinstance(load, IncludedLoad)
            for load in earthquake_without_vertical_rs.modal_analysis_params.included_load_types
        )

    def test_earthquake_without_vertical_rs_included_load_first(self, earthquake_without_vertical_rs):
        first = earthquake_without_vertical_rs.modal_analysis_params.included_load_types[0]
        assert first.load_nature == AashtoLoadNatureEnum.DC
        assert first.mass_participation == pytest.approx(1.0)

    def test_earthquake_without_vertical_rs_included_load_second(self, earthquake_without_vertical_rs):
        second = earthquake_without_vertical_rs.modal_analysis_params.included_load_types[1]
        assert second.load_nature == AashtoLoadNatureEnum.DW
        assert second.mass_participation == pytest.approx(1.2)

    # ------------------------------------------------------------------
    # Earthquake load — with vertical response spectrum (index 16)
    # ------------------------------------------------------------------

    def test_earthquake_with_vertical_rs_concrete_type(self, earthquake_with_vertical_rs):
        assert isinstance(earthquake_with_vertical_rs, EarthquakeLoad)

    def test_earthquake_with_vertical_rs_load_application_domain(self, earthquake_with_vertical_rs):
        assert earthquake_with_vertical_rs.load_application_domain == LoadApplicationDomainEnum.ENVIRONMENT

    def test_earthquake_with_vertical_rs_load_service_state(self, earthquake_with_vertical_rs):
        assert earthquake_with_vertical_rs.load_service_state == LoadServiceStateEnum.IN_SERVICE

    def test_earthquake_with_vertical_rs_env_load_type(self, earthquake_with_vertical_rs):
        assert earthquake_with_vertical_rs.env_load_type == EnvironmentLoadTypeEnum.EARTHQUAKE

    def test_earthquake_with_vertical_rs_load_nature(self, earthquake_with_vertical_rs):
        assert earthquake_with_vertical_rs.load_nature == AashtoLoadNatureEnum.EQ

    def test_earthquake_with_vertical_rs_damping_ratio(self, earthquake_with_vertical_rs):
        assert earthquake_with_vertical_rs.response_spectrum_params.damping_ratio == pytest.approx(0.05)

    def test_earthquake_with_vertical_rs_consider_vertical_rs(self, earthquake_with_vertical_rs):
        assert earthquake_with_vertical_rs.response_spectrum_params.consider_vertical_rs is True

    def test_earthquake_with_vertical_rs_use_horizontal_as_vertical(self, earthquake_with_vertical_rs):
        assert earthquake_with_vertical_rs.response_spectrum_params.use_horizontal_rs_as_vertical is False

    def test_earthquake_with_vertical_rs_vertical_rs_length(self, earthquake_with_vertical_rs):
        assert len(earthquake_with_vertical_rs.response_spectrum_params.vertical_response_spectrum) == 6

    def test_earthquake_with_vertical_rs_vertical_rs_point_type(self, earthquake_with_vertical_rs):
        assert all(
            isinstance(point, ResponseSpectrumPoint)
            for point in earthquake_with_vertical_rs.response_spectrum_params.vertical_response_spectrum
        )

    def test_earthquake_with_vertical_rs_vertical_rs_first_point(self, earthquake_with_vertical_rs):
        first = earthquake_with_vertical_rs.response_spectrum_params.vertical_response_spectrum[0]
        assert_quantity(first.period, 0.0, "s")
        assert_quantity(first.acceleration, 0.0, "m/s^2")

    def test_earthquake_with_vertical_rs_vertical_rs_last_point(self, earthquake_with_vertical_rs):
        last = earthquake_with_vertical_rs.response_spectrum_params.vertical_response_spectrum[-1]
        assert_quantity(last.period, 5.0, "s")
        assert_quantity(last.acceleration, 12.5, "m/s^2")

    def test_earthquake_with_vertical_rs_modal_analysis_type(self, earthquake_with_vertical_rs):
        assert earthquake_with_vertical_rs.modal_analysis_params.modal_analysis_type == ModalAnalysisTypeEnum.EIGEN_VECTORS_LANCZOS

    def test_earthquake_with_vertical_rs_number_of_modes(self, earthquake_with_vertical_rs):
        assert earthquake_with_vertical_rs.modal_analysis_params.number_of_modes == 10

    def test_earthquake_with_vertical_rs_included_load_types_length(self, earthquake_with_vertical_rs):
        assert len(earthquake_with_vertical_rs.modal_analysis_params.included_load_types) == 2

    # ------------------------------------------------------------------
    # Settlement load (index 17)
    # ------------------------------------------------------------------

    def test_settlement_concrete_type(self, settlement_load):
        assert isinstance(settlement_load, SettlementLoad)

    def test_settlement_load_context(self, settlement_load):
        assert settlement_load.load_context == LoadContextEnum.DESIGN

    def test_settlement_main_code(self, settlement_load):
        assert settlement_load.main_code == MainCodeEnum.AASHTO

    def test_settlement_secondary_code_is_none(self, settlement_load):
        assert settlement_load.secondary_code == SecondaryCodeEnum.NONE

    def test_settlement_load_application_domain(self, settlement_load):
        assert settlement_load.load_application_domain == LoadApplicationDomainEnum.ENVIRONMENT

    def test_settlement_load_service_state(self, settlement_load):
        assert settlement_load.load_service_state == LoadServiceStateEnum.IN_SERVICE

    def test_settlement_env_load_type(self, settlement_load):
        assert settlement_load.env_load_type == EnvironmentLoadTypeEnum.SETTLEMENT

    def test_settlement_load_nature(self, settlement_load):
        assert settlement_load.load_nature == AashtoLoadNatureEnum.SE

    def test_settlement_diff_settlement_value(self, settlement_load):
        assert_quantity(settlement_load.diff_settlement_value, 15.0, "mm")

    # ------------------------------------------------------------------
    # Error handling / negative tests
    # ------------------------------------------------------------------

    def test_file_not_found(self):
        provider = DataFileProvider(folder="/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            provider.get_loads_for_project()

    def test_invalid_json_raises_decode_error(self):
        with patch("builtins.open", mock_open(read_data="{ invalid json }")):
            with pytest.raises(json.JSONDecodeError):
                DataFileProvider(folder=".").get_loads_for_project()

    def test_none_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder=None).get_loads_for_project()

    def test_empty_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder="").get_loads_for_project()

    def test_missing_static_loads_key_returns_empty_list(self):
        with patch("builtins.open", mock_open(read_data=json.dumps({"other_key": []}))):
            result = DataFileProvider(folder=".").get_loads_for_project()
            assert result == []

    def test_unknown_load_type_raises_validation_error(self):
        bad = json.dumps({
            "loads": [
                {
                    "load_context": "design",
                    "main_code": "AASHTO",
                    "load_application_domain": "Structure",
                    "load_service_state": "In Service",
                    "load_nature": "DC",
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_loads_for_project()

    def test_invalid_load_nature_raises_validation_error(self):
        bad = json.dumps({
            "loads": [
                {
                    "load_context": "design",
                    "main_code": "AASHTO",
                    "load_application_domain": "Structure",
                    "load_service_state": "In Service",
                    "load_nature": "INVALID_NATURE",
                    "loading": {"method": "density enhancement", "enhancement_factor": 0.0},
                    "load_application": {"application_type": "structural group id", "group_id": "G1"},
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_loads_for_project()

    def test_enhancement_factor_below_minus_100_raises_validation_error(self):
        bad = json.dumps({
            "loads": [
                {
                    "load_context": "design",
                    "main_code": "AASHTO",
                    "load_application_domain": "Structure",
                    "load_service_state": "In Service",
                    "load_nature": "DC",
                    "loading": {"method": "density enhancement", "enhancement_factor": -150.0},
                    "load_application": {"application_type": "structural group id", "group_id": "G1"},
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_loads_for_project()

    def test_max_traffic_lanes_zero_raises_validation_error(self):
        bad = json.dumps({
            "loads": [
                {
                    "load_context": "design",
                    "main_code": "AASHTO",
                    "load_application_domain": "Live load",
                    "load_service_state": "In Service",
                    "load_nature": "BR",
                    "primary_traffic_type": "road",
                    "vehicle_def_type": "default",
                    "traffic_load_type": "braking",
                    "max_traffic_lanes_in_one_direction": 0,
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_loads_for_project()

    def test_invalid_dead_loading_method_raises_validation_error(self):
        bad = json.dumps({
            "loads": [
                {
                    "load_context": "design",
                    "main_code": "AASHTO",
                    "load_application_domain": "Structure",
                    "load_service_state": "In Service",
                    "load_nature": "DC",
                    "loading": {"method": "volume calculation"},
                    "load_application": {"application_type": "structural group id", "group_id": "G1"},
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_loads_for_project()

    def test_invalid_wind_exposure_category_raises_validation_error(self):
        bad = json.dumps({
            "loads": [
                {
                    "load_context": "design",
                    "main_code": "AASHTO",
                    "load_application_domain": "Environment",
                    "load_service_state": "In Service",
                    "load_nature": "WS",
                    "env_load_type": "wind",
                    "exposure_category": "Category_Z",
                    "reference_superstructure_height": {"value": 5.0, "unit": "m"},
                    "reference_substructure_height": {"value": 2.0, "unit": "m"},
                    "wind_speed_3s_gust_strength_iii": {"value": 45.0, "unit": "m/s"},
                    "wind_speed_3s_gust_service_iv": {"value": 38.0, "unit": "m/s"},
                    "wind_speed_3s_gust_service_i": {"value": 35.0, "unit": "m/s"},
                    "wind_speed_3s_gust_strength_v": {"value": 50.0, "unit": "m/s"},
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_loads_for_project()

    # ------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------

    def test_consistent_results_across_calls(self, provider: DataFileProvider):
        first = provider.get_loads_for_project()
        second = provider.get_loads_for_project()

        assert len(first) == len(second)
        for a, b in zip(first, second):
            assert type(a) is type(b)
            assert a.load_nature == b.load_nature

    def test_provider_stores_folder_path(self, fixtures_path: Path):
        provider = DataFileProvider(folder=str(fixtures_path))
        assert provider.Folder == str(fixtures_path)
