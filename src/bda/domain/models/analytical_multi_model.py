from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, List

from pint.registry import Quantity

from bda.domain.enums import UnitSystem
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.loads import Loads
from bda.domain.models.analytical_typology import BearingKey, BearingNodes
from bda.domain.models.submodels.boundary_conditions.beam_end_release import BeamEndRelease
from bda.domain.models.submodels.boundary_conditions.supports import NodeBoundaryBase
from bda.domain.models.submodels.element import Element1D, Element1DBase, ElementLink, LinkType
from bda.domain.models.submodels.material import Material
from bda.domain.models.submodels.node import Node
from bda.domain.models.submodels.section_base import Section
from bda.domain.models.submodels.sections import SectionCompositeBase, SectionTapered
from bda.domain.managers import NodesManager, ElementsManager


@dataclass
class AnalyticalMultiModel:
    """
    Root aggregate representing the complete analytical model of
    a structure.

    The AnalyticalMultiModel serves as the central domain object
    shared by all preprocessing, modelling and export modules.
    It owns the geometry hierarchy and maintains collections of
    materials and sections used to build the analytical
    representation of a structure.

    The model acts as a single source of truth throughout the
    application workflow. Individual modules progressively enrich
    the model by adding materials, sections, geometry, analytical
    entities, boundary conditions and other structural data.

    Responsibilities
    ----------------
    - Store project and structure metadata.
    - Manage the root geometry hierarchy.
    - Maintain collections of available materials and sections.
    - Assign materials and sections to geometry groups.
    - Provide access to all materials, sections and analytical
      entities used within the model.
    - Ensure consistency between geometry and referenced model
      components.
    - Supply a complete analytical representation for export to
      external finite element analysis software.

    Notes
    -----
    The model is populated incrementally by dedicated modules.
    Materials and sections are typically added before geometry.
    Once geometry is assigned, references to materials and
    sections are automatically resolved and propagated to the
    appropriate geometry groups.

    The geometry hierarchy stored in `geometry_group` is treated
    as the root of the analytical model and may contain all
    structural components, analytical elements, links, bearings,
    releases and other entities required to build the finite
    element representation.

    Main Operations
    ---------------
    get_all_materials()
        Returns all materials available in the model.

    get_all_used_materials()
        Returns materials currently assigned to geometry groups.

    get_all_sections()
        Returns all sections available in the model.

    get_all_used_sections()
        Returns sections currently assigned to geometry groups.

    get_all_nodes()
        Returns all unique analytical nodes referenced by the
        analytical model.

    add_initial_material(material)
        Registers a material before geometry assignment.

    add_initial_section(section)
        Registers a section before geometry assignment.

    add_initial_geometry(geometry)
        Assigns the root geometry hierarchy and resolves
        material and section references.

    Examples
    --------
    >>> amm = AnalyticalMultiModel(
    ...     unit_system=UnitSystem.SI,
    ...     project_id=1,
    ...     structure_id=100,
    ...     structure_name="Composite Bridge"
    ... )

    >>> amm.add_initial_material(steel)
    >>> amm.add_initial_section(girder_section)
    >>> amm.add_initial_geometry(root_geometry)

    >>> all_materials = amm.get_all_materials()
    >>> all_sections = amm.get_all_sections()

    After all preprocessing modules have executed, the model
    contains the complete analytical definition of the structure
    and can be exported to a target analysis platform such as
    MIDAS Civil.
    """
    unit_system: UnitSystem

    project_id: int|None

    structure_id: int|None
    structure_name: str|None
    description: str|None

    geometry_group: GeometryGroup | None
    loads: Loads

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
        self.loads = Loads()

        self._nodes_manager: NodesManager = NodesManager()
        self._elements_manager: ElementsManager = ElementsManager()

    def __str__(self):
        return (f"AnalyticalMultiModel(Project id = {self.project_id}, "
                f"structure id = {self.structure_id}, "
                f"structure name = {self.structure_name}, ")

    # ------------------------------------------------------------------ #
    # Analytical topology facade                                         #
    #                                                                    #
    # The AMM is the single entry point for adding FE topology to a      #
    # geometry group. Nodes are created exclusively through              #
    # ``create_node`` (so they are always canonical); elements/links are #
    # ingested pre-built and deduplicated by their node key before being #
    # attached to the target group. Callers must use the returned        #
    # canonical instance, never the one they passed in.                  #
    # ------------------------------------------------------------------ #

    def get_or_create_node(self, x: Quantity, y: Quantity, z: Quantity | None = None) -> Node:
        """Create (or reuse) a canonical node via the nodes manager."""
        return self._nodes_manager.get_or_create_node(x, y, z)

    def get_or_create_beam(self, node_start: Node, node_end: Node) -> Element1D:
        """Create (or reuse) a canonical beam element (not attached to a group)."""
        return self._elements_manager.get_or_create_beam(node_start, node_end)

    def create_and_add_beam(self, group: GeometryGroup, node_start: Node, node_end: Node) -> Element1D:
        """Create a beam and attach it to the group's analytical typology."""
        beam = self.get_or_create_beam(node_start, node_end)
        group.analytical_typology._add_element(beam)
        return beam

    def get_or_create_link(self, node_start: Node, node_end: Node, link_type: LinkType) -> ElementLink:
        """Create (or reuse) a canonical link element (not attached to a group)."""
        return self._elements_manager.get_or_create_link(node_start, node_end, link_type)

    def create_and_add_link(
        self,
        group: GeometryGroup,
        node_start: Node,
        node_end: Node,
        link_type: LinkType,
    ) -> ElementLink:
        """Create a link and attach it to the group's analytical typology."""
        link = self.get_or_create_link(node_start, node_end, link_type)
        group.analytical_typology._add_link(link)
        return link

    def add_element(self, group: GeometryGroup, element: Element1DBase) -> Element1DBase:
        """Ingest a pre-built beam/link and attach it to the group's typology."""
        canonical = self._elements_manager._get_or_create(
            element, element.node_start, element.node_end
        )
        group.analytical_typology._add(canonical)
        return canonical

    def add_elements(self, group: GeometryGroup, elements: Iterable[Element1DBase]) -> None:
        """Ingest and attach a batch of beams/links to the group."""
        for element in elements:
            self.add_element(group, element)

    def create_and_add_reference_element(self, group: GeometryGroup, node_start: Node, node_end: Node) -> Element1D:
        """Create a beam and attach it to the group's reference elements."""
        beam = Element1D(node_start, node_end)
        group._add_reference_element(beam)
        return beam

    def add_reference_node(self, group: GeometryGroup, node: Node) -> Node:
        """Attach a (canonical) reference node to the group."""
        group._add_reference_node(node)
        return node

    def add_reference_nodes(self, group: GeometryGroup, nodes: Iterable[Node]) -> None:
        for node in nodes:
            self.add_reference_node(group, node)

    def add_reference_element(self, group: GeometryGroup, element: Element1DBase) -> Element1DBase:
        """Add a reference element attached to the group."""
        group._add_reference_element(element)
        return element

    def add_reference_elements(self, group: GeometryGroup, elements: Iterable[Element1DBase]) -> None:
        for element in elements:
            self.add_reference_element(group, element)

    def add_support(self, group: GeometryGroup, support: NodeBoundaryBase) -> None:
        group.analytical_typology._add_support(support)

    def add_supports(self, group: GeometryGroup, supports: List[NodeBoundaryBase]) -> None:
        group.analytical_typology._add_supports(supports)

    def add_beam_end_release(self, group: GeometryGroup, beam_end_release: BeamEndRelease) -> None:
        group.analytical_typology._add_beam_end_release(beam_end_release)

    def add_bearing_nodes(
        self,
        group: GeometryGroup,
        girder_index: int,
        bearing_index: int,
        node_start: Node,
        node_end: Node | None = None,
    ) -> None:
        """Store (canonical) bearing nodes on the group's typology."""
        group.analytical_typology._add_bearing_nodes(
            girder_index, bearing_index, node_start, node_end
        )

    def update_bearing_nodes(
        self,
        group: GeometryGroup,
        key: BearingKey,
        node_start: Node | None = None,
        node_end: Node | None = None,
    ) -> None:
        group.analytical_typology._update_bearing_nodes(key, node_start, node_end)

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

    def get_all_nodes(self):
        """
        Returns a list of all nodes in the model, including free nodes, element nodes, and bearing nodes.
        """
        nodes: dict[int, Node] = defaultdict()

        if self.geometry_group is None:
            return nodes

        for g in self.geometry_group.iter_groups():
            for element in g.analytical_typology.elements:
                assert isinstance(element, Element1D)

                nodes[element.node_start.node_id] = element.node_start
                nodes[element.node_end.node_id] = element.node_end

            for link in g.analytical_typology.links:
                nodes[link.node_start.node_id]= link.node_start
                nodes[link.node_end.node_id]= link.node_end

            for bearing_nodes in g.analytical_typology.bearing_nodes.values():
                assert isinstance(bearing_nodes, BearingNodes)
                nodes[bearing_nodes.node_top.node_id]= bearing_nodes.node_top

                if bearing_nodes.node_bottom is not None:
                    nodes[bearing_nodes.node_bottom.node_id] = bearing_nodes.node_bottom

        return nodes