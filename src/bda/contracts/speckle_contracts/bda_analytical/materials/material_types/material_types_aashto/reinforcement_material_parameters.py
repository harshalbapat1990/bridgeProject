from __future__ import annotations

from bda.contracts.speckle_contracts.base_objects import (
    Parameter,
    UnitParameter,
    ParameterGroup,
    BridgeDataObjectProperties,
    DataObjectSpeckleType,
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
from bda.contracts.speckle_contracts.bda_analytical.materials.material_types.material_types_aashto.steel_material_parameters import (
    SteelMaterialParameters_AASHTO
    )

from pydantic import BaseModel, Field, StrictFloat
from typing import Literal
import json

# --------------------------------------------------
# Material Type – Steel Reinforcement
# --------------------------------------------------

class MaterialType_SteelReinforcement(MaterialType):
    provided_value: MaterialTypeParaModel = MaterialTypeParaModel.REINFORCEMENT


# --------------------------------------------------
# Fixed Speckle Type Parameter
# --------------------------------------------------

class BridgeSpeckleType_BDA_ReinforcementMaterial(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Reinforcement_Material_AASHTO"
    ] = "Objects.Data.DataObject:BDA_Reinforcement_Material_AASHTO"


# --------------------------------------------------
# Parameter Containers (Schema‑Strict)
# --------------------------------------------------

class GeneralMaterialParameters_SteelReinforcement_AASHTO(GeneralMaterialParameters_AASHTO):
    material_type: MaterialType_SteelReinforcement = Field(alias="Material Type")




# --------------------------------------------------
# Parameter Groups (Semantic)
# --------------------------------------------------

class GeneralMaterialPropertiesParameterGroup_SteelReinforcement_AASHTO(ParameterGroup):
    name: Literal["General Material Properties"] = "General Material Properties"
    description: Literal[
        "General material properties"
    ] = "General material properties"

    group_parameters: GeneralMaterialParameters_SteelReinforcement_AASHTO


class SteelReinforcementMaterialPropertiesParameterGroup_AASHTO(ParameterGroup):
    name: Literal["Steel Material Properties"] = "Steel Material Properties"
    description: Literal[
        "Steel material properties"
    ] = "Steel material properties"

    group_parameters: SteelMaterialParameters_AASHTO


# --------------------------------------------------
# DataObject Properties (Contract Boundary)
# --------------------------------------------------

class MaterialDataObject_Properties_SteelReinforcement_AASHTO(BridgeDataObjectProperties):
    bda_speckle_type: BridgeSpeckleType_BDA_ReinforcementMaterial

    general_material_properties: GeneralMaterialPropertiesParameterGroup_SteelReinforcement_AASHTO = Field(
        alias="General Material Properties"
    )
    steel_material_properties: SteelReinforcementMaterialPropertiesParameterGroup_AASHTO = Field(
        alias="Design Material Properties"
    )


# --------------------------------------------------
# Debug / Schema Output
# --------------------------------------------------

if __name__ == "__main__":
    schema = MaterialDataObject_Properties_SteelReinforcement_AASHTO.model_json_schema()
    print(json.dumps(schema, indent=2))
