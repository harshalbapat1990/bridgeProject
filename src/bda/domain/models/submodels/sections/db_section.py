from dataclasses import dataclass, field

from bda.domain.enums import SectionFamily
from bda.domain.models.submodels.section_base import SectionBase


@dataclass(kw_only=True, eq=False)
class SectionDB(SectionBase):
    standard: str
    profile_name: str

    section_family: SectionFamily = field(default=SectionFamily.DB, init=False)
