from __future__ import annotations
from bda.contracts.speckle_contracts.base_objects import Parameter, BridgeDataObject, ParameterGroup, Geometry
from bda.contracts.speckle_contracts.bda_analytical.materials.materials_DataObject_base import (
    GeneralMaterialDataObject
)

from bda.contracts.speckle_contracts.bda_analytical.materials.material_types.material_types_aashto.general_material_properties_AASHTO import (
    GeneralMaterialDataObject_Properties_AASHTO
)

from bda.contracts.speckle_contracts.bda_analytical.materials.material_types.material_types_aashto.concrete_material_parameters_AASHTO import (
    MaterialDataObject_Properties_Concrete_AASHTO
)
from bda.contracts.speckle_contracts.bda_analytical.materials.material_types.material_types_aashto.steel_material_parameters import (
    MaterialDataObject_Properties_Steel_AASHTO
)
from bda.contracts.speckle_contracts.bda_analytical.materials.material_types.material_types_aashto.tendon_material_parameters import (
    MaterialDataObject_Properties_Tendon_AASHTO
)

from bda.contracts.speckle_contracts.bda_analytical.materials.material_types.material_types_aashto.reinforcement_material_parameters import (
    MaterialDataObject_Properties_SteelReinforcement_AASHTO
)


from bda.contracts.speckle_contracts.bda_analytical.materials.material_types.material_types_aashto.general_material_properties_AASHTO import GeneralMaterialParameterGroup_AASHTO
from typing import Annotated, Literal, Union, Optional, Any
from pydantic import Field, BaseModel
import json


class GeneralMaterialDataObject_AASHTO(GeneralMaterialDataObject):
    speckle_type: Literal["Objects.Data.DataObject:BDA_General_Material_AASHTO"] = Field("Objects.Data.DataObject:BDA_General_Material_AASHTO", frozen=True)
    properties: GeneralMaterialDataObject_Properties_AASHTO

class ConcreteMaterialDataObject_AASHTO(GeneralMaterialDataObject):
    speckle_type: Literal["Objects.Data.DataObject:BDA_Concrete_Material_AASHTO"] = Field("Objects.Data.DataObject:BDA_Concrete_Material_AASHTO", frozen=True)
    properties: MaterialDataObject_Properties_Concrete_AASHTO

class SteelMaterialDataObject_AASHTO(GeneralMaterialDataObject):
    speckle_type: Literal["Objects.Data.DataObject:BDA_Steel_Material_AASHTO"] = Field("Objects.Data.DataObject:BDA_Steel_Material_AASHTO", frozen=True)
    properties: MaterialDataObject_Properties_Steel_AASHTO

class TendonMaterialDataObject_AASHTO(GeneralMaterialDataObject):
    speckle_type: Literal["Objects.Data.DataObject:BDA_Tendon_Material_AASHTO"] = Field("Objects.Data.DataObject:BDA_Tendon_Material_AASHTO", frozen=True)
    properties: MaterialDataObject_Properties_Tendon_AASHTO

class SteelReinforcementMaterialDataObject_AASHTO(GeneralMaterialDataObject):
    speckle_type: Literal["Objects.Data.DataObject:BDA_Reinforcement_Material_AASHTO"] = Field("Objects.Data.DataObject:BDA_Reinforcement_Material_AASHTO", frozen=True)
    properties: MaterialDataObject_Properties_SteelReinforcement_AASHTO


if __name__ == "__main__":
    # Example usage
    print("\n=== General Material Dataobject json schema ===")
    general_material_DataObject_schema = GeneralMaterialDataObject.model_json_schema()
    print(json.dumps(general_material_DataObject_schema, indent=2)) 

    print("\n=== Concrete Material Dataobject json schema ===")
    concrete_material_DataObject_schema = ConcreteMaterialDataObject_AASHTO.model_json_schema()
    print(json.dumps(concrete_material_DataObject_schema, indent=2)) 

    print("\n=== Steel Material Dataobject json schema ===")
    steel_material_DataObject_schema = SteelMaterialDataObject_AASHTO.model_json_schema()
    print(json.dumps(steel_material_DataObject_schema, indent=2)) 

    print("\n=== Tendon Material Dataobject json schema ===")
    tendon_material_DataObject_schema = TendonMaterialDataObject_AASHTO.model_json_schema()
    print(json.dumps(steel_material_DataObject_schema, indent=2)) 

    print("\n=== Steel Reinforment Material Dataobject json schema ===")
    tendon_material_DataObject_schema = SteelReinforcementMaterialDataObject_AASHTO.model_json_schema()
    print(json.dumps(steel_material_DataObject_schema, indent=2)) 