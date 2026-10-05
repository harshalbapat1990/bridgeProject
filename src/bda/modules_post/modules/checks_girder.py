from bda.infrastructure.adapters.analytical_software.config_providers.csi_config_provider import CSIBridgeConfigProvider
from bda.application.interfaces.module.i_module_post import IModulePost

class PT_Box_Module(IModulePost):

    @property
    def module_name(self) -> str:
        return "PT BOX"

    def _run(self):
        try:
            config = csi_config = CSIBridgeConfigProvider()
            # importer = CSI_Bridge_Importer(config_provider=config, create_new_instance=False)
            importer = self.importer

            multiModel = self.multiModel

            # pobieramy dane z programu
            forces = importer.import_forces(load_cases=['LC1', 'LC2'])  # Example load cases

            # wykonujemy sprawdzenia nośności przekazując pobrane dane
            bendingResult = BendingCheck().check(forces)
            shearResult = ShearCheck().check(forces)

            if not bendingResult:
                raise ValueError("Bending check failed")
            
            deflectionCheck = DeflectionCheck().check(bendingResult)

        except Exception as e:
            logger.error(f"GirderChecks failed: {e}")
            raise