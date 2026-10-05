from dataclasses import dataclass
from typing import List

from bda.domain.enums import UnitSystem, StructuralComponentType
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.material import Material
from bda.domain.models.submodels.section_base import Section
from bda.domain.models.submodels.sections import SectionCompositeBase, SectionTapered


@dataclass
class AnalyticalMultiModel:

    unit_system: UnitSystem

    project_id: int|None

    structure_id: int|None
    structure_name: str|None
    description: str|None

    geometry_group: GeometryGroup | None

    _initial_materials: List[Material]
    _initial_sections: List[Section]

    def __init__(self, unit_system: UnitSystem,
                 project_id: int|None = None,
                 structure_id: int|None = None,
                 structure_name: str|None = None,
                 description: str|None = None,):
        self.unit_system = unit_system
        self.project_id = project_id
        self.structure_id = structure_id
        self.structure_name = structure_name
        self.description = description
        self._initial_materials = []
        self._initial_sections = []
        self.geometry_group = None

    def __str__(self):
        return (f"AnalyticalMultiModel(Project id = {self.project_id}, "
                f"structure id = {self.structure_id}, "
                f"structure name = {self.structure_name}, ")

    def get_all_used_materials(self) -> List[Material]:
        """ Return a list of materials assigned to the geometry groups"""
        materials: List[Material] = []
        if self.geometry_group is not None:
            materials.extend(self.geometry_group.get_all_materials())

        # remove duplicates from the list
        unique = []
        seen = set()

        for material in materials:
            if material.guid not in seen:
                seen.add(material.guid)
                unique.append(material)

        return unique

    def get_all_materials(self) -> List[Material]:
        """ Return a list of materials either assigned to the geometry groups and not used"""
        materials = list(self._initial_materials)
        materials.extend(self.get_all_used_materials())

        # remove duplicates from the list
        unique = []
        seen = set()

        for material in materials:
            if material.guid not in seen:
                seen.add(material.guid)
                unique.append(material)

        return unique

    def get_all_used_sections(self) -> List[Section]:
        """ Return a list of sections assigned to the geometry groups """
        sections: List[Section] = []
        if self.geometry_group is not None:
            sections.extend(self.geometry_group.get_all_sections())

        # remove duplicates from the list
        unique = []
        seen = set()

        for section in sections:
            if section.guid not in seen:
                seen.add(section.guid)
                unique.append(section)

        return unique

    def get_all_sections(self) -> List[Section]:
        """ Return a list of sections either assigned to the geometry groups and not used"""
        sections = list(self._initial_sections)
        if self.geometry_group is not None:
            sections.extend(self.geometry_group.get_all_sections())

        # remove duplicates from the list
        unique = []
        seen = set()

        for section in sections:
            if section.guid not in seen:
                seen.add(section.guid)
                unique.append(section)

        return unique

    def add_initial_material(self, material: Material):
        """
        Adds an initial material to the multimodel. The material is not assigned to any geometry group at this stage.
        Initial materials are assigned to geometry groups only when the geometry group is added.
        To add a material at a later stage, it should be assigned directly to the appropriate geometry group.
        """

        # check if material with same guid already exists
        if any(mat.guid == material.guid for mat in self._initial_materials):
            raise ValueError(f"Material with ID {material.guid} and name '{material.name}' "
                             f"already exists in the multimodel.")

        last_id = max([mat.model_id for mat in self._initial_materials], default=0)
        material.set_id(last_id + 1)
        self._initial_materials.append(material)

    def add_initial_section(self, section: Section):
        """
        Adds an initial section to the multimodel. The section is not assigned to any geometry group at this stage.
        Initial sections are assigned to geometry groups only when the geometry group is added.
        To add a section at a later stage, it should be assigned directly to the appropriate geometry group.
        """

        # check if material with same guid already exists
        if any(sec.guid == section.guid for sec in self._initial_sections):
            raise ValueError(f"Section with ID {section.guid} and name '{section.name}' "
                             f"already exists in the multimodel.")

        last_id = max([sec.model_id for sec in self._initial_sections], default=0)
        section.set_id(last_id + 1)
        self._initial_sections.append(section)

    def add_initial_geometry(self, geometry: GeometryGroup):
        """
        Adds an initial geometry to the multimodel and maps and assigns
        all initial materials and sections to the corresponding groups.
        """
        self.geometry_group = geometry

        for g in self.geometry_group.iter_groups():
            if g.material_uid is not None:
                material = next((m for m in self._initial_materials if m.guid == g.material_uid), None)
                if material is not None:
                    g.material = material
                else:
                    raise ValueError(
                        f"Material with ID {g.material_uid} assigned to group '{g.name}' "
                        f"was not found in the initial materials collection.")
            if g.section_uid is not None:
                section = next((s for s in self._initial_sections if s.guid == g.section_uid), None)
                if section is not None:
                    g.section = section
                    # assign main material to the section
                    section.set_material_main(g.get_material())
                    # composite material needs to be assigned at module level as it depends on structure type

                    #if section is tapered, assign material to belonging sections as well
                    if isinstance(section, SectionTapered):
                        self._assign_materials_to_tapered_components(section)

                else:
                    raise ValueError(
                        f"Section with ID {g.section_uid} assigned to group '{g.name}' "
                        f"was not found in the initial sections collection.")

    @staticmethod
    def _assign_materials_to_tapered_components(section: SectionTapered):
        """
        Assigns materials of a tapered section to its start and end sections.

        A tapered section and its start and end sections describe the same structural member,
        so they refer to the very same material instances. The composite material is not carried
        by the tapered section itself, so the start and end sections share it between themselves.
        """

        components = [c for c in (section.section_start, section.section_end) if c is not None]

        if section.material_main is not None:
            for component in components:
                component.set_material_main(section.material_main)

        material_composite = next(
            (c.material_composite for c in components
             if isinstance(c, SectionCompositeBase) and c.material_composite is not None), None)

        if material_composite is not None:
            for component in components:
                if isinstance(component, SectionCompositeBase) and component.material_composite is None:
                    component.set_material_composite(material_composite)

