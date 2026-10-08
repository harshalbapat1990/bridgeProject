"""Convert validated Speckle deck layout contracts to ParaModels."""

from __future__ import annotations

from typing import Any

from bda.contracts.paramodel.deck_appurtenances.deck_appurtenances_para_model import (
    BridgeDeckLayoutParaModelAdapter,
)
from bda.contracts.paramodel.sections.dimensions_para_models import Point2DParaModel
from bda.contracts.shared import QuantityParaModel
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_layout_base import (
    DeckLayoutPropertiesBase,
    MiscellaneousItemsCollection,
    StandardLayoutAppurtenancesCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_layout_types.deck_appurtenances import (
    Carriageway,
    CentralReserve,
    EdgeBarrier,
    VergeFootway,
)


class DeckLayoutSpeckleAdapter:
    """Flatten the Speckle deck collection tree to the existing layout shape."""

    @classmethod
    def parse_list(cls, collection: Any) -> list:
        return [cls.parse(layout) for layout in collection.elements]

    @classmethod
    def parse(cls, layout: Any):
        layout_properties = cls._single(
            layout.elements, DeckLayoutPropertiesBase, "layout properties"
        )
        standard = cls._single(
            layout.elements, StandardLayoutAppurtenancesCollection,
            "standard appurtenances",
        )
        misc = next(
            (item for item in layout.elements if isinstance(item, MiscellaneousItemsCollection)),
            None,
        )
        layout_data = layout_properties.properties
        deck_type = layout_data.deck_layout_type.provided_value
        normalized = {
            "name": f"{layout.name} Layout",
            "deck_layout_type": deck_type.value,
            "layout_index": layout_data.layout_index.provided_value,
            "start_x_point": {
                "value": layout_data.start_x_point.provided_value,
                "unit": layout_data.start_x_point.provided_unit or "m",
            },
        }
        fixed_items = [cls._appurtenance(item) for item in standard.elements]
        fixed_items.sort(key=lambda item: item["element_index"])
        free_items = (
            [cls._appurtenance(item) for item in misc.elements]
            if misc is not None else []
        )
        if deck_type.value == "single-carriageway":
            cls._assign_occurrences(
                normalized,
                fixed_items,
                ((EdgeBarrier, "edge_barrier"),
                 (VergeFootway, "verge_footway"),
                 (Carriageway, "carriageway")),
            )
        else:
            cls._assign_occurrences(
                normalized,
                fixed_items,
                ((EdgeBarrier, "edge_barrier"),
                 (VergeFootway, "verge_footway"),
                 (Carriageway, "carriageway"),
                 (CentralReserve, "central_reserve")),
            )
        normalized["miscellaneous_items"] = free_items
        return BridgeDeckLayoutParaModelAdapter.parse(normalized)

    @staticmethod
    def _single(items: list, item_type: type, label: str):
        matches = [item for item in items if isinstance(item, item_type)]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {label}, found {len(matches)}")
        return matches[0]

    @classmethod
    def _assign_occurrences(
        cls,
        normalized: dict,
        values: list[dict],
        occurrence_types: tuple[tuple[type, str], ...],
    ) -> None:
        for contract_type, field_prefix in occurrence_types:
            matches = [
                value for value in values
                if isinstance(value["_contract"], contract_type)
            ]
            for index, value in enumerate(matches, start=1):
                normalized[f"{field_prefix}_{index}"] = value
        for value in values:
            value.pop("_contract", None)

    @staticmethod
    def _appurtenance(item: Any) -> dict:
        values = item.properties.model_dump(mode="python", by_alias=True)

        def raw(name: str, default=None):
            parameter = values.get(name)
            return parameter.get("provided_value", default) if parameter else default

        def quantity(name: str):
            parameter = values[name]
            return QuantityParaModel(
                value=parameter["provided_value"],
                unit=parameter.get("provided_unit") or "m",
            ).model_dump()

        parsed = {
            "appurtenance_id": raw("Appurtenance ID"),
            "name": item.name,
            "element_index": raw("Element Index"),
            "appurtenance_type": raw("Appurtenance Type").value,
            "material_id": raw("Material ID"),
            "positioned_by": raw("Positioned By").value,
            "geometry_type": raw("Geometry Type").value,
            "width": quantity("Width"),
            "_contract": item,
        }
        for key, parameter_name in (
            ("height", "Height"),
            ("thickness_left", "Thickness Left"),
            ("thickness_right", "Thickness Right"),
            ("offset", "Offset"),
        ):
            if parameter_name in values:
                parsed[key] = quantity(parameter_name)
        outline = raw("Outline")
        if outline is not None:
            if any(value is None for value in outline):
                raise ValueError(
                    f"Outline for {item.name!r} contains polygon separators, "
                    "which the current ParaModel outline type cannot represent"
                )
            if len(outline) % 2:
                raise ValueError(f"Outline for {item.name!r} must contain coordinate pairs")
            parsed["outline"] = [
                Point2DParaModel(
                    x=QuantityParaModel(value=x, unit="m"),
                    y=QuantityParaModel(value=y, unit="m"),
                ).model_dump()
                for x, y in zip(outline[::2], outline[1::2])
            ]
        return parsed
