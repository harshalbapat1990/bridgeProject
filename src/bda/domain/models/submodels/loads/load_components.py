"""Value objects describing load magnitudes and offsets.

All quantity fields are declared as ``Annotated[Quantity, "<dimension>"]`` so
that ``MultiModelObjectBase.__post_init__`` validates their dimensionality.

NOTE: do not add ``from __future__ import annotations`` to modules in this
package. Postponed annotations turn ``Annotated[...]`` field types into
strings and silently disable ``validate_pint_fields`` dimension checks.
"""
from dataclasses import dataclass, field, fields
from typing import Annotated

from pint.registry import Quantity

from bda.domain.base import MultiModelObjectBase
from bda.domain.enums.load_enums import LocalAxis
from bda.domain.units.registry import N, m


def _zero_force() -> Quantity:
    return 0.0 * N


def _zero_moment() -> Quantity:
    return 0.0 * N * m


def _zero_force_per_length() -> Quantity:
    return 0.0 * N / m


def _zero_moment_per_length() -> Quantity:
    return 0.0 * N * m / m


@dataclass(kw_only=True)
class LoadOffset(MultiModelObjectBase):
    """Eccentricity of a load with respect to the element axis, expressed in
    the element's local coordinate system.

    Attributes:
        axis (LocalAxis): Local axis (``Y`` or ``Z``) along which the load is offset.
        value (Quantity [length]): Signed offset distance.
    """

    axis: LocalAxis
    value: Annotated[Quantity, "[length]"]

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.axis, LocalAxis):
            raise TypeError(f"axis must be a LocalAxis, got {type(self.axis).__name__}.")
        if not isinstance(self.value, Quantity):
            raise TypeError(f"value must be a pint Quantity of dimension [length], got {type(self.value).__name__}.")

    def __repr__(self) -> str:
        return f"LoadOffset(axis={self.axis.value}, value={self.value})"


@dataclass(kw_only=True)
class _LoadComponentsBase(MultiModelObjectBase):
    """Shared helpers for six-component load vectors expressed in the global axes."""

    def __post_init__(self) -> None:
        for f in fields(self):
            if not isinstance(getattr(self, f.name), Quantity):
                raise TypeError(
                    f"Field '{f.name}' must be a pint Quantity, got {type(getattr(self, f.name)).__name__}.")
        super().__post_init__()

    @property
    def is_zero(self) -> bool:
        """True when every component has zero magnitude."""
        return all(getattr(self, f.name).magnitude == 0 for f in fields(self))

    def __repr__(self) -> str:
        parts = ", ".join(f"{f.name}={getattr(self, f.name)}" for f in fields(self))
        return f"{self.__class__.__name__}({parts})"


@dataclass(kw_only=True, repr=False)
class PointLoadComponents(_LoadComponentsBase):
    """Concentrated load components in the global coordinate system.

    Forces are of dimension [force], moments of dimension [force]*[length].
    """

    Fx: Annotated[Quantity, "[force]"] = field(default_factory=_zero_force)
    Fy: Annotated[Quantity, "[force]"] = field(default_factory=_zero_force)
    Fz: Annotated[Quantity, "[force]"] = field(default_factory=_zero_force)
    Mx: Annotated[Quantity, "[force]*[length]"] = field(default_factory=_zero_moment)
    My: Annotated[Quantity, "[force]*[length]"] = field(default_factory=_zero_moment)
    Mz: Annotated[Quantity, "[force]*[length]"] = field(default_factory=_zero_moment)


@dataclass(kw_only=True, repr=False)
class LineLoadComponents(_LoadComponentsBase):
    """Distributed (per unit length) load components in the global coordinate system.

    Forces are of dimension [force]/[length], moments of dimension
    [force]*[length]/[length] (i.e. moment per unit length).
    """

    Fx: Annotated[Quantity, "[force]/[length]"] = field(default_factory=_zero_force_per_length)
    Fy: Annotated[Quantity, "[force]/[length]"] = field(default_factory=_zero_force_per_length)
    Fz: Annotated[Quantity, "[force]/[length]"] = field(default_factory=_zero_force_per_length)
    Mx: Annotated[Quantity, "[force]*[length]/[length]"] = field(default_factory=_zero_moment_per_length)
    My: Annotated[Quantity, "[force]*[length]/[length]"] = field(default_factory=_zero_moment_per_length)
    Mz: Annotated[Quantity, "[force]*[length]/[length]"] = field(default_factory=_zero_moment_per_length)
