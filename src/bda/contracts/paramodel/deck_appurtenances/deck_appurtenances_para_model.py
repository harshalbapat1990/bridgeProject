from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Type, Union

from pydantic import Field, model_validator

from bda.contracts.paramodel.shared.base_model_para_model import BaseModelParaModel
from bda.contracts.paramodel.sections.dimensions_para_models import Point2DParaModel
from bda.contracts.shared import QuantityParaModel
from bda.contracts.paramodel.deck_appurtenances.enums import (
    BridgeDeckLayoutTypeParaModel,
    DeckAppurtenanceTypeParaModel,
    GeometryTypeParaModel,
    PositionDefEnumParaModel,
)


# ---------------------------------------------------------------------------
# Base ParaModels
# ---------------------------------------------------------------------------


class DeckAppurtenanceBaseParaModel(BaseModelParaModel):
    """Common fields shared by all deck appurtenance elements."""

    appurtenance_id: str
    name: str
    element_index: int = Field(ge=0)
    appurtenance_type: DeckAppurtenanceTypeParaModel
    material_id: str
    positioned_by: PositionDefEnumParaModel
    geometry_type: GeometryTypeParaModel
    width: QuantityParaModel


# ---------------------------------------------------------------------------
# Geometry mixins
# ---------------------------------------------------------------------------


class LinearDeckAppurtenanceBaseParaModel(DeckAppurtenanceBaseParaModel):
    """Linear geometry — described by height and/or outline."""

    geometry_type: GeometryTypeParaModel = GeometryTypeParaModel.LINEAR
    height: QuantityParaModel
    outline: Optional[List[Point2DParaModel]] = None


class SurfaceDeckAppurtenanceBaseParaModel(DeckAppurtenanceBaseParaModel):
    """Surface geometry — described by variable thickness and optional outline."""

    geometry_type: GeometryTypeParaModel = GeometryTypeParaModel.SURFACE
    thickness_left: QuantityParaModel
    thickness_right: QuantityParaModel


# ---------------------------------------------------------------------------
# Positioning mixins
# ---------------------------------------------------------------------------


class DeckAppurtenanceFixedBaseParaModel(DeckAppurtenanceBaseParaModel):
    """Element whose transverse position is fully determined by the deck layout."""

    positioned_by: PositionDefEnumParaModel = PositionDefEnumParaModel.FIXED


class DeckAppurtenanceByOffsetBaseParaModel(DeckAppurtenanceBaseParaModel):
    """Element placed freely across the deck via a transverse offset from centreline."""

    positioned_by: PositionDefEnumParaModel = PositionDefEnumParaModel.BY_OFFSET
    # Transverse offset measured from the bridge centreline.
    offset: QuantityParaModel


# ---------------------------------------------------------------------------
# Concrete models  (positioned_by × geometry_type)
# ---------------------------------------------------------------------------


class LinearFixedDeckAppurtenanceParaModel(
    DeckAppurtenanceFixedBaseParaModel,
    LinearDeckAppurtenanceBaseParaModel,
):
    """Fixed-position linear element (e.g. edge barrier, metal railing)."""


class SurfaceFixedDeckAppurtenanceParaModel(
    DeckAppurtenanceFixedBaseParaModel,
    SurfaceDeckAppurtenanceBaseParaModel,
):
    """Fixed-position surface element (e.g. carriageway, verge/footway surfacing)."""


class LinearByOffsetDeckAppurtenanceParaModel(
    DeckAppurtenanceByOffsetBaseParaModel,
    LinearDeckAppurtenanceBaseParaModel,
):
    """Offset-positioned linear element placed freely across the deck."""


class SurfaceByOffsetDeckAppurtenanceParaModel(
    DeckAppurtenanceByOffsetBaseParaModel,
    SurfaceDeckAppurtenanceBaseParaModel,
):
    """Offset-positioned surface element placed freely across the deck."""


# ---------------------------------------------------------------------------
# Union type alias
# ---------------------------------------------------------------------------

DeckAppurtenanceParaModel = Union[
    LinearFixedDeckAppurtenanceParaModel,
    SurfaceFixedDeckAppurtenanceParaModel,
    LinearByOffsetDeckAppurtenanceParaModel,
    SurfaceByOffsetDeckAppurtenanceParaModel,
]

# ---------------------------------------------------------------------------
# Dispatch table  (positioned_by, geometry_type) → model class
# ---------------------------------------------------------------------------

_APPURTENANCE_CLASS_BY_POSITION_AND_GEOMETRY: Dict[
    Tuple[PositionDefEnumParaModel, GeometryTypeParaModel],
    Type[DeckAppurtenanceBaseParaModel],
] = {
    (PositionDefEnumParaModel.FIXED, GeometryTypeParaModel.LINEAR): LinearFixedDeckAppurtenanceParaModel,
    (PositionDefEnumParaModel.FIXED, GeometryTypeParaModel.SURFACE): SurfaceFixedDeckAppurtenanceParaModel,
    (PositionDefEnumParaModel.BY_OFFSET, GeometryTypeParaModel.LINEAR): LinearByOffsetDeckAppurtenanceParaModel,
    (PositionDefEnumParaModel.BY_OFFSET, GeometryTypeParaModel.SURFACE): SurfaceByOffsetDeckAppurtenanceParaModel,
}


# ---------------------------------------------------------------------------
# Brain: DeckAppurtenanceParaModelAdapter
# ---------------------------------------------------------------------------


class DeckAppurtenanceParaModelAdapter(BaseModelParaModel):
    """Brain — dispatches raw data to the correct concrete appurtenance model."""

    appurtenance: DeckAppurtenanceParaModel

    @model_validator(mode="before")
    @classmethod
    def _dispatch(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        raw_positioned_by = data.get("positioned_by")
        raw_geometry_type = data.get("geometry_type")

        try:
            positioned_by = (
                raw_positioned_by
                if isinstance(raw_positioned_by, PositionDefEnumParaModel)
                else PositionDefEnumParaModel(raw_positioned_by)
            )
        except (TypeError, ValueError):
            raise ValueError(
                f"Unknown positioned_by value '{raw_positioned_by}'"
            ) from None

        try:
            geometry_type = (
                raw_geometry_type
                if isinstance(raw_geometry_type, GeometryTypeParaModel)
                else GeometryTypeParaModel(raw_geometry_type)
            )
        except (TypeError, ValueError):
            raise ValueError(
                f"Unknown geometry_type value '{raw_geometry_type}'"
            ) from None

        appurtenance_cls = _APPURTENANCE_CLASS_BY_POSITION_AND_GEOMETRY.get(
            (positioned_by, geometry_type)
        )
        if appurtenance_cls is None:
            raise ValueError(
                f"No model for positioned_by='{positioned_by}' and geometry_type='{geometry_type}'"
            )
        return {"appurtenance": appurtenance_cls.model_validate(data)}

    @classmethod
    def parse(cls, data: dict) -> DeckAppurtenanceParaModel:
        return cls.model_validate(data).appurtenance


# ---------------------------------------------------------------------------
# Bridge Deck Layout
# ---------------------------------------------------------------------------


class BridgeDeckLayoutBaseParaModel(BaseModelParaModel):
    """Common fields for all bridge deck layout definitions.

    Note: It is assumed that the current cross-section applies from
    ``start_x_point`` to the end of the bridge, unless another cross-section
    is defined further along the alignment. In such a case, a linear
    interpolation of the cross-section transition is applied between the two
    definitions.
    """
    name: str
    deck_layout_type: BridgeDeckLayoutTypeParaModel
    layout_index: int = Field(default=0, ge=0)
    start_x_point: QuantityParaModel = Field(
        default_factory=lambda: QuantityParaModel(value=0.0, unit="m")
    )
    miscellaneous_items: List[
        Union[LinearByOffsetDeckAppurtenanceParaModel, SurfaceByOffsetDeckAppurtenanceParaModel]
    ] = Field(default_factory=list)


class SingleCarriagewayBridgeDeckLayoutParaModel(BridgeDeckLayoutBaseParaModel):
    """Single-carriageway bridge deck layout."""

    deck_layout_type: BridgeDeckLayoutTypeParaModel = BridgeDeckLayoutTypeParaModel.SINGLE_CARRIAGEWAY
    edge_barrier_1: LinearFixedDeckAppurtenanceParaModel
    verge_footway_1: Optional[SurfaceFixedDeckAppurtenanceParaModel] = None
    carriageway_1: SurfaceFixedDeckAppurtenanceParaModel
    verge_footway_2: Optional[SurfaceFixedDeckAppurtenanceParaModel] = None
    edge_barrier_2: LinearFixedDeckAppurtenanceParaModel


class DualCarriagewayBridgeDeckLayoutParaModel(BridgeDeckLayoutBaseParaModel):
    """Dual-carriageway bridge deck layout."""

    deck_layout_type: BridgeDeckLayoutTypeParaModel = BridgeDeckLayoutTypeParaModel.DUAL_CARRIAGEWAY
    edge_barrier_1: LinearFixedDeckAppurtenanceParaModel
    verge_footway_1: Optional[SurfaceFixedDeckAppurtenanceParaModel] = None
    carriageway_1: SurfaceFixedDeckAppurtenanceParaModel
    central_reserve: Optional[SurfaceFixedDeckAppurtenanceParaModel] = None
    carriageway_2: SurfaceFixedDeckAppurtenanceParaModel
    verge_footway_2: Optional[SurfaceFixedDeckAppurtenanceParaModel] = None
    edge_barrier_2: LinearFixedDeckAppurtenanceParaModel


# ---------------------------------------------------------------------------
# Union type alias
# ---------------------------------------------------------------------------

BridgeDeckLayoutParaModel = Union[
    SingleCarriagewayBridgeDeckLayoutParaModel,
    DualCarriagewayBridgeDeckLayoutParaModel,
]

# ---------------------------------------------------------------------------
# Dispatch table  deck_layout_type → model class
# ---------------------------------------------------------------------------

_LAYOUT_CLASS_BY_TYPE: Dict[
    BridgeDeckLayoutTypeParaModel,
    Type[BridgeDeckLayoutBaseParaModel],
] = {
    BridgeDeckLayoutTypeParaModel.SINGLE_CARRIAGEWAY: SingleCarriagewayBridgeDeckLayoutParaModel,
    BridgeDeckLayoutTypeParaModel.DUAL_CARRIAGEWAY: DualCarriagewayBridgeDeckLayoutParaModel,
}


# ---------------------------------------------------------------------------
# Brain: BridgeDeckLayoutParaModelAdapter
# ---------------------------------------------------------------------------


class BridgeDeckLayoutParaModelAdapter(BaseModelParaModel):
    """Brain — dispatches raw data to the correct concrete deck layout model."""

    layout: BridgeDeckLayoutParaModel

    @model_validator(mode="before")
    @classmethod
    def _dispatch(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        raw_layout_type = data.get("deck_layout_type")

        try:
            layout_type = (
                raw_layout_type
                if isinstance(raw_layout_type, BridgeDeckLayoutTypeParaModel)
                else BridgeDeckLayoutTypeParaModel(raw_layout_type)
            )
        except (TypeError, ValueError):
            raise ValueError(
                f"Unknown deck_layout_type '{raw_layout_type}'"
            ) from None

        layout_cls = _LAYOUT_CLASS_BY_TYPE.get(layout_type)
        if layout_cls is None:
            raise ValueError(
                f"No layout model for deck_layout_type='{layout_type}'"
            )
        return {"layout": layout_cls.model_validate(data)}

    @classmethod
    def parse(cls, data: dict) -> BridgeDeckLayoutParaModel:
        return cls.model_validate(data).layout
