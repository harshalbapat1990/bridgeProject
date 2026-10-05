from abc import ABC
from dataclasses import dataclass, field
from typing import Set

from bda.domain.enums import SectionType, SectionFamily
from bda.domain.models.submodels.material import MaterialBase
from bda.domain.models.submodels.section_base import DimensionsBase, SectionBase
from bda.domain.units.quantities import Length

@dataclass
class SectionCompositeBase(SectionBase, ABC):
    section_family: SectionFamily = field(default=SectionFamily.COMPOSITE, init=False)
    material_composite: MaterialBase | None = field(default=None, init= False)
    dimensions: DimensionsBase

    def set_material_composite(self, material_composite: MaterialBase | None = None):
        self.material_composite = material_composite

    def _shallow_copy_fields(self) -> Set[str]:
        return super()._shallow_copy_fields() | {
            "material_composite"
        }

@dataclass
class SectionCompositeSteelISymmetric(SectionCompositeBase):
    section_type: SectionType = field(default=SectionType.STEEL_I_SYMMETRIC, init=False)
    dimensions: DimensionsCompositeSteelISymmetric

@dataclass
class DimensionsCompositeSteelISymmetric(DimensionsBase):
    slab_width_bc: Length
    slab_thickness_tc: Length
    slab_girder_spacing_hh: Length

    girder_top_flange_width_b1: Length
    girder_top_flange_thickness_tf1: Length
    girder_bottom_flange_width_b2: Length
    girder_bottom_flange_thickness_tf2: Length
    girder_web_thickness_tw: Length
    girder_web_height_hw: Length

    @property
    def total_height(self) -> Length:
        """Return total height of section"""
        return self.slab_thickness_tc + self.slab_girder_spacing_hh + self.girder_top_flange_thickness_tf1 + \
            self.girder_web_height_hw + self.girder_bottom_flange_thickness_tf2

    @property
    def total_width(self) -> Length:
        """Return total width of section"""
        return max(self.slab_width_bc,
                   self.girder_top_flange_width_b1,
                   self.girder_bottom_flange_width_b2,
                   self.girder_web_thickness_tw,
                   key=lambda x: x.to_base_units().magnitude)

@dataclass
class SectionCompositeSteelIAsymmetric(SectionCompositeBase):
    section_type: SectionType = field(default=SectionType.STEEL_I_ASYMMETRIC, init=False)
    dimensions: DimensionsCompositeSteelIAsymmetric


@dataclass
class DimensionsCompositeSteelIAsymmetric(DimensionsBase):
    slab_distance_rf_sg: Length
    top_flange_distance_rf_top: Length
    bottom_flange_distance_rf_bot: Length

    slab_width_bc: Length
    slab_thickness_tc: Length
    slab_girder_spacing_hh: Length

    girder_top_flange_left_width_b1: Length
    girder_top_flange_right_width_b2: Length
    girder_top_flange_thickness_t1: Length
    girder_bottom_flange_left_width_b3: Length
    girder_bottom_flange_right_width_b4: Length
    girder_bottom_flange_thickness_t2: Length
    girder_web_thickness_tw: Length
    girder_web_height_h: Length

    @property
    def total_height(self) -> Length:
        """Return total height of section"""
        return self.slab_thickness_tc + self.slab_girder_spacing_hh + self.girder_top_flange_thickness_t1 +\
            self.girder_web_height_h + self.girder_bottom_flange_thickness_t2

    @property
    def total_width(self) -> Length:
        """Return total width of section"""
        return max(self.slab_width_bc,
                   self.girder_top_flange_left_width_b1 + self.girder_top_flange_right_width_b2,
                   self.girder_bottom_flange_left_width_b3 + self.girder_bottom_flange_right_width_b4,
                   self.girder_web_thickness_tw,
                   key=lambda x: x.to_base_units().magnitude)