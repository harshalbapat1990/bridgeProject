from bda.contracts.paramodel.deck_appurtenances import (
    DeckLayoutSpeckleAdapter,
    SingleCarriagewayBridgeDeckLayoutParaModel,
)
from bda.contracts.paramodel.deck_appurtenances.enums import (
    BridgeDeckLayoutTypeParaModel,
    DeckAppurtenanceTypeParaModel,
)
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layout_collection import (
    DeckLayoutCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_layout_types.deck_appurtenances import (
    Carriageway,
    EdgeBarrier,
)
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_layout_types.deck_layout_single_carriageway import (
    SingleCarriagewayDeckLayoutCollection,
    SingleCarriagewayStandardAppurtenances,
)
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_layout_base import (
    DeckLayoutPropertiesBase,
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
from bda.infrastructure.data_providers.data_speckle_provider import DataSpeckleProvider


def _example_collection():
    left_barrier = EdgeBarrier.create(
        name="EdgeBarrier 1",
        application_id="DA-LF-0001",
        appurtenance_id="barrier-left",
        element_index=0,
        appurtenance_type=DeckAppurtenanceTypeParaModel.CONCRETE_BARRIER,
        material_id="mat-concrete",
        width=0.5,
        height=1.0,
        outline=[0.0, 0.0, 0.5, 1.0],
    )
    right_barrier = EdgeBarrier.create(
        name="EdgeBarrier 2",
        application_id="DA-LF-0002",
        appurtenance_id="barrier-right",
        element_index=2,
        appurtenance_type=DeckAppurtenanceTypeParaModel.CONCRETE_BARRIER,
        material_id="mat-concrete",
        width=0.5,
        height=1.0,
        outline=[0.0, 0.0, 0.5, 1.0],
    )
    carriageway = Carriageway.create(
        name="Carriageway 1",
        application_id="DA-SF-0001",
        appurtenance_id="carriageway",
        element_index=1,
        appurtenance_type=DeckAppurtenanceTypeParaModel.SURFACING,
        material_id="mat-asphalt",
        width=7.0,
        thickness_left=0.1,
        thickness_right=0.1,
    )
    standard = SingleCarriagewayStandardAppurtenances.create(
        application_id="STD-DECK-LAYOUT-0001-SINGLE-CARRIAGEWAY",
        edge_barrier_1=left_barrier,
        carriageway_1=carriageway,
        edge_barrier_2=right_barrier,
    )
    layout = SingleCarriagewayDeckLayoutCollection.create(
        application_id="COL-DECK-LAYOUT-0001-SINGLE-CARRIAGEWAY",
        properties=DeckLayoutPropertiesBase.create(
            application_id="PROP-DECK-LAYOUT-0001-SINGLE-CARRIAGEWAY",
            deck_layout_type=BridgeDeckLayoutTypeParaModel.SINGLE_CARRIAGEWAY,
            layout_index=0,
            start_x_point=12.5,
        ),
        standard_appurtenances=standard,
    )
    return DeckLayoutCollection.create([layout])


def test_deck_layout_collection_round_trips_through_root_and_adapter():
    collection = _example_collection()
    config = BDA_ModelDataDataObject.create(
        model_unit_system=ModelUnitSystemEnum.METRIC,
        output_software=OutputSoftwareEnum.MIDAS_CIVIL,
        design_code=DesignCodesEnum.AASHTO,
        structure_type=StructureTypeEnum.STEEL_COMPOSITE,
    )

    root = ModelRootCollection.create(config, deck_layouts=collection)
    validated = ModelRootCollection.model_validate(
        root.model_dump(mode="json", by_alias=True)
    )
    parsed = DeckLayoutSpeckleAdapter.parse_list(validated.elements[1])

    assert len(parsed) == 1
    assert isinstance(parsed[0], SingleCarriagewayBridgeDeckLayoutParaModel)
    assert parsed[0].start_x_point.value == 12.5
    assert parsed[0].edge_barrier_1.appurtenance_id == "barrier-left"
    assert parsed[0].carriageway_1.width.value == 7.0


def test_speckle_provider_extracts_deck_layouts(monkeypatch):
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
        "Validated", (), {"elements": [_example_collection()]}
    )()
    provider.SpeckleModelUrl = "test-speckle-url"

    layouts = provider.get_deck_appurtenances_for_project()

    assert len(layouts) == 1
    assert layouts[0].layout_index == 0
