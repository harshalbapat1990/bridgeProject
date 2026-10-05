from typing import Literal, Set

from bda.domain.enums import UnitSystem, TaperVariation
from bda.domain.models.submodels import GeometryGroup, Element1D
from bda.domain.models.submodels.boundary_conditions.beam_end_release import BeamEndRelease, StiffnessType, DirectionalRelease
from bda.domain.models.submodels.geometry_group_props.shared import SymmetricPlaneType
from bda.domain.models.submodels.sections import SectionTapered
from bda.domain.units.export_units import ExportUnits, to_float
from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import MidasConfigProvider
from bda.infrastructure.adapters.analytical_software.session_managers import MidasCivilSession
from bda.infrastructure.utils import AppLogger

class MidasGeometryExporter:

    def __init__(self, eu: ExportUnits):
        self._eu = eu

        from midas_civil import Node as MidasNode
        from midas_civil import NodeLocalAxis as MidasNodeLocalAxis

        self.MidasNode = MidasNode
        self.MidasNodeLocalAxis = MidasNodeLocalAxis

        from midas_civil import Element as MidasElement
        self.MidasElement = MidasElement

        from midas_civil import Boundary as MidasBoundary
        self.MidasBoundary = MidasBoundary
        self._logger = AppLogger()


    def export(self, amm: AnalyticalMultiModel) -> None:
        self._export_all_nodes(amm)
        self._export_geometry(amm)

    def _export_all_nodes(self, amm: AnalyticalMultiModel):
        nodes=  amm.get_all_nodes()
        eu = self._eu

        for nid, node in nodes.items():
            self.MidasNode(
                x=to_float(node.X, eu.length),
                y=to_float(node.Y, eu.length),
                z=to_float(node.Z, eu.length),
                id=int(nid),
            )

            # assign local UCS to the Node if it's defined, otherwise 0.0 is assigned
            if any(
                angle is not None
                for angle in (
                    node.rotation_angle_x,
                    node.rotation_angle_y,
                    node.rotation_angle_z,
                )
            ):

                self.MidasNodeLocalAxis(
                    nodeID= int(nid),
                    type= "XYZ",
                    angle = [
                        node.rotation_angle_x.to("deg").magnitude if node.rotation_angle_x is not None else 0.0,
                        node.rotation_angle_y.to("deg").magnitude if node.rotation_angle_y is not None else 0.0,
                        node.rotation_angle_z.to("deg").magnitude if node.rotation_angle_z is not None else 0.0
                    ],
                )


    def _get_material_id(self, group: GeometryGroup) -> int:
        cur_mat = group.get_material()
        current_mat_id = 999

        if cur_mat is not None and cur_mat.model_id is not None:
            current_mat_id = cur_mat.model_id

        return current_mat_id

    def _get_section_id(self, group: GeometryGroup) -> int:
        cur_sec = group.get_section()
        current_sec_id = 999

        if cur_sec is not None and cur_sec.model_id is not None:
            current_sec_id = cur_sec.model_id

        return current_sec_id

    def _get_taper_variation_type_code(self, taper_variation: TaperVariation) -> Literal["LINEAR", "POLY"]:
        if taper_variation == TaperVariation.LINEAR:
            return "LINEAR"
        elif taper_variation == TaperVariation.PARABOLIC:
            return "POLY"
        elif taper_variation == TaperVariation.CUBIC:
            return "POLY"
        else:
            raise NotImplementedError(f"Taper variation {taper_variation} not implemented")

    def _export_geometry(self, amm: AnalyticalMultiModel) -> None:
        """Export a GeometryGroup to MIDAS Civil."""

        MidasElement = self.MidasElement
        group = amm.geometry_group
        unknown_group_name = "unknown"

        for gr in group.iter_groups():

            current_mat_id = self._get_material_id(gr)
            current_sec_id = self._get_section_id(gr)

            group_collection: Set[str] = {gr.name} if gr.name is not None else {unknown_group_name}
            g=gr
            while g.parent_group is not None and g.parent_group.name is not None:
                group_collection.add(g.parent_group.name)
                g = g.parent_group

            for element in gr.analytical_typology.elements:
                if not isinstance(element, Element1D):
                    raise NotImplementedError("Elements other than Element1D (beam) are not yet supported")

                MidasElement.Beam(i=element.node_start.node_id,
                                  j=element.node_end.node_id,
                                  mat=current_mat_id,
                                  sect=current_sec_id,
                                  angle= element.beta_angle.to("deg").magnitude,
                                  id=element.element_id,
                                  group=list(group_collection))

            for beam_end_release in gr.analytical_typology.beam_end_releases:
                self._export_beam_end_release(beam_end_release, gr.name or 'beam_end_release')

            sec = gr.get_section()
            if isinstance(sec, SectionTapered):
                element_numbers = [e.element_id for e in gr.analytical_typology.elements]
                from midas_civil import Section
                Section.TaperedGroup(
                    name=gr.name or gr.get_section().name,
                    elem_list=element_numbers,
                    z_var=self._get_taper_variation_type_code(sec.taper_z_variation),
                    y_var=self._get_taper_variation_type_code(sec.taper_y_variation),
                    z_exp=2.0,
                    y_exp=2.0,
                    z_from= "j" if gr.properties.symmetric_plane == SymmetricPlaneType.END else "i",
                )

    def _export_beam_end_release(self, beam_end_release: BeamEndRelease, group_name: str) -> None:
        MidasBoundary = self.MidasBoundary
        element = beam_end_release.element_reference
        i_node_release = beam_end_release.start_node_release
        j_node_release = beam_end_release.end_node_release

        eu = self._eu

        # Determine release type based on stiffness_type
        if beam_end_release.stiffness_type == StiffnessType.RELATIVE_VALUE:
            release_type = "Relative"
        elif beam_end_release.stiffness_type == StiffnessType.ABSOLUTE_VALUE:
            release_type = "Value"
        else:
            raise NotImplementedError(
                f"Stiffness type {beam_end_release.stiffness_type.value} not implemented"
            )

        def to_value(release: DirectionalRelease) -> float|None:
            if release.enabled:
                if beam_end_release.stiffness_type == StiffnessType.RELATIVE_VALUE:
                    return release.value if isinstance(release.value, float) else 0.0
                else:
                    return to_float(
                        release.value,
                        eu.stiffness_force if 'F' in release.__class__.__name__ else eu.stiffness_moment)
            return None

        MidasBoundary.BeamEndRelease(
            beamElemID=element.element_id,
            type=release_type,
            Fx_I=to_value(i_node_release.F_x),
            Fy_I=to_value(i_node_release.F_y),
            Fz_I=to_value(i_node_release.F_z),
            Mx_I=to_value(i_node_release.M_x),
            My_I=to_value(i_node_release.M_y),
            Mz_I=to_value(i_node_release.M_z),
            Fx_J=to_value(j_node_release.F_x),
            Fy_J=to_value(j_node_release.F_y),
            Fz_J=to_value(j_node_release.F_z),
            Mx_J=to_value(j_node_release.M_x),
            My_J=to_value(j_node_release.M_y),
            Mz_J=to_value(j_node_release.M_z),
            group=group_name
        )


if __name__ == "__main__":
    from bda.domain.units.export_units import get_export_units

    from midas_civil import Node as MidasNode
    from midas_civil import Model
    from bda.domain import AnalyticalMultiModel
    from bda.infrastructure.data_providers import DataFileProvider
    from bda.modules_pre.m1_materials import MaterialsModule
    from bda.modules_pre.m2_sections.module_sections import SectionsModule
    from bda.modules_pre.m3_geometry.module_geometry_steel_composite import GeometrySteelCompositeModule
    from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.boundary_bcs_exporter import MidasBoundaryExporter
    from bda.modules_pre.m3_geometry.module_geometry_psc_box import GeometryPSCBoxModule
    from bda.modules_pre.m5_bearings.module_bearings import BearingsBCsModule

    eu = get_export_units(unit_system=UnitSystem.SI)
    midas_config = MidasConfigProvider()
    midas_session = MidasCivilSession(midas_config)
    midas_session.open_session(create_new_instance=False, template_file_path=None)

    exporter = MidasGeometryExporter(eu)
    bearing_exporter = MidasBoundaryExporter(eu)

    # Example usage

    amm = AnalyticalMultiModel(
        unit_system=UnitSystem.IM,
        project_id=1,
        structure_id=1,
        structure_name="Test Structure",
        description="Test Description")

    if amm is None:
        raise Exception("No amm provided")

    data_provider = DataFileProvider("C:\\Users\\CZERPAG\\GitHub\\DesignAutomation.BridgeAutomationAndOptimisation\\tests\\unit\\fixtures\\mvp_cases\\psc-box")

    logger = AppLogger()

    module_materials = MaterialsModule(amm, data_provider, logger)
    module_materials.run()

    module_sections = SectionsModule(amm, data_provider, logger)
    module_sections.run()

    # module_geometry = GeometrySteelCompositeModule(amm=amm, data_provider=data_provider, logger=logger)
    module_geometry = GeometryPSCBoxModule(amm=amm, data_provider=data_provider, logger=logger)
    module_geometry.run()

    module_bearings = BearingsBCsModule(amm, data_provider, logger)
    module_bearings.run()

    # Export
    exporter.export(amm)
    bearing_exporter.export(amm)

    Model.create()

    print('Model has been exported!')