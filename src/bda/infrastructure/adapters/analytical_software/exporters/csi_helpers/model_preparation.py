import uuid
from collections import defaultdict
from typing import Dict, List, Sequence, Tuple

from bda.domain import AnalyticalMultiModel
from bda.domain.enums import MaterialType
from bda.domain.models.submodels.material import Material
from bda.domain.models.submodels.section_base import Section
from bda.domain.models.submodels.sections import SectionCompositeBase
from bda.infrastructure.adapters.analytical_software.exporters.common.section_materials import (
    SectionMaterialsResolver,
)
from bda.infrastructure.utils import AppLogger

logger = AppLogger()

SOFTWARE_NAME = "CSI Bridge"


class CsiModelPraparator:

    @staticmethod
    def prepare_model_file(sapModel, export_units_code: int) -> None:
        file_name = sapModel.GetModelFilename()
        sapModel.InitializeNewModel(export_units_code)
        sapModel.File.NewBlank()
        sapModel.File.Save(file_name)


    @staticmethod
    def prepare_materials_for_export(amm: AnalyticalMultiModel) -> None:
        """
        Prepare materials for export by ensuring their names are unique.

        Materials have to be prepared before sections, as section copies created
        during sections preparation derive their names from material names.

        Parameters
        ----------
        amm: AnalyticalMultiModel

        Returns
        -------

        """

        CsiModelPraparator._ensure_unique_material_names(amm)


    @staticmethod
    def prepare_sections_for_export(amm: AnalyticalMultiModel) -> None:

        CsiModelPraparator._assign_materials_to_sections(amm)
        SectionMaterialsResolver.fill_missing_section_materials(amm, SOFTWARE_NAME)
        CsiModelPraparator._ensure_unique_section_names(amm)


    @staticmethod
    def _assign_materials_to_sections(amm: AnalyticalMultiModel):

        # this step is only for testing purposes during development when geometry group does not exist
        # but there is a need to test section export
        if amm.geometry_group is None:
            sections = amm.get_all_sections()
            materials = amm.get_all_materials()
            if not materials:
                return
            # main material is the steel part of the section and composite material is its concrete
            # part, so materials of those types are preferred; when there is none, the first and the
            # second material are used as before
            material_main = next(
                (m for m in materials if m.material_type == MaterialType.STEEL),
                materials[0])
            material_composite = next(
                (m for m in materials if m.material_type == MaterialType.CONCRETE),
                materials[1] if len(materials) > 1 else materials[0])
            for section in sections:
                section.set_material_main(material_main)
                if isinstance(section, SectionCompositeBase):
                    section.set_material_composite(material_composite)
            return

        # following steps are intented to ensure that each section has it's own material assigned according
        # to relations in geometry groups and there are no cases where the same section needs
        # two or more different materials to be assigned.

        # iterate through groups and replace section's material with the material assigned to the group
        for g in amm.geometry_group.iter_groups():
            if (g.section is not None) and ((m := g.get_material()) is not None):
                if (g.section.material_main is not m):
                    g.section.set_material_main(m)

        # iterating by groups, collect all pairs section-material for groups
        pairs: Dict[Tuple[uuid.UUID, uuid.UUID], Tuple[Section, Material]] = defaultdict()

        for g in amm.geometry_group.iter_groups():
            if (s := g.get_section()) is not None and (m := g.get_material()) is not None:
                pairs[(s.guid, m.guid)] = (s, m)

        section_materials: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)

        for (section_guid, material_guid), _ in pairs.items():
            section_materials[section_guid].add(material_guid)

        sections_to_split = {
            section_guid
            for section_guid, materials in section_materials.items()
            if len(materials) > 1
        }

        # create sections copy for each section with many materials assigned
        from copy import deepcopy

        new_sections: dict[tuple[uuid.UUID, uuid.UUID], Section] = {}

        processed: set[uuid.UUID] = set()

        for (section_guid, material_guid), (section, material) in pairs.items():

            if section_guid not in sections_to_split:
                continue

            if section_guid not in processed:
                # the first material stays with the original section
                new_sections[(section_guid, material_guid)] = section
                processed.add(section_guid)
            else:
                # next materials get section copy
                new_section = deepcopy(section)

                # section new name
                new_section.name = f"{section.name}_{material.name}"

                new_sections[(section_guid, material_guid)] = new_section

        # iterate through groups and replace section with new section
        # and assign material to each section
        # do this only for groups that contain any finite elements to avoid creating unused sections
        for g in amm.geometry_group.iter_groups():
            if (s := g.get_section()) is not None and (m := g.get_material()) is not None:
                key = (s.guid, m.guid)

                replacement = new_sections.get(key)

                if replacement is None:
                    continue

                if replacement is not s and len(g.analytical_typology.elements) > 0:
                    g.section = replacement
                    g.section.set_material_main(m)


    @staticmethod
    def _ensure_unique_material_names(amm: AnalyticalMultiModel) -> None:
        """
        Ensure that all materials sent to CSI Bridge have unique names.

        Materials sharing the same name but having different guids are renamed,
        as CSI Bridge identifies materials by their name. All materials of the model are
        checked, not only the used ones, as the unused ones are exported as well.

        Parameters
        ----------
        amm: AnalyticalMultiModel

        Returns
        -------

        """

        CsiModelPraparator._make_names_unique(amm.get_all_materials(), "material")


    @staticmethod
    def _ensure_unique_section_names(amm: AnalyticalMultiModel) -> None:
        """
        Ensure that all sections sent to CSI Bridge have unique names.

        All sections taking part in the export are checked, including the ones not used by
        any geometry group and the start and end sections of tapered sections.

        Parameters
        ----------
        amm: AnalyticalMultiModel

        Returns
        -------

        """

        CsiModelPraparator._make_names_unique(
            SectionMaterialsResolver.collect_sections_for_export(amm), "section")


    @staticmethod
    def _make_names_unique(objects: Sequence[Material | Section], object_kind: str) -> None:
        """
        Rename objects whose names are already taken by another object.

        The first object using a given name keeps it, each following object with the same
        name but a different guid gets a numbered suffix, e.g. 'C30 (1)', 'C30 (2)'.
        Names are collected first, so that generated names never take over a name
        already belonging to another object.

        Parameters
        ----------
        objects: Sequence[Material | Section]
            Objects to check, in the order they are exported.
        object_kind: str
            Name of the object type, used in log messages only.

        Returns
        -------

        """

        names_owners: Dict[str, uuid.UUID] = {}
        duplicates: List[Material | Section] = []
        processed_guids: set[uuid.UUID] = set()

        for obj in objects:
            if obj.guid in processed_guids:
                continue

            processed_guids.add(obj.guid)

            if obj.name in names_owners:
                duplicates.append(obj)
            else:
                names_owners[obj.name] = obj.guid

        for obj in duplicates:
            current_name = obj.name

            suffix = 1
            new_name = f"{current_name} ({suffix})"
            while new_name in names_owners:
                suffix += 1
                new_name = f"{current_name} ({suffix})"

            obj.name = new_name
            names_owners[new_name] = obj.guid

            logger.warning(
                "Duplicated %s name '%s' (guid: %s) renamed to '%s'. "
                "Renaming was required because CSI Bridge requires unique names.",
                object_kind, current_name, obj.guid, new_name)


