from bda.application.interfaces.module import IModule
from bda.application.mapping.boundary_conditions.bearing_mapper import BearingMapper
from bda.modules_pre.m3_geometry.module_geometry_steel_composite import GeometrySteelCompositeModule

from bda.modules_pre.m5_bearings.helpers.bearings_bcs_builder import BearingsBCsBuilder


class BearingsBCsModule(IModule):

    @property
    def module_name(self):
        return "Bearings Boundary Conditions"

    def _run(self) -> bool:
        bearings = self._load_bearings()

        builder = BearingsBCsBuilder(
            amm= self.amm,
            logger= self.logger,
        )

        for support_bearings in bearings:
            builder.build(support_bearings)

        return True
        
    def _load_bearings(self):
        dto = (
            self.data_provider
            .get_bearing_boundary_conditions_for_project()
        )

        if not dto:
            raise ValueError("No Bearings Boundary Conditions found.")

        return BearingMapper.to_domain(dto)

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

    #
    #   COMMENT ONE OF THE FOLLOWING TWO LINES TO TEST THE OTHER BRIDGE TYPE
    #

    # BRIDGE_TYPE = "steel"
    BRIDGE_TYPE = "psc"

    if BRIDGE_TYPE == "steel":
        data_path = (
            r"C:\Users\CZERPAG\GitHub"
            r"\DesignAutomation.BridgeAutomationAndOptimisation"
            r"\tests\unit\fixtures\mvp_cases\steel-composite"
        )
        _GeometryModule = GeometrySteelCompositeModule
        structure_name = "Steel Composite Test Structure"

    else:
        data_path = (
            r"C:\Users\CZERPAG\GitHub"
            r"\DesignAutomation.BridgeAutomationAndOptimisation"
            r"\tests\unit\fixtures\mvp_cases\psc-box"
        )
        _GeometryModule = GeometryPSCBoxModule
        structure_name = "PSC Box Test Structure"
    # ------------------------------------------------------------------

    amm = AnalyticalMultiModel(
        unit_system=UnitSystem.SI,
        project_id=1,
        structure_id=1,
        structure_name=structure_name,
        description="Test Description")

    data_provider = DataFileProvider(data_path)

    logger = AppLogger()

    module_materials = MaterialsModule(amm, data_provider, logger)
    module_materials.run()

    module_sections = SectionsModule(amm, data_provider, logger)
    module_sections.run()

    module_geometry = _GeometryModule(amm, data_provider, logger)
    module_geometry.run()

    module_bearings = BearingsBCsModule(amm, data_provider, logger)
    module_bearings.run()

    assert isinstance(amm.geometry_group, GeometryGroup)

    fig = GeometryVisualizer.plot(
        amm.geometry_group,
        title=structure_name,
        show=True,
        include_finite_elements=True,
        include_reference_elements=True,
        include_links=True,
        flat=False,
        isometric=False,
        interactive=True
    )