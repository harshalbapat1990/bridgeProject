from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_parameters import (
    GeneralMaterialParameters,
    MaterialDesignCode
)
from bda.contracts.paramodel.materials.materials_para_model import StandardCodeParaModel
from bda.contracts.speckle_contracts.base_objects import ParameterGroup
from typing import Literal
from pydantic import Field

from bda.contracts.speckle_contracts.base_objects import DataObjectSpeckleType, BridgeDataObjectProperties

class MaterialDesignCode_AASHTO(MaterialDesignCode):
    """Concrete-specialised Material Type"""

    provided_value: StandardCodeParaModel = StandardCodeParaModel.AASHTO

class GeneralMaterialDataObjectType_AASHTO(DataObjectSpeckleType):
    provided_value: Literal["Objects.Data.DataObject:BDA_General_Material_AASHTO"]="Objects.Data.DataObject:BDA_General_Material_AASHTO"


class GeneralMaterialParameters_AASHTO(GeneralMaterialParameters):
    material_design_code: MaterialDesignCode_AASHTO = Field(alias="Material Design Code") # Each Material Is associated to a design code


class GeneralMaterialParameterGroup_AASHTO(ParameterGroup):
    name: Literal["General Material Properties"] = "General Material Properties"
    description: Literal["General material properties"] = \
        "General material properties"

    group_parameters: GeneralMaterialParameters_AASHTO


class GeneralMaterialDataObject_Properties_AASHTO(BridgeDataObjectProperties):
    bda_speckle_type:GeneralMaterialDataObjectType_AASHTO
    general_material_properties: GeneralMaterialParameterGroup_AASHTO = Field(
        alias="General Material Properties"
    )