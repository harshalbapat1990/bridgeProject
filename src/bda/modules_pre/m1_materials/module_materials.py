from bda.application.mapping.materials import MaterialMapper
from bda.application.interfaces.module.i_module import IModule

class MaterialsModule(IModule):

    @property
    def module_name(self) -> str:
        return "Materials"

    def _run(self) -> bool:
        materials_dto = self.data_provider.get_materials_for_project()
        self.logger.info("Retrieved %d materials from data provider.", len(materials_dto))

        for material in materials_dto:
            try:
                self.logger.debug("Processing material: %s", material.name)
                mat = MaterialMapper.to_domain(material)
                self.amm.add_initial_material(mat)
                self.logger.debug("Material: %s successfully added to MultiModel", material.name)


            except ValueError as e:
                self.logger.error(f"Material {material.name} not added to MultiModel due to: '{str(e)}'")
            except Exception as e:
                raise RuntimeError(f"Error processing material '{material.name}': {e}") from e

        return True