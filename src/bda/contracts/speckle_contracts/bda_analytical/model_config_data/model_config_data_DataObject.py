from bda.contracts.speckle_contracts.base_objects import BridgeDataObject, EnumParameter, \
    DataObjectSpeckleType, BridgeDataObjectProperties, Geometry
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_enums import \
    ModelUnitSystemEnum, OutputSoftwareEnum, DesignCodesEnum, StructureTypeEnum
from typing import Literal
from pydantic import Field


class ModelConfigDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal["Objects.Data.DataObject:BDA_Model_Config"]="Objects.Data.DataObject:BDA_Model_Config"

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
    bda_speckle_type:ModelConfigDataObjectSpeckleType
    model_unit_system :BDA_ModelUnitSystem = Field(alias="Model Unit System")
    output_software:BDA_OutputSoftware = Field(alias="Output Software")
    design_code:BDA_DesignCode = Field(alias="Design Code")
    structure_type:BDA_StructureType = Field(alias="Structure Type")

class BDA_ModelDataDataObject(BridgeDataObject):
    name: Literal["BDA Analytical Model Data"] = "BDA Analytical Model Data"

    properties: ModelConfigDataObjectProperties
    
    displayValue: list[Geometry] = Field(
        default_factory=list,
        frozen=True,
        description="Always empty for config object.",
        json_schema_extra={"const": []},
    )
    