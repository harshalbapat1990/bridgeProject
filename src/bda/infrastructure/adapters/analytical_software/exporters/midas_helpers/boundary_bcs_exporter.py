from bda.domain import AnalyticalMultiModel
from bda.domain.models.submodels import NodeSupport, NodeSpring
from bda.domain.models.submodels.boundary_conditions.enums import DofTypeEnum
from bda.domain.models.submodels.boundary_conditions.spring_stiffness import TranslationalStiffness, \
    RotationalStiffness, SpringStiffness
from bda.domain.models.submodels.boundary_conditions.supports import NodeConstraints
from bda.domain.models.submodels.element import LinkType
from bda.domain.units import ExportUnits, to_float
from bda.infrastructure.utils import AppLogger

# CONSTANTS
_INFINITE_STIFFNESS = 10.0e10


#
#   BOUNDARY MODULE
#
class MidasBoundaryExporter:
    def __init__(self, eu: ExportUnits):
        self._eu = eu
        self._logger = AppLogger()

        from midas_civil import Boundary as MidasBoundary
        self.MidasBoundary = MidasBoundary
        self._infinite_stiffness = _INFINITE_STIFFNESS # temporary solution for fixed DOF, to be changed when API allows for modelling fixed ElasticLinks

    def export(self, amm: AnalyticalMultiModel) -> None:
        if amm.geometry_group is None:
            self._logger.warning("No geometry group found in the analytical model. Skipping boundary condition export.")
            return

        self._export_rigid_links(amm)
        self._export_elastic_links(amm)
        self._export_foundations(amm)

    def _get_stiffness(
            self,
            stiffness: TranslationalStiffness | RotationalStiffness | None,
            unit,
    ) -> float:
        """
        Resolve a translational or rotational stiffness definition to a numerical value.

        The returned value depends on the degree-of-freedom (DOF) type:

        - ``None`` or ``DofTypeEnum.FREE``: returns ``0.0``.
        - ``DofTypeEnum.FIXED``: returns the predefined infinite stiffness
          value stored in ``self._infinite_stiffness``.
        - ``DofTypeEnum.CUSTOM``: converts and returns the user-defined
          stiffness value in the specified unit.

        Parameters
        ----------
        stiffness : TranslationalStiffness | RotationalStiffness | None
            Stiffness definition associated with a translational or rotational
            degree of freedom. If ``None``, the DOF is treated as free.
        unit
            Target stiffness unit used for conversion by ``to_float``.

        Returns
        -------
        float
            Numerical stiffness value corresponding to the specified DOF type.

        Raises
        ------
        ValueError
            If the DOF type is ``CUSTOM`` but no stiffness value is provided.
        NotImplementedError
            If an unsupported ``dof_type`` is encountered.

        Notes
        -----
        The method maps analytical DOF definitions to stiffness values used by
        the target analysis software:

        - FREE  -> 0.0
        - FIXED -> infinite stiffness
        - CUSTOM -> user-defined stiffness
        """
        if stiffness is None:
            return 0.0

        if stiffness.dof_type == DofTypeEnum.FREE:
            return 0.0

        if stiffness.dof_type == DofTypeEnum.FIXED:
            return self._infinite_stiffness

        if stiffness.dof_type == DofTypeEnum.CUSTOM:
            if stiffness.stiffness is None:
                raise ValueError(
                    "CUSTOM stiffness requires a stiffness value."
                )

            return to_float(stiffness.stiffness, unit)

        raise NotImplementedError(
            f"Unsupported dof_type: {stiffness.dof_type}"
        )

    def _export_rigid_links(self, amm: AnalyticalMultiModel):
        MidasBoundary = self.MidasBoundary

        for gr in amm.geometry_group.iter_groups():
            for link in gr.analytical_typology.links:
                if link.link_type == LinkType.RIGID:

                    MidasBoundary.ElasticLink(
                        i_node=link.node_start.node_id,
                        j_node=link.node_end.node_id,
                        group= "rigid",
                        link_type='RIGID',
                        beta_angle= link.beta_angle.to("deg").magnitude,
                    )

    def _export_elastic_links(self, amm: AnalyticalMultiModel):
        MidasBoundary = self.MidasBoundary

        for gr in amm.geometry_group.iter_groups():
            for link in gr.analytical_typology.links:
                if link.link_type == LinkType.ELASTIC:
                    _p = link.properties

                    MidasBoundary.ElasticLink(
                        i_node=link.node_start.node_id,
                        j_node=link.node_end.node_id,
                        group= "elastic",
                        link_type='GEN',
                        beta_angle= link.beta_angle.to("deg").magnitude,
                        shear= True,    #   shear spring location: default value: 0.5 (relative)

                        # TODO: to be changed when API allows for modelling fixed ElasticLinks
                        sdx= self._get_stiffness(_p.sdx, self._eu.stiffness_force),
                        sdy= self._get_stiffness(_p.sdy, self._eu.stiffness_force),
                        sdz= self._get_stiffness(_p.sdz, self._eu.stiffness_force),
                        srx= self._get_stiffness(_p.srx, self._eu.stiffness_moment),
                        sry= self._get_stiffness(_p.sry, self._eu.stiffness_moment),
                        srz= self._get_stiffness(_p.srz, self._eu.stiffness_moment),
                    )

    def _export_foundations(self, amm: AnalyticalMultiModel):
        MidasBoundary = self.MidasBoundary
        root_group = amm.geometry_group

        if root_group is None:
            self._logger.warning("No geometry group found in the analytical model.")
            return

        for g in root_group.iter_groups():
            for s in g.analytical_typology.supports:

                if isinstance(s, NodeSupport):
                    MidasBoundary.Support(
                        nodeID=s.node.node_id,
                        constraint= self._constraint_to_string(s.constraints),
                        group= g.name or "default_support_group",
                    )

                elif isinstance(s, NodeSpring):
                    MidasBoundary.PointSpring(
                        node= s.node.node_id,
                        group= g.name or "default_spring_group",
                        spring_type= "LINEAR",
                        stiffness= self._spring_stiffness_to_list(s.spring_stiffness),
                        fixed_option= self._fixed_option_list(s.spring_stiffness),
                    )

                else:
                    raise NotImplementedError(f"{type(s)} is not supported foundation Node.")

    @staticmethod
    def _constraint_to_string(constraint: NodeConstraints) -> str:
        "Return a string representing the constraint. Example format: '1110000' "
        s = ''
        s= s.join(
            [
                '1' if constraint.dx else '0',
                '1' if constraint.dy else '0',
                '1' if constraint.dz else '0',
                '1' if constraint.rx else '0',
                '1' if constraint.ry else '0',
                '1' if constraint.rz else '0',
                str(0), # WARP - not implemented in this module
            ]
        )
        return s

    def _spring_stiffness_to_list(self, s: SpringStiffness) -> list[float]:
        return [
            self._get_stiffness(s.sdx, self._eu.stiffness_force),
            self._get_stiffness(s.sdy, self._eu.stiffness_force),
            self._get_stiffness(s.sdz, self._eu.stiffness_force),
            self._get_stiffness(s.srx, self._eu.stiffness_moment),
            self._get_stiffness(s.sry, self._eu.stiffness_moment),
            self._get_stiffness(s.srz, self._eu.stiffness_moment)
        ]

    def _fixed_option_list(self, s: SpringStiffness) -> list[bool]:
        return [
            s.sdx.dof_type == DofTypeEnum.FIXED,
            s.sdy.dof_type == DofTypeEnum.FIXED,
            s.sdz.dof_type == DofTypeEnum.FIXED,
            s.srx.dof_type == DofTypeEnum.FIXED,
            s.sry.dof_type == DofTypeEnum.FIXED,
            s.srz.dof_type == DofTypeEnum.FIXED,
        ]