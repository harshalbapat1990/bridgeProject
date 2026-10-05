from bda.contracts.paramodel.shared.base_model_para_model import BaseModelParaModel
from bda.domain.enums import UnitSystem, OutputSoftware, BridgeType, DesignCode

from pydantic import BaseModel, Field, AliasChoices, AliasPath


class BdaModelConfig(BaseModelParaModel):
    unit_system: UnitSystem = Field(
        validation_alias=AliasChoices(
            "unit_system",
            AliasPath( "properties",
                             "Model Unit System",
                                   "provided_value")))
    output_software: OutputSoftware = Field(
        validation_alias=AliasChoices(
            "output_software",
            AliasPath( "properties",
                             "Output Software",
                                   "provided_value")))
    design_code: DesignCode = Field(
        validation_alias=AliasChoices(
            "design_code",
            AliasPath( "properties",
                             "Design Code",
                                   "provided_value")))
    bridge_type: BridgeType = Field(
        validation_alias=AliasChoices(
            "bridge_type",
            AliasPath( "properties",
                             "Structure Type",
                                   "provided_value")))
    # structure_type: str
    # Structure Name
    # Project Name
    # Project ID
    # Structure ID


class BdaModelConfigAdapter(BaseModel):
    """
    Top-level wrapper that matches the ``{ "model_config": {...}}`` JSON envelope.

    Usage::

        import json
        from bda.contracts.shared.bda_model_config import BdaModelConfigAdapter

        data = json.load(open("model_config.json"))
        adapter = BdaModelConfigAdapter.model_validate(data)
        config: BdaModelConfig = adapter.config
    """

    config: BdaModelConfig = Field(..., alias="model_config")

    @classmethod
    def parse(cls, data) -> BdaModelConfig:
        adapter = BdaModelConfigAdapter.model_validate(data)
        return adapter.config
