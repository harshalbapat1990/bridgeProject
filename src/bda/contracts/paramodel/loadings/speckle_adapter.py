"""Convert nested loading Speckle collections to the existing ParaModels."""

from __future__ import annotations

from typing import Any

from bda.contracts.paramodel.loadings.adapter import LoadParaModelAdapter
from bda.contracts.speckle_contracts.base_objects import Parameter, ParameterGroup
from bda.contracts.speckle_contracts.bda_analytical.loading.loading_base import (
    LoadingCollection,
    PrestressingLoadDataObject,
)


class LoadingSpeckleAdapter:
    @classmethod
    def parse_list(cls, collection: LoadingCollection) -> list:
        parsed = []
        for domain in collection.elements:
            if not hasattr(domain, "elements") or domain.name == "Design Code & Secondary Code":
                continue
            for state in domain.elements:
                for load in state.elements:
                    parsed.append(cls.parse(load))
        return parsed

    @classmethod
    def parse(cls, load: Any):
        properties = load.properties
        raw = {
            "load_context": properties.load_context.provided_value,
            "main_code": properties.main_code.provided_value,
            "secondary_code": properties.secondary_code.provided_value,
            "load_application_domain": properties.load_application_domain.provided_value,
            "load_service_state": properties.load_service_state.provided_value,
            "load_nature": properties.load_nature.provided_value,
        }
        for key, value in properties.load_parameters.group_parameters.items():
            raw[key] = cls._value(value)
        # The Speckle object type already selects these ParaModel union variants.
        # Add their discriminator fields when flattening the generic parameter
        # group, instead of requiring the same choice to be entered twice.
        discriminator_defaults = {
            "StructuralDeadLoadDataObject": {"structural_load_type": "dead load"},
            "PrestressingLoadDataObject": {"structural_load_type": "prestressing"},
            "WindInServiceLoadDataObject": {"env_load_type": "wind"},
            "WindInConstructionLoadDataObject": {"env_load_type": "wind"},
            "UniformTemperatureLoadDataObject": {
                "env_load_type": "temperature",
                "temperature_effect_type": "uniform",
            },
            "GradientTemperatureLoadDataObject": {
                "env_load_type": "temperature",
                "temperature_effect_type": "gradient",
            },
            "EarthquakeLoadDataObject": {"env_load_type": "earthquake"},
            "HL93VerticalDirectLoadDataObject": {
                "primary_traffic_type": "road",
                "vehicle_def_type": "standard",
                "traffic_load_model": "HL-93",
                "traffic_load_type": "vertical traffic direct",
            },
            "HL93BrakingLoadDataObject": {
                "primary_traffic_type": "road",
                "vehicle_def_type": "standard",
                "traffic_load_model": "HL-93",
                "traffic_load_type": "braking",
            },
            "PedestrianLoadDataObject": {
                "primary_traffic_type": "road",
                "vehicle_def_type": "standard",
                "traffic_load_model": "Pedestrian",
            },
            "SettlementLoadDataObject": {"env_load_type": "settlement"},
        }
        raw.update(discriminator_defaults.get(type(load).__name__, {}))
        if isinstance(load, PrestressingLoadDataObject):
            application = raw.get("load_application")
            if isinstance(application, dict):
                if application and all(
                    isinstance(item, dict) for item in application.values()
                ):
                    raw["load_application"] = list(application.values())
                else:
                    raw["load_application"] = [application]
        return LoadParaModelAdapter.parse(raw)

    @classmethod
    def _value(cls, value: Any):
        if isinstance(value, ParameterGroup):
            return {
                key: cls._value(item)
                for key, item in value.group_parameters.items()
            }
        if isinstance(value, Parameter):
            if value.provided_unit is not None:
                return {
                    "value": value.provided_value,
                    "unit": value.provided_unit,
                }
            return value.provided_value
        if isinstance(value, list):
            return [cls._value(item) for item in value]
        if isinstance(value, dict):
            return {key: cls._value(item) for key, item in value.items()}
        return value
