from typing import List, Set
from uuid import UUID

from bda.domain.enums import SectionFamily
from bda.domain.models.submodels import SectionBase
from bda.domain.models.submodels.sections import SectionTapered


def order_sections_for_export(sections: List[SectionBase]) -> List[SectionBase]:
    """
    Return the sections in the order they have to be sent to the analytical software.

    Analytical software builds a tapered section out of already existing sections, so the
    tapered ones are exported last, after the sections they refer to. Start and end sections
    of the tapered sections are exported as well, as the multimodel does not return them on
    their own while the software still needs them.

    Parameters
    ----------
    sections: List[SectionBase]
        Sections of the model, in any order.

    Returns
    -------
    List[SectionBase]
        Non-tapered sections first, followed by the tapered ones.

    """

    non_tapered = [s for s in sections if s.section_family != SectionFamily.TAPERED]
    tapered = [s for s in sections if s.section_family == SectionFamily.TAPERED]

    non_tapered_guids: Set[UUID] = {s.guid for s in non_tapered}

    for tapered_section in tapered:
        if not isinstance(tapered_section, SectionTapered):
            continue

        for end_section in (tapered_section.section_start, tapered_section.section_end):
            if end_section is not None and end_section.guid not in non_tapered_guids:
                non_tapered.append(end_section)
                non_tapered_guids.add(end_section.guid)

    return non_tapered + tapered
