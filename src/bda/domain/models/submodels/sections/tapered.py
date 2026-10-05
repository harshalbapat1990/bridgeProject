from dataclasses import dataclass, field
from typing import Set
from uuid import UUID

from bda.domain.enums import SectionFamily, TaperVariation, SectionType
from bda.domain.models.submodels.section_base import SectionBase


@dataclass(kw_only=True, eq=False)
class SectionTapered(SectionBase):
    section_start: SectionBase | None = field(default=None, init=False)
    section_start_id: UUID
    section_end: SectionBase | None = field(default=None, init=False)
    section_end_id: UUID
    taper_y_variation: TaperVariation
    taper_z_variation: TaperVariation
    section_family: SectionFamily = field(default=SectionFamily.TAPERED, init=False)
    section_type: SectionType | None = field(default=None, init=False)

    def set_section_start(self, section_start: SectionBase) -> None:
        self.section_start = section_start
        self.section_type = section_start.section_type

    def set_section_end(self, section_end: SectionBase) -> None:
        self.section_end = section_end

    def _shallow_copy_fields(self) -> Set[str]:
        return super()._shallow_copy_fields() | {
            "section_start",
            "section_end"
        }