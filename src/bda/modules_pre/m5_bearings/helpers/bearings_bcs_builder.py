from bda.application.interfaces import IAppLogger, NullLogger
from bda.domain import AnalyticalMultiModel, units
from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import GeometryGroup
from bda.domain.models.analytical_typology import BearingKey
from bda.domain.models.submodels.boundary_conditions.bearings import (
    BearingBCsSupport,
    BearingItem,
    MultiBearingBCs,
    SingleBearingBCs, BearingBCsGirderBase,
)
from bda.domain.models.submodels.element import (
    ElementLink,
    LinkType,
)
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation

from bda.domain.models.submodels.geometry_group_props.linkage_properties import (
    GroupPropertiesLinkageSupToSub,
)
from bda.domain.models.submodels.geometry_group_props.substructure_properties import GroupPropertiesSupport
from bda.domain.units.quantities import Angle


class BearingsBCsBuilder:
    """
    Builds analytical bearing links from bearing boundary condition
    definitions and attaches them to `SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS`
    geometry groups.

    The builder maps bearing boundary condition data to analytical
    finite-element links representing bearing stiffness between girders
    and supports. Bearing nodes are resolved from previously generated
    linkage topology and used as end nodes of elastic link elements.

    Notes
    -----
    The geometry model must already contain:

    - GeometryGroup: `LINKAGE`,
    - GeometryGroup: `SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS`,
    - `SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS.analytical_typology.bearing_nodes`
    definitions containing both `node_start` and `node_end` defined.

    The builder does not create geometry or nodes. It only creates
    analytical link elements based on existing bearing topology and
    bearing stiffness definitions.
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

        self._groups_by_support: dict[int, GeometryGroup] = {
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

    def build(
            self,
            support_bearings: BearingBCsSupport,
    ) -> None:
        """
        Build all bearing links assigned to a single support.

        Parameters
        ----------
        support_bearings : BearingBCsSupport
            Boundary condition definition for one support, including
            all girders connected to that support.

        Notes
        -----
        The method resolves the corresponding geometry group and
        delegates processing of individual girders to specialized
        methods depending on bearing configuration type.
        """

        group = self._find_group(support_bearings.support_index)

        for bearing in support_bearings.bearings_by_girder:
            self._build_bearing(
                bearing=bearing,
                group=group,
            )

    def _build_bearing(
            self,
            bearing: BearingBCsGirderBase,
            group: GeometryGroup,
    ) -> None:
        """
        Dispatch bearing processing based on configuration type.

        Parameters
        ----------
        bearing : SingleBearingBCs | MultiBearingBCs
            Bearing boundary condition definition assigned to a girder.
        group : GeometryGroup
            `SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS` geometry group associated with the support.

        Raises
        ------
        NotImplementedError
            If the bearing configuration type is not supported.
        """

        if isinstance(bearing, SingleBearingBCs):
            self._build_single_bearing(
                bearing= bearing,
                group= group,
            )
            return

        if isinstance(bearing, MultiBearingBCs):
            self._build_multiple_bearing(
                bearing= bearing,
                group= group,
            )
            return

        raise NotImplementedError(
            f"Unsupported bearing configuration: "
            f"{bearing.bearing_configuration_type}"
        )

    def _build_single_bearing(
            self,
            bearing: SingleBearingBCs,
            group: GeometryGroup,
    ) -> None:
        """
        Create and add a link for a single-bearing configuration.

        Parameters
        ----------
        bearing : SingleBearingBCs
            Single bearing definition assigned to a girder.
        group : GeometryGroup
            `SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS` geometry group containing bearing nodes.

        Notes
        -----
        Exactly one finite-element link is created from the bearing
        definition and added to the analytical typology.
        """

        link = self._create_link(
            girder_id=bearing.girder_index,
            bearing_definition=bearing.bearing_definition,
            group=group,
        )

        if link is not None:
            self._amm.add_element(group, link)

    def _build_multiple_bearing(
            self,
            bearing: MultiBearingBCs,
            group: GeometryGroup,
    ) -> None:
        """
        Create and add links for a multiple-bearing configuration.

        Parameters
        ----------
        bearing : MultiBearingBCs
            Multiple-bearing definition assigned to a girder.
        group : GeometryGroup
            `SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS` geometry group containing bearing nodes.

        Notes
        -----
        A separate finite-element link is created for each bearing
        definition contained in the configuration.
        """

        for definition in bearing.bearing_definitions:

            link = self._create_link(
                girder_id= bearing.girder_index,
                bearing_definition= definition,
                group= group,
            )

            if link is not None:
                self._amm.add_element(group, link)

    def _create_link(
            self,
            girder_id: int,
            bearing_definition: BearingItem,
            group: GeometryGroup,
    ) -> ElementLink | None:
        """
        Create an elastic link representing bearing stiffness.

        Parameters
        ----------
        girder_id : int
            Identifier of the girder to which the bearing belongs.
        bearing_definition : BearingItem
            Bearing definition containing index, orientation and
            stiffness properties.
        group : GeometryGroup
            `SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS` geometry group containing bearing nodes.

        Returns
        -------
        ElementLink | None
            Created elastic link or None when the bearing does not
            contain a valid bottom node.

        Notes
        -----
        The link stiffness is taken directly from the bearing
        stiffness definition.
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

    def _find_group(
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
            return self._groups_by_support[support_idx]

        except KeyError as ex:
            raise ValueError(
                f"No support linkage group found "
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