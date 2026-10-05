from bda.contracts.speckle_contracts.base_objects import BridgeCollection
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_DataObject import (
    BDA_ModelDataDataObject
)
from bda.contracts.speckle_contracts.bda_analytical.materials.materials_collection import (
    MaterialsCollection
)

from bda.contracts.speckle_contracts.bda_analytical.sections.section_collection import (
    SectionsCollection
)
from pydantic import Field, model_validator
from typing import Literal

from typing import Union, Annotated
import json


RootObjects = Annotated[
    Union[
        BDA_ModelDataDataObject,
        MaterialsCollection,
        SectionsCollection
    ],
    Field(discriminator="name"),
]


class ModelRootCollection(BridgeCollection):
    speckle_type: str
    name: Literal["Model Root"] = "Model Root"

    elements: list[RootObjects] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "maxItems": 3,
            "allOf": [
                # Materials (optional)
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "const": MaterialsCollection.model_fields[
                                    "name"
                                ].default
                            }
                        },
                        "required": ["name"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                # Config (REQUIRED)
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "const": BDA_ModelDataDataObject.model_fields[
                                    "name"
                                ].default
                            }
                        },
                        "required": ["name"],
                    },
                    "minContains": 1,  # ✅ required
                    "maxContains": 1,
                },
                # Sections (optional)
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "const": SectionsCollection.model_fields[
                                    "name"
                                ].default
                            }
                        },
                        "required": ["name"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
            ],
        },
    )

    @model_validator(mode="before")
    @classmethod
    def ensure_names(cls, values):
        for el in values.get("elements", []):
            if isinstance(el, dict) and "name" not in el:
                st = el.get("speckle_type", "")

                if "Material" in st:
                    el["name"] = "Materials"
                elif "Section" in st:
                    el["name"] = "Sections"
                elif "Model_Config" in st:
                    el["name"] = "Model Config"

        return values


if __name__ == "__main__":
    import json
    from pathlib import Path
    from bda.contracts.speckle_contracts.example_from_json import example_from_schema
    from bda.infrastructure.data_providers.speckle_helpers.speckle_send_object import ingest_ui_json_and_commit

    print("\n=== BDA Model Root Schema ===")

    # Generate schema
    model_root_collection_schema = ModelRootCollection.model_json_schema()

    # Pretty-print to terminal (may truncate in IDEs)
    print(json.dumps(model_root_collection_schema, indent=2))

    example = example_from_schema(model_root_collection_schema)

    print(json.dumps(example,indent=2))

    example_reponse_path = Path(
    "src/bda/contracts/speckle_contracts/bda_analytical/bda_example_model.json"
    )

    
    with example_reponse_path.open("r", encoding="utf-8") as f:
        ui_payload: dict = json.load(f)

    ingest_ui_json_and_commit(
        json_data=ui_payload,
        pydantic_model=ModelRootCollection,
        speckle_url="https://design.jacobs.com/projects/65752c2ae8/models/9c80c4bf6b"
    )