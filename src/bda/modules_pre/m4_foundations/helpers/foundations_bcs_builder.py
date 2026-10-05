from typing import cast

from pint.registry import Quantity

from bda.application.interfaces import IAppLogger, NullLogger
from bda.domain import AnalyticalMultiModel, units
from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import GeometryGroup, NodeSupport, NodeSpring, Node, NodeBoundaryBase
from bda.domain.models.analytical_typology import BearingKey
from bda.domain.models.submodels.boundary_conditions.bearings import (
    BearingBCsSupport,
    BearingItem,
)
from bda.domain.models.submodels.boundary_conditions.enums import FoundationApplicationType, SoilProfileType, \
    DofTypeEnum
from bda.domain.models.submodels.boundary_conditions.foundations import FoundationBCsSupportBase, LumpedFoundationBCs, \
    PileInteractionFoundationBCs, BearingBasedFoundationApplication, SubstructureElementBasedFoundationApplication, \
    PileStiffnessUniformDataset
from bda.domain.models.submodels.boundary_conditions.spring_stiffness import SpringStiffness, RotationalStiffness
from bda.domain.models.submodels.boundary_conditions.supports import NodeConstraints
from bda.domain.models.submodels.element import (
    ElementLink,
    LinkType, Element1DBase,
)
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation

from bda.domain.models.submodels.geometry_group_props.linkage_properties import (
    GroupPropertiesLinkageSupToSub,
)
from bda.domain.models.submodels.geometry_group_props.substructure_properties import GroupPropertiesSupport, \
    GroupPropertiesPile
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import GroupPropertiesSpan
from bda.domain.units.quantities import Angle


class FoundationsBCsBuilder:
    """
    Creates analytical foundation boundary conditions from foundation
    boundary-condition definitions and attaches them to the analytical model.

    The builder converts foundation definitions associated with SUPPORT
    geometry groups into analytical supports, springs and rigid links.
    Depending on the selected foundation model, supports may be applied
    directly to substructure elements, to a generated foundation node, or
    to pile element nodes.

    Supported foundation models
    ---------------------------
    - Lumped foundation model
    - Pile interaction foundation model

    Notes
    -----
    The analytical geometry model must already contain SUPPORT geometry
    groups together with the analytical elements and nodes required by the
    selected foundation application strategy.

    The builder may create analytical support nodes and rigid links, but it
    assumes that the underlying bridge geometry, substructure elements and
    pile elements have already been generated.
    """
    def __init__(
        self,
        amm: AnalyticalMultiModel,
        logger: IAppLogger | None = None,
    ):
        self._amm = amm
        self._logger = logger or NullLogger()

        if self._amm.geometry_group is None:
            raise ValueError(
                f"AnalyticalMultiModel has no geometry_group. "
                f"Add geometry to AMM before creating "
                f"{self.__class__.__name__}."
            )

        self._groups_connections_by_support_index: dict[int, GeometryGroup] = {
            g.properties.support_index: g
            for g in self._amm.geometry_group.get_groups_by_component_type(
                StructuralComponentType
                .SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS
            )
            if isinstance(
                g.properties,
                GroupPropertiesLinkageSupToSub,
            )
        }

        self._support_skew_angles = {
            g.properties.support_index: g.properties.skew_angle
            for g in self._amm.geometry_group.get_groups_by_component_type(
                StructuralComponentType.SUPPORT
            )
            if isinstance(g.properties, GroupPropertiesSupport)
        }

        self._support_offsets: dict[int, Quantity] = (
            self._initialize_support_offsets()
        )

        self._support_structure_groups_by_index: dict[int, GeometryGroup] = {
            g.properties.support_index: g
            for g in self._amm.geometry_group.get_groups_by_component_type(
                StructuralComponentType.SUPPORT
            )
            if isinstance(g.properties, GroupPropertiesSupport)
        }

    def build(
            self,
            foundation: FoundationBCsSupportBase,
    ) -> None:
        """
        Build analytical foundation boundary conditions for a single support.

        Parameters
        ----------
        foundation : FoundationBCsSupportBase
            Foundation boundary-condition definition assigned to a support.

        Notes
        -----
        The method resolves the corresponding SUPPORT geometry group and
        dispatches processing to the implementation associated with the
        specified foundation model type.
        """

        group = self._find_group_support_structure(foundation.support_index)

        if foundation.foundation_model_type == foundation.foundation_model_type.LUMPED_FOUNDATION_MODEL and \
            isinstance(foundation, LumpedFoundationBCs):
            self._build_lumped_foundation(foundation, group)

        elif foundation.foundation_model_type == foundation.foundation_model_type.PILE_INTERACTION_MODEL and \
            isinstance(foundation, PileInteractionFoundationBCs):
            self._build_pile_interaction_foundation(foundation, group)

        else:
            raise ValueError(
                f"Unsupported foundation model type: {foundation.foundation_model_type} "
                f"for support {foundation.support_index}, support {group.name}."
            )

    def _create_link(
            self,
            girder_id: int,
            bearing_definition: BearingItem,
            group: GeometryGroup,
    ) -> ElementLink | None:
        """
        Create an analytical elastic link representing a bearing connection.

        Parameters
        ----------
        girder_id : int
            Girder identifier.
        bearing_definition : BearingItem
            Bearing definition containing stiffness and orientation data.
        group : GeometryGroup
            SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS geometry group that
            contains the bearing-node definition.

        Returns
        -------
        ElementLink | None
            Elastic link connecting the bearing top and bottom nodes. Returns
            None when the bearing definition does not contain a bottom node.

        Notes
        -----
        Link orientation follows the bearing orientation definition. When the
        bearing is marked as skewed, the support skew angle is applied as the
        link beta angle.
        """
        if not isinstance(group.properties, GroupPropertiesLinkageSupToSub):
            raise ValueError(f"Provided group {group.name} properties is not of type GroupPropertiesLinkageSupToSub")

        bearing_nodes = self._get_bearing_nodes(
            girder_id=girder_id,
            bearing_id=bearing_definition.bearing_index,
            group=group,
        )

        if bearing_nodes.node_bottom is None:
            return None

        idx = group.properties.support_index

        support_skew = self._find_support_skew_angle(idx)
        bearing_skew = (
            support_skew
            if bearing_definition.orientation == ElementOrientation.SKEWED
            else 0 * units.ureg.degrees
        )

        return ElementLink(
            link_type= LinkType.ELASTIC,
            node_start= bearing_nodes.node_top,
            node_end= bearing_nodes.node_bottom,
            beta_angle= bearing_skew,
            properties= (
                bearing_definition
                .bearing_stiffness_definition
            ),
        )

    @staticmethod
    def _get_bearing_nodes(
            girder_id: int,
            bearing_id: int,
            group: GeometryGroup,
    ):
        """
        Resolve bearing nodes assigned to a SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS GeometryGroup.
        The method searches `group.analytical_typology.bearing_nodes`
        for a bearing definition matching the specified identifiers.

        Parameters
        ----------
        girder_id : int
            Girder identifier.
        bearing_id : int
            Bearing identifier within the girder.
        group : GeometryGroup
            Support linkage geometry group containing bearing nodes.

        Returns
        -------
        BearingNodes
            Pair of analytical nodes representing the bearing
            connection.

        Raises
        ------
        ValueError
            If no bearing node definition can be found for the
            specified girder and bearing identifiers.
        """

        key = BearingKey(
            girder_id=girder_id,
            bearing_id=bearing_id,
        )

        bearing_nodes = (
            group.analytical_typology
            .bearing_nodes
            .get(key)
        )

        if bearing_nodes is None:
            raise ValueError(
                f"No bearing nodes found "
                f"for girder {girder_id} "
                f"and bearing {bearing_id}."
            )

        return bearing_nodes

    def _find_group_sup_to_sub(
            self,
            support_idx: int,
    ) -> GeometryGroup:
        """
        Find the SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS GeometryGroup associated with a support index.

        Parameters
        ----------
        support_idx : int
            Support identifier.

        Returns
        -------
        GeometryGroup
            Geometry group:
            StructuralComponentType.SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS
            for the specified support index.

        Raises
        ------
        ValueError
            If no linkage group exists for the specified support.
        """

        try:
            return self._groups_connections_by_support_index[support_idx]

        except KeyError as ex:
            raise ValueError(
                f"No support linkage group found "
                f"for support index {support_idx}."
            ) from ex

    def _find_group_support_structure(
            self,
            support_idx: int,
    ) -> GeometryGroup:
        """
        Find the SUPPORT GeometryGroup associated with a support index.

        Parameters
        ----------
        support_idx : int
            Support identifier.

        Returns
        -------
        GeometryGroup
            Geometry group:
            StructuralComponentType.SUPPORT
            for the specified support index.

        Raises
        ------
        ValueError
            If no SUPPORT group exists for the specified support.
        """

        try:
            return self._support_structure_groups_by_index[support_idx]

        except KeyError as ex:
            raise ValueError(
                f"No SUPPORT group found "
                f"for support index {support_idx}."
            ) from ex

    def _find_support_skew_angle(self, idx: int) -> Angle:
        """
        Return the skew angle associated with the specified SUPPORT GeometryGroup.

        Parameters
        ----------
        idx : int
            Support identifier.

        Returns
        -------
        Angle
            Skew angle defined for the SUPPORT GeometryGroup.

        Raises
        ------
        ValueError
            If no support with the specified identifier exists.
        """
        try:
            return self._support_skew_angles[idx]

        except KeyError as ex:
            raise ValueError(
                f"No skew angle found for support index {idx}."
            ) from ex

    def _initialize_support_offsets(self) -> dict[int, Quantity]:
        """
        Determine the longitudinal offset (chainage) of each support.

        The offset of the first support is zero (bridge start). Each
        subsequent support offset is the cumulative sum of the lengths
        of all preceding spans. This mirrors the span-offset
        accumulation performed by ``InitializeSpanStates`` in the
        geometry module, where support ``i`` sits at the end of span
        ``i - 1`` and at the start of span ``i``.

        Returns
        -------
        dict[int, Quantity]
            Mapping of support index to its longitudinal offset along
            the bridge.

        Notes
        -----
        SPAN groups are processed in ascending ``span_index`` order so
        that the running offset is accumulated consistently.
        """

        spans = sorted(
            (
                g
                for g in self._amm.geometry_group.get_groups_by_component_type(
                    StructuralComponentType.SPAN
                )
                if isinstance(g.properties, GroupPropertiesSpan)
            ),
            key=lambda g: g.properties.span_index,
        )

        support_offsets: dict[int, Quantity] = {}
        running_offset = 0 * units.ureg.m

        for span in spans:
            props = span.properties
            assert isinstance(props, GroupPropertiesSpan)

            # Support at the start of this span.
            support_offsets[props.span_index] = running_offset

            running_offset = cast(Quantity, running_offset + props.span_length)

        if spans:
            # Support at the far end of the last span.
            last_props = spans[-1].properties
            assert isinstance(last_props, GroupPropertiesSpan)
            support_offsets[last_props.span_index + 1] = running_offset

        return support_offsets

    def _find_support_offset(self, idx: int) -> Quantity:
        """
        Return the longitudinal offset (chainage) of the specified support.

        Parameters
        ----------
        idx : int
            Support identifier.

        Returns
        -------
        Quantity
            Longitudinal offset of the support along the bridge.

        Raises
        ------
        ValueError
            If no offset is defined for the specified support index.
        """
        try:
            return self._support_offsets[idx]

        except KeyError as ex:
            raise ValueError(
                f"No offset found for support index {idx}."
            ) from ex

    def _build_lumped_foundation(
            self,
            foundation: LumpedFoundationBCs,
            support_group: GeometryGroup,
    ) -> None:
        """
        Build a lumped foundation model for a support.

        Parameters
        ----------
        foundation : LumpedFoundationBCs
            Lumped foundation definition.
        support_group : GeometryGroup
            SUPPORT geometry group associated with the foundation.

        Notes
        -----
        The implementation is delegated according to the foundation
        application strategy:

        - Bearing-based application
        - Substructure-element-based application
        """
        application = foundation.application

        if application.application_type == FoundationApplicationType.BEARING_BASED and \
                isinstance(application, BearingBasedFoundationApplication):
            self._build_lumped_foundation_bearing_based(foundation, application, support_group)

        elif application.application_type == FoundationApplicationType.SUBSTRUCTURE_ELEMENT_BASED and \
                isinstance(application, SubstructureElementBasedFoundationApplication):
            self._build_lumped_foundation_substructure_element_based(foundation, support_group)


    def _build_pile_interaction_foundation(
            self,
            foundation: PileInteractionFoundationBCs,
            support_group: GeometryGroup):
        """
        Create analytical soil springs for pile elements using pile-interaction
        foundation definitions.

        Parameters
        ----------
        foundation : PileInteractionFoundationBCs
            Foundation definition containing spring properties for individual
            piles.
        support_group : GeometryGroup
            SUPPORT geometry group containing PILE subgroups.

        Notes
        -----
        The method locates pile geometry groups, extracts their analytical
        nodes and assigns spring supports to pile head, intermediate and pile
        tip nodes.

        Currently only uniform soil-profile datasets are supported.
        """

        # find piles in the support group
        pile_groups = support_group.get_groups_by_component_type(StructuralComponentType.PILE)
        # pile_groups = list(support_group.iter_groups(
        #     lambda g: g.component_type == StructuralComponentType.PILE and isinstance(g, GroupPropertiesPile) > 0))

        if not pile_groups:
            raise ValueError(f"No PILE groups found in support group "
                             f"{support_group.name} for support index {foundation.support_index}.")

        for pile_spring in foundation.pile_springs:
            # get the nodes of the pile group

            pile_group = next((g for g in pile_groups if isinstance(g.properties, GroupPropertiesPile) and \
                               g.properties.pile_index == pile_spring.pile_index), None)

            if pile_group is None:
                raise ValueError(f"No pile group found for pile index {pile_spring.pile_index} in support group "
                                 f"{support_group.name} for support index {foundation.support_index}.")

            pile_nodes: set[Node] = set()
            for element in pile_group.analytical_typology.elements:
                if isinstance(element, Element1DBase):
                    pile_nodes.add(element.node_start)
                    pile_nodes.add(element.node_end)

            sorted_pile_nodes = sorted(pile_nodes, key=lambda n: n.Z.to_base_units().magnitude)
            very_bottom_node = sorted_pile_nodes[0]
            very_top_node = sorted_pile_nodes[-1]
            intermediate_nodes = sorted_pile_nodes[1:-1]

            # find soil profile for the pile group
            soil_profile = next(
                (ps for ps in foundation.pile_springs
                 if ps.pile_index == pile_group.properties.pile_index), None)

            if soil_profile is None:
                raise ValueError(f"No soil profile found for pile index "
                                 f"{pile_group.properties.pile_index} in foundation "
                                 f"{foundation.support_index}.")

            if soil_profile.soil_profile_type != SoilProfileType.UNIFORM or \
                    not isinstance(pile_spring, PileStiffnessUniformDataset):
                raise NotImplementedError(f"Soil profile type {soil_profile.soil_profile_type} "
                                          f"is not yet implemented for pile interaction foundation "
                                          f"{foundation.support_index}.")

            free_rotation = RotationalStiffness(dof_type=DofTypeEnum.FREE)

            top_sup = self._create_a_support_for_node(
                node=very_top_node,
                stiffness=SpringStiffness(
                    sdx=pile_spring.top_node.sdx,
                    sdy=pile_spring.top_node.sdy,
                    sdz=pile_spring.top_node.sdz,
                    srx=free_rotation,
                    sry=free_rotation,
                    srz=free_rotation,
                ))
            self._amm.add_support(support_group, top_sup)

            bot_sup = self._create_a_support_for_node(
                node=very_bottom_node,
                stiffness=SpringStiffness(
                    sdx=pile_spring.bottom_node.sdx,
                    sdy=pile_spring.bottom_node.sdy,
                    sdz=pile_spring.bottom_node.sdz,
                    srx=free_rotation,
                    sry=free_rotation,
                    srz=free_rotation,
                ))
            self._amm.add_support(support_group, bot_sup)

            for int_node in intermediate_nodes:
                int_sup = self._create_a_support_for_node(
                    node=int_node,
                    stiffness=SpringStiffness(
                        sdx=pile_spring.intermediate_nodes.sdx,
                        sdy=pile_spring.intermediate_nodes.sdy,
                        sdz=pile_spring.intermediate_nodes.sdz,
                        srx=free_rotation,
                        sry=free_rotation,
                        srz=free_rotation,
                    )
                )
                self._amm.add_support(support_group, int_sup)


    def _build_lumped_foundation_bearing_based(
            self,
            foundation: LumpedFoundationBCs,
            application: BearingBasedFoundationApplication,
            support_group: GeometryGroup):
        """
        Build a lumped foundation based on a bearing-based foundation application.
        Parameters
        ----------
        foundation : LumpedFoundationBCs
            The lumped foundation to be built.
        application : BearingBasedFoundationApplication
            The bearing-based foundation application providing the necessary parameters.
        support_group : GeometryGroup
            The geometry group to which the foundation belongs.

        Returns
        -------
        None
        """

        root_group = support_group.get_parent_group_by_component_type(StructuralComponentType.BRIDGE)
        linkage_groups = root_group.get_groups_by_component_type(
            StructuralComponentType.SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS)

        support_group = self._find_group_support_structure(foundation.support_index)

        if linkage_groups is None or len(linkage_groups) == 0:
            raise ValueError("No SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS groups found in the geometry model.")

        linkage_group = next(g for g in iter(linkage_groups)
                             if isinstance(props:=g.properties, GroupPropertiesLinkageSupToSub) and \
                             props.support_index == foundation.support_index)

        if linkage_group is None:
            raise ValueError(f"No SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS "
                             f"group found for support index {foundation.support_index}.")

        bearing_bottom_nodes = list(n.node_bottom for n in linkage_group.analytical_typology.bearing_nodes.values()
                                    if n.node_bottom is not None)

        bearing_bottom_nodes.sort(key=lambda n: n.Z.to_base_units().magnitude)
        very_bottom_node = bearing_bottom_nodes[0]
        minZ = very_bottom_node.Z
        foundation_z = cast(Quantity, minZ - application.vertical_offset)

        x_support = self._find_support_offset(foundation.support_index)

        # Create a new node at the foundation level
        foundation_node = self._amm.get_or_create_node(
            x=x_support,
            y=0 * units.ureg.m,
            z=foundation_z
        )

        if foundation.orientation == ElementOrientation.SKEWED:
            support_skew_angle = self._find_support_skew_angle(foundation.support_index)
            foundation_node.rotation_angle_z = support_skew_angle

        if foundation.orientation == ElementOrientation.SKEWED:
            support_skew_angle = self._find_support_skew_angle(foundation.support_index)
            foundation_node.rotation_angle_z = support_skew_angle

        # Connect each bearing bottom node to the foundation node with a link element (rigid link)
        # and assign to group
        for bearing_bottom_node in bearing_bottom_nodes:
            link = self._amm.get_or_create_link(
                node_start=bearing_bottom_node,
                node_end=foundation_node,
                link_type=LinkType.RIGID
            )
            self._amm.add_element(support_group, link)

        # assign constraints to the foundation node
        support = self._create_a_support_for_node(foundation_node, foundation.stiffness_definition)
        self._amm.add_support(support_group, support)


    def _build_lumped_foundation_substructure_element_based(
            self,
            foundation: LumpedFoundationBCs,
            support_group: GeometryGroup):
        """
        Build a lumped foundation based on a substructure element-based foundation application.
        Parameters
        ----------
        foundation : LumpedFoundationBCs
            The lumped foundation for which the support conditions are being applied.
        application : SubstructureElementBasedFoundationApplication
            The substructure element-based foundation application containing the necessary information for support placement.
        support_group : GeometryGroup
            The geometry group representing the support structure to which the foundation support will be applied.

        Returns
        -------
        None
            This method does not return any value.
        """
        matching_types = [
            StructuralComponentType.PILE_CAP,
            StructuralComponentType.GROUND_BEAM,
            StructuralComponentType.SPREAD_FOOTING
        ]

        backup_types = [
            StructuralComponentType.PIER,
            StructuralComponentType.WALL,
            StructuralComponentType.CROSSBEAM
        ]

        # find the substructure element group that can be used to apply the foundation support
        below_ground_group = support_group.get_first_group_by_component_type(StructuralComponentType.BELOW_GROUND)
        if below_ground_group is None:
            raise ValueError(f"No BELOW_GROUND group found in support group "
                             f"{support_group.name} for support index {foundation.support_index}.")

        horizontal_group = below_ground_group.get_first_group_by_component_type(StructuralComponentType.HORIZONTAL_MEMBERS)
        if horizontal_group is None:
            raise ValueError(f"No HORIZONTAL_MEMBERS group found in support group "
                             f"{support_group.name} for support index {foundation.support_index}.")

        matching_group = next(horizontal_group.iter_groups(
            lambda g: g.component_type in matching_types and len(g.analytical_typology.elements) > 0), None)

        if matching_group is None:
            matching_group = next(support_group.iter_groups(
                lambda g: g.component_type in backup_types and len(g.analytical_typology.elements) > 0), None)

        if matching_group is None:
            raise ValueError(f"No matching substructure element group that contains elements found "
                             f"for support index {foundation.support_index}."
                             f" Expected one of: {', '.join(t.name for t in matching_types + backup_types)}.")

        # get the nodes of the matching group
        matching_nodes: set[Node] = set()
        for element in matching_group.analytical_typology.elements:
            if isinstance(element, Element1DBase):
                matching_nodes.add(element.node_start)
                matching_nodes.add(element.node_end)

        if not matching_nodes:
            raise ValueError(f"Matching substructure element group found for support index {foundation.support_index} "
                             f"but it contains no nodes to apply support conditions.")

        # find the node with the lowest Z coordinate and as close as possible to the center of the support
        support_offset = self._find_support_offset(foundation.support_index)
        y_value = 0 * units.ureg.m

        node = min(
            matching_nodes,
            key=lambda n: (
                n.Z.to_base_units().magnitude,
                abs(n.Y.to_base_units().magnitude - y_value.to_base_units().magnitude),
                abs(n.X.to_base_units().magnitude - support_offset.to_base_units().magnitude),
            )
        )

        if foundation.orientation == ElementOrientation.SKEWED:
            support_skew_angle = self._find_support_skew_angle(foundation.support_index)
            node.rotation_angle_z = support_skew_angle

        # assign constraints to the foundation node
        support = self._create_a_support_for_node(node, foundation.stiffness_definition)
        self._amm.add_support(support_group, support)


    def _create_a_support_for_node(self, node: Node, stiffness: SpringStiffness) -> NodeBoundaryBase:
        """
        Add a support to a node with the specified stiffness.

        Parameters
        ----------
        node : Node
            The node to which the support will be added.
        stiffness : SpringStiffness
            The stiffness definition for the support.

        Returns
        -------
        NodeBoundaryBase
            The created node support.
        """

        directions = [
            stiffness.sdx.dof_type,
            stiffness.sdy.dof_type,
            stiffness.sdz.dof_type,
            stiffness.srx.dof_type,
            stiffness.sry.dof_type,
            stiffness.srz.dof_type
        ]

        support_type = 'spring' if any(d == DofTypeEnum.CUSTOM for d in directions) else 'support'

        if support_type == 'spring':
            support = NodeSpring(
                node=node,
                spring_stiffness=stiffness
            )
        else:
            support = NodeSupport(
                node=node,
                constraints=NodeConstraints(
                    dx=stiffness.sdx.dof_type == DofTypeEnum.FIXED,
                    dy=stiffness.sdy.dof_type == DofTypeEnum.FIXED,
                    dz=stiffness.sdz.dof_type == DofTypeEnum.FIXED,
                    rx=stiffness.srx.dof_type == DofTypeEnum.FIXED,
                    ry=stiffness.sry.dof_type == DofTypeEnum.FIXED,
                    rz=stiffness.srz.dof_type == DofTypeEnum.FIXED
                )
            )

        return support