from typing import List

from pydantic import TypeAdapter

from bda.contracts.paramodel.foundations.foundation_bc_para_model import (
    FoundationBCsParaModel, LumpedFoundationBCsParaModel,
    PileInteractionFoundationBCsParaModel,
)


class FoundationBCsParaModelAdapter:

    @staticmethod
    def parse_list(raw_list: List) -> List[FoundationBCsParaModel]:
        if isinstance(raw_list, dict):
            raw_list = raw_list.get("elements", [raw_list])
        adapter = TypeAdapter(FoundationBCsParaModel)
        parsed = []
        for raw in raw_list:
            if not isinstance(raw, dict) or "properties" not in raw:
                parsed.append(adapter.validate_python(raw))
                continue
            # The Speckle models store the union tag as a provided parameter.
            # Keep the existing concrete-model selection, while exposing that
            # tag to Pydantic's discriminated union for either input format.
            properties = raw.get("properties", {}) if isinstance(raw, dict) else {}
            lumped = properties.get("Lumped Foundation Parameters", {}).get("group_parameters", {})
            tag = raw.get("foundation_model_type") or lumped.get("Foundation Model Type", {}).get("provided_value") or properties.get("Foundation Model Type", {}).get("provided_value")
            if tag is None:
                parsed.append(adapter.validate_python(raw))
                continue
            payload = dict(raw)
            payload["foundation_model_type"] = tag
            if str(tag).lower().endswith("lumped_foundation_model"):
                app_type = lumped.get("Foundation Application Type", {}).get("provided_value")
                application = {}
                if app_type is not None:
                    application["application_type"] = app_type
                if "Vertical Offset" in lumped:
                    application["Vertical Offset"] = lumped["Vertical Offset"]
                payload["application"] = application
                parsed.append(LumpedFoundationBCsParaModel.model_validate(payload))
            else:
                definitions = properties.get("Pile Definitions", {}).get("group_parameters", {})
                piles = []
                for key, group in definitions.items():
                    params = group.get("group_parameters", {})
                    pile = dict(params)
                    pile["pile_key"] = key
                    soil_type = params.get("Soil Profile Type", {}).get("provided_value")
                    if soil_type is not None:
                        pile["soil_profile_type"] = soil_type
                    piles.append(pile)
                payload["pile_springs"] = piles
                parsed.append(PileInteractionFoundationBCsParaModel.model_validate(payload))
        return parsed
