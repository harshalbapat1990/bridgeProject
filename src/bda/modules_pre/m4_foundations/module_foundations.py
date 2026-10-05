from bda.application.interfaces.module import IModule
from bda.application.mapping.foundation_conditions.foundation_mapper import FoundationMapper
from bda.modules_pre.m4_foundations.helpers.foundations_bcs_builder import FoundationsBCsBuilder


class FoundationsBCsModule(IModule):

    @property
    def module_name(self):
        return "Foundations Boundary Conditions"

    def _run(self) -> bool:

        # Loading Foundations Boundary Conditions from Data Provider
        foundations_bcs_dto = (
            self
            .data_provider
            .get_foundation_boundary_conditions_for_project()
        )

        if not foundations_bcs_dto:
            self.logger.error("No Foundations Boundary Conditions found.")
            return False

        # --- Mapping ---
        foundations = FoundationMapper.to_domain(foundations_bcs_dto)

        builder = FoundationsBCsBuilder(
            amm= self.amm,
            logger= self.logger,
        )

        # --- Building ---
        for foundation in foundations:
            builder.build(foundation)

        return True

if __name__ == "__main__":
    from bda.domain import AnalyticalMultiModel
    from bda.domain.enums import UnitSystem
    from bda.infrastructure.data_providers import DataFileProvider
    from bda.infrastructure.utils import AppLogger
    from bda.modules_pre.m1_materials import MaterialsModule
    from bda.modules_pre.m2_sections.module_sections import SectionsModule
    from bda.modules_pre.m3_geometry.module_geometry_psc_box import GeometryPSCBoxModule
    from bda.modules_pre.m3_geometry.helpers.tools.visualizer import GeometryVisualizer
    from bda.domain.models.submodels import GeometryGroup

    amm = AnalyticalMultiModel(
        unit_system=UnitSystem.SI,
        project_id=1,
        structure_id=1,
        structure_name="PSC Box Test Structure",
        description="Test Description")

    data_provider = DataFileProvider(
        "C:\\Users\\CZERPAG\\GitHub\\DesignAutomation.BridgeAutomationAndOptimisation\\tests\\unit\\fixtures\\mvp_cases\\psc-box")

    logger = AppLogger()

    module_materials = MaterialsModule(amm, data_provider, logger)
    module_materials.run()

    module_sections = SectionsModule(amm, data_provider, logger)
    module_sections.run()

    module_geometry = GeometryPSCBoxModule(amm=amm, data_provider=data_provider, logger=logger)
    module_geometry.run()

    module_foundations = FoundationsBCsModule(amm=amm, data_provider=data_provider, logger=logger)
    module_foundations.run()

    assert isinstance(amm.geometry_group, GeometryGroup)

    fig = GeometryVisualizer.plot(
        amm.geometry_group,
        title="Geometry for PSC Box bridge",
        show=True,
        include_finite_elements=True,
        include_reference_elements=True,
        include_links=True,
        flat=False,
        isometric=False,
        interactive=True
    )