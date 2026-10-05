from dataclasses import fields
from typing import get_origin, get_args
from collections.abc import Iterable, Mapping
from pint import Quantity


def _validate_quantity(
    value: Quantity,
    dimension: str,
    field_name: str
) -> None:
    """Validate single pint.Quantity against expected dimensionality."""
    if not value.check(dimension):
        raise TypeError(
            f"Field '{field_name}' must have dimension {dimension}, "
            f"got {value:~P}"
        )


def validate_pint_fields(instance) -> None:
    """
    Validate all pint.Quantity fields in a dataclass instance.

    Supported:
    - Quantity
    - list[Quantity] / tuple[Quantity]
    - dict[Any, Quantity]

    Dimensionality is read from Annotated[..., '<dimension>'].
    """
    for field_def in fields(instance):
        field_name = field_def.name
        value = getattr(instance, field_name)

        if value is None:
            continue

        annotation = field_def.type
        origin = get_origin(annotation)

        # --- operate only on Annotated[...] ---
        if origin is None or origin.__name__ != "Annotated":
            continue

        base_type, *metadata = get_args(annotation)

        # Extract dimension string like "[pressure]"
        dimension = next(
            (m for m in metadata if isinstance(m, str) and m.startswith("[")),
            None
        )

        if dimension is None:
            continue

        # --- single Quantity ---
        if isinstance(value, Quantity):
            _validate_quantity(value, dimension, field_name)

        # --- list / tuple of Quantities ---
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
            for idx, item in enumerate(value):
                if not isinstance(item, Quantity):
                    continue
                _validate_quantity(item, dimension, f"{field_name}[{idx}]")

        # --- dict of Quantities ---
        elif isinstance(value, Mapping):
            for key, item in value.items():
                if not isinstance(item, Quantity):
                    continue
                _validate_quantity(item, dimension, f"{field_name}[{key}]")