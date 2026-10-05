from bda.domain.enums import UnitSystem, StructuralComponentType
from bda.application.mapping.geometry_groups.group_mapper import GeometryGroupMapper
from bda.application.interfaces.module.i_module import IModule
from bda.domain.models.submodels.sections import SectionCompositeBase
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.geometry_builder import (
    GeometrySteelCompositeBuilder,
)


class GeometrySteelCompositeModule(IModule):

    @property
    def module_name(self) -> str:
        return "Geometry for Steel composite bridge"

    def _run(self) -> bool:
        geometry_groups_dto = (self.data_provider.get_geometry_groups_for_project())
        self.logger.info("Retrieved %d groups from data provider.", len(geometry_groups_dto))

        if len(geometry_groups_dto) > 1:
            self.logger.warning("More than one geometry group found, using only the first one.")

        geometry_group_dto = geometry_groups_dto[0]

        geometry = GeometryGroupMapper.map_group(geometry_group_dto)

        self.amm.add_initial_geometry(geometry)

        # iterating through each span find all composite sections and assign first accessible deck material
        all_composite_sections = [s for s in self.amm.get_all_sections() if isinstance(s, SectionCompositeBase)]
        all_used_composite_sections = [s for s in self.amm.get_all_used_sections() if isinstance(s, SectionCompositeBase)]
        spans = self.amm.geometry_group.get_groups_by_component_type(StructuralComponentType.SPAN)

        for span in spans:
            deck_material = (
                next(
                    iter(
                        span.get_groups_by_component_type(StructuralComponentType.DECK_SLAB)
                    )
                ).get_material())

            sections = span.get_all_sections()
            composite_sections = [s for s in sections if isinstance(s, SectionCompositeBase)]

            for cs in composite_sections:
                cs.set_material_composite(deck_material)

        # Build geometry
        # Builder owns a fixed pipeline and only requires AMM with geometry.
        builder = GeometrySteelCompositeBuilder(amm=self.amm, logger=self.logger)
        builder.build()

        total_elements = sum(len(g.analytical_typology.elements) for g in self.amm.geometry_group.iter_groups())
        total_reference_elements = sum(len(g.reference_elements) for g in self.amm.geometry_group.iter_groups())
        self.logger.debug(
            "Initialized ModelSpace from AMM geometry (nodes=%d, elements=%d, reference_elements=%d).",
            len(builder.nodes_manager.nodes),
            total_elements,
            total_reference_elements,
        )

        return True


if __name__ == "__main__":

    from bda.domain import AnalyticalMultiModel
    from bda.infrastructure.data_providers import DataFileProvider
    from bda.infrastructure.utils import AppLogger
    from bda.modules_pre.m1_materials import MaterialsModule
    from bda.modules_pre.m2_sections.module_sections import SectionsModule

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

    from bda.modules_pre.m3_geometry.helpers.tools.visualizer import GeometryVisualizer
    # GeometryVisualizer.plot(amm.geometry_group,
    #                         title="Steel Composite Geometry",
    #                         show=False,
    #                         include_finite_elements=True,
    #                         include_reference_elements=False,
    #                         flat=False,
    #                         isometric=True,
    #                         interactive=True)

    bracings = amm.geometry_group.get_groups_by_component_type(StructuralComponentType.TRANSVERSE_BRACING)

    decks = amm.geometry_group.get_groups_by_component_type(StructuralComponentType.DECK_SLAB)
    deck_segments = decks[0].get_groups_by_component_type(StructuralComponentType.SEGMENT)

    girders = amm.geometry_group.get_groups_by_component_type(StructuralComponentType.GIRDER)

    diaphragms = amm.geometry_group.get_groups_by_component_type(StructuralComponentType.DIAPHRAGM)

    GeometryVisualizer.plot(amm.geometry_group,
                            title="Steel Composite Geometry",
                            show=True,
                            include_finite_elements=True,
                            include_reference_elements=True,
                            include_links=True,
                            flat=False,
                            isometric=False,
                            interactive=True
                            )

    print("finito")