import uuid
from typing import Dict, List, Sequence

from bda.domain import AnalyticalMultiModel
from bda.domain.enums import MaterialType, SectionFamily
from bda.domain.models.submodels.material import Material
from bda.domain.models.submodels.section_base import Section
from bda.domain.models.submodels.sections import SectionCompositeBase, SectionTapered
from bda.infrastructure.utils import AppLogger

logger = AppLogger()


class SectionMaterialsResolver:
    """
    Assigns materials to the sections that are still missing them.

    Analytical software requires a material for every exported section, also for the ones
    not used by any element, so this step is shared by all the exporters. Materials already
    assigned are never overwritten, so the assignments made by the geometry modules are kept.
    """

    @staticmethod
    def fill_missing_section_materials(amm: AnalyticalMultiModel, software_name: str) -> None:
        """
        Assign materials to the sections that are still missing them.

        Sections absent from the geometry group are not used by any element, so their materials
        matter for the export rather than for the model itself. Such sections are usually source
        sections, whose copies are used by the groups and already have their materials resolved
        there. They are matched with those copies by 'source_id', which is preserved when a
        section is copied, and reuse the very same material instances. Sections that cannot be
        matched fall back to the first material of the type typical for their section family.

        Parameters
        ----------
        amm: AnalyticalMultiModel
        software_name: str
            Name of the analytical software, used in log messages only.

        Returns
        -------

        """

        sections = SectionMaterialsResolver.collect_sections_for_export(amm)

        if not sections:
            return

        SectionMaterialsResolver._assign_materials_by_source_id(amm, sections)
        SectionMaterialsResolver._propagate_materials_within_tapered_sections(sections)
        SectionMaterialsResolver._assign_fallback_materials(amm, sections, software_name)


    @staticmethod
    def collect_sections_for_export(amm: AnalyticalMultiModel) -> List[Section]:
        """
        Return all sections sent to the analytical software.

        Beside the sections of the model, start and end sections of tapered sections are
        taken into account, as those are exported as well while not being returned by the
        multimodel on their own.

        Parameters
        ----------
        amm: AnalyticalMultiModel

        Returns
        -------
        List[Section]
            Sections in the order they are exported.

        """

        sections: List[Section] = []
        collected_guids: set[uuid.UUID] = set()

        for section in amm.get_all_sections():
            if section.guid not in collected_guids:
                collected_guids.add(section.guid)
                sections.append(section)

        index = 0
        while index < len(sections):
            section = sections[index]
            index += 1

            if not isinstance(section, SectionTapered):
                continue

            for end_section in (section.section_start, section.section_end):
                if end_section is not None and end_section.guid not in collected_guids:
                    collected_guids.add(end_section.guid)
                    sections.append(end_section)

        return sections


    @staticmethod
    def _assign_materials_by_source_id(amm: AnalyticalMultiModel, sections: Sequence[Section]) -> None:
        """
        Reuse materials of the sections sharing the same source section.

        Parameters
        ----------
        amm: AnalyticalMultiModel
        sections: Sequence[Section]
            All sections taking part in the export.

        Returns
        -------

        """

        used_guids = {s.guid for s in amm.get_all_used_sections()}

        # sections used by the geometry groups have their materials resolved from the group
        # hierarchy, so they are preferred as donors over the remaining ones
        donors = sorted(sections, key=lambda s: s.guid not in used_guids)

        materials_main: Dict[str, Material] = {}
        materials_composite: Dict[str, Material] = {}
        ambiguous_source_ids: set[str] = set()

        for donor in donors:
            if donor.source_id is None:
                continue

            if donor.material_main is not None:
                known = materials_main.setdefault(donor.source_id, donor.material_main)
                if known.guid != donor.material_main.guid:
                    ambiguous_source_ids.add(donor.source_id)

            if isinstance(donor, SectionCompositeBase) and donor.material_composite is not None:
                materials_composite.setdefault(donor.source_id, donor.material_composite)

        for source_id in sorted(ambiguous_source_ids):
            logger.warning(
                "Sections originating from source section '%s' use different main materials. "
                "The material of the section used by the geometry groups was reused for the "
                "sections missing one.", source_id)

        for section in sections:
            if section.source_id is None:
                continue

            if section.material_main is None:
                material = materials_main.get(section.source_id)
                if material is not None:
                    section.set_material_main(material)

            if isinstance(section, SectionCompositeBase) and section.material_composite is None:
                material = materials_composite.get(section.source_id)
                if material is not None:
                    section.set_material_composite(material)


    @staticmethod
    def _propagate_materials_within_tapered_sections(sections: Sequence[Section]) -> None:
        """
        Share materials between a tapered section and its start and end sections.

        A tapered section and its start and end sections describe the same structural member,
        so they refer to the very same material instances, the same way as the copies of a
        tapered section keep referring to the start and end sections of their source.

        Parameters
        ----------
        sections: Sequence[Section]
            All sections taking part in the export.

        Returns
        -------

        """

        for section in sections:
            if not isinstance(section, SectionTapered):
                continue

            components = [c for c in (section.section_start, section.section_end) if c is not None]

            if not components:
                continue

            material_main = section.material_main or next(
                (c.material_main for c in components if c.material_main is not None), None)

            if material_main is not None:
                if section.material_main is None:
                    section.set_material_main(material_main)
                for component in components:
                    if component.material_main is None:
                        component.set_material_main(material_main)

            # a tapered section carries no composite material on its own, so its start and end
            # sections share the composite material between themselves
            material_composite = next(
                (c.material_composite for c in components
                 if isinstance(c, SectionCompositeBase) and c.material_composite is not None), None)

            if material_composite is not None:
                for component in components:
                    if isinstance(component, SectionCompositeBase) and component.material_composite is None:
                        component.set_material_composite(material_composite)


    @staticmethod
    def _assign_fallback_materials(amm: AnalyticalMultiModel, sections: Sequence[Section],
                                   software_name: str) -> None:
        """
        Assign materials to the sections that could not be matched with any other section.

        Parameters
        ----------
        amm: AnalyticalMultiModel
        sections: Sequence[Section]
            All sections taking part in the export.
        software_name: str
            Name of the analytical software, used in log messages only.

        Returns
        -------

        """

        materials = amm.get_all_materials()

        if not materials:
            logger.warning("No materials found in the model, sections missing a material "
                           "are exported without one.")
            return

        material_steel = next((m for m in materials if m.material_type == MaterialType.STEEL), None)
        material_concrete = next((m for m in materials if m.material_type == MaterialType.CONCRETE), None)

        # the concrete already used by the composite sections of the model comes from the deck slab,
        # so it is a better guess than an arbitrary concrete material, but only when it is unambiguous
        composite_materials = {
            s.material_composite.guid: s.material_composite
            for s in sections
            if isinstance(s, SectionCompositeBase) and s.material_composite is not None
        }
        material_deck = (next(iter(composite_materials.values()))
                         if len(composite_materials) == 1 else None)

        for section in sections:
            if section.material_main is None:
                material = SectionMaterialsResolver._get_default_main_material(
                    section, material_steel, material_concrete, materials)
                section.set_material_main(material)
                logger.warning(
                    "Section '%s' (guid: %s) had no main material assigned, material '%s' was "
                    "used instead. Assignment was required because %s requires a material "
                    "for every exported section.",
                    section.name, section.guid, material.name, software_name)

            if isinstance(section, SectionCompositeBase) and section.material_composite is None:
                material = material_deck or material_concrete or material_steel or materials[0]
                section.set_material_composite(material)
                logger.warning(
                    "Composite section '%s' (guid: %s) had no composite material assigned, "
                    "material '%s' was used instead. Assignment was required because %s "
                    "requires a material for every exported section.",
                    section.name, section.guid, material.name, software_name)


    @staticmethod
    def _get_default_main_material(section: Section, material_steel: Material | None,
                                   material_concrete: Material | None,
                                   materials: Sequence[Material]) -> Material:
        """
        Return the material best matching the section family.

        Concrete is preferred for the PSC sections, steel for the remaining ones, as the main
        material of a composite section is its steel girder.

        Parameters
        ----------
        section: Section
        material_steel: Material | None
            The first steel material of the model, if any.
        material_concrete: Material | None
            The first concrete material of the model, if any.
        materials: Sequence[Material]
            All materials of the model, used when neither steel nor concrete is available.

        Returns
        -------
        Material

        """

        # the tapered family says nothing about the material, so the family of the start
        # section is used instead
        section_family = section.section_family
        if isinstance(section, SectionTapered) and section.section_start is not None:
            section_family = section.section_start.section_family

        if section_family == SectionFamily.PSC:
            return material_concrete or material_steel or materials[0]

        return material_steel or material_concrete or materials[0]
