from pydantic import BaseModel, TypeAdapter
from typing import Type

def make_received_model_recursive(model: Type[BaseModel]) -> BaseModel:
    "Given a Pydantic model, create a new version of that model (and all nested models) which allows extra fields. This is used to allow Speckle's additional metadata fields to be present without breaking validation."
    
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