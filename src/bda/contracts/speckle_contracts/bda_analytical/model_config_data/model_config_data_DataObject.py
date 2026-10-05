from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
from bda.contracts.speckle_contracts.base_objects import BridgeDataObject, EnumParameter, \
    BridgeDataObjectProperties, Geometry
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_enums import \
    ModelUnitSystemEnum, OutputSoftwareEnum, DesignCodesEnum, StructureTypeEnum
from typing import ClassVar, Literal
import re
from pydantic import Field, field_validator


class BDA_ModelUnitSystem(EnumParameter[ModelUnitSystemEnum]):
    name: Literal["Model Unit System"] = "Model Unit System"
    description: Literal["The preferred unit system used for the model. This will impact the output unit systems of any models"] = \
        "The preferred unit system used for the model. This will impact the output unit systems of any models"
    isUser :bool = True
    symbol : None = None
    provided_value: ModelUnitSystemEnum

class BDA_OutputSoftware(EnumParameter[OutputSoftwareEnum]):
    name: Literal["Output Software"] = "Output Software"
    description: Literal["The software used for output generation"] = \
        "The software used for output generation"
    isUser :bool = True
    symbol : None = None
    provided_value: OutputSoftwareEnum

class BDA_DesignCode(EnumParameter[DesignCodesEnum]):
    name: Literal["Design Code"] = "Design Code"
    description: Literal["Design Code of bridge project (e.g Eurocode, AASHTO)"] = \
        "Design Code of bridge project (e.g Eurocode, AASHTO)"
    isUser :bool = True
    symbol : None = None
    provided_value: DesignCodesEnum

class BDA_StructureType(EnumParameter[StructureTypeEnum]):
    name: Literal["Structure Type"] = "Structure Type"
    description: Literal["Bridge structure type. This dictates the parameters for the analysis"] = \
        "Bridge structure type. This dictates the parameters for the analysis"
    isUser :bool = True
    symbol : None = None
    provided_value: StructureTypeEnum

# model config dataobject Properties

class ModelConfigDataObjectProperties(BridgeDataObjectProperties):
    model_unit_system :BDA_ModelUnitSystem = Field(alias="Model Unit System")
    output_software:BDA_OutputSoftware = Field(alias="Output Software")
    design_code:BDA_DesignCode = Field(alias="Design Code")
    structure_type:BDA_StructureType = Field(alias="Structure Type")

class BDA_ModelDataDataObject(BridgeDataObject):
    name: Literal["BDA Analytical Model Data"] = "BDA Analytical Model Data"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_MODEL_CONFIG
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_MODEL_CONFIG.value, frozen=True)

    properties: ModelConfigDataObjectProperties

    displayValue: list[Geometry] = Field(
        default_factory=list,
        frozen=True,
        description="Always empty for config object.",
        json_schema_extra={"const": []},
    )

    CONFIG_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^CFG-\d{4}$"
    )

    applicationId: str = Field(pattern=CONFIG_ID_PATTERN)

    @field_validator("applicationId")
    @classmethod
    def validate_application_id(
        cls,
        value: str,
    ):

        if not cls.CONFIG_ID_PATTERN.match(value):
            raise ValueError(
                "Config applicationId must match CFG-0001"
            )

        return value

    @classmethod
    def create(
        cls,
        model_unit_system: ModelUnitSystemEnum,
        output_software: OutputSoftwareEnum,
        design_code: DesignCodesEnum,
        structure_type: StructureTypeEnum,
        application_id: str = "CFG-0001",
    ) -> "BDA_ModelDataDataObject":
        return cls(
            applicationId=application_id,
            properties=ModelConfigDataObjectProperties(
                **{
                    "Model Unit System": BDA_ModelUnitSystem(
                        provided_value=model_unit_system
                    ),
                    "Output Software": BDA_OutputSoftware(
                        provided_value=output_software
                    ),
                    "Design Code": BDA_DesignCode(
                        provided_value=design_code
                    ),
                    "Structure Type": BDA_StructureType(
                        provided_value=structure_type
                    ),
                },
            )
        )
    
if __name__ == "__main__":

    from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_enums import (
        ModelUnitSystemEnum,
        OutputSoftwareEnum,
        DesignCodesEnum,
        StructureTypeEnum,
    )

    model_config = BDA_ModelDataDataObject.create(
        model_unit_system=ModelUnitSystemEnum.METRIC,
        output_software=OutputSoftwareEnum.MIDAS_CIVIL,
        design_code=DesignCodesEnum.EUROCODE,
        structure_type=StructureTypeEnum.PSC_BOX,
    )

    print(
            model_config.model_dump_json(
                indent=4,
                by_alias=True,
            )
        )
    