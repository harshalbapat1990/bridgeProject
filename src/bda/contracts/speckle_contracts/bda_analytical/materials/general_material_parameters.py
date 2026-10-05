from __future__ import annotations
from pathlib import Path
import sys

from bda.contracts.speckle_contracts.base_objects import Parameter, UnitlessParameter, EnumParameter, UnitParameter, ParameterGroup, BridgeDataObjectProperties, DataObjectSpeckleType
from bda.contracts.paramodel.materials.materials_para_model import MaterialTypeParaModel, MaterialModelTypeParaModel, StandardCodeParaModel
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_enums import DesignCodesEnum
from typing import Literal, Optional
from pydantic import BaseModel, Field, StrictFloat
import json




class GeneralMaterialDataObjectType(DataObjectSpeckleType):
    provided_value: Literal["Objects.Data.DataObject:BDA_General_Material"]="Objects.Data.DataObject:BDA_General_Material"

# Material Type

class MaterialType(EnumParameter[MaterialTypeParaModel]):
    # Fixed identity

    name: Literal["Material Type"] = "Material Type"
    symbol: Literal["MatType"] = "MatType"
    description: Literal["Type of material (e.g., Concrete, Steel, Timber)"] = \
        "Type of material (e.g., Concrete, Steel, Timber)"

    # User value
    provided_value: MaterialTypeParaModel

    model_config = {
        "use_enum_values":True
    }

# Design Code

class MaterialDesignCode(EnumParameter[StandardCodeParaModel]):
    name: Literal["Material Design Code"] = "Material Design Code"
    symbol: None = None
    description: Literal["Associated design code of material"] = (
        "Associated design code of material"
    )

    provided_value: StandardCodeParaModel

# Isotropy

class Isotropy(EnumParameter[MaterialModelTypeParaModel]):
    name: Literal["Isotropy"] = "Isotropy"
    symbol: None = None
    description: Literal["Whether the material is isotropic or orthotropic"] = \
        "Whether the material is isotropic or orthotropic"

    provided_value: MaterialModelTypeParaModel


# Unit Weight
class UnitWeight(UnitParameter[StrictFloat]):
    name: Literal["Unit Weight"] = "Unit Weight"
    symbol: Literal["γ"] = "γ"
    description: Literal["Weight per unit volume of a material"] = "Weight per unit volume of a material"

    # Allowed user units
    provided_unit: Literal["kN/m³", "kips/ft³"]
    base_unit: Literal["kN/m³"] = "kN/m³"

    # Value constraints
    provided_value: StrictFloat = Field(..., ge=0) # Density must be positive

# Modulus of Elasticity

class ModulusOfElasticity(UnitParameter[StrictFloat]):
    name: Literal["Modulus of Elasticity"] = "Modulus of Elasticity"
    symbol: Literal["E"] = "E"
    description: Literal["Ratio of stress to strain in a material"] = \
        "Ratio of stress to strain in a material"

    provided_unit: Literal["Pa", "kPa", "GPa", "kip/ft²"]
    base_unit: Literal["Pa"] = "Pa"


# Poissons Ratio

class PoissonsRatio(UnitlessParameter[StrictFloat]):
    name: Literal["Poisson's Ratio"] = "Poisson's Ratio"
    symbol: Literal["ν"] = "ν"
    description: Literal["Ratio of transverse strain to axial strain in a material"] = \
        "Ratio of transverse strain to axial strain in a material"

   
    provided_value: StrictFloat = Field(..., ge=0.0) # Poissons ratio must be non-negative

# Coefficient of Thermal Expansion

class CoefficientOfThermalExpansion(UnitParameter[StrictFloat]):
    name: Literal["Coefficient of Thermal Expansion"] = "Coefficient of Thermal Expansion"
    symbol: Literal["α"] = "α"
    description: Literal["Change in length per unit length per degree of temperature change"] = \
        "Change in length per unit length per degree of temperature change"

    provided_unit: Literal["1/°C", "1/°F"]
    base_unit: Literal["1/°C"] = "1/°C"

# == General Material Parameter Group ==

class GeneralMaterialParameters(BaseModel):
    material_type: MaterialType = Field(alias="Material Type")
    material_design_code: MaterialDesignCode = Field(alias="Material Design Code") # Each Material Is associated to a design code
    isotropy: Isotropy = Field(alias="Isotropy")
    unit_weight: UnitWeight = Field(alias="Unit Weight")
    modulus_of_elasticity: ModulusOfElasticity = Field(alias="Modulus of Elasticity")
    poissons_ratio: PoissonsRatio = Field(alias="Poisson's Ratio")
    coefficient_of_thermal_expansion: CoefficientOfThermalExpansion = Field(alias="Coefficient of Thermal Expansion")



class GeneralMaterialParameterGroup(ParameterGroup):
    name: Literal["General Material Properties"] = "General Material Properties"
    description: Literal["General material properties"] = \
        "General material properties"

    group_parameters: GeneralMaterialParameters

class GeneralMaterialDataObject_Properties(BridgeDataObjectProperties):
    bda_speckle_type:GeneralMaterialDataObjectType
    general_material_properties: GeneralMaterialParameterGroup = Field(
        alias="General Material Properties"
    )

if __name__ == "__main__":
    # Example usage
    print("\n=== General Material Properties json schema ===")
    ui_schema = GeneralMaterialParameters.model_json_schema()
    print(json.dumps(ui_schema, indent=2))  


