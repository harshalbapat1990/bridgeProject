from bda.contracts.paramodel.bearings.adapter import BearingBCsParaModelAdapter
from bda.contracts.paramodel.foundations.adapter import FoundationBCsParaModelAdapter
from bda.contracts.paramodel.groups.adapter import GroupsParaModelAdapter
from bda.infrastructure.data_providers.data_speckle_provider import DataSpeckleProvider
from bda.contracts.paramodel.groups.enums import (
    BearingConfigurationTypeParaModel,
    ElementOrientationParaModel,
)
from bda.contracts.paramodel.foundations.enums import (
    FoundationApplicationTypeEnumParaModel,
    FoundationModelTypeParaModel,
    SoilProfileTypeEnumParaModel,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.bearings.bearing_bc_collection import (
    BearingBCCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.boundary_conditions_collection import (
    BoundaryConditionsCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.bearings.bearing_bc_data_object import (
    BearingBCDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.foundations.lumped_foundation_data_object import (
    LumpedFoundationDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.foundations.pile_interaction_foundation_data_object import (
    PileDefinitionInput,
    PileInteractionFoundationDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.foundations.foundation_bc_collection import (
    FoundationBCCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_bridge import (
    GeometryGroupBridge,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_superstructure import (
    GeometryGroupSuperstructure,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_diaphragm import (
    GeometryGroupDiaphragm,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_above_ground import (
    GeometryGroupAboveGround,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_below_ground import (
    GeometryGroupBelowGround,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_brace import (
    GeometryGroupBrace,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_span import (
    GeometryGroupSpan,
    CrackedExtentsParameterGroup,
    SplicesParameterGroup,
    ConstructionSequenceDetailsParameterGroup,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.shared_parameters.geometry_group_taper_details import (
    TaperedDetailsParameterGroup,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_girder import (
    GeometryGroupGirder,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_longitudinal_members import (
    GeometryGroupLongitudinalMembers,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_superstructure_to_substructure_connections import (
    GeometryGroupSuperstructureToSubstructureConnections,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_transverse_bracing import (
    GeometryGroupTransverseBracing,
)
from bda.contracts.paramodel.groups.enums import (
    DiaphragmTypeParaModel,
    SupportTypeParaModel,
    FoundationTypeParaModel,
    BracingTypeParaModel,
)
from bda.contracts.paramodel.groups.enums import SpacingTypeParaModel
from bda.contracts.paramodel.groups.enums import (
    BridgeIdealisationParaModel,
    BridgeTypeParaModel,
)


def test_groups_adapter_normalizes_nested_unit_bearing_lists():
    properties = {
        "Bearing Configuration Details": {
            "group_parameters": {
                "Bearing Spacing": {
                    "provided_value": [5.0, 2.0],
                    "provided_unit": "m",
                }
            }
        }
    }

    normalized = GroupsParaModelAdapter._normalize_unit_lists(properties)

    assert normalized["Bearing Configuration Details"]["group_parameters"][
        "Bearing Spacing"
    ]["provided_value"] == [
        {"value": 5.0, "unit": "m"},
        {"value": 2.0, "unit": "m"},
    ]


def test_lumped_foundation_speckle_dump_parses_through_adapter():
    contract = LumpedFoundationDataObject.create(
        name="Foundation",
        application_id="BC-FOUNDATION-LUMPED-0001",
        support_index=2,
        foundation_model_type=FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL,
        foundation_application_type=FoundationApplicationTypeEnumParaModel.BEARING_BASED,
        vertical_offset=0.25,
    )

    collection = FoundationBCCollection.create([contract])
    parsed = FoundationBCsParaModelAdapter.parse_list(
        collection.model_dump(mode="json", by_alias=True)
    )[0]

    assert parsed.support_index == 2
    assert parsed.application.application_type == FoundationApplicationTypeEnumParaModel.BEARING_BASED
    assert parsed.application.vertical_offset.value == 0.25


def test_pile_foundation_speckle_dump_parses_nested_springs():
    contract = PileInteractionFoundationDataObject.create(
        name="Pile foundation",
        application_id="BC-FOUNDATION-PILE-0001",
        support_index=3,
        foundation_model_type=FoundationModelTypeParaModel.PILE_INTERACTION_MODEL,
        pile_definitions=[
            PileDefinitionInput(
                pile_index=4,
                soil_profile_type=SoilProfileTypeEnumParaModel.UNIFORM,
                top_node_spring_definition={},
                bottom_node_spring_definition={},
            )
        ],
    )

    collection = FoundationBCCollection.create([contract])
    parsed = FoundationBCsParaModelAdapter.parse_list(
        collection.model_dump(mode="json", by_alias=True)
    )[0]

    assert parsed.support_index == 3
    assert parsed.pile_springs[0].pile_index == 4
    assert parsed.pile_springs[0].soil_profile_type == SoilProfileTypeEnumParaModel.UNIFORM


def test_bearing_collection_speckle_dump_parses_configuration_and_springs():
    bearing = BearingBCDataObject.create_user_defined(
        name="Bearing",
        application_id="BC-BEARING-0001",
        support_index=1,
        girder_index=2,
        bearing_index=0,
        configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
        orientation=ElementOrientationParaModel.ORTHOGONAL,
        sdx_value=100.0,
        sdy_value=110.0,
        sdz_value=120.0,
        srx_value=20.0,
        sry_value=21.0,
        srz_value=22.0,
    )
    contract = BearingBCCollection.create([bearing])

    parsed = BearingBCsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    girder = parsed.bearings_by_girder[0]
    assert parsed.support_index == 1
    assert girder.girder_index == 2
    assert girder.bearing_configuration_type == BearingConfigurationTypeParaModel.SINGULAR
    assert girder.bearing_definition.bearing_index == 0
    assert girder.bearing_definition.bearing_stiffness_definition.sdx.stiffness.value == 100.0


def test_multiple_bearing_speckle_dump_keeps_each_bearing_definition():
    def bearing_definition(index):
        return BearingBCDataObject.create_free(
            name=f"Bearing {index}",
            application_id=f"BC-BEARING-{index + 1:04d}",
            support_index=1,
            girder_index=0,
            bearing_index=index,
            configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
            orientation=ElementOrientationParaModel.SKEWED,
        ).properties.bearing_boundary_condition_parameters.group_parameters.spring_definitions.group_parameters[
            f"bearing-{index:04d}"
        ]

    contract = BearingBCCollection.create([
        BearingBCDataObject.create(
            name="Multiple bearings",
            application_id="BC-BEARING-0003",
            support_index=1,
            girder_index=0,
            bearing_index=0,
            configuration_type=BearingConfigurationTypeParaModel.MULTIPLE,
            orientation=ElementOrientationParaModel.ORTHOGONAL,
            spring_definitions={
                "bearing-0000": bearing_definition(0),
                "bearing-0001": bearing_definition(1),
            },
        )
    ])

    parsed = BearingBCsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    girder = parsed.bearings_by_girder[0]
    assert len(girder.bearing_definitions) == 2
    assert [item.bearing_index for item in girder.bearing_definitions] == [0, 1]


def test_geometry_group_speckle_dump_parses_bridge_properties():
    superstructure = GeometryGroupSuperstructure.create(
        total_deck_width=12.0,
        number_of_girders=3,
        girder_spacing_type=SpacingTypeParaModel.UNIFORM,
        girder_spacing_values=[4.0, 4.0],
        stringcourse_left_barrier_width=0.4,
        stringcourse_right_barrier_width=0.4,
        cantilever_left_width=1.0,
        cantilever_right_width=1.0,
    )
    contract = GeometryGroupBridge.create(
        bridge_type=BridgeTypeParaModel.STEEL_COMPOSITE,
        bridge_idealisation=BridgeIdealisationParaModel.GRILLAGE,
        number_of_spans=2,
        top_deck_level=5.0,
        girder_mesh_divisor=3,
        superstructure=superstructure,
    )

    parsed = GroupsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    assert parsed.group_id == contract.applicationId
    assert parsed.structural_component_type.value == "bridge"
    assert parsed.properties.no_of_spans == 2
    assert parsed.properties.analysis_settings.mesh_divisor == 3
    nested = parsed.nested_groups[0]
    assert nested.properties.no_of_girders == 3
    assert [q.value for q in nested.properties.girder_spacing_values] == [4.0, 4.0]


def test_diaphragm_discriminator_and_grouped_properties_parse_from_contract_dump():
    contract = GeometryGroupDiaphragm.create(
        material_id=None,
        section_id=None,
        support_index=0,
        diaphragm_type=DiaphragmTypeParaModel.CONCRETE_NON_MODELLED,
        diaphragm_thickness=0.2,
    )

    parsed = GroupsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    assert parsed.properties.support_index == 0
    assert parsed.properties.geometry_details.diaphragm_type == DiaphragmTypeParaModel.CONCRETE_NON_MODELLED
    assert parsed.properties.geometry_details.diaphragm_thickness.value == 0.2


def test_above_ground_support_discriminator_parses_from_contract_dump():
    contract = GeometryGroupAboveGround.create(
        support_type=SupportTypeParaModel.COLUMN_TYPE,
        number_of_piers=2,
    )

    parsed = GroupsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    assert parsed.properties.details.support_type == SupportTypeParaModel.COLUMN_TYPE
    assert parsed.properties.details.no_of_piers == 2


def test_below_ground_foundation_discriminator_parses_from_contract_dump():
    contract = GeometryGroupBelowGround.create(
        foundation_type=FoundationTypeParaModel.DEEP,
        number_of_piles=4,
    )

    parsed = GroupsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    assert parsed.properties.foundation_details.foundation_type == FoundationTypeParaModel.DEEP
    assert parsed.properties.foundation_details.no_of_piles == 4


def test_bracing_discriminator_and_geometry_values_parse_from_contract_dump():
    contract = GeometryGroupBrace.create(
        material_id="mat-1",
        section_id="sec-1",
        brace_type=BracingTypeParaModel.X_TYPE,
        vertical_offset_left_bottom=0.1,
        vertical_offset_left_top=0.2,
        vertical_offset_right_bottom=0.3,
        vertical_offset_right_top=0.4,
    )

    parsed = GroupsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    details = parsed.properties.geometry_details
    assert details.bracing_type == BracingTypeParaModel.X_TYPE
    assert details.vertical_offset_left_top.value == 0.2


def test_span_core_fields_parse_from_contract_dump():
    contract = GeometryGroupSpan.create(
        span_index=1,
        span_length=32.5,
        top_deck_level_at_end=4.0,
        cracked_extents=CrackedExtentsParameterGroup.create([(1.0, 3.0)]),
        tapered_details=TaperedDetailsParameterGroup.create([(0.0, 32.5, "sec-taper")]),
        splices=SplicesParameterGroup.create([(15.0, "sec-splice")]),
        construction_sequence_details=ConstructionSequenceDetailsParameterGroup.create(
            [(0.0, 10.0), (10.0, 32.5)],
            ElementOrientationParaModel.ORTHOGONAL,
        ),
    )

    parsed = GroupsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    assert parsed.properties.span_index == 1
    assert parsed.properties.span_length.value == 32.5
    assert parsed.properties.top_deck_level_at_end.value == 4.0
    assert parsed.properties.cracked_extents[0].x_end.value == 3.0
    assert parsed.properties.tapered_details[0].section_id == "sec-taper"
    assert parsed.properties.splices[0].section_id == "sec-splice"
    assert len(parsed.properties.construction_sequence_details.segments) == 2


def test_linkage_configuration_discriminator_parses_from_contract_dump():
    contract = GeometryGroupSuperstructureToSubstructureConnections.create(
        support_index=0,
        bearing_configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
    )

    parsed = GroupsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    assert parsed.properties.support_index == 0
    assert parsed.properties.bearing_configuration_details.bearing_configuration_type == BearingConfigurationTypeParaModel.SINGULAR
    assert parsed.properties.bearing_configuration_details.no_of_bearings == 1


def test_girder_identifiers_and_properties_parse_from_contract_dump():
    contract = GeometryGroupGirder.create(
        material_id="steel-1",
        section_id="girder-section-1",
        girder_index=3,
    )

    parsed = GroupsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    assert parsed.material_id == "steel-1"
    assert parsed.section_id == "girder-section-1"
    assert parsed.properties.girder_index == 3


def test_transverse_bracing_group_parameters_parse_from_contract_dump():
    contract = GeometryGroupTransverseBracing.create(
        bracing_orientation=ElementOrientationParaModel.ORTHOGONAL,
        x_start_first_bracing=1.0,
        spacing_type=SpacingTypeParaModel.UNIFORM,
        spacing_values=[2.0, 2.0],
        number_of_bracings=2,
        left_girder_index=0,
        right_girder_index=1,
        horizontal_offset_left_girder=0.2,
        horizontal_offset_right_girder=0.3,
    )

    parsed = GroupsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    assert parsed.properties.no_of_bracings == 2
    assert [spacing.value for spacing in parsed.properties.spacing_values] == [2.0, 2.0]
    assert parsed.properties.bracing_details.horizontal_offset_at_left.value == 0.2


def test_empty_properties_group_with_nested_girder_contract_parses():
    girder = GeometryGroupGirder.create(girder_index=2)
    contract = GeometryGroupLongitudinalMembers.create(girders=[girder])

    parsed = GroupsParaModelAdapter.parse_list(
        contract.model_dump(mode="json", by_alias=True)
    )[0]

    assert parsed.nested_groups[0].structural_component_type.value == "girder"
    assert parsed.nested_groups[0].properties.girder_index == 2


def test_speckle_provider_uses_geometry_paramodel_adapter(monkeypatch):
    superstructure = GeometryGroupSuperstructure.create(
        total_deck_width=12.0,
        number_of_girders=3,
        girder_spacing_type=SpacingTypeParaModel.UNIFORM,
        girder_spacing_values=[4.0, 4.0],
        stringcourse_left_barrier_width=0.4,
        stringcourse_right_barrier_width=0.4,
        cantilever_left_width=1.0,
        cantilever_right_width=1.0,
    )
    bridge = GeometryGroupBridge.create(
        bridge_type=BridgeTypeParaModel.STEEL_COMPOSITE,
        bridge_idealisation=BridgeIdealisationParaModel.GRILLAGE,
        number_of_spans=2,
        top_deck_level=5.0,
        girder_mesh_divisor=3,
        superstructure=superstructure,
    )

    class SilentLogger:
        @staticmethod
        def info(_message):
            pass

    monkeypatch.setattr(
        "bda.infrastructure.data_providers.data_speckle_provider.AppLogger",
        lambda: SilentLogger(),
    )
    provider = object.__new__(DataSpeckleProvider)
    provider.ModelDataValidated = type("Validated", (), {"elements": [bridge]})()
    provider.SpeckleModelUrl = "test-speckle-url"

    parsed = provider.get_geometry_groups_for_project()

    assert len(parsed) == 2
    assert parsed[0].properties.no_of_spans == 2
    assert parsed[1].properties.no_of_girders == 3


def test_speckle_provider_uses_foundation_and_bearing_adapters(monkeypatch):
    foundation = LumpedFoundationDataObject.create(
        name="Foundation",
        application_id="BC-FOUNDATION-LUMPED-0002",
        support_index=5,
        foundation_model_type=FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL,
        foundation_application_type=FoundationApplicationTypeEnumParaModel.SUBSTRUCTURE_ELEMENT_BASED,
    )
    foundation_collection = FoundationBCCollection.create([foundation])
    bearing = BearingBCDataObject.create_free(
        name="Bearing",
        application_id="BC-BEARING-0040",
        support_index=5,
        girder_index=1,
        bearing_index=0,
        configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
        orientation=ElementOrientationParaModel.ORTHOGONAL,
    )
    bearing_collection = BearingBCCollection.create([bearing])
    boundary_conditions = BoundaryConditionsCollection.create(
        bearing_conditions=bearing_collection,
        foundation_conditions=foundation_collection,
    )

    class SilentLogger:
        @staticmethod
        def info(_message):
            pass

    monkeypatch.setattr(
        "bda.infrastructure.data_providers.data_speckle_provider.AppLogger",
        lambda: SilentLogger(),
    )
    provider = object.__new__(DataSpeckleProvider)
    provider.ModelDataValidated = type(
        "Validated", (), {"elements": [boundary_conditions]}
    )()
    provider.SpeckleModelUrl = "test-speckle-url"

    foundations = provider.get_foundation_boundary_conditions_for_project()
    bearings = provider.get_bearing_boundary_conditions_for_project()

    assert foundations[0].support_index == 5
    assert bearings[0].support_index == 5
    assert bearings[0].bearings_by_girder[0].girder_index == 1


def test_speckle_provider_returns_empty_lists_for_missing_boundary_condition_type(monkeypatch):
    bearing = BearingBCDataObject.create_free(
        name="Bearing",
        application_id="BC-BEARING-0041",
        support_index=6,
        girder_index=0,
        bearing_index=0,
        configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
        orientation=ElementOrientationParaModel.ORTHOGONAL,
    )
    boundary_conditions = BoundaryConditionsCollection.create(
        bearing_conditions=BearingBCCollection.create([bearing])
    )

    class SilentLogger:
        @staticmethod
        def info(_message):
            pass

    monkeypatch.setattr(
        "bda.infrastructure.data_providers.data_speckle_provider.AppLogger",
        lambda: SilentLogger(),
    )
    provider = object.__new__(DataSpeckleProvider)
    provider.ModelDataValidated = type(
        "Validated", (), {"elements": [boundary_conditions]}
    )()
    provider.SpeckleModelUrl = "test-speckle-url"

    assert provider.get_foundation_boundary_conditions_for_project() == []
    assert len(provider.get_bearing_boundary_conditions_for_project()) == 1
