from typing import List, Literal, Set

from bda.domain.enums import UnitSystem, TaperVariation
from bda.domain.models.submodels import GeometryGroup, Element1D
from bda.domain.models.submodels.sections import SectionTapered
from bda.domain.units.export_units import ExportUnits, to_float
from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import MidasConfigProvider
from bda.infrastructure.adapters.analytical_software.session_managers import MidasCivilSession
from bda.infrastructure.utils import AppLogger

logger = AppLogger()

class MidasGeometryExporter:

    def __init__(self, eu: ExportUnits):
        self._eu = eu
        from midas_civil import Node as MidasNode
        self.MidasNode = MidasNode
        from midas_civil import Element as MidasElement
        self.MidasElement = MidasElement
        from midas_civil import Boundary as MidasBoundary
        self.MidasBoundary = MidasBoundary

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

    def export_geometry_group(self, group: GeometryGroup) -> None:
        """Export a GeometryGroup to MIDAS Civil."""

        eu = self._eu
        MidasNode = self.MidasNode
        MidasElement = self.MidasElement
        MidasBoundary = self.MidasBoundary

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
                for n in [element.node_start, element.node_end]:
                    MidasNode(x=to_float(n.X, eu.length),
                              y=to_float(n.Y, eu.length),
                              z=to_float(n.Z, eu.length),
                              id=n.node_id)
                MidasElement.Beam(i=element.node_start.node_id,
                                  j=element.node_end.node_id,
                                  mat=current_mat_id,
                                  sect=current_sec_id,
                                  id=element.element_id,
                                  group=list(group_collection))

            for link in gr.analytical_typology.links:
                for n in [link.node_start, link.node_end]:
                    MidasNode(x=to_float(n.X, eu.length),
                              y=to_float(n.Y, eu.length),
                              z=to_float(n.Z, eu.length),
                              id=n.node_id)
                MidasBoundary.ElasticLink(i_node=link.node_start.node_id,
                                          j_node=link.node_end.node_id,
                                          group=gr.name,
                                          link_type='RIGID',
                                          id=link.element_id)

            sec = gr.get_section()
            if isinstance(sec, SectionTapered):
                element_numbers = [e.element_id for e in gr.analytical_typology.elements]
                from midas_civil import Section
                Section.TaperedGroup(
                    name=gr.get_section().name,
                    elem_list=element_numbers,
                    z_var=self._get_taper_variation_type_code(sec.taper_z_variation),
                    y_var=self._get_taper_variation_type_code(sec.taper_y_variation),
                    z_exp=2.0,
                    y_exp=2.0
                )



if __name__ == "__main__":
    from bda.domain.units.export_units import get_export_units

    from midas_civil import Node as MidasNode
    from midas_civil import Model
    from bda.domain.units.registry import m
    from bda.domain import AnalyticalMultiModel
    from bda.infrastructure.data_providers import DataFileProvider
    from bda.modules_pre.m1_materials import MaterialsModule
    from bda.modules_pre.m2_sections.module_sections import SectionsModule
    from bda.modules_pre.m3_geometry.module_geometry_steel_composite import GeometrySteelCompositeModule

    eu = get_export_units(unit_system=UnitSystem.SI)
    midas_config = MidasConfigProvider()
    midas_session = MidasCivilSession(midas_config)
    midas_session.open_session(create_new_instance=False, template_file_path=None)

    exporter = MidasGeometryExporter(eu)

    # Example usage
    from bda.domain.models.submodels.sections import SectionStandardSolidRectangle
    from dataclasses import fields

    amm = AnalyticalMultiModel(
        unit_system=UnitSystem.IM,
        project_id=1,
        structure_id=1,
        structure_name="Test Structure",
        description="Test Description")

    data_provider = DataFileProvider("C:\\Users\\TS040198\\GitHub\\DesignAutomation.BridgeAutomationAndOptimisation\\tests\\unit\\fixtures\\mvp_cases\\steel-composite")

    logger = AppLogger()

    module_materials = MaterialsModule(amm, data_provider, logger)
    module_materials.run()

    module_sections = SectionsModule(amm, data_provider, logger)
    module_sections.run()

    module_geometry = GeometrySteelCompositeModule(amm=amm, data_provider=data_provider, logger=logger)

    module_geometry.run()

    # node1 = Node(X=0*m, Y=0*m, Z=0*m)
    # node1.node_id = 10
    # node2 = Node(X=5*m, Y=0*m, Z=0*m)
    # node2.node_id = 20
    #
    # element = Element1D(node_start=node1, node_end=node2)
    # element.set_id(5)
    # group = GeometryGroup(component_type=StructuralComponentType.GIRDER, name="GIRDER_group")
    # group.add_analytical_element(element)

    exporter.export_geometry_group(amm.geometry_group)

    Model.create()

    print('finito')