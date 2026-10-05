from abc import ABC
from dataclasses import dataclass, field
from typing import List, cast

from openpyxl.worksheet import dimensions
from pint.registry import Quantity

from bda.domain.enums import SectionFamily, SectionType
from bda.domain.models.submodels.section_base import SectionBase, DimensionsBase
from bda.domain.units.quantities import Length


@dataclass
class Point2D:
    """A 2-D coordinate pair with physical length units."""
    x: Length
    y: Length


# ---------------------------------------------------------------------------
# PSC 1–2 cell sub-dimension dataclasses (vSIZE_PSC_A/B/C/D + Joint On/Off)
# ---------------------------------------------------------------------------

@dataclass
class JointsPSC:
    """Joint On/Off flags (indices 0-7): JO1-JO3 (outer), JI1-JI5 (inner)."""
    jo1: bool
    jo2: bool
    jo3: bool
    ji1: bool
    ji2: bool
    ji3: bool
    ji4: bool
    ji5: bool

    def to_list(self) -> List[bool]:
        return [self.jo1, self.jo2, self.jo3, self.ji1, self.ji2, self.ji3, self.ji4, self.ji5]


@dataclass
class OuterHeightHo:
    """Outer-Height parameters – vSIZE_PSC_A (indices 0-5)."""
    ho1: Length
    ho2: Length
    ho2_1: Length
    ho2_2: Length
    ho3: Length
    ho3_1: Length

    def to_list(self) -> List:
        return [self.ho1, self.ho2, self.ho2_1, self.ho2_2, self.ho3, self.ho3_1]

@dataclass
class OuterBreadthBo:
    """Outer-Breadth parameters – vSIZE_PSC_B (indices 1-6)."""
    bo1: Length
    bo1_1: Length
    bo1_2: Length
    bo2: Length
    bo2_1: Length
    bo3: Length

    def to_list(self) -> List:
        return [self.bo1, self.bo1_1, self.bo1_2, self.bo2, self.bo2_1, self.bo3]


@dataclass
class InnerHeightHi:
    """Inner-Height parameters – vSIZE_PSC_C (indices 0-9)."""
    hi1: Length
    hi2: Length
    hi2_1: Length
    hi2_2: Length
    hi3: Length
    hi3_1: Length
    hi4: Length
    hi4_1: Length
    hi4_2: Length  # index 8
    hi5: Length    # index 9

    def to_list(self) -> List:
        return [self.hi1, self.hi2, self.hi2_1, self.hi2_2, self.hi3,
                self.hi3_1, self.hi4, self.hi4_1, self.hi4_2, self.hi5]


@dataclass
class InnerBreadthBi:
    """Inner-Breadth parameters – vSIZE_PSC_D (indices 0-7).

    ``bi4`` is present only in the 2-cell (2CEL) configuration; leave as
    ``None`` for 1-cell sections.
    """
    bi1: Length
    bi1_1: Length
    bi1_2: Length
    bi2_1: Length
    bi3: Length
    bi3_1: Length
    bi3_2: Length
    bi4: Length = field(default=None) # applicable only for 2Cells type

    def to_list(self) -> List:
        return [self.bi1, self.bi1_1, self.bi1_2, self.bi2_1, self.bi3,
                self.bi3_1, self.bi3_2, self.bi4]


# ---------------------------------------------------------------------------
# PSC section models
# ---------------------------------------------------------------------------

@dataclass(kw_only=True, eq=False)
class SectionPSCBase(SectionBase, ABC):
    section_family: SectionFamily = field(default=SectionFamily.PSC, init=False)

@dataclass(kw_only=True, eq=False)
class SectionPSCValue(SectionPSCBase):
    section_type: SectionType = field(default=SectionType.PSC_VALUE, init=False)
    dimensions: DimensionsPSCValues


@dataclass
class DimensionsPSCValues(DimensionsBase):
    outer_outline: List[Point2D]
    inner_outlines: List[List[Point2D]]

    @property
    def total_height(self) -> Length:
        vertices = self.outer_outline
        y_values = [cast(Quantity, v.y).to_base_units() for v in vertices]
        return max(y_values, key=lambda q: q.magnitude) - min(y_values, key=lambda q: q.magnitude)

    @property
    def total_width(self) -> Length:
        """Return total width of section"""
        vertices = self.outer_outline
        x_values = [cast(Quantity, v.x).to_base_units() for v in vertices]
        return max(x_values, key=lambda q: q.magnitude) - min(x_values, key=lambda q: q.magnitude)

@dataclass(kw_only=True, eq=False)
class SectionPSC12Cell(SectionPSCBase):
    dimensions: DimensionsPSC12Cell


@dataclass
class DimensionsPSC12Cell(DimensionsBase):
    joints: JointsPSC
    outer_height_ho: OuterHeightHo
    outer_breadth_bo: OuterBreadthBo
    inner_height_hi: InnerHeightHi
    inner_breadth_bi: InnerBreadthBi

    @property
    def total_height(self) -> Length:
        """Return total height of section"""
        raise NotImplementedError

    @property
    def total_width(self) -> Length:
        """Return total width of section"""
        raise NotImplementedError