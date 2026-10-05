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
    MaterialType,
    Isotropy,
    UnitWeight,
    ModulusOfElasticity,
    PoissonsRatio,
    CoefficientOfThermalExpansion,
)
from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_parameters import (
    MaterialType
)
from bda.contracts.speckle_contracts.bda_analytical.materials.material_types.material_types_aashto.general_material_properties_AASHTO import GeneralMaterialParameters_AASHTO


from pydantic import BaseModel, Field, StrictFloat
from typing import Literal
import json

# ----------------------------
# Material Type – Steel
# ----------------------------


class MaterialType_Steel(MaterialType):
    """Steel-specialised Material Type"""

    provided_value: MaterialTypeParaModel = MaterialTypeParaModel.STEEL

class SteelMaterialDataObjectType_AASHTO(DataObjectSpeckleType):
    provided_value: Literal["Objects.Data.DataObject:BDA_Steel_Material_AASHTO"]="Objects.Data.DataObject:BDA_Steel_Material_AASHTO"


# ----------------------------
# Steel Strength Parameters
# ----------------------------

class SpecifiedMinimumYieldStrengthSteel(UnitParameter[StrictFloat]):
    name: Literal["Specified Minimum Steel Yield Strength"] = "Specified Minimum Steel Yield Strength"
    symbol: Literal["fy,min"] = "fy,min"
    description: Literal[
        "Specified Minimum yield strength of steel"
    ] = "Specified Minimum yield strength of steel"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbs/ft²"]
    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat
    isUser: bool


class ExpectedYieldStrengthSteel(UnitParameter[StrictFloat]):
    name: Literal["Expected Steel Yield Strength"] = "Expected Steel Yield Strength"
    symbol: Literal["fy,exp"] = "fy,exp"
    description: Literal[
        "Expected yield strength of steel"
    ] = "Expected yield strength of steel"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbs/ft²"]
    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat
    isUser: bool


class SpecifiedMinimumTensileStrengthSteel(UnitParameter[StrictFloat]):
    name: Literal["Specified Minimum Steel Tensile Strength"] = "Specified Minimum Steel Tensile Strength"
    symbol: Literal["fu,min"] = "fu,min"
    description: Literal[
        "Specified minimum tensile strength of steel"
    ] = "Specified minimum tensile strength of steel"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbs/ft²"]
    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat
    isUser: bool


class ExpectedTensileStrengthSteel(UnitParameter[StrictFloat]):
    name: Literal["Expected Steel Tensile Strength"] = "Expected Steel Tensile Strength"
    symbol: Literal["fu,exp"] = "fu,exp"
    description: Literal[
        "Expected tensile strength of steel"
    ] = "Expected tensile strength of steel"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbs/ft²"]
    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat
    isUser: bool


# ----------------------------
# Parameter Containers (Schema-Strict)
# ----------------------------

class GeneralMaterialParameters_Steel_AASHTO(GeneralMaterialParameters_AASHTO):
    material_type: MaterialType_Steel = Field(alias="Material Type")

class SteelMaterialParameters_AASHTO(BaseModel):
    expected_steel_yield_strength: ExpectedYieldStrengthSteel = Field(
        alias="Expected Steel Yield Strength"
    )
    minimum_steel_yield_strength: SpecifiedMinimumYieldStrengthSteel = Field(
        alias="Minimum Steel Yield Strength"
    )
    expected_steel_tensile_strength: ExpectedTensileStrengthSteel = Field(
        alias="Expected Steel Tensile Strength"
    )
    minimum_steel_tensile_strength: SpecifiedMinimumTensileStrengthSteel = Field(
        alias="Minimum Steel Tensile Strength"
    )


# ----------------------------
# Parameter Groups (Semantic)
# ----------------------------

class GeneralMaterialPropertiesParameterGroup_Steel_AASHTO(ParameterGroup):
    name: Literal["General Material Properties"] = "General Material Properties"
    description: Literal[
        "General material properties"
    ] = "General material properties"

    group_parameters: GeneralMaterialParameters_Steel_AASHTO


class SteelMaterialPropertiesParameterGroup_AASHTO(ParameterGroup):
    name: Literal["Steel Material Properties"] = "Steel Material Properties"
    description: Literal[
        "Steel material properties"
    ] = "Steel material properties"

    group_parameters: SteelMaterialParameters_AASHTO


# ----------------------------
# DataObject Properties (Contract Boundary)
# ----------------------------

class MaterialDataObject_Properties_Steel_AASHTO(BridgeDataObjectProperties):
    bda_speckle_type:SteelMaterialDataObjectType_AASHTO
    general_material_properties: GeneralMaterialPropertiesParameterGroup_Steel_AASHTO = Field(
        alias="General Material Properties"
    )
    steel_material_properties: SteelMaterialPropertiesParameterGroup_AASHTO = Field(
        alias="Design Material Properties"
    )


# ----------------------------
# Debug / Schema Output
# ----------------------------

if __name__ == "__main__":
    schema = MaterialDataObject_Properties_Steel_AASHTO.model_json_schema()
    print(json.dumps(schema, indent=2))