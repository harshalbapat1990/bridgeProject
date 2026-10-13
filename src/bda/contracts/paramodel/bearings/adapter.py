from typing import List

from pydantic import TypeAdapter

from bda.contracts.paramodel.bearings.bearing_bc_para_model import BearingBCsSupportParaModel
from bda.contracts.paramodel.groups.enums import BearingConfigurationTypeParaModel


class BearingBCsParaModelAdapter:

    @staticmethod
    def parse_list(raw_list: List) -> List[BearingBCsSupportParaModel]:
        if isinstance(raw_list, dict):
            raw_list = raw_list.get("elements", [raw_list])

        if (
            raw_list
            and isinstance(raw_list[0], dict)
            and "properties" in raw_list[0]
            and "Bearing Boundary Condition Parameters" in raw_list[0]["properties"]
        ):
            grouped: dict[int, dict[int, list[dict]]] = {}
            for bc in raw_list:
                props = bc["properties"]
                support = props["Support Index"]["provided_value"]
                girder = props["Girder Index"]["provided_value"]
                params = props["Bearing Boundary Condition Parameters"]["group_parameters"]
                definitions = []
                for definition in params["Bearing Spring Definitions"]["group_parameters"].values():
                    item = definition["group_parameters"]
                    definitions.append(
                        {
                            "bearing_index": item["Bearing Index"]["provided_value"],
                            "orientation": item["Orientation"]["provided_value"],
                            "bearing_stiffness_definition": item[
                                "Bearing Stiffness Definition"
                            ]["group_parameters"],
                        }
                    )

                grouped.setdefault(support, {}).setdefault(girder, []).extend(definitions)

            raw_list = []
            for support, girders in grouped.items():
                bearings_by_girder = []
                for girder, definitions in girders.items():
                    if not definitions:
                        raise ValueError(
                            f"No bearing definitions found for support {support}, girder {girder}."
                        )

                    girder_payload = {"girder_index": girder}
                    if len(definitions) == 1:
                        girder_payload["bearing_configuration_type"] = (
                            BearingConfigurationTypeParaModel.SINGULAR.value
                        )
                        girder_payload["bearing_definition"] = definitions[0]
                    else:
                        girder_payload["bearing_configuration_type"] = (
                            BearingConfigurationTypeParaModel.MULTIPLE.value
                        )
                        girder_payload["bearing_definitions"] = definitions
                    bearings_by_girder.append(girder_payload)

                raw_list.append(
                    {
                        "support_index": support,
                        "bearings_by_girder": bearings_by_girder,
                    }
                )

        adapter = TypeAdapter(List[BearingBCsSupportParaModel])
        return adapter.validate_python(raw_list)
