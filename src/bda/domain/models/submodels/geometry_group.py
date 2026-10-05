from dataclasses import dataclass, field

from uuid import UUID, uuid4
from typing import Optional, List, Iterable, Sequence, Self, Callable, Iterator

from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels.analytical_model_data import AnalyticalTypology
from bda.domain.models.submodels.element import Element, ElementLink
from bda.domain.models.submodels.geometry_group_props.bridge_properties import *
from bda.domain.models.submodels.geometry_group_props.linkage_properties import *
from bda.domain.models.submodels.geometry_group_props.shared import *
from bda.domain.models.submodels.geometry_group_props.substructure_properties import *
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import *
from bda.domain.models.submodels.material import Material
from bda.domain.models.submodels.node import Node
from bda.domain.models.submodels.section_base import Section

GroupProperties = Union[
    # COMMON
    GroupPropertiesSegment,
    # SUPERSTRUCTURE
    GroupPropertiesBridge,
    GroupPropertiesSuperstructure,
    GroupPropertiesSpan,
    GroupPropertiesGirder,
    GroupPropertiesEdgeBeam,
    GroupPropertiesDiaphragm,
    GroupPropertiesTransverseBracing,
    GroupPropertiesBrace,
    GroupPropertiesChord,
    GroupPropertiesPlanBracing,
    # SUBSTRUCTURE
    GroupPropertiesSupport,
    GroupPropertiesAboveGround,
    GroupPropertiesPier,
    GroupPropertiesWall,
    GroupPropertiesCrossbeam,
    GroupPropertiesBelowGround,
    GroupPropertiesPile,
    GroupPropertiesPileCap,
    # LINKAGE
    GroupPropertiesLinkageSupToSub,
]


@dataclass(kw_only=True)
class GeometryGroup:
    """
    Represents a class of hierarchical group within a structural model.

    A Group organizes structural elements, nodes, materials, and sections
    into a tree-like hierarchy. Each group can contain nested subgroups
    and has an optional parent group for upward hierarchy traversal.

    Attributes:
        guid (UUID): Unique identifier for this group.
        component_type (StructuralComponentType): Standard structural classification of the group.
        name (Optional[str]): Custom or user-friendly name for the group.
        material_uid (Optional[UUID]): Identifier of the directly assigned material, if any.
        section_uid (Optional[UUID]): Identifier of the directly assigned section, if any.
        properties (Optional[GroupProperties]): Additional typed properties for this group.

    Notes:
        FE collections (``free_fe_nodes``, ``finite_elements``, ``links``)
        are stored in ``_analytical_typology``.

        Reference collections (``reference_nodes``, ``reference_elements``)
        remain owned directly by ``GeometryGroup``.

        Direct assignments are stored in ``_material`` and ``_section`` and exposed via
        ``material`` and ``section`` properties. Use ``get_material()`` and ``get_section()``
        when inherited values from parent groups should be resolved.

        Parent-child hierarchy links are managed through ``_parent_group`` and
        ``_nested_groups``, and exposed through ``parent_group`` and ``nested_groups``.
    """
    guid: UUID = field(default_factory=uuid4)
    source_id: str|None = field(default=None)
    component_type: StructuralComponentType
    name: Optional[str] = ""

    _analytical_typology: AnalyticalTypology = field(default_factory=AnalyticalTypology)

    _reference_nodes: List[Node] = field(default_factory=list)
    _reference_elements: List[Element] = field(default_factory=list)

    material_uid: UUID | None = field(
        default=None,
        doc=(
            "Identifier of the material assigned to this group. Primarily used "
            "for mapping materials imported from ParaModel and may be `None` for "
            "groups created at later stages. Use `get_material()` to retrieve the "
            "effective material, whether assigned directly or inherited from a "
            "parent group."
        ),)

    section_uid: UUID | None = field(
        default=None,
        doc=(
            "Identifier of the section assigned to this group. Primarily used "
            "for mapping sections imported from ParaModel and may be `None` for "
            "groups created at later stages. Use `get_section()` to retrieve the "
            "effective section, whether assigned directly or inherited from a "
            "parent group."
        ),)

    _material: Optional[Material] = field(
        default=None,
        doc=(
            "Material directly assigned to this group. This field does not "
            "resolve material inheritance and therefore may be `None` even if "
            "the group has an effective material inherited from one of its "
            "parent groups. Use `get_material()` to retrieve the effective "
            "material, including inherited assignments."
        ),)

    _section: Optional[Section] = field(
        default=None,
        doc=(
            "Section directly assigned to this group. This field does not "
            "resolve section inheritance and therefore may be `None` even if "
            "the group has an effective section inherited from one of its "
            "parent groups. Use `get_section()` to retrieve the effective "
            "section, including inherited assignments."
        ),)

    properties: Optional[GroupProperties] = None

    _nested_groups: List['GeometryGroup'] = field(default_factory=list)
    _parent_group: Optional['GeometryGroup'] = None

    @property
    def analytical_typology(self) -> AnalyticalTypology:
        return self._analytical_typology

    @property
    def section(self) -> Section | None:
        return self._section

    @section.setter
    def section(self, value: Section | None) -> None:
        self._section = value
        self.section_uid = value.guid if value is not None else None

    @property
    def material(self) -> Material | None:
        return self._material

    @material.setter
    def material(self, value: Material | None) -> None:
        self._material = value
        self.material_uid = value.guid if value is not None else None


    @property
    def reference_nodes(self) -> Sequence['Node']:
        return tuple(self._reference_nodes)

    @property
    def reference_elements(self) -> Sequence['Element']:
        return tuple(self._reference_elements)

    @property
    def parent_group(self) -> Optional['GeometryGroup']:
        """
        The parent geometry group of this group, if any.

        Returns:
        Optional[GeometryGroup]: The parent group, or None if this group
        has no parent.
        """
        return self._parent_group

    @property
    def nested_groups(self) -> Sequence['GeometryGroup']:
        """
        Child geometry groups nested within this group.

        Returns:
            Sequence[GeometryGroup]: An immutable sequence (tuple) of child geometry groups.
        """
        return tuple(self._nested_groups)

    def __repr__(self):
        """
        Returns a string representation of the GeometryGroup instance,
        including its component type and name. Used by default for
        debug representation.
        """
        return f"Group: {self.component_type.name} ({self.name or "- - -"}) - [{len(self.nested_groups)} children]"

    def iter_groups(self, predicate: Callable[[Self], bool] | None = None) -> Iterator[GeometryGroup]:
        """
        Iterate over all groups with optional filtering.
        e.g. all groups with material: iter_groups(lambda g: g.material is not None)
        """
        if predicate is None or predicate(self):
            yield self

        for child in self.nested_groups:
            yield from child.iter_groups(predicate)

    def get_all_materials(self) -> list[Material]:
        """
        Recursively retrieves all unique materials from this group and its nested groups.

        Returns:
            List[Material]: A list containing the unique materials assigned to this group
                               (if present) followed by unique materials from nested groups.
                               Duplicate references to the same material instance are removed.
                               Separate material instances sharing the same ``guid`` are also
                               treated as duplicates. Returns an empty list if no materials are found.
        """
        unique_materials: list[Material] = []
        seen_instance_ids: set[int] = set()
        seen_guids: set[UUID] = set()

        for group in self.iter_groups():
            material = group.material
            if material is None:
                continue

            material_instance_id = id(material)
            if material_instance_id in seen_instance_ids or material.guid in seen_guids:
                continue

            seen_instance_ids.add(material_instance_id)
            seen_guids.add(material.guid)
            unique_materials.append(material)

        return unique_materials

    def get_material(self) -> Material | None:
        """
        Retrieves the material assigned to this group or its nearest parent group.

        Searches up the hierarchy chain until a material is found.

        Returns:
            Material: The material from this group or the first parent group that has one.
                         Returns None if no material is found in the hierarchy.
        """
        if self.material is not None:
            return self.material
        parent_group = self.parent_group
        return parent_group.get_material() if parent_group else None

    def get_all_sections(self) -> list[Section]:
        """
        Recursively retrieves all unique sections from this group and its nested groups.

        Returns:
            List[Section]: A list containing the unique sections assigned to this
                group (if present) followed by unique sections from nested groups.
                Duplicate references to the same section instance are removed.
                Separate section instances sharing the same ``guid`` are also
                treated as duplicates. Returns an empty list if no sections are found.
        """
        unique_sections: list[Section] = []
        seen_instance_ids: set[int] = set()
        seen_guids: set[UUID] = set()

        for group in self.iter_groups():
            section = group.section
            if section is None:
                continue

            section_instance_id = id(section)
            if section_instance_id in seen_instance_ids or section.guid in seen_guids:
                continue

            seen_instance_ids.add(section_instance_id)
            seen_guids.add(section.guid)
            unique_sections.append(section)

        return unique_sections

    def get_section(self) -> Section | None:
        """
        Retrieves the section assigned to this group or its nearest parent group.

        Searches up the hierarchy chain until a section is found.

        Returns:
            Section: The section from this group or the first parent group that has one.
                         Returns None if no section is found in the hierarchy.
        """
        if self.section is not None:
            return self.section
        parent_group = self.parent_group
        return parent_group.get_section() if parent_group else None

    def get_no_of_groups(self) -> int:
        """
        Retrieves the total number of groups included in this group together with this group.

        Returns:
            int: The total number of groups included in this group together with this group.
        -------
        """
        return sum(1 for _ in self.iter_groups())

    def get_groups_by_component_type(self, component_type: StructuralComponentType) -> list['GeometryGroup']:
        """
        Retrieves all groups of a specific structural component type.

        Args:
            component_type (StructuralComponentType): The structural component type to filter by.

        Returns:
            List[GeometryGroup]: A list of groups that match the specified component type.
        """
        return [g for g in self.iter_groups() if g.component_type == component_type]

    def get_parent_group_by_component_type(self, component_type: StructuralComponentType) -> Optional['GeometryGroup']:
        """
        Retrieves recursively the parent group of a specific structural component type.

        Args:
            component_type (StructuralComponentType): The structural component type to filter by.
        ----------

        Returns
            GeometryGroup: The parent group of the specified component type.

        """
        parent = self.parent_group
        while parent is not None:
            if parent.component_type == component_type:
                return parent
            parent = parent.parent_group

        return None

    def has_children(self) -> bool:
        """
        Checks if this group has any nested child groups.

        Returns:
            bool: True if there are nested groups, False otherwise.
        """
        return len(self.nested_groups) > 0

    def add_nested_group(self, group: GeometryGroup) -> None:
        """
        Adds a geometry group as a nested (child) group.

        This method also sets this group as the parent of the added group.

        Args:
            group (GeometryGroup): The group to add as a child.
        """
        self._nested_groups.append(group)
        group._parent_group = self

    def add_reference_node(self, node: Node) -> None:
        self._reference_nodes.append(node)

    def add_reference_nodes(self, nodes: Iterable[Node]) -> None:
        for node in nodes:
            self.add_reference_node(node)

    def add_reference_element(self, element: Element) -> None:
        self._reference_elements.append(element)

    def add_reference_elements(self, elements: Iterable[Element]) -> None:
        for element in elements:
            self.add_reference_element(element)
