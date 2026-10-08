import pytest
from pydantic import ValidationError

from bda.contracts.paramodel.loadings.design.aashto.structural_loads import (
    StructuralInServiceDeadLoad,
)
from bda.contracts.paramodel.loadings.design.aashto.live_loads import (
    HL93ModelBrakingLoad,
    HL93ModelVerticalDirectLoad,
    PedestrianStandardLoad,
)
from bda.contracts.paramodel.loadings.design.aashto.environment_loads import (
    SettlementLoad,
)
from bda.contracts.paramodel.loadings.enums import (
    DeadLoadingMethodEnum,
    LoadApplicationDomainEnum,
    LoadContextEnum,
    LoadServiceStateEnum,
    MainCodeEnum,
    SecondaryCodeEnum,
)
from bda.contracts.speckle_contracts.base_objects import Parameter, ParameterGroup
from bda.contracts.speckle_contracts.bda_analytical.loading.loading_base import (
    AashtoLoadNatureParameter,
    AncillaryWorksCollection,
    InServiceLoadCollection,
    LoadContextParameter,
    LoadDataObjectProperties,
    LoadDomainParameter,
    LoadParameters,
    LoadServiceStateParameter,
    MainCodeParameter,
    SecondaryCodeParameter,
    StructureLoadsCollection,
    StructuralDeadLoadDataObject,
    HL93BrakingLoadDataObject,
    HL93VerticalDirectLoadDataObject,
    PedestrianLoadDataObject,
    SettlementLoadDataObject,
    LiveLoadsCollection,
    EnvironmentalLoadsCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.loading.loading_base import (
    LoadingCollection,
    LoadingCodeDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_DataObject import (
    BDA_ModelDataDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_enums import (
    DesignCodesEnum,
    ModelUnitSystemEnum,
    OutputSoftwareEnum,
    StructureTypeEnum,
)
from bda.contracts.speckle_contracts.bda_analytical.model_root import ModelRootCollection
from bda.contracts.paramodel.loadings.speckle_adapter import LoadingSpeckleAdapter
from bda.infrastructure.data_providers.data_speckle_provider import DataSpeckleProvider


def _parameter(name, value):
    return Parameter(name=name, isUser=True, provided_value=value)


def _structural_dead_load():
    parameters = LoadParameters(
        name="Load Parameters",
        isUser=True,
        group_parameters={
            "loading": ParameterGroup(
                name="Loading",
                isUser=True,
                group_parameters={
                    "method": _parameter(
                        "Method", DeadLoadingMethodEnum.DENSITY_ENHANCEMENT
                    ),
                    "enhancement_factor": _parameter("Enhancement Factor", 0.1),
                },
            ),
            "load_application": ParameterGroup(
                name="Load Application",
                isUser=True,
                group_parameters={
                    "application_type": _parameter(
                        "Application Type", "structural group id"
                    ),
                    "group_id": _parameter("Group ID", "GEOMGROUP-0001"),
                },
            ),
        },
    )
    return StructuralDeadLoadDataObject(
        applicationId="LOAD-STRUCTURAL-DEAD-0001",
        properties=LoadDataObjectProperties(
            **{
                "Load Context": LoadContextParameter(
                    isUser=True, provided_value=LoadContextEnum.DESIGN
                ),
                "Main Code": MainCodeParameter(
                    isUser=True, provided_value=MainCodeEnum.AASHTO
                ),
                "Secondary Code": SecondaryCodeParameter(
                    isUser=True, provided_value=SecondaryCodeEnum.UAE
                ),
                "Load Application Domain": LoadDomainParameter(
                    isUser=True,
                    provided_value=LoadApplicationDomainEnum.STRUCTURE,
                ),
                "Load Service State": LoadServiceStateParameter(
                    isUser=True, provided_value=LoadServiceStateEnum.IN_SERVICE
                ),
                "Load Nature": AashtoLoadNatureParameter(
                    isUser=True, provided_value="DC"
                ),
                "Load Parameters": parameters,
            }
        ),
    )


def test_loading_tree_validates_and_adapts_to_existing_paramodel(monkeypatch):
    load = _structural_dead_load()
    structure = StructureLoadsCollection(
        applicationId="COL-LOAD-STRUCTURE",
        elements=[
            InServiceLoadCollection(
                applicationId="COL-LOAD-STRUCTURE-IN-SERVICE",
                elements=[load],
            )
        ],
    )
    loading = LoadingCollection.create(
        code_configuration=LoadingCodeDataObject.create(),
        structure=structure,
    )
    config = BDA_ModelDataDataObject.create(
        model_unit_system=ModelUnitSystemEnum.METRIC,
        output_software=OutputSoftwareEnum.MIDAS_CIVIL,
        design_code=DesignCodesEnum.AASHTO,
        structure_type=StructureTypeEnum.STEEL_COMPOSITE,
    )

    root = ModelRootCollection.create(config, loading=loading)
    validated = ModelRootCollection.model_validate(
        root.model_dump(mode="json", by_alias=True)
    )
    loaded = next(item for item in validated.elements if isinstance(item, LoadingCollection))
    parsed = LoadingSpeckleAdapter.parse_list(loaded)

    assert len(parsed) == 1
    assert isinstance(parsed[0], StructuralInServiceDeadLoad)
    assert parsed[0].secondary_code == SecondaryCodeEnum.UAE
    assert parsed[0].loading.enhancement_factor == 0.1

    class SilentLogger:
        @staticmethod
        def info(_message):
            pass

    monkeypatch.setattr(
        "bda.infrastructure.data_providers.data_speckle_provider.AppLogger",
        lambda: SilentLogger(),
    )
    provider = object.__new__(DataSpeckleProvider)
    provider.ModelDataValidated = validated
    provider.SpeckleModelUrl = "test-speckle-url"
    assert len(provider.get_loads_for_project()) == 1


def test_domain_collection_rejects_load_object_from_another_domain():
    load = _structural_dead_load()
    with pytest.raises(ValidationError, match="wrong Ancillary Works"):
        AncillaryWorksCollection(
            applicationId="COL-LOAD-ANCILLARY-WORKS",
            elements=[
                InServiceLoadCollection(
                    applicationId="COL-LOAD-ANCILLARY-WORKS-IN-SERVICE",
                    elements=[load],
                )
            ],
        )


def _load_object(cls, application_id, domain, nature, parameters):
    return cls(
        applicationId=application_id,
        properties=LoadDataObjectProperties(
            **{
                "Load Context": LoadContextParameter(
                    isUser=True, provided_value=LoadContextEnum.DESIGN
                ),
                "Main Code": MainCodeParameter(
                    isUser=True, provided_value=MainCodeEnum.AASHTO
                ),
                "Secondary Code": SecondaryCodeParameter(
                    isUser=True, provided_value=SecondaryCodeEnum.UAE
                ),
                "Load Application Domain": LoadDomainParameter(
                    isUser=True, provided_value=domain
                ),
                "Load Service State": LoadServiceStateParameter(
                    isUser=True, provided_value=LoadServiceStateEnum.IN_SERVICE
                ),
                "Load Nature": AashtoLoadNatureParameter(
                    isUser=True, provided_value=nature
                ),
                "Load Parameters": LoadParameters(
                    name="Load Parameters",
                    isUser=True,
                    group_parameters={
                        key: _parameter(key, value)
                        for key, value in parameters.items()
                    },
                ),
            }
        ),
    )


def test_traffic_and_settlement_contracts_validate_against_existing_paramodels():
    from bda.contracts.paramodel.loadings.design.aashto.enums import (
        AashtoLoadNatureEnum,
    )
    from bda.contracts.paramodel.loadings.enums import (
        LoadApplicationDomainEnum,
    )

    traffic_types = [
        (
            HL93VerticalDirectLoadDataObject,
            HL93ModelVerticalDirectLoad,
            "LL",
            {
                "primary_traffic_type": "road",
                "vehicle_def_type": "standard",
                "traffic_load_model": "HL-93",
                "traffic_load_type": "vertical traffic direct",
                "include_truck_model": True,
                "include_tandem_model": True,
                "include_fatigue_model": False,
                "lane_parameters": {"lane_definition_type": "standard"},
            },
        ),
        (
            HL93BrakingLoadDataObject,
            HL93ModelBrakingLoad,
            "BR",
            {
                "primary_traffic_type": "road",
                "vehicle_def_type": "standard",
                "traffic_load_model": "HL-93",
                "traffic_load_type": "braking",
                "max_traffic_lanes_in_one_direction": 2,
            },
        ),
        (
            PedestrianLoadDataObject,
            PedestrianStandardLoad,
            "PL",
            {
                "primary_traffic_type": "road",
                "vehicle_def_type": "standard",
                "traffic_load_model": "Pedestrian",
            },
        ),
    ]
    traffic_contracts = []
    expected_models = []
    for index, (speckle_cls, paramodel_cls, nature, values) in enumerate(traffic_types):
        contract = _load_object(
            speckle_cls,
            f"LOAD-TRAFFIC-{index:04d}",
            LoadApplicationDomainEnum.LIVE_LOAD,
            AashtoLoadNatureEnum(nature),
            values,
        )
        traffic_contracts.append(contract)
        expected_models.append(paramodel_cls)

    settlement = _load_object(
        SettlementLoadDataObject,
        "LOAD-SETTLEMENT-0001",
        LoadApplicationDomainEnum.ENVIRONMENT,
        AashtoLoadNatureEnum.SE,
        {
            "env_load_type": "settlement",
            "diff_settlement_value": {"value": 0.05, "unit": "m"},
        },
    )
    live = LiveLoadsCollection(
        applicationId="COL-LOAD-LIVE-LOADS",
        elements=[
            InServiceLoadCollection(
                applicationId="COL-LOAD-LIVE-IN-SERVICE",
                elements=traffic_contracts,
            )
        ],
    )
    environment = EnvironmentalLoadsCollection(
        applicationId="COL-LOAD-ENVIRONMENTAL-LOADS",
        elements=[
            InServiceLoadCollection(
                applicationId="COL-LOAD-ENV-IN-SERVICE",
                elements=[settlement],
            )
        ],
    )
    hierarchy = LoadingCollection.create(
        code_configuration=LoadingCodeDataObject.create(),
        live_loads=live,
        environmental_loads=environment,
    )
    parsed = LoadingSpeckleAdapter.parse_list(hierarchy)
    assert [type(item) for item in parsed] == [*expected_models, SettlementLoad]


def test_lifecycle_collections_can_be_subset_of_standard_states():
    # Live Loads currently have only In Service; construction and temporary
    # states remain legal options on the other domain collections.
    collection = LiveLoadsCollection(
        applicationId="COL-LOAD-LIVE-LOADS",
        elements=[
            InServiceLoadCollection(
                applicationId="COL-LOAD-LIVE-IN-SERVICE", elements=[]
            )
        ],
    )
    assert len(collection.elements) == 1
