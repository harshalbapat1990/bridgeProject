from __future__ import annotations

from bda.contracts.paramodel.shared.case_insensitive_enum import CaseInsensitiveEnum


class GeometryTypeParaModel(CaseInsensitiveEnum):
    LINEAR = "linear"
    SURFACE = "surface"


class PositionDefEnumParaModel(CaseInsensitiveEnum):
    FIXED = "fixed"
    BY_OFFSET = "by offset"


class DeckAppurtenanceTypeParaModel(CaseInsensitiveEnum):
    PERMANENT_FORMWORK = "PERMANENT FORMWORK"
    CONCRETE_BARRIER = "CONCRETE BARRIER"
    METAL_RAILING = "METAL RAILING"
    RAISED_VERGE_FOOTWAY = "RAISED VERGE / FOOTWAY"
    RAISED_CENTRAL_RESERVE = "RAISED CENTRAL RESERVE"
    SURFACING = "SURFACING"


class BridgeDeckLayoutTypeParaModel(CaseInsensitiveEnum):
    SINGLE_CARRIAGEWAY = "single-carriageway"
    DUAL_CARRIAGEWAY = "dual-carriageway"
