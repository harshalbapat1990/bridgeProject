# This file contains the base object structure used for all of the speckle schema contracts
from __future__ import annotations

import re
from enum import Enum
from typing import Any, ClassVar, Generic, TypeAlias, TypeVar, Union, Optional, Annotated, Iterable
from uuid import UUID, uuid4

from typing_extensions import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

T = TypeVar("T")

from collections.abc import Sequence
from pydantic import model_validator


# -------------------------
# Recursive JSON value type
# -------------------------
JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonPrimitive | list["JsonValue"] | dict

#--------------------------
# Parameter Objects
# -------------------------

from typing import Any, Union, get_args, get_origin
from types import UnionType

from pydantic import BaseModel


def validate_parameter_tree(
    value: Any,
    path: list[str] | None = None,
) -> None:
    path = path or ["root"]

    def fmt_path() -> str:
        return " -> ".join(path)

    def fail(v: Any, reason: str = "") -> None:
        raise TypeError(
            f"Invalid value in parameter tree\n"
            f"Path: {fmt_path()}\n"
            f"Type: {type(v).__name__}\n"
            f"Value: {repr(v)}\n"
            f"{reason}\n"
            f"Expected Parameter or ParameterGroup "
            f"(directly or indirectly)."
        )

    def allows_none(annotation: Any) -> bool:
        if annotation is None:
            return False

        origin = get_origin(annotation)

        # Optional[T] / Union[T, None]
        if origin is Union:
            return type(None) in get_args(annotation)

        # T | None (Python 3.10+)
        if origin is UnionType:
            return type(None) in get_args(annotation)

        return False

    if value is None:
        fail(
            value,
            "Encountered None. Likely a missing or null field in payload.",
        )

    if isinstance(value, Parameter):
        return

    if isinstance(value, ParameterGroup):
        validate_parameter_tree(
            value.group_parameters,
            path + ["group_parameters"],
        )
        return

    if isinstance(value, dict):
        for k, v in value.items():
            validate_parameter_tree(
                v,
                path + [str(k)],
            )
        return

    if isinstance(value, BaseModel):
        model_fields = value.__class__.model_fields

        for k, v in value.__dict__.items():
            if k.startswith("_"):
                continue

            field_info = model_fields.get(k)

            path_name = (
                field_info.alias
                if field_info is not None
                and field_info.alias is not None
                else k
            )

            # Allow None only when the field annotation explicitly supports it
            if v is None:
                if (
                    field_info is not None
                    and allows_none(field_info.annotation)
                ):
                    continue

                fail(
                    v,
                    "Encountered None for non-optional field.",
                )

            validate_parameter_tree(
                v,
                path + [str(path_name)],
            )

        model_extra = getattr(value, "model_extra", None) or {}

        for k, v in model_extra.items():
            validate_parameter_tree(
                v,
                path + [str(k)],
            )

        return

    fail(value)

def iter_bridges_objects(root: Any) -> Iterable["BridgesBase"]:
    """
    Recursively yield all BridgesBase-derived objects
    from a collection tree.
    """
    if isinstance(root, BridgesBase):
        yield root

    if isinstance(root, BridgeCollection):
        for element in root.elements:
            yield from iter_bridges_objects(element)



#--------------------------
# Parameter Objects
# -------------------------

class Parameter(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str
    isUser: bool
    provided_value: T

    description: str | None = None
    symbol: str | None = None

    provided_unit: str | None = None
    base_unit: str | None = None
    base_value: T | None = None

    @model_validator(mode="after")
    def _validate_units_and_base_value(self) -> "Parameter[T]":
        pu, bu, bv = self.provided_unit, self.base_unit, self.base_value

        unitless = (pu is None and bu is None)
        unit_defined = (isinstance(pu, str) and isinstance(bu, str))

        if not (unitless or unit_defined):
            raise ValueError("Units must be either both None or both strings.")

        if unitless and bv is not None:
            raise ValueError("Unitless parameters must not define base_value.")

        if unit_defined and bv is None:
            raise ValueError("Unit-defined parameters must include base_value.")

        return self

    


class UnitlessParameter(Parameter[T], Generic[T]):
    provided_unit: None = None
    base_unit: None = None
    base_value: None = None


class EnumParameter(UnitlessParameter[T], Generic[T]):
    """Parameter for enum values with case-insensitive matching.
    
    Automatically normalizes string inputs to lowercase before validation,
    enabling case-insensitive enum matching for all enum-based parameters.
    """
    
    @field_validator('provided_value', mode='before')
    @classmethod
    def normalize_enum_value(cls, v):
        """Normalize string enum values to match case-insensitively.
        
        For enum types, finds the matching enum member by comparing
        lowercase versions of the input and enum values.
        """
        if not isinstance(v, str):
            return v
        
        # Get the annotation for provided_value
        annotation = cls.model_fields.get('provided_value')
        if annotation is None:
            return v.lower()
        
        # Try to find the annotation type
        field_type = annotation.annotation
        if hasattr(field_type, '__origin__'):  # Handle Optional, Union, etc.
            field_type = field_type.__args__[0] if field_type.__args__ else field_type
        
        # If it's an Enum type, find matching member case-insensitively
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            v_lower = v.lower()
            for member in field_type:
                if member.value.lower() == v_lower:
                    return member.value
        
        return v.lower()

UnitValue = (
    float
    | list[float]
    | tuple[float, ...]
)

UnitT = TypeVar("UnitT", bound=UnitValue)



# General Minimum Property
class DataObjectSpeckleType(UnitlessParameter[str]):
    name: Literal["DataObject Speckle Type"] = "DataObject Speckle Type"
    description: Literal["Entity speckle type used for creation. This is used for round tripping of objects and persistance of custom speckle object variants that are not persisted in deserialisation of objects"] =\
        "Entity speckle type used for creation. This is used for round tripping of objects and persistance of custom speckle object variants that are not persisted in deserialisation of objects"
    symbol: str | None = None
    isUser: bool = False


GroupItem = Union["Parameter[Any]", "ParameterGroup"]


class ParameterGroup(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str
    isUser: bool
    description: str | None = None

    group_parameters: dict[str, GroupItem] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_group_parameters(self) -> "ParameterGroup":
        validate_parameter_tree(self.group_parameters)
        return self




# -------------------------
# Generic Data Object Base
# -------------------------


PropertyValue = Union["Parameter[Any]", "ParameterGroup"]


class BridgesBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    id: Optional[str] = Field(
        default=None,
        description="Backend-assigned identifier. Must be null in input payloads.",
        json_schema_extra={
            "type": ["null"]
        },
    )

    applicationId: str = Field(
        description=(
            "Application-defined identifier. Must contain one or more uppercase letters, digits, or hyphens."
        ),
        json_schema_extra={
            "type": ["string", "null"]
        },
    )

    @field_validator("id", mode="before")
    @classmethod
    def validate_uuid_string(cls, v):
        if v is None:
            return v

        # Accept UUID objects
        if isinstance(v, UUID):
            return str(v)

        # Validate UUID strings
        UUID(str(v))
        return str(v)

    @model_validator(mode="after")
    def _assign_backend_id(self) -> "BridgesBase":
        if self.id is None:
            object.__setattr__(self, "id", str(uuid4()))
        return self

    """Validates applicationId by trimming whitespace and ensuring a non-empty value."""
    APPLICATION_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^[A-Z0-9-]+$"
    )

    @field_validator("applicationId")
    @classmethod
    def validate_application_id_not_empty(
        cls,
        value: str,
    ):

        value = value.strip()

        if not value:
            raise ValueError(
                "applicationId cannot be empty"
            )

        return value

 #Geometry Objects
# -------------------------
class GeometryBase(BridgesBase):
    units: Literal["m", "mm", "ft", "in"] = "m"


class Point(GeometryBase):
    speckle_type: Literal["BDA.Point"] = Field("BDA.Point", frozen=True)
    x: float
    y: float
    z: float


class Line(GeometryBase):
    speckle_type: Literal["BDA.Line"] = Field("BDA.Line", frozen=True)
    start: Point
    end: Point


class Mesh(GeometryBase):
    speckle_type: Literal["BDA.Mesh"] = Field("BDA.Mesh", frozen=True)
    vertices: list[float]
    faces: list[int]  # typically int-encoded topology

Geometry = Annotated[Union[Point, Line, Mesh], Field(discriminator="speckle_type")]


# -------------------------
# Data Object + Collection
# -------------------------

class BridgeDataObjectProperties(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=True)

    @model_validator(mode="after")
    def _validate_properties_tree(self) -> "BridgeDataObjectProperties":
        validate_parameter_tree(self.__dict__)
        return self


DATA_OBJECT_PREFIX = "Objects.Data.DataObject"
DATA_OBJECT_PATTERN = re.compile(
    r"^Objects\.Data\.DataObject(:.+)?$"
)

class BridgeDataObject(BridgesBase):
    name: str
    speckle_type: str  # allow suffix, validated below

    # Mirrors `speckle_type` so the concrete data object type survives specklepy's
    # send/receive round trip, which silently collapses custom DataObject suffixes
    # back to the bare "Objects.Data.DataObject". Required (not defaulted) so it is
    # a mandatory constant in the generated JSON schema, matching `speckle_type`
    # itself: every concrete subclass must redeclare it as a matching Literal.
    bda_speckle_type: str = Field(
        ...,
        description="Entity speckle type used for creation. This is used for round tripping of objects and persistance of custom speckle object variants that are not persisted in deserialisation of objects",
    )

    properties: BridgeDataObjectProperties
    displayValue: list[Geometry] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_speckle_type_contract(self) -> "BridgeDataObject":
        # 1. Must begin with Objects.Data.DataObject (with optional suffix)
        for value, source in [
            (self.speckle_type, "BridgeDataObject.speckle_type"),
            (self.bda_speckle_type, "BridgeDataObject.bda_speckle_type"),
        ]:
            if not value or not DATA_OBJECT_PATTERN.match(value):
                raise ValueError(
                    f"{source} must start with "
                    f"'{DATA_OBJECT_PREFIX}' and may include "
                    f"an optional suffix after ':' "
                    f"(got '{value}')"
                )

        # 2. Must match exactly
        if self.speckle_type != self.bda_speckle_type:
            raise ValueError(
                "BridgeDataObject.speckle_type must match "
                "BridgeDataObject.bda_speckle_type "
                f"(got '{self.speckle_type}' vs '{self.bda_speckle_type}')"
            )

        return self


BridgeElement = Annotated[
    Union[
        "BridgeCollection",
        # ONLY concrete data objects go here
    ],
    Field(discriminator="bda_speckle_type"),
]

class BridgeCollection(BridgesBase):
    speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection"
    ] = Field(
        "Speckle.Core.Models.Collections.Collection",
        frozen=True #NOTE we should use this to ensure immutability across the geom group files, i am making the changes, so you can just review them if you agree or revert wherever you dont
    )

    # Mirrors `speckle_type` so the concrete collection type survives specklepy's
    # send/receive round trip, which silently collapses custom Collection suffixes
    # back to the bare "Speckle.Core.Models.Collections.Collection". Required (not
    # defaulted) so it is a mandatory constant in the generated JSON schema,
    # matching `speckle_type` itself: every concrete subclass must redeclare it as
    # a matching Literal.
    bda_speckle_type: str = Field(
        ...,
        description="Entity speckle type used for creation. This is used for round tripping of objects and persistance of custom speckle object variants that are not persisted in deserialisation of objects",
    )

    name: str
    elements: list[BridgeElement] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_bda_speckle_type(self) -> "BridgeCollection":
        if self.bda_speckle_type != self.speckle_type:
            raise ValueError(
                "BridgeCollection.bda_speckle_type must match speckle_type "
                f"(got '{self.bda_speckle_type}' vs '{self.speckle_type}')"
            )
        return self

    @model_validator(mode="after")
    def _validate_unique_application_ids(self) -> "BridgeCollection":
        seen: dict[str, UUID] = {}

        for obj in iter_bridges_objects(self):
            app_id = obj.applicationId

            if app_id is None:
                continue

            if app_id in seen:
                raise ValueError(
                    "Duplicate applicationId detected.\n"
                    f"applicationId: '{app_id}'\n"
                    f"First object id: {seen[app_id]}\n"
                    f"Duplicate object id: {obj.id}"
                )

            seen[app_id] = obj.id

        return self



if __name__ == "__main__":
    import json
    from pathlib import Path

    # Import the example generator
    from bda.contracts.speckle_contracts.example_from_json import example_from_schema

    print("\n=== BridgeCollection Base Schema ===")

    # ------------------------------------------------------------------
    # Ensure models are fully resolved
    # (important for forward refs + discriminated unions)
    # ------------------------------------------------------------------
    BridgeCollection.model_rebuild()

    # ------------------------------------------------------------------
    # Generate schema
    # ------------------------------------------------------------------
    schema = BridgeCollection.model_json_schema()

    # Pretty-print to terminal (may truncate in some IDEs)
    print(json.dumps(schema, indent=2))

    # ------------------------------------------------------------------
    # Generate example JSON payload from schema
    # ------------------------------------------------------------------
    example = example_from_schema(schema)

    print("\n=== Example BridgeCollection JSON Payload ===")
    print(json.dumps(example, indent=2))
