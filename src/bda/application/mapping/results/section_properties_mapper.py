"""Mapper: SectionPropertiesResultModel → SectionProperties domain object.

Software-agnostic. Both Midas and CSI Bridge fetchers produce the same
`SectionPropertiesResultModel` DTO; this single mapper handles both.
"""
from __future__ import annotations

from bda.contracts.result_models.section_properties_result_model import SectionPropertiesResultModel
from bda.domain.results.section_properties import SectionProperties
from bda.infrastructure.utils import CANONICAL_UNIT_SYSTEM, Q_, ureg

_m2 = ureg.meter ** 2
_m4 = ureg.meter ** 4
_m  = ureg.meter


class SectionPropertiesMapper:
    """Convert `SectionPropertiesResultModel` → `SectionProperties`."""

    @staticmethod
    def to_domain(rm: SectionPropertiesResultModel) -> SectionProperties:
        """Apply SI units and return a `SectionProperties` value object.

        Asserts that `rm.unit_system` equals ``CANONICAL_UNIT_SYSTEM``
        before wrapping values in Pint quantities.

        Raises:
            AssertionError: If the result model was built under a
                non-canonical unit system.
        """
        assert rm.unit_system == CANONICAL_UNIT_SYSTEM, (
            f"SectionPropertiesResultModel unit_system must be {CANONICAL_UNIT_SYSTEM!r}, "
            f"got {rm.unit_system!r}. Ensure the fetcher requests canonical units "
            "from the FEM API."
        )
        return SectionProperties(
            name=rm.section_name,
            area=Q_(rm.area, _m2),
            shear_area_y=Q_(rm.shear_area_y, _m2),
            shear_area_z=Q_(rm.shear_area_z, _m2),
            torsional_inertia=Q_(rm.torsional_inertia, _m4),
            moment_inertia_y=Q_(rm.moment_inertia_y, _m4),
            moment_inertia_z=Q_(rm.moment_inertia_z, _m4),
            czp=Q_(rm.czp, _m),
            czm=Q_(rm.czm, _m),
            cyp=Q_(rm.cyp, _m),
            cym=Q_(rm.cym, _m),
        )

    @staticmethod
    def to_domain_dict(
        result_models: list[SectionPropertiesResultModel],
    ) -> dict[str, SectionProperties]:
        """Convert a list of result models to a name-keyed dict.

        Convenience wrapper for the common case where the caller needs
        to look up properties by section name.
        """
        return {
            rm.section_name: SectionPropertiesMapper.to_domain(rm)
            for rm in result_models
        }
