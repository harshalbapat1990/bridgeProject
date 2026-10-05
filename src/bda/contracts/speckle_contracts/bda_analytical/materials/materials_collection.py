from bda.contracts.paramodel.materials import MaterialBaseParaModel
from bda.contracts.speckle_contracts.base_objects import BridgeCollection

from pydantic import Field, field_validator
from typing import Literal

import json

from bda.contracts.speckle_contracts.bda_analytical.materials.material_types.material_types_aashto.materials_DataObjects_AASHTO import (
    GeneralMaterialDataObject_AASHTO,
    ConcreteMaterialDataObject_AASHTO,
    SteelMaterialDataObject_AASHTO,
    TendonMaterialDataObject_AASHTO,
    SteelReinforcementMaterialDataObject_AASHTO
)

from typing import Union, Annotated


Material_AASHTO = Annotated[
    Union[
        GeneralMaterialDataObject_AASHTO,
        ConcreteMaterialDataObject_AASHTO,
        SteelMaterialDataObject_AASHTO,
        TendonMaterialDataObject_AASHTO,
        SteelReinforcementMaterialDataObject_AASHTO
    ],
    Field(discriminator="speckle_type"),
]


class MaterialsCollection(BridgeCollection):
    name: Literal["Materials"] = "Materials"
    elements: list[Material_AASHTO] = Field(default_factory=list)  # type: ignore[reportIncompatibleVariableOverride]


if __name__ == "__main__":
    # Example usage
    print("\n=== General Material Dataobject json schema ===")
    material_collection_schema = MaterialsCollection.model_json_schema()
    print(json.dumps(material_collection_schema, indent=2))