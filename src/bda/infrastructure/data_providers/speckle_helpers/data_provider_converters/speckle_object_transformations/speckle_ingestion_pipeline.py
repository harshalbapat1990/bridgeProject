from .normalise_speckle import fix_speckle_types
from .santise_speckle import strip_speckle_metadata
from specklepy.objects import Base
from specklepy.api import operations
import json
from pydantic import BaseModel, TypeAdapter
from bda.contracts.speckle_contracts.ingestion_schemas import make_received_model_recursive
from typing import Type

def canonicalise_speckle_payload(speckle_obj: Base) -> dict:
    data_str = operations.serialize(speckle_obj)
    data = json.loads(data_str)
    # print("Original Speckle payload:", json.dumps(data, indent=2)) TODO Implement logging instead of print statements
    fix_speckle_types(data)
    # print("After fixing speckle types:", json.dumps(data, indent=2)) TODO Implement logging instead of print statements
    strip_speckle_metadata(data)
    # print("After stripping metadata:", json.dumps(data, indent=2)) TODO Implement logging instead of print statements
    return data


def validate_speckle_payload(data: Base, schema: Type[BaseModel]) -> BaseModel:
    ReceivedModel = make_received_model_recursive(schema)
    canonical_data = canonicalise_speckle_payload(data)
    adapter = TypeAdapter(ReceivedModel)

    parsed = adapter.validate_python(canonical_data)
    return parsed