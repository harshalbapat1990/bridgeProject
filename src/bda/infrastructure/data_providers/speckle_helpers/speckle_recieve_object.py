from pydantic import BaseModel, BaseModel, TypeAdapter, ValidationError
from typing import Type, Dict
from specklepy.core.api import operations
from specklepy.objects import Base
import json

def hydrate_speckle_types(obj):
    """
    Recursively traverse a Speckle JSON-like structure and fix
    speckle_type values for DataObjects.

    Replaces:
        "speckle_type": "Objects.Data.DataObject"
    with:
        properties["bda_speckle_type"]["provided_value"]
    """

    if isinstance(obj, dict):

        # ✅ Check if this is a DataObject needing correction
        if obj.get("speckle_type") == "Objects.Data.DataObject":
            props = obj.get("properties", {})
            bda = props.get("bda_speckle_type")

            if isinstance(bda, dict):
                provided = bda.get("provided_value")

                if isinstance(provided, str):
                    obj["speckle_type"] = provided

        # ✅ Recurse into all dictionary values
        for value in obj.values():
            hydrate_speckle_types(value)

    elif isinstance(obj, list):
        for item in obj:
            hydrate_speckle_types(item)

def strip_speckle_metadata(obj):
    """
    Remove known Speckle-added fields that break strict schemas.
    """

    if isinstance(obj, dict):
        # ✅ Remove known Speckle fields
        obj.pop("totalChildrenCount", None)
        obj.pop("bbox", None)  # optional
        obj.pop("units", None)  # optional

        for v in obj.values():
            strip_speckle_metadata(v)

    elif isinstance(obj, list):
        for item in obj:
            strip_speckle_metadata(item)

def make_received_model_recursive(model: Type[BaseModel]) -> Type[BaseModel]:
    
    base_config = getattr(model, "model_config", {})
    new_config = {**base_config, "extra": "allow"}

    # patch nested fields
    annotations = getattr(model, "__annotations__", {})
    new_annotations = {}

    for name, field_type in annotations.items():
        try:
            if issubclass(field_type, BaseModel):
                new_annotations[name] = make_received_model_recursive(field_type)
            else:
                new_annotations[name] = field_type
        except TypeError:
            new_annotations[name] = field_type

    received_model = type(
        f"{model.__name__}Received",
        (model,),
        {
            "__annotations__": new_annotations,
            "model_config": new_config,
        },
    )

    return received_model

def normalise_received_object(obj: Base,schema: Type[BaseModel]) -> BaseModel:
    """
    Normalise the received object to ensure all Speckle types are properly hydrated.
    This is a workaround for cases where the initial hydration might miss nested objects.
    """
    ReceivedModel = make_received_model_recursive(schema)
    data_str = operations.serialize(obj)
    data = json.loads(data_str)
    hydrate_speckle_types(data)
    strip_speckle_metadata(data)
    adapter = TypeAdapter(ReceivedModel)

    parsed = adapter.validate_python(data)
    return parsed


if __name__ == "__main__":
    from pathlib import Path
    from bda.infrastructure.data_providers.speckle_helpers.speckle_connector import BridgeDataPlatformSpeckleConnector
    from bda.contracts.speckle_contracts.bda_analytical.model_root import ModelRootCollection

    PROJECT_ID = "c05550b96c"
    MODEL_ID = "a100464ad3"
    VERSION_ID = "13587dee72"
    model = ModelRootCollection

    

    speckle_connector = BridgeDataPlatformSpeckleConnector()
    speckle_connector.select_project(PROJECT_ID)
    speckle_connector.select_model(MODEL_ID)

    received_object = speckle_connector.read_version_object(
        project_id=PROJECT_ID,
        model_id=MODEL_ID,
        version_id=VERSION_ID
    )

    parsed = normalise_received_object(received_object, model)
    print(parsed)

    


