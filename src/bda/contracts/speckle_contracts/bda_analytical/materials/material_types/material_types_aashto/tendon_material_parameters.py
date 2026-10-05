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

# --------------------------------------------------
# Material Type – Tendon
# --------------------------------------------------


class MaterialType_Tendon(MaterialType):
    provided_value: MaterialTypeParaModel = MaterialTypeParaModel.TENDON

class TendonMaterialDataObjectType(DataObjectSpeckleType):
    provided_value: Literal["Objects.Data.DataObject:BDA_Tendon_Material_AASHTO"]="Objects.Data.DataObject:BDA_Tendon_Material_AASHTO"
# --------------------------------------------------
# Tendon Strength Parameters
# --------------------------------------------------

class TendonYieldStrength(UnitParameter[StrictFloat]):
    name: Literal["Prestressing/Post-Tensioning Steel Yield Strength"] = "Prestressing/Post-Tensioning Steel Yield Strength"
    symbol: Literal["fy,min"] = "fy,min"
    description: Literal[
        "Yield strength of prestressing or post-tensioning steel"
    ] = "Yield strength of prestressing or post-tensioning steel"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbs/ft²"]
    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat
    isUser: bool

class TendonSpecifiedMinimumTensileStrength(UnitParameter[StrictFloat]):
    name: Literal["Prestressing/Post-Tensioning Steel Specified Minimum Tensile Strength"] = "Prestressing/Post-Tensioning Steel Specified Minimum Tensile Strength"
    symbol: Literal["fu,min"] = "fu,min"
    description: Literal[
        "Minimum tensile strength of tendon"
    ] = "Minimum tensile strength of tendon"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbs/ft²"]
    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat
    isUser: bool

# --------------------------------------------------
# Parameter Containers (Schema‑Strict)
# --------------------------------------------------

class GeneralMaterialParameters_Tendon_AASHTO(GeneralMaterialParameters_AASHTO):
    material_type: MaterialType_Tendon = Field(alias="Material Type")


class TendonMaterialParameters_AASHTO(BaseModel):
    tendon_yield_strength: TendonYieldStrength = Field(
        alias="Prestressing/Post-Tensioning Steel Yield Strength"
    )
    minimum_tensile_strength: TendonSpecifiedMinimumTensileStrength = Field(
        alias="Prestressing/Post-Tensioning Steel Specified Minimum Tensile Strength"
    )


# --------------------------------------------------
# Parameter Groups (Semantic)
# --------------------------------------------------

class GeneralMaterialPropertiesParameterGroup_Tendon_AASHTO(ParameterGroup):
    name: Literal["General Material Properties"] = "General Material Properties"
    description: Literal[
        "General material properties"
    ] = "General material properties"

    group_parameters: GeneralMaterialParameters_Tendon_AASHTO


class TendonMaterialPropertiesParameterGroup_AASHTO(ParameterGroup):
    name: Literal["Tendon Material Properties"] = "Tendon Material Properties"
    description: Literal[
        "Tendon material properties"
    ] = "Tendon material properties"

    group_parameters: TendonMaterialParameters_AASHTO


# --------------------------------------------------
# DataObject Properties (Contract Boundary)
# --------------------------------------------------

class MaterialDataObject_Properties_Tendon_AASHTO(BridgeDataObjectProperties):
    bda_speckle_type:TendonMaterialDataObjectType
    general_material_properties: GeneralMaterialPropertiesParameterGroup_Tendon_AASHTO = Field(
        alias="General Material Properties"
    )
    tendon_material_properties: TendonMaterialPropertiesParameterGroup_AASHTO = Field(
        alias="Design Material Properties"
    )


# --------------------------------------------------
# Debug / Schema Output
# --------------------------------------------------

if __name__ == "__main__":
    schema = MaterialDataObject_Properties_Tendon_AASHTO.model_json_schema()
    print(json.dumps(schema, indent=2))