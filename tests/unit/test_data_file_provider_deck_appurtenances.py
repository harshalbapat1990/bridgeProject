import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from pydantic import ValidationError

from bda.contracts.paramodel.deck_appurtenances import (
    BridgeDeckLayoutBaseParaModel,
    BridgeDeckLayoutTypeParaModel,
    DeckAppurtenanceTypeParaModel,
    DualCarriagewayBridgeDeckLayoutParaModel,
    GeometryTypeParaModel,
    LinearByOffsetDeckAppurtenanceParaModel,
    LinearFixedDeckAppurtenanceParaModel,
    PositionDefEnumParaModel,
    SingleCarriagewayBridgeDeckLayoutParaModel,
    SurfaceByOffsetDeckAppurtenanceParaModel,
    SurfaceFixedDeckAppurtenanceParaModel,
)
from bda.contracts.shared import QuantityParaModel
from bda.infrastructure.data_providers.data_file_provider import DataFileProvider


def assert_quantity(q: QuantityParaModel, value: float, unit: str) -> None:
    assert isinstance(q, QuantityParaModel)
    assert q.value == pytest.approx(value)
    assert q.unit == unit


class TestDataFileProvider_DeckAppurtenances:
    """Unit tests for DataFileProvider.get_deck_appurtenances_for_project."""

    @pytest.fixture
    def fixtures_path(self) -> Path:
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def provider(self, fixtures_path: Path) -> DataFileProvider:
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture
    def layouts(self, provider: DataFileProvider):
        return provider.get_deck_appurtenances_for_project()

    @pytest.fixture
    def single_carriageway(self, layouts):
        return layouts[0]

    @pytest.fixture
    def dual_carriageway(self, layouts):
        return layouts[1]

    # ------------------------------------------------------------------
    # Fixture existence
    # ------------------------------------------------------------------

    def test_deck_appurtenances_json_exists(self, fixtures_path: Path):
        assert (fixtures_path / "deck_appurtenances.json").exists()

    # ------------------------------------------------------------------
    # Collection shape
    # ------------------------------------------------------------------

    def test_returns_list(self, layouts):
        assert isinstance(layouts, list)

    def test_returns_two_layouts(self, layouts):
        assert len(layouts) == 2

    def test_all_items_are_bridge_deck_layout_base(self, layouts):
        assert all(isinstance(item, BridgeDeckLayoutBaseParaModel) for item in layouts)

    def test_first_layout_is_single_carriageway(self, single_carriageway):
        assert isinstance(single_carriageway, SingleCarriagewayBridgeDeckLayoutParaModel)

    def test_second_layout_is_dual_carriageway(self, dual_carriageway):
        assert isinstance(dual_carriageway, DualCarriagewayBridgeDeckLayoutParaModel)

    # ------------------------------------------------------------------
    # Single carriageway — layout-level fields
    # ------------------------------------------------------------------

    def test_single_layout_name(self, single_carriageway):
        assert single_carriageway.name == "Single Carriageway Layout"

    def test_single_layout_index(self, single_carriageway):
        assert single_carriageway.layout_index == 0

    def test_single_layout_type_enum(self, single_carriageway):
        assert single_carriageway.deck_layout_type == BridgeDeckLayoutTypeParaModel.SINGLE_CARRIAGEWAY

    def test_single_start_x_point(self, single_carriageway):
        assert_quantity(single_carriageway.start_x_point, 0.0, "m")

    def test_single_miscellaneous_count(self, single_carriageway):
        assert len(single_carriageway.miscellaneous_items) == 2

    # ------------------------------------------------------------------
    # Single carriageway — edge_barrier_1 (LinearFixed)
    # ------------------------------------------------------------------

    def test_single_edge_barrier_1_type(self, single_carriageway):
        assert isinstance(single_carriageway.edge_barrier_1, LinearFixedDeckAppurtenanceParaModel)

    def test_single_edge_barrier_1_positioned_by(self, single_carriageway):
        assert single_carriageway.edge_barrier_1.positioned_by == PositionDefEnumParaModel.FIXED

    def test_single_edge_barrier_1_geometry_type(self, single_carriageway):
        assert single_carriageway.edge_barrier_1.geometry_type == GeometryTypeParaModel.LINEAR

    def test_single_edge_barrier_1_appurtenance_type(self, single_carriageway):
        assert single_carriageway.edge_barrier_1.appurtenance_type == DeckAppurtenanceTypeParaModel.CONCRETE_BARRIER

    def test_single_edge_barrier_1_id(self, single_carriageway):
        assert single_carriageway.edge_barrier_1.appurtenance_id == "eb1-sc"

    def test_single_edge_barrier_1_width(self, single_carriageway):
        assert_quantity(single_carriageway.edge_barrier_1.width, 0.50, "m")

    def test_single_edge_barrier_1_height(self, single_carriageway):
        assert_quantity(single_carriageway.edge_barrier_1.height, 1.20, "m")

    def test_single_edge_barrier_1_element_index(self, single_carriageway):
        assert single_carriageway.edge_barrier_1.element_index == 0

    # ------------------------------------------------------------------
    # Single carriageway — verge_footway_1 (SurfaceFixed)
    # ------------------------------------------------------------------

    def test_single_verge_footway_1_not_none(self, single_carriageway):
        assert single_carriageway.verge_footway_1 is not None

    def test_single_verge_footway_1_type(self, single_carriageway):
        assert isinstance(single_carriageway.verge_footway_1, SurfaceFixedDeckAppurtenanceParaModel)

    def test_single_verge_footway_1_positioned_by(self, single_carriageway):
        assert single_carriageway.verge_footway_1.positioned_by == PositionDefEnumParaModel.FIXED

    def test_single_verge_footway_1_geometry_type(self, single_carriageway):
        assert single_carriageway.verge_footway_1.geometry_type == GeometryTypeParaModel.SURFACE

    def test_single_verge_footway_1_appurtenance_type(self, single_carriageway):
        assert single_carriageway.verge_footway_1.appurtenance_type == DeckAppurtenanceTypeParaModel.RAISED_VERGE_FOOTWAY

    def test_single_verge_footway_1_thickness_left(self, single_carriageway):
        assert_quantity(single_carriageway.verge_footway_1.thickness_left, 0.25, "m")

    def test_single_verge_footway_1_thickness_right(self, single_carriageway):
        assert_quantity(single_carriageway.verge_footway_1.thickness_right, 0.20, "m")

    # ------------------------------------------------------------------
    # Single carriageway — carriageway_1 (SurfaceFixed)
    # ------------------------------------------------------------------

    def test_single_carriageway_1_type(self, single_carriageway):
        assert isinstance(single_carriageway.carriageway_1, SurfaceFixedDeckAppurtenanceParaModel)

    def test_single_carriageway_1_appurtenance_type(self, single_carriageway):
        assert single_carriageway.carriageway_1.appurtenance_type == DeckAppurtenanceTypeParaModel.SURFACING

    def test_single_carriageway_1_thickness(self, single_carriageway):
        assert_quantity(single_carriageway.carriageway_1.thickness_left, 0.08, "m")
        assert_quantity(single_carriageway.carriageway_1.thickness_right, 0.08, "m")

    # ------------------------------------------------------------------
    # Single carriageway — verge_footway_2 (SurfaceFixed)
    # ------------------------------------------------------------------

    def test_single_verge_footway_2_not_none(self, single_carriageway):
        assert single_carriageway.verge_footway_2 is not None

    def test_single_verge_footway_2_type(self, single_carriageway):
        assert isinstance(single_carriageway.verge_footway_2, SurfaceFixedDeckAppurtenanceParaModel)

    def test_single_verge_footway_2_thickness_left(self, single_carriageway):
        assert_quantity(single_carriageway.verge_footway_2.thickness_left, 0.20, "m")

    def test_single_verge_footway_2_thickness_right(self, single_carriageway):
        assert_quantity(single_carriageway.verge_footway_2.thickness_right, 0.25, "m")

    # ------------------------------------------------------------------
    # Single carriageway — edge_barrier_2 (LinearFixed)
    # ------------------------------------------------------------------

    def test_single_edge_barrier_2_type(self, single_carriageway):
        assert isinstance(single_carriageway.edge_barrier_2, LinearFixedDeckAppurtenanceParaModel)

    def test_single_edge_barrier_2_id(self, single_carriageway):
        assert single_carriageway.edge_barrier_2.appurtenance_id == "eb2-sc"

    def test_single_edge_barrier_2_element_index(self, single_carriageway):
        assert single_carriageway.edge_barrier_2.element_index == 4

    # ------------------------------------------------------------------
    # Single carriageway — miscellaneous_items
    # ------------------------------------------------------------------

    def test_single_misc_item_0_is_linear_by_offset(self, single_carriageway):
        assert isinstance(single_carriageway.miscellaneous_items[0], LinearByOffsetDeckAppurtenanceParaModel)

    def test_single_misc_item_0_positioned_by(self, single_carriageway):
        assert single_carriageway.miscellaneous_items[0].positioned_by == PositionDefEnumParaModel.BY_OFFSET

    def test_single_misc_item_0_geometry_type(self, single_carriageway):
        assert single_carriageway.miscellaneous_items[0].geometry_type == GeometryTypeParaModel.LINEAR

    def test_single_misc_item_0_appurtenance_type(self, single_carriageway):
        assert single_carriageway.miscellaneous_items[0].appurtenance_type == DeckAppurtenanceTypeParaModel.METAL_RAILING

    def test_single_misc_item_0_offset(self, single_carriageway):
        assert_quantity(single_carriageway.miscellaneous_items[0].offset, -4.50, "m")

    def test_single_misc_item_0_width(self, single_carriageway):
        assert_quantity(single_carriageway.miscellaneous_items[0].width, 0.15, "m")

    def test_single_misc_item_1_is_surface_by_offset(self, single_carriageway):
        assert isinstance(single_carriageway.miscellaneous_items[1], SurfaceByOffsetDeckAppurtenanceParaModel)

    def test_single_misc_item_1_positioned_by(self, single_carriageway):
        assert single_carriageway.miscellaneous_items[1].positioned_by == PositionDefEnumParaModel.BY_OFFSET

    def test_single_misc_item_1_geometry_type(self, single_carriageway):
        assert single_carriageway.miscellaneous_items[1].geometry_type == GeometryTypeParaModel.SURFACE

    def test_single_misc_item_1_appurtenance_type(self, single_carriageway):
        assert single_carriageway.miscellaneous_items[1].appurtenance_type == DeckAppurtenanceTypeParaModel.PERMANENT_FORMWORK

    def test_single_misc_item_1_offset(self, single_carriageway):
        assert_quantity(single_carriageway.miscellaneous_items[1].offset, -3.00, "m")

    def test_single_misc_item_1_thickness(self, single_carriageway):
        assert_quantity(single_carriageway.miscellaneous_items[1].thickness_left, 0.06, "m")
        assert_quantity(single_carriageway.miscellaneous_items[1].thickness_right, 0.06, "m")

    # ------------------------------------------------------------------
    # Dual carriageway — layout-level fields
    # ------------------------------------------------------------------

    def test_dual_layout_name(self, dual_carriageway):
        assert dual_carriageway.name == "Dual Carriageway Layout"

    def test_dual_layout_index(self, dual_carriageway):
        assert dual_carriageway.layout_index == 1

    def test_dual_layout_type_enum(self, dual_carriageway):
        assert dual_carriageway.deck_layout_type == BridgeDeckLayoutTypeParaModel.DUAL_CARRIAGEWAY

    def test_dual_start_x_point(self, dual_carriageway):
        assert_quantity(dual_carriageway.start_x_point, 25.0, "m")

    def test_dual_miscellaneous_count(self, dual_carriageway):
        assert len(dual_carriageway.miscellaneous_items) == 2

    # ------------------------------------------------------------------
    # Dual carriageway — edge_barrier_1 (LinearFixed, METAL RAILING)
    # ------------------------------------------------------------------

    def test_dual_edge_barrier_1_type(self, dual_carriageway):
        assert isinstance(dual_carriageway.edge_barrier_1, LinearFixedDeckAppurtenanceParaModel)

    def test_dual_edge_barrier_1_appurtenance_type(self, dual_carriageway):
        assert dual_carriageway.edge_barrier_1.appurtenance_type == DeckAppurtenanceTypeParaModel.METAL_RAILING

    def test_dual_edge_barrier_1_width(self, dual_carriageway):
        assert_quantity(dual_carriageway.edge_barrier_1.width, 0.12, "m")

    def test_dual_edge_barrier_1_height(self, dual_carriageway):
        assert_quantity(dual_carriageway.edge_barrier_1.height, 1.10, "m")

    # ------------------------------------------------------------------
    # Dual carriageway — verge_footway_1 (SurfaceFixed, optional present)
    # ------------------------------------------------------------------

    def test_dual_verge_footway_1_not_none(self, dual_carriageway):
        assert dual_carriageway.verge_footway_1 is not None

    def test_dual_verge_footway_1_type(self, dual_carriageway):
        assert isinstance(dual_carriageway.verge_footway_1, SurfaceFixedDeckAppurtenanceParaModel)

    def test_dual_verge_footway_1_appurtenance_type(self, dual_carriageway):
        assert dual_carriageway.verge_footway_1.appurtenance_type == DeckAppurtenanceTypeParaModel.RAISED_VERGE_FOOTWAY

    def test_dual_verge_footway_1_thickness_left(self, dual_carriageway):
        assert_quantity(dual_carriageway.verge_footway_1.thickness_left, 0.30, "m")

    # ------------------------------------------------------------------
    # Dual carriageway — carriageway_1 (SurfaceFixed)
    # ------------------------------------------------------------------

    def test_dual_carriageway_1_type(self, dual_carriageway):
        assert isinstance(dual_carriageway.carriageway_1, SurfaceFixedDeckAppurtenanceParaModel)

    def test_dual_carriageway_1_appurtenance_type(self, dual_carriageway):
        assert dual_carriageway.carriageway_1.appurtenance_type == DeckAppurtenanceTypeParaModel.SURFACING

    def test_dual_carriageway_1_thickness(self, dual_carriageway):
        assert_quantity(dual_carriageway.carriageway_1.thickness_left, 0.10, "m")

    # ------------------------------------------------------------------
    # Dual carriageway — central_reserve (SurfaceFixed, optional present)
    # ------------------------------------------------------------------

    def test_dual_central_reserve_not_none(self, dual_carriageway):
        assert dual_carriageway.central_reserve is not None

    def test_dual_central_reserve_type(self, dual_carriageway):
        assert isinstance(dual_carriageway.central_reserve, SurfaceFixedDeckAppurtenanceParaModel)

    def test_dual_central_reserve_appurtenance_type(self, dual_carriageway):
        assert dual_carriageway.central_reserve.appurtenance_type == DeckAppurtenanceTypeParaModel.RAISED_CENTRAL_RESERVE

    def test_dual_central_reserve_thickness(self, dual_carriageway):
        assert_quantity(dual_carriageway.central_reserve.thickness_left, 0.35, "m")
        assert_quantity(dual_carriageway.central_reserve.thickness_right, 0.35, "m")

    # ------------------------------------------------------------------
    # Dual carriageway — carriageway_2 (SurfaceFixed)
    # ------------------------------------------------------------------

    def test_dual_carriageway_2_type(self, dual_carriageway):
        assert isinstance(dual_carriageway.carriageway_2, SurfaceFixedDeckAppurtenanceParaModel)

    def test_dual_carriageway_2_id(self, dual_carriageway):
        assert dual_carriageway.carriageway_2.appurtenance_id == "cw2-dc"

    # ------------------------------------------------------------------
    # Dual carriageway — verge_footway_2 (SurfaceFixed)
    # ------------------------------------------------------------------

    def test_dual_verge_footway_2_not_none(self, dual_carriageway):
        assert dual_carriageway.verge_footway_2 is not None

    def test_dual_verge_footway_2_thickness_right(self, dual_carriageway):
        assert_quantity(dual_carriageway.verge_footway_2.thickness_right, 0.30, "m")

    # ------------------------------------------------------------------
    # Dual carriageway — edge_barrier_2 (LinearFixed)
    # ------------------------------------------------------------------

    def test_dual_edge_barrier_2_type(self, dual_carriageway):
        assert isinstance(dual_carriageway.edge_barrier_2, LinearFixedDeckAppurtenanceParaModel)

    def test_dual_edge_barrier_2_id(self, dual_carriageway):
        assert dual_carriageway.edge_barrier_2.appurtenance_id == "eb2-dc"

    # ------------------------------------------------------------------
    # Dual carriageway — miscellaneous_items
    # ------------------------------------------------------------------

    def test_dual_misc_item_0_is_linear_by_offset(self, dual_carriageway):
        assert isinstance(dual_carriageway.miscellaneous_items[0], LinearByOffsetDeckAppurtenanceParaModel)

    def test_dual_misc_item_0_appurtenance_type(self, dual_carriageway):
        assert dual_carriageway.miscellaneous_items[0].appurtenance_type == DeckAppurtenanceTypeParaModel.CONCRETE_BARRIER

    def test_dual_misc_item_0_offset(self, dual_carriageway):
        assert_quantity(dual_carriageway.miscellaneous_items[0].offset, 0.30, "m")

    def test_dual_misc_item_1_is_surface_by_offset(self, dual_carriageway):
        assert isinstance(dual_carriageway.miscellaneous_items[1], SurfaceByOffsetDeckAppurtenanceParaModel)

    def test_dual_misc_item_1_appurtenance_type(self, dual_carriageway):
        assert dual_carriageway.miscellaneous_items[1].appurtenance_type == DeckAppurtenanceTypeParaModel.PERMANENT_FORMWORK

    def test_dual_misc_item_1_offset(self, dual_carriageway):
        assert_quantity(dual_carriageway.miscellaneous_items[1].offset, 5.50, "m")

    def test_dual_misc_item_1_thickness(self, dual_carriageway):
        assert_quantity(dual_carriageway.miscellaneous_items[1].thickness_left, 0.07, "m")

    # ------------------------------------------------------------------
    # Optional fields — absent verge_footway means None
    # ------------------------------------------------------------------

    def test_optional_verge_footway_absent_returns_none(self):
        payload = json.dumps({
            "deck_appurtenances": [
                {
                    "deck_layout_type": "single-carriageway",
                    "name": "Minimal SC",
                    "layout_index": 0,
                    "start_x_point": {"value": 0.0, "unit": "m"},
                    "edge_barrier_1": {
                        "appurtenance_id": "eb1", "name": "EB1", "element_index": 0,
                        "appurtenance_type": "CONCRETE BARRIER", "material_id": "m1",
                        "positioned_by": "fixed", "geometry_type": "linear",
                        "width": {"value": 0.5, "unit": "m"}, "height": {"value": 1.2, "unit": "m"}
                    },
                    "carriageway_1": {
                        "appurtenance_id": "cw1", "name": "CW1", "element_index": 1,
                        "appurtenance_type": "SURFACING", "material_id": "m2",
                        "positioned_by": "fixed", "geometry_type": "surface",
                        "width": { "value": 0.50, "unit": "m" },
                        "thickness_left": {"value": 0.08, "unit": "m"},
                        "thickness_right": {"value": 0.08, "unit": "m"}
                    },
                    "edge_barrier_2": {
                        "appurtenance_id": "eb2", "name": "EB2", "element_index": 2,
                        "appurtenance_type": "CONCRETE BARRIER", "material_id": "m1",
                        "positioned_by": "fixed", "geometry_type": "linear",
                        "width": {"value": 0.5, "unit": "m"}, "height": {"value": 1.2, "unit": "m"}
                    }
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=payload)):
            result = DataFileProvider(folder=".").get_deck_appurtenances_for_project()
        layout = result[0]
        assert layout.verge_footway_1 is None
        assert layout.verge_footway_2 is None

    def test_optional_central_reserve_absent_returns_none(self):
        payload = json.dumps({
            "deck_appurtenances": [
                {
                    "deck_layout_type": "dual-carriageway",
                    "name": "Minimal DC",
                    "layout_index": 0,
                    "start_x_point": {"value": 0.0, "unit": "m"},
                    "edge_barrier_1": {
                        "appurtenance_id": "eb1", "name": "EB1", "element_index": 0,
                        "appurtenance_type": "METAL RAILING", "material_id": "m1",
                        "positioned_by": "fixed", "geometry_type": "linear",
                        "width": {"value": 0.1, "unit": "m"}, "height": {"value": 1.0, "unit": "m"}
                    },
                    "carriageway_1": {
                        "appurtenance_id": "cw1", "name": "CW1", "element_index": 1,
                        "appurtenance_type": "SURFACING", "material_id": "m2",
                        "positioned_by": "fixed", "geometry_type": "surface",
                        "width": { "value": 5.50, "unit": "m" },
                        "thickness_left": {"value": 0.1, "unit": "m"},
                        "thickness_right": {"value": 0.1, "unit": "m"}
                    },
                    "carriageway_2": {
                        "appurtenance_id": "cw2", "name": "CW2", "element_index": 2,
                        "appurtenance_type": "SURFACING", "material_id": "m2",
                        "positioned_by": "fixed", "geometry_type": "surface",
                        "width": { "value": 7.50, "unit": "m" },
                        "thickness_left": {"value": 0.1, "unit": "m"},
                        "thickness_right": {"value": 0.1, "unit": "m"}
                    },
                    "edge_barrier_2": {
                        "appurtenance_id": "eb2", "name": "EB2", "element_index": 3,
                        "appurtenance_type": "METAL RAILING", "material_id": "m1",
                        "positioned_by": "fixed", "geometry_type": "linear",
                        "width": {"value": 0.1, "unit": "m"}, "height": {"value": 1.0, "unit": "m"}
                    }
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=payload)):
            result = DataFileProvider(folder=".").get_deck_appurtenances_for_project()
        assert result[0].central_reserve is None

    # ------------------------------------------------------------------
    # Error handling / negative tests
    # ------------------------------------------------------------------

    def test_file_not_found(self):
        provider = DataFileProvider(folder="/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            provider.get_deck_appurtenances_for_project()

    def test_invalid_json_raises_decode_error(self):
        with patch("builtins.open", mock_open(read_data="{ invalid json }")):
            with pytest.raises(json.JSONDecodeError):
                DataFileProvider(folder=".").get_deck_appurtenances_for_project()

    def test_none_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder=None).get_deck_appurtenances_for_project()

    def test_empty_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder="").get_deck_appurtenances_for_project()

    def test_missing_key_returns_empty_list(self):
        with patch("builtins.open", mock_open(read_data=json.dumps({"other_key": []}))):
            result = DataFileProvider(folder=".").get_deck_appurtenances_for_project()
            assert result == []

    def test_unknown_deck_layout_type_raises_value_error(self):
        bad = json.dumps({
            "deck_appurtenances": [
                {
                    "deck_layout_type": "triple-carriageway",
                    "layout_index": 0,
                    "start_x_point": {"value": 0.0, "unit": "m"}
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValueError):
                DataFileProvider(folder=".").get_deck_appurtenances_for_project()

    def test_unknown_positioned_by_in_appurtenance_raises_validation_error(self):
        bad = json.dumps({
            "deck_appurtenances": [
                {
                    "deck_layout_type": "single-carriageway",
                    "name": "Bad Layout",
                    "layout_index": 0,
                    "start_x_point": {"value": 0.0, "unit": "m"},
                    "edge_barrier_1": {
                        "appurtenance_id": "eb1", "name": "EB1", "element_index": 0,
                        "appurtenance_type": "CONCRETE BARRIER", "material_id": "m1",
                        "positioned_by": "floating",
                        "geometry_type": "linear",
                        "width": {"value": 0.5, "unit": "m"}, "height": {"value": 1.2, "unit": "m"}
                    },
                    "carriageway_1": {
                        "appurtenance_id": "cw1", "name": "CW1", "element_index": 1,
                        "appurtenance_type": "SURFACING", "material_id": "m2",
                        "positioned_by": "fixed", "geometry_type": "surface",
                        "thickness_left": {"value": 0.08, "unit": "m"},
                        "thickness_right": {"value": 0.08, "unit": "m"},
                        "width": { "value": 5.50, "unit": "m" }
                    },
                    "edge_barrier_2": {
                        "appurtenance_id": "eb2", "name": "EB2", "element_index": 2,
                        "appurtenance_type": "CONCRETE BARRIER", "material_id": "m1",
                        "positioned_by": "fixed", "geometry_type": "linear",
                        "width": {"value": 0.5, "unit": "m"}, "height": {"value": 1.2, "unit": "m"}
                    }
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_deck_appurtenances_for_project()

    def test_unknown_geometry_type_raises_validation_error(self):
        bad = json.dumps({
            "deck_appurtenances": [
                {
                    "deck_layout_type": "single-carriageway",
                    "name": "Bad Layout",
                    "layout_index": 0,
                    "start_x_point": {"value": 0.0, "unit": "m"},
                    "edge_barrier_1": {
                        "appurtenance_id": "eb1", "name": "EB1", "element_index": 0,
                        "appurtenance_type": "CONCRETE BARRIER", "material_id": "m1",
                        "positioned_by": "fixed", "geometry_type": "volumetric",
                        "width": {"value": 0.5, "unit": "m"}, "height": {"value": 1.2, "unit": "m"}
                    },
                    "carriageway_1": {
                        "appurtenance_id": "cw1", "name": "CW1", "element_index": 1,
                        "appurtenance_type": "SURFACING", "material_id": "m2",
                        "positioned_by": "fixed", "geometry_type": "surface",
                        "thickness_left": {"value": 0.08, "unit": "m"},
                        "thickness_right": {"value": 0.08, "unit": "m"},
                        "width": { "value": 5.50, "unit": "m" }
                    },
                    "edge_barrier_2": {
                        "appurtenance_id": "eb2", "name": "EB2", "element_index": 2,
                        "appurtenance_type": "CONCRETE BARRIER", "material_id": "m1",
                        "positioned_by": "fixed", "geometry_type": "linear",
                        "width": {"value": 0.5, "unit": "m"}, "height": {"value": 1.2, "unit": "m"}
                    }
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_deck_appurtenances_for_project()

    def test_unknown_appurtenance_type_raises_validation_error(self):
        bad = json.dumps({
            "deck_appurtenances": [
                {
                    "deck_layout_type": "single-carriageway",
                    "name": "Bad Layout",
                    "layout_index": 0,
                    "start_x_point": {"value": 0.0, "unit": "m"},
                    "edge_barrier_1": {
                        "appurtenance_id": "eb1", "name": "EB1", "element_index": 0,
                        "appurtenance_type": "INVISIBLE BARRIER",
                        "material_id": "m1",
                        "positioned_by": "fixed", "geometry_type": "linear",
                        "width": {"value": 0.5, "unit": "m"}, "height": {"value": 1.2, "unit": "m"}
                    },
                    "carriageway_1": {
                        "appurtenance_id": "cw1", "name": "CW1", "element_index": 1,
                        "appurtenance_type": "SURFACING", "material_id": "m2",
                        "positioned_by": "fixed", "geometry_type": "surface",
                        "thickness_left": {"value": 0.08, "unit": "m"},
                        "thickness_right": {"value": 0.08, "unit": "m"},
                        "width": { "value": 5.50, "unit": "m" }
                    },
                    "edge_barrier_2": {
                        "appurtenance_id": "eb2", "name": "EB2", "element_index": 2,
                        "appurtenance_type": "CONCRETE BARRIER", "material_id": "m1",
                        "positioned_by": "fixed", "geometry_type": "linear",
                        "width": {"value": 0.5, "unit": "m"}, "height": {"value": 1.2, "unit": "m"}
                    }
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_deck_appurtenances_for_project()

    def test_negative_element_index_raises_validation_error(self):
        bad = json.dumps({
            "deck_appurtenances": [
                {
                    "deck_layout_type": "single-carriageway",
                    "name": "Bad Layout",
                    "layout_index": 0,
                    "start_x_point": {"value": 0.0, "unit": "m"},
                    "edge_barrier_1": {
                        "appurtenance_id": "eb1", "name": "EB1", "element_index": -1,
                        "appurtenance_type": "CONCRETE BARRIER", "material_id": "m1",
                        "positioned_by": "fixed", "geometry_type": "linear",
                        "width": {"value": 0.5, "unit": "m"}, "height": {"value": 1.2, "unit": "m"}
                    },
                    "carriageway_1": {
                        "appurtenance_id": "cw1", "name": "CW1", "element_index": 1,
                        "appurtenance_type": "SURFACING", "material_id": "m2",
                        "positioned_by": "fixed", "geometry_type": "surface",
                        "thickness_left": {"value": 0.08, "unit": "m"},
                        "thickness_right": {"value": 0.08, "unit": "m"},
                        "width": { "value": 5.50, "unit": "m" }
                    },
                    "edge_barrier_2": {
                        "appurtenance_id": "eb2", "name": "EB2", "element_index": 2,
                        "appurtenance_type": "CONCRETE BARRIER", "material_id": "m1",
                        "positioned_by": "fixed", "geometry_type": "linear",
                        "width": {"value": 0.5, "unit": "m"}, "height": {"value": 1.2, "unit": "m"}
                    }
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_deck_appurtenances_for_project()

    # ------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------

    def test_consistent_results_across_calls(self, provider: DataFileProvider):
        first = provider.get_deck_appurtenances_for_project()
        second = provider.get_deck_appurtenances_for_project()

        assert len(first) == len(second)
        for a, b in zip(first, second):
            assert a.deck_layout_type == b.deck_layout_type
            assert a.layout_index == b.layout_index

    def test_provider_stores_folder_path(self, fixtures_path: Path):
        provider = DataFileProvider(folder=str(fixtures_path))
        assert provider.Folder == str(fixtures_path)
