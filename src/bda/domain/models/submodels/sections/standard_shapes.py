from abc import ABC
from dataclasses import dataclass, field

from bda.domain.enums import SectionFamily, SectionType
from bda.domain.models.submodels.section_base import DimensionsBase, SectionBase
from bda.domain.units.quantities import Length


@dataclass(kw_only=True, eq=False)
class SectionStandard(SectionBase, ABC):
    section_family: SectionFamily = field(default=SectionFamily.STANDARD_SHAPE, init=False)
    dimensions: DimensionsBase

@dataclass
class DimensionsAngle(DimensionsBase):
    height: Length
    width: Length
    thickness_web: Length
    thickness_flange: Length

    @property
    def total_height(self) -> Length:
        """Return total height of section"""
        return self.height

    @property
    def total_width(self) -> Length:
        """Return total width of section"""
        return self.width

@dataclass(kw_only=True, eq=False)
class SectionStandardAngle(SectionStandard):
    section_type: SectionType = field(default=SectionType.ANGLE, init=False)
    dimensions: DimensionsAngle

@dataclass
class DimensionsISection(DimensionsBase):
    total_height_h: Length
    top_flange_width_b1: Length
    bottom_flange_width_b2: Length
    bottom_flange_thickness_tf2: Length
    top_flange_thickness_tf1: Length
    web_thickness_tw: Length
    web_inner_radius_r1: Length
    flange_end_radius_r2: Length

    @property
    def total_height(self) -> Length:
        """Return total height of section"""
        return self.total_height_h

    @property
    def total_width(self) -> Length:
        """Return total width of section"""
        return max(
            self.top_flange_width_b1,
            self.bottom_flange_width_b2,
            self.web_thickness_tw,
            key=lambda x: x.to_base_units().magnitude,
        )

@dataclass(kw_only=True, eq=False)
class SectionStandardISection(SectionStandard):
    section_type: SectionType = field(default=SectionType.I_SECTION, init=False)
    dimensions: DimensionsISection

@dataclass
class DimensionsBox(DimensionsBase):
    height_h: Length
    top_flange_width_b: Length
    web_thickness_tw: Length
    top_flange_thickness_tf1: Length

    @property
    def total_height(self) -> Length:
        """Return total height of section"""
        raise self.height_h

    @property
    def total_width(self) -> Length:
        """Return total width of section"""
        return max(
            self.top_flange_width_b,
            self.web_thickness_tw * 2,
            key=lambda x: x.to_base_units().magnitude,
        )

@dataclass(kw_only=True, eq=False)
class SectionStandardBox(SectionStandard):
    section_type: SectionType = field(default=SectionType.BOX, init=False)
    dimensions: DimensionsBox

@dataclass
class DimensionsChannel(DimensionsBase):
    height_h: Length
    top_flange_width_b1: Length
    bottom_flange_width_b2: Length
    web_thickness_tw: Length
    top_flange_thickness_tf1: Length
    bottom_flange_thickness_tf2: Length
    web_inner_radius_r1: Length
    flange_end_radius_r2: Length

    @property
    def total_height(self) -> Length:
        """Return total height of section"""
        raise self.height_h

    @property
    def total_width(self) -> Length:
        """Return total width of section"""
        return max(
            self.top_flange_width_b1,
            self.bottom_flange_width_b2,
            self.web_thickness_tw,
            key=lambda x: x.to_base_units().magnitude)

@dataclass(kw_only=True, eq=False)
class SectionStandardChannel(SectionStandard):
    section_type: SectionType = field(default=SectionType.CHANNEL, init=False)
    dimensions: DimensionsChannel

@dataclass
class DimensionsSolidRectangle(DimensionsBase):
    height_h: Length
    width_b: Length

    @property
    def total_height(self) -> Length:
        """Return total height of section"""
        return self.height_h

    @property
    def total_width(self) -> Length:
        """Return total width of section"""
        return self.width_b


@dataclass(kw_only=True, eq=False)
class SectionStandardSolidRectangle(SectionStandard):
    section_type: SectionType = field(default=SectionType.SOLID_RECTANGLE, init=False)
    dimensions: DimensionsSolidRectangle

@dataclass
class DimensionsSolidRound(DimensionsBase):
    diameter_d: Length

    @property
    def total_height(self) -> Length:
        """Return total height of section"""
        raise self.diameter_d

    @property
    def total_width(self) -> Length:
        """Return total width of section"""
        return self.diameter_d

@dataclass(kw_only=True, eq=False)
class SectionStandardSolidRound(SectionStandard):
    section_type: SectionType = field(default=SectionType.SOLID_ROUND, init=False)
    dimensions: DimensionsSolidRound

@dataclass
class DimensionsPipe(DimensionsBase):
    external_diameter_d: Length
    wall_thickness_tw: Length

    @property
    def total_height(self) -> Length:
        """Return total height of section"""
        raise self.external_diameter_d

    @property
    def total_width(self) -> Length:
        """Return total width of section"""
        return self.external_diameter_d

@dataclass(kw_only=True, eq=False)
class SectionStandardPipe(SectionStandard):
    section_type: SectionType = field(default=SectionType.PIPE, init=False)
    dimensions: DimensionsPipe