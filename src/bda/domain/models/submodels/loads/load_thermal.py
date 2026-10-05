from abc import ABC
from dataclasses import dataclass, field
from typing import Annotated

from pint.registry import Quantity

from bda.domain import units
from bda.domain.enums import LoadType, LoadTargetType, OffsetReference
from bda.domain.models.submodels.loads.load_base import LoadBase
from bda.domain.models.submodels.section_base import Offset
from bda.domain.units.quantities import Length


@dataclass(kw_only=True, repr=False, eq=False)
class ThermalLoadElementBase(LoadBase, ABC):
    """Base class for thermal loads."""
    thermal_load: ThermalLoadUniform | ThermalLoadGradient


@dataclass(kw_only=True, repr=False, eq=False)
class ThermalLoadUniform:
    """Represents a uniform temperature change over the entire cross-section of a member."""
    temperature_change: Annotated[Quantity, "[temperature]"]


@dataclass(kw_only=True, repr=False, eq=False)
class ThermalLoadGradient:
    """
    Represents a non-uniform temperature distribution across a member cross-section.
    The temperature profile is defined by a collection of
    gradient definitions, each specifying a temperature value
    at a given cross-sectional location.
    """
    gradient_definitions: list[GradientDefinition] = field(default_factory=list)

    def get_horizontal(self, reverse: bool = False) -> list[GradientDefinition]:
        """
        Gradient definitions sorted by horizontal offset.

        Returns
        -------
        list[GradientDefinition]
            Gradient definitions ordered by increasing
            horizontal offset from the reference location.
        """
        return sorted(self.gradient_definitions,
                      key= lambda g: g.offset.horizontal_value,
                      reverse= reverse
                      )
    def get_vertical(self, reverse: bool = True) -> list[GradientDefinition]:
        """
        Gradient definitions sorted by vertical offset.

        Returns
        -------
        list[GradientDefinition]
            Gradient definitions ordered by increasing
            vertical offset from the reference location.
        """
        v_sorted = sorted(self.gradient_definitions,
                      key= lambda g: g.offset.vertical_value,
                      reverse= reverse
                      )

        return v_sorted

    def get_vertical_profile(self, reverse: bool = True):
        """
        Returns the vertical temperature profile as separate lists
        of vertical coordinates and corresponding temperature values.

        The profile is sorted by the vertical offset of each
        gradient definition relative to the specified offset
        reference.

        Parameters
        ----------
        reverse : bool, default=False
            If True, the profile is ordered from the largest to
            the smallest vertical coordinate.

        Returns
        -------
        tuple[list[Length], list[Quantity]]
            A tuple containing:

            - vertical coordinates,
            - corresponding temperature values.

        Notes
        -----
        The returned lists have matching indices, where each
        coordinate corresponds to the temperature value at the
        same position in the profile.

        Examples
        --------
        #>>> gradient = ThermalLoadGradient(...)
        #>>> z, t = gradient.get_vertical_profile()
        #>>> z
        [-0.5 m, 0.0 m, 0.5 m]

        #>>> t
        [10 Δ°C, 20 Δ°C, 30 Δ°C]
        """
        profile = self.get_vertical(reverse= reverse)
        z = [g.offset.vertical_value for g in profile]
        t = [g.value for g in profile]

        return z, t

    def get_horizontal_profile(self, reverse: bool = False):
        """
        Returns the horizontal temperature profile as separate lists
        of horizontal coordinates and corresponding temperature values.

        The profile is sorted by the horizontal offset of each
        gradient definition relative to the specified offset
        reference.

        Parameters
        ----------
        reverse : bool, default=False
            If True, the profile is ordered from the largest to
            the smallest horizontal coordinate.

        Returns
        -------
        tuple[list[Length], list[Quantity]]
            A tuple containing:

            - horizontal coordinates,
            - corresponding temperature values.

        Notes
        -----
        The returned lists have matching indices, where each
        coordinate corresponds to the temperature value at the
        same position in the profile.

        Examples
        --------
        #>>> gradient = ThermalLoadGradient(...)
        #>>> x, t = gradient.get_horizontal_profile()
        #>>> x
        [-1.0 m, 0.0 m, 1.0 m]

        #>>> t
        [10 Δ°C, 35 Δ°C, 15 Δ°C]
        """
        profile = self.get_horizontal(reverse= reverse)
        x = [g.offset.horizontal_value for g in profile]
        t = [g.value for g in profile]

        return x, t


@dataclass(kw_only=True, repr=False, eq=False)
class GradientDefinition:
    """
    Defines a temperature value at a specific location
    within a cross-section.
    Multiple gradient definitions may be combined to
    describe a thermal gradient or an arbitrary temperature
    distribution over the cross-section.
    """
    offset: Offset
    value: Annotated[Quantity, "[temperature]"]

if __name__ == "__main__":

    ref = OffsetReference.CENTER_TOP

    vertical_gradient = ThermalLoadGradient(
        gradient_definitions=[
            GradientDefinition(
                offset=Offset(vertical_value= 0.50 * units.ureg.meter, offset_reference= ref),
                value=10 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(vertical_value= 0.25 * units.ureg.meter, offset_reference= ref),
                value=15 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(vertical_value= 0.00 * units.ureg.meter, offset_reference= ref),
                value=30 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(vertical_value= -0.25 * units.ureg.meter, offset_reference= ref),
                value=25 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(vertical_value= -0.50 * units.ureg.meter, offset_reference= ref),
                value=20 * units.ureg.delta_degC,
            ),
        ]
    )

    horizontal_gradient = ThermalLoadGradient(
        gradient_definitions=[
            GradientDefinition(
                offset=Offset(
                    horizontal_value=-1.00 * units.ureg.meter,
                    offset_reference=OffsetReference.CENTER_CENTER,
                ),
                value=10 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(
                    horizontal_value=-0.50 * units.ureg.meter,
                    offset_reference=OffsetReference.CENTER_CENTER,
                ),
                value=18 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(
                    horizontal_value=0.00 * units.ureg.meter,
                    offset_reference=OffsetReference.CENTER_CENTER,
                ),
                value=35 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(
                    horizontal_value=0.50 * units.ureg.meter,
                    offset_reference=OffsetReference.CENTER_CENTER,
                ),
                value=22 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(
                    horizontal_value=1.00 * units.ureg.meter,
                    offset_reference=OffsetReference.CENTER_CENTER,
                ),
                value=15 * units.ureg.delta_degC,
            ),
        ]
    )

    print(vertical_gradient.get_vertical_profile())
    print(horizontal_gradient.get_horizontal_profile())