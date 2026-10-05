from typing import List

from pydantic import TypeAdapter

from bda.contracts.paramodel.bearings.bearing_bc_para_model import BearingBCsSupportParaModel
from bda.contracts.paramodel.groups.enums import BearingConfigurationTypeParaModel


class BearingBCsParaModelAdapter:

    @staticmethod
    def parse_list(raw_list: List) -> List[BearingBCsSupportParaModel]:
        if isinstance(raw_list, dict):
            raw_list = raw_list.get("elements", [raw_list])
        if raw_list and isinstance(raw_list[0], dict) and "properties" in raw_list[0] and "Bearing Boundary Condition Parameters" in raw_list[0]["properties"]:
            grouped = {}
            for bc in raw_list:
                props = bc["properties"]
                support = props["Support Index"]["provided_value"]
                girder = props["Girder Index"]["provided_value"]
                params = props["Bearing Boundary Condition Parameters"]["group_parameters"]
                config = params["Bearing Configuration Type"]["provided_value"]
                defs = params["Bearing Spring Definitions"]["group_parameters"]
                definitions = []
                for definition in defs.values():
                    p = definition["group_parameters"]
                    spring = p["Bearing Stiffness Definition"]["group_parameters"]
                    definitions.append({
                        "bearing_index": p["Bearing Index"]["provided_value"],
                        "orientation": p["Orientation"]["provided_value"],
                        "bearing_stiffness_definition": spring,
                    })
                girder_payload = {"girder_index": girder, "bearing_configuration_type": config}
                if str(config).lower().endswith("singular"):
                    girder_payload["bearing_definition"] = definitions[0]
                else:
                    girder_payload["bearing_definitions"] = definitions
                group = grouped.setdefault(support, {})
                group[girder] = girder_payload
            raw_list = [
                {"support_index": support, "bearings_by_girder": list(girders.values())}
                for support, girders in grouped.items()
            ]
        adapter = TypeAdapter(List[BearingBCsSupportParaModel])
        return adapter.validate_python(raw_list)
