from bda.domain import AnalyticalMultiModel
from bda.domain.enums import StructuralComponentType
from bda.domain.models.analytical_typology import BearingKey
from bda.domain.models.submodels import GeometryGroup, NodeSupport, NodeSpring
from bda.domain.models.submodels.boundary_conditions.enums import DofTypeEnum
from bda.domain.models.submodels.boundary_conditions.spring_stiffness import TranslationalStiffness, RotationalStiffness
from bda.domain.models.submodels.element import ElementLink, LinkType
from bda.domain.units import ExportUnits, to_float
from bda.infrastructure.utils import AppLogger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.csi_stubs.c_sap_model import cSapModel

# CONSTANTS
_INFINITE_STIFFNESS = 10.0e10

class CSIBoundaryBCsExporter:
    """
Export analytical boundary-condition links from an ``AnalyticalMultiModel``
to SAP2000.

The exporter processes analytical link objects stored in geometry groups
and converts them into SAP2000 link properties and link objects.

Export Workflow
---------------
1. Validate that the analytical model contains a geometry group.
2. Iterate through all geometry groups in the model hierarchy.
3. Build a lookup table that maps bearing node pairs to their
   corresponding ``BearingKey``.
4. Iterate through all analytical links defined in each group's
   analytical typology.
5. Assign a unique sequential identifier to every exported link.
6. Export each link according to its ``LinkType``:

   * ``LinkType.RIGID``

     - Create a rigid SAP2000 link property.
     - Create the corresponding SAP2000 link object between the
       start and end nodes.

   * ``LinkType.ELASTIC``

     - Verify that the link belongs to a supported structural component.
     - Resolve the corresponding bearing definition.
     - Generate a unique SAP2000 link property name.
     - Map analytical stiffness definitions to SAP2000 link-property
       parameters.
     - Create the SAP2000 link object.

7. Assign local axes and SAP2000 group membership to every exported link.

Notes
-----
* Elastic links are currently supported only for
  ``StructuralComponentType.SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS``.
* Bearing-based elastic links rely on the
  ``analytical_typology.bearing_nodes`` mapping to resolve the
  corresponding ``BearingKey``.
* Unsupported link types are skipped and reported through the logger.
"""
    def __init__(self, sapModel: "cSapModel", eu: ExportUnits):
        self.sapModel = sapModel
        self._eu = eu
        self._unknown_group_name = "unknown"
        self._logger = AppLogger()

    #
    #   MAIN BCS EXPORTER
    #
    def export(self, amm: AnalyticalMultiModel) -> None:
        """
        Export all analytical link-based boundary conditions from the analytical
        model to SAP2000.
        The method traverses all geometry groups, assigns unique identifiers to
        analytical links, exports rigid links directly, and creates elastic link
        properties for bearing connections. Elastic links are currently supported
        only for SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS groups.
        """
        if amm.geometry_group is None:
            self._logger.warning("No geometry group found in the analytical model. "
                                 "Skipping boundary condition export.")
            return

        counter = 0

        #
        #   MAIN LOOP
        #
        for group in amm.geometry_group.iter_groups():
            bearing_lookup = self._create_bearing_lookup(group)

            #
            #   LINKS
            #
            for link in group.analytical_typology.links:
                counter += 1
                link.set_id(counter)

                self._export_link(
                    link= link,
                    group= group,
                    bearing_lookup= bearing_lookup,
                )

            #
            # SUPPORTS
            #
            for support in group.analytical_typology.supports:
                match support:

                    case NodeSupport():
                        self._export_node_support(support)

                    case NodeSpring():
                        self._export_node_spring(support)

                    case _:
                        raise NotImplementedError(
                            f"Unsupported support type {type(support)}. "
                        )

    #
    #   LINKs EXPORTS
    #
    def _export_link(
            self,
            link: ElementLink,
            group: GeometryGroup,
            bearing_lookup: dict,
    ) -> None:
        """
        Dispatch link export based on its type using pattern matching.

        Routes the export of an analytical link to the appropriate handler
        method based on the link's type (RIGID or ELASTIC). Logs a warning
        if an unsupported link type is encountered.

        Parameters
        ----------
        link : ElementLink
            The link element to export.
        group : GeometryGroup
            The geometry group containing the link.
        bearing_lookup : dict
            Lookup dictionary mapping bearing node pairs to BearingKey objects.
            Required for elastic link exports.

        Returns
        -------
        None
        """
        match link.link_type:

            case LinkType.RIGID:
                self._export_rigid_link(
                    link= link,
                    group= group,
                )

            case LinkType.ELASTIC:
                self._export_elastic_link(
                    link= link,
                    group= group,
                    bearing_lookup= bearing_lookup,
                )

            case _:
                self._logger.warning(
                    f"Unsupported link type {link.link_type}. Skipping link export."
                )

    def _export_rigid_link(
            self,
            group: GeometryGroup,
            link: ElementLink,
            property_name: str = "Rigid",
    ) -> None:
        """
        Export an analytical link as a rigid SAP2000 link with all translational
        and rotational degrees of freedom fully restrained.
        """

        DOF = (True, ) * 6
        Fixed = (True, ) * 6
        Ke = (0, ) * 6
        Ce = (0, ) * 6

        self.sapModel.PropLink.SetLinear(
            Name=property_name,
            DOF=DOF,
            Fixed=Fixed,
            Ke=Ke,
            Ce=Ce,
            DJ2=0.5,    # shear spring location: relative
            DJ3=0.5,    # shear spring location: relative
        )

        self.sapModel.LinkObj.AddByPoint(
            Point1=str(link.node_start.node_id),
            Point2=str(link.node_end.node_id),
            Name=str(link.element_id),
            PropName=property_name,
            UserName=str(link.element_id),
        )

        self.sapModel.LinkObj.SetLocalAxes(
            Name=str(link.element_id),
            Ang=link.beta_angle.to("deg").magnitude,
        )

        self.sapModel.LinkObj.SetGroupAssign(
            Name=str(link.element_id),
            GroupName=group.name or self._unknown_group_name
        )

    def _export_elastic_link(
            self,
            link: ElementLink,
            group: GeometryGroup,
            bearing_lookup: dict,
    ) -> None:
        """
        Create and assign a SAP2000 linear elastic link property and instantiate
        the corresponding link element between the specified analytical nodes.
        """
        if (group.component_type!= StructuralComponentType.SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS):
            raise NotImplementedError(
                "Elastic links are only supported for "
                "SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS."
            )

        bearing_key = self._find_bearing_key(
            link= link,
            bearing_lookup= bearing_lookup
        )

        property_name = self._get_bearing_property_name(
            group = group,
            bearing_key= bearing_key,
        )

        props = link.properties
        _f = self._eu.stiffness_force
        _m = self._eu.stiffness_moment

        """
        In CSI axis 1 -> X, 2 -> Z and 3 -> -Y
        Therefore the U2 and U3 directions are intentionally swapped.
        The rotations for the respective directions are also swapped. 
        Since the spring stiffness is identical for movement in both the positive and negative directions, 
        the sense of the displacement vector is not critical for this model. 
        """

        u1 = self._map_dof(props.sdx, _f)
        u2 = self._map_dof(props.sdz, _f)
        u3 = self._map_dof(props.sdy, _f)
        r1 = self._map_dof(props.srx, _m)
        r2 = self._map_dof(props.srz, _m)
        r3 = self._map_dof(props.sry, _m)

        DOF = (u1[0], u2[0], u3[0], r1[0], r2[0], r3[0])

        Fixed = (u1[1], u2[1], u3[1], r1[1], r2[1], r3[1])

        Ke = (u1[2], u2[2], u3[2], r1[2], r2[2], r3[2])

        self.sapModel.PropLink.SetLinear(
            Name= property_name,
            DOF=DOF,
            Fixed=Fixed,
            Ke=Ke,
            Ce= (0.0, ) * 6,
            DJ2= 0.5,    # shear spring location: relative
            DJ3=0.5,    # shear spring location: relative
        )

        self.sapModel.LinkObj.AddByPoint(
            Point1= str(link.node_start.node_id),
            Point2= str(link.node_end.node_id),
            Name= str(link.element_id),
            PropName= property_name,
            UserName= str(link.element_id),
        )

        self.sapModel.LinkObj.SetLocalAxes(
            Name= str(link.element_id),
            Ang= link.beta_angle.to("deg").magnitude,
        )

        self.sapModel.LinkObj.SetGroupAssign(
            Name= str(link.element_id),
            GroupName= group.name or self._unknown_group_name
        )

    #
    #   SUPPORTS
    #
    def _export_node_support(self, support: NodeSupport):
        nid = support.node.node_id
        _s = support.constraints

        value = (_s.dx, _s.dz, _s.dy, _s.rx, _s.rz, _s.ry)  #   directions swapped u2 <-> u3, r2 <-> r3

        self.sapModel.PointObj.SetRestraint(
            Name= str(nid),
            Value= value,
        )

    def _export_node_spring(self, support: NodeSpring):
        nid = support.node.node_id
        _s = support.spring_stiffness
        _f = self._eu.stiffness_force
        _m = self._eu.stiffness_moment
        _map = self._map_point_stiffness

        """
        In CSI axis 1 -> X, 2 -> Z and 3 -> -Y
        """

        K = (
            _map(_s.sdx, _f),
            _map(_s.sdz, _f),
            _map(_s.sdy, _f),
            _map(_s.srx, _m),
            _map(_s.srz, _m),
            _map(_s.sry, _m),
        )

        self.sapModel.PointObj.SetSpring(
            Name= str(nid),
            K= K,
        )


    #
    #   HELPER METHODS
    #
    def _create_bearing_lookup(
            self,
            group: GeometryGroup,
    ):
        """
    Create a lookup dictionary mapping bearing node pairs to bearing keys.

    Creates a mapping from tuple of (node_top, node_bottom) pairs to their
    corresponding BearingKey objects. This lookup is used to find bearing
    definitions when exporting elastic links.

    Parameters
    ----------
    group : GeometryGroup
        The geometry group containing bearing node definitions.

    Returns
    -------
    dict
        Dictionary with keys as tuples (node_top, node_bottom) and values
        as BearingKey objects representing bearing definitions.
    """
        return {
            (nodes.node_top, nodes.node_bottom): key
            for key, nodes in group.analytical_typology.bearing_nodes.items()
        }

    def _find_bearing_key(
            self,
            link: ElementLink,
            bearing_lookup: dict,
    ):
        """
        Find the bearing key associated with an elastic link's node pair.

        Looks up the bearing definition for an elastic link using its start and
        end node pair. Raises ValueError if no bearing definition is found.

        Parameters
        ----------
        link : ElementLink
            The elastic link element whose bearing key is being searched for.
        bearing_lookup : dict
            Lookup dictionary mapping bearing node pairs to BearingKey objects.

        Returns
        -------
        BearingKey
            The bearing key corresponding to the link's node pair.

        Raises
        ------
        ValueError
            If no bearing definition is found for the link's node pair.
        """
        bearing_key = bearing_lookup.get((link.node_start, link.node_end))
        assert isinstance(bearing_key, BearingKey | None), f"Assertion error: expected BearingKey or None. "

        if bearing_key is None:
            raise ValueError(
                f"No bearing definition found for elastic link "
                f"{link.node_start} and {link.node_end} "
            )

        return bearing_key

    @staticmethod
    def _map_dof(
            stiffness: TranslationalStiffness | RotationalStiffness | None,
            unit: ExportUnits,
    ):
        """
        Convert a stiffness DOF definition into the target support/link format.

        Parameters
        ----------
        stiffness : TranslationalStiffness | RotationalStiffness | None
            Stiffness definition for a single degree of freedom. The DOF can be
            defined as FREE, FIXED, or CUSTOM.
        unit : Any
            Unit used to convert custom stiffness values to the target numerical
            representation.

        Returns
        -------
        tuple[bool, bool, float]
            A tuple containing:
            - enabled (bool): Indicates that the DOF is defined and should be exported.
            - fixed (bool): Indicates whether the DOF is fully restrained.
            - stiffness_value (float): Stiffness value associated with the DOF.
              Returns 0.0 for FREE and FIXED DOFs, and the converted stiffness
              value for CUSTOM DOFs.

        Notes
        -----
        Mapping rules:
        - FREE   -> (True, False, 0.0)
        - FIXED  -> (True, True, 0.0)
        - CUSTOM -> (True, False, converted stiffness value)
        """
        if stiffness.dof_type == DofTypeEnum.FREE:
            return True, False, 0.0

        if stiffness.dof_type == DofTypeEnum.FIXED:
            return True, True, 0.0

        if stiffness.dof_type == DofTypeEnum.CUSTOM:
            return True, False, to_float(stiffness.stiffness, unit)

    @staticmethod
    def _map_point_stiffness(
            stiffness: TranslationalStiffness | RotationalStiffness | None,
            unit: ExportUnits,
    ) -> float:
        """
        Convert a stiffness DOF definition into the target support/link format.

        Parameters
        ----------
        stiffness : TranslationalStiffness | RotationalStiffness | None
            Stiffness definition for a single degree of freedom. The DOF can be
            defined as FREE, FIXED, or CUSTOM.
        unit : Any
            Unit used to convert custom stiffness values to the target numerical
            representation.

        Returns
        -------
        tuple[bool, bool, float]
            A tuple containing:
            - enabled (bool): Indicates that the DOF is defined and should be exported.
            - fixed (bool): Indicates whether the DOF is fully restrained.
            - stiffness_value (float): Stiffness value associated with the DOF.
              Returns 0.0 for FREE and FIXED DOFs, and the converted stiffness
              value for CUSTOM DOFs.

        Notes
        -----
        Mapping rules:
        - FREE   -> (True, False, 0.0)
        - FIXED  -> (True, True, 0.0)
        - CUSTOM -> (True, False, converted stiffness value)
        """
        match stiffness.dof_type:

            case DofTypeEnum.FREE:
                return 0.0

            case DofTypeEnum.FIXED:
                return _INFINITE_STIFFNESS

            case DofTypeEnum.CUSTOM:
                return to_float(stiffness.stiffness, unit)

            case _:
                raise NotImplementedError(f"Dof {stiffness.dof_type} is not supported.")

    def _get_bearing_property_name(
            self,
            group: GeometryGroup,
            bearing_key: BearingKey,
    ) -> str:
        """
        Generate a unique SAP2000 property name for a bearing link.

        Constructs a formatted property name using support index, girder ID,
        and bearing ID to uniquely identify the bearing in SAP2000.

        Parameters
        ----------
        group : GeometryGroup
            The geometry group containing the support index.
        bearing_key : BearingKey
            The bearing key containing girder and bearing identifiers.

        Returns
        -------
        str
            Formatted property name in format: Bearing_S{support_id}_G{girder_id}_B{bearing_id}

        Example
        -------
        >>> name = self._get_bearing_property_name(group, bearing_key)
        >>> print(name)
        'Bearing_S1_G2_B3'
        """
        return(
            f"Bearing_S{group.properties.support_index}"
            f"_G{bearing_key.girder_id}"
            f"_B{bearing_key.bearing_id}"
        )