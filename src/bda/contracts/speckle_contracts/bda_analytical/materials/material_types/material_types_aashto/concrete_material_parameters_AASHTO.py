from __future__ import annotations

from bda.contracts.speckle_contracts.base_objects import (
    Parameter,
    UnitParameter,
    ParameterGroup,
    BridgeDataObjectProperties,
    DataObjectSpeckleType
)
from bda.contracts.paramodel.materials.materials_para_model import MaterialTypeParaModel
from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_parameters import (
    MaterialType
)
from bda.contracts.speckle_contracts.bda_analytical.materials.material_types.material_types_aashto.general_material_properties_AASHTO import GeneralMaterialParameters_AASHTO
from pydantic import BaseModel, Field, StrictFloat
from typing import Literal
import json

# ----------------------------
# Material Type – Concrete - Fixed Parameters
# ----------------------------

class MaterialType_Concrete(MaterialType):
    """Concrete-specialised Material Type"""

    provided_value: MaterialTypeParaModel = MaterialTypeParaModel.CONCRETE

class ConcreteMaterialDataObjectType_AASHTO(DataObjectSpeckleType):
    provided_value: Literal["Objects.Data.DataObject:BDA_Concrete_Material_AASHTO"]="Objects.Data.DataObject:BDA_Concrete_Material_AASHTO"

# ----------------------------
# Concrete Strength Parameters
# ----------------------------

class SpecifiedMinimumCompressiveStrength(UnitParameter[StrictFloat]):
    name: Literal["Specified Minimum Compressive Strength"] = "Specified Minimum Compressive Strength"
    symbol: Literal["fc,min"] = "fc,min"
    description: Literal[
        "Specified minimum compressive strength of concrete"
    ] = "Specified minimum compressive strength of concrete"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbs/ft³"]
    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat
    isUser: bool


class ExpectedCompressoveStrength(UnitParameter[StrictFloat]):
    name: Literal["Expected Compressive Strength"] = "Expected Compressive Strength"
    symbol: Literal["fc,exp"] = "fc,exp"
    description: Literal[
        "Expected compressive strength of concrete at 28 days"
    ] = "Expected compressive strength of concrete at 28 days"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbs/ft³"]
    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat
    isUser: bool


# ----------------------------
# Parameter Containers (Schema-Strict)
# ----------------------------

class GeneralMaterialParameters_Concrete_AASHTO(GeneralMaterialParameters_AASHTO):
    material_type: MaterialType_Concrete = Field(alias="Material Type") # Each Material Is associated to a design code

class MaterialParameters_Concrete_AASHTO(BaseModel):
    expected_concrete_strength: ExpectedCompressoveStrength = Field(
        alias="Expected Concrete Strength"
    )
    specified_concrete_strength: SpecifiedMinimumCompressiveStrength = Field(
        alias="Specified Concrete Strength"
    )


# ----------------------------
# Parameter Groups (Semantic)
# ----------------------------

class GeneralMaterialProperties_ParameterGroup_Concrete_AASHTO(ParameterGroup):
    name: Literal["General Material Properties"] = "General Material Properties"
    description: Literal["General material properties"] = "General material properties"

    group_parameters: GeneralMaterialParameters_Concrete_AASHTO


class ConcreteMaterialPropertiesParameterGroup_AASHTO(ParameterGroup):
    name: Literal["Concrete Material Properties"] = "Concrete Material Properties"
    description: Literal[
        "Concrete material properties"
    ] = "Concrete material properties"

    group_parameters: MaterialParameters_Concrete_AASHTO


# ----------------------------
# DataObject Properties (Contract Boundary)
# ----------------------------

class MaterialDataObject_Properties_Concrete_AASHTO(BridgeDataObjectProperties):
    bda_speckle_type:ConcreteMaterialDataObjectType_AASHTO
    general_material_properties: GeneralMaterialProperties_ParameterGroup_Concrete_AASHTO = Field(
        alias="General Material Properties"
    )
    concrete_material_properties: ConcreteMaterialPropertiesParameterGroup_AASHTO = Field(
        alias="Design Material Properties"
    )


# ----------------------------
# Debug / Schema Output
# ----------------------------

if __name__ == "__main__":
    schema = MaterialDataObject_Properties_Concrete_AASHTO.model_json_schema()
    print(json.dumps(schema, indent=2))