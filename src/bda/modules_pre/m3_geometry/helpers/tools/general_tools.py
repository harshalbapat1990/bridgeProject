from typing import List, Iterable, TypeVar

from pint.registry import Quantity

from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import SpacingType
from bda.modules_pre.m3_geometry.helpers.tools.models.applied_vector import AppliedVector
from bda.modules_pre.m3_geometry.helpers.tools.models.point import Point
from bda.modules_pre.m3_geometry.helpers.tools.models.vector import Vector

TClose = TypeVar("TClose", float, Quantity)


def element_to_applied_vector(element: Element1D) -> AppliedVector:
    start_point = Point(element.node_start.X, element.node_start.Y, element.node_start.Z)
    end_point = Point(element.node_end.X, element.node_end.Y, element.node_end.Z)
    return AppliedVector(start_point, vector=Vector.from_points(start_point, end_point))


def resolve_spacing(spacing_type: SpacingType,
                    spacing_values: List[Quantity],
                    number_of_elements: int) -> List[Quantity]:
    match spacing_type:
        case SpacingType.VARIABLE:
            if len(spacing_values) != number_of_elements - 1:
                raise ValueError(f"Spacing type {spacing_type.value} requires the number of spacing values "
                                 f"to be equal to the number of elements minus one")
            return spacing_values
        case SpacingType.UNIFORM:
            if not spacing_values:
                raise ValueError("Uniform spacing requires at least one spacing value.")
            return [spacing_values[0]] * (number_of_elements - 1)
        case _:
            raise ValueError(f"Unsupported spacing type: {spacing_type}")


def is_close(a: TClose, b: TClose, tol: TClose) -> bool:
    """Compare two values with tolerance using strict same-type arguments.

    Notes
    -----
    - All three arguments must be of the same runtime type.
    - With static type checking enabled (e.g. Pyright/Mypy), the generic
      signature also helps catch mixed argument types before runtime.

    Raises
    ------
    TypeError
        If ``a``, ``b`` and ``tol`` do not share the same runtime type.
    """
    if not (type(a) is type(b) is type(tol)):
        raise TypeError(
            "is_close expects all arguments to have the same type "
            f"(got {type(a).__name__}, {type(b).__name__}, {type(tol).__name__})."
        )
    return abs(a - b) <= tol


def to_sorted_unique_collection(values: Iterable[Quantity], tolerance: Quantity) -> Iterable[Quantity]:
    sort_key = lambda p: p.to_base_units().magnitude

    sorted_values = sorted(set(values), key=sort_key)

    unique_values = []

    for i, value in enumerate(sorted_values):
        if i == 0:
            unique_values.append(value)
            continue
        if not is_close(value,
                        sorted_values[i - 1],
                        tolerance):
            unique_values.append(value)

    return unique_values