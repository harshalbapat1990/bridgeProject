from bda.application.mapping.geometry_groups.group_mapper import GeometryGroupMapper
from bda.application.interfaces.module.i_module import IModule
from bda.domain.models.submodels import GeometryGroup
from bda.modules_pre.m3_geometry.builders.psc_box_builder.geometry_builder import GeometryPSCBoxBuilder
from bda.modules_pre.m3_geometry.helpers.tools.visualizer import GeometryVisualizer


class GeometryPSCBoxModule(IModule):

    @property
    def module_name(self) -> str:
        return "Geometry for PSC Box bridge"

    def _run(self) -> bool:
        geometry_groups_dto = (
            self
            .data_provider
            .get_geometry_groups_for_project()
        )
        self.logger.info("Retrieved %d groups from data provider.", len(geometry_groups_dto))

        if not geometry_groups_dto:
            self.logger.error("No geometry group found.")
            return False

        if len(geometry_groups_dto) > 1:
            self.logger.warning("More than one geometry group found, using only the first one.")
            return False

        # --- Mapping ---
        geometry_group_dto = geometry_groups_dto[0]
        geometry = GeometryGroupMapper.map_group(geometry_group_dto)
        self.amm.add_initial_geometry(geometry)

        builder = GeometryPSCBoxBuilder(amm=self.amm, logger=self.logger)
        builder.build()

        return True

if __name__ == "__main__":

    from bda.domain import AnalyticalMultiModel
    from bda.domain.enums import UnitSystem, StructuralComponentType
    from bda.infrastructure.data_providers import DataFileProvider
    from bda.infrastructure.utils import AppLogger
    from bda.modules_pre.m1_materials import MaterialsModule
    from bda.modules_pre.m2_sections.module_sections import SectionsModule

    amm = AnalyticalMultiModel(
        unit_system=UnitSystem.SI,
        project_id=1,
        structure_id=1,
        structure_name="PSC Box Test Structure",
        description="Test Description")

    data_provider = DataFileProvider("C:\\Users\\CZERPAG\\GitHub\\DesignAutomation.BridgeAutomationAndOptimisation\\tests\\unit\\fixtures\\mvp_cases\\psc-box")

    logger = AppLogger()

    module_materials = MaterialsModule(amm, data_provider, logger)
    module_materials.run()

    module_sections = SectionsModule(amm, data_provider, logger)
    module_sections.run()

    module_geometry = GeometryPSCBoxModule(amm=amm, data_provider=data_provider, logger=logger)
    module_geometry.run()

    girder = amm.geometry_group.get_groups_by_component_type(StructuralComponentType.GIRDER)
    piles = amm.geometry_group.get_groups_by_component_type(StructuralComponentType.PILE)
    links = amm.geometry_group.get_groups_by_component_type(StructuralComponentType.LINKAGE)

    assert isinstance(amm.geometry_group, GeometryGroup)

    fig = GeometryVisualizer.plot(
        amm.geometry_group,
        title="Geometry for PSC Box bridge",
        show=True,
        include_finite_elements=True,
        include_reference_elements=False,
        include_links=True,
        flat=False,
        isometric=False,
        interactive=True
    )
