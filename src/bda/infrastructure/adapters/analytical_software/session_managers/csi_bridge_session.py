"""Session adapter for CSI Bridge COM runtime."""
from pathlib import Path
from typing import Optional

from bda.application.interfaces.analytical_software.session_manager import IAnalyticalSoftwareSession
from bda.infrastructure.adapters.analytical_software.config_providers.csi_config_provider import CSIBridgeConfigProvider
from bda.infrastructure.utils.logger import AppLogger

def _load_comtypes():
    """Load comtypes safely and provide a fake fallback for non-Windows tests."""
    try:
        import comtypes
        import comtypes.client as com_client
        import comtypes.gen as com_gen
        return comtypes, com_client, com_gen

    except Exception:
        class _FakeComtypes:
            class COMError(Exception):
                pass

            class client:
                @staticmethod
                def CreateObject(*args, **kwargs):
                    raise RuntimeError("COM is not available on this platform")

            class gen:
                class CSiBridge1:
                    class cHelper:
                        pass

        fake = _FakeComtypes()
        return fake, fake.client, fake.gen


comtypes, com_client, com_gen = _load_comtypes()


class CSIBridgeSession(IAnalyticalSoftwareSession):
    """Lifecycle owner for CSI Bridge COM objects."""

    def __init__(self, config_provider: CSIBridgeConfigProvider):
        self._config = config_provider
        self._program_id: str = self._config.program_id
        self._program_path: str = self._config.program_path
        self._helper_object: str = self._config.helper_object
        self._headless_mode: bool = self._config.headless_mode or False

        self._helper = None
        self._sap_object = None
        self._sap_model = None
        self._bridge_modeler = None

        self._initialize_helper()

        self.logger = AppLogger()

    @property
    def software_name(self) -> str:
        return "CSI Bridge"

    @property
    def sap_model(self):
        return self._sap_model

    @property
    def bridge_modeler(self):
        return self._bridge_modeler

    @property
    def config(self) -> CSIBridgeConfigProvider:
        return self._config

    def _initialize_helper(self) -> None:
        try:
            helper = comtypes.client.CreateObject(self._helper_object)
            self._helper = helper.QueryInterface(comtypes.gen.CSiBridge1.cHelper)
        except (OSError, comtypes.COMError) as e:
            raise RuntimeError(f"Failed to create CSI Bridge helper object: {e}")

    def open_session(
            self,
            create_new_instance: bool,
            template_file_path: Optional[str],
    ) -> bool:
        try:
            if create_new_instance:
                self._create_new_instance(template_file_path)

                self._initialize_model_objects()

                if template_file_path is None:
                    self._create_blank_model()
            else:
                self._attach_to_existing_instance()
                self._initialize_model_objects()

            return True

        except Exception as e:
            raise RuntimeError(f"Failed to open CSI Bridge session: {e}") from e

    def _attach_to_existing_instance(self) -> None:
        try:
            self._sap_object = self._helper.GetObject(self._program_id)
            self.logger.info("Attached to existing CSI Bridge instance")
        except (OSError, comtypes.COMError) as e:
            raise RuntimeError(f"No running CSI Bridge instance found: {e}")

    def _create_new_instance(self, template_file_path: Optional[str]) -> None:
        try:
            self._sap_object = self._helper.CreateObjectProgID(self._program_id)
            self._sap_object.ApplicationStart(
                Visible=not self._headless_mode, FileName=template_file_path
            )
        except (OSError, comtypes.COMError):
            try:
                self._sap_object = self._helper.CreateObject(self._program_path)
                self._sap_object.ApplicationStart(
                    Visible=not self._headless_mode, FileName=template_file_path
                )
            except (OSError, comtypes.COMError) as e:
                raise RuntimeError(f"Cannot create CSI Bridge instance: {e}")

        if self._headless_mode:
            self._sap_object.Hide()

    def _initialize_model_objects(self) -> None:
        self._sap_model = self._sap_object.SapModel
        self._bridge_modeler = self._sap_model.BridgeModeler_1

    def _create_blank_model(self) -> None:
        ret1 = self._sap_model.InitializeNewModel()
        ret2 = self._sap_model.File.NewBlank()
        if ret1 != 0 or ret2 != 0:
            raise RuntimeError("Failed to create blank model")

    def open_file(self, path: str) -> bool:
        return self._sap_model.File.OpenFile(path) == 0

    def save_model(self) -> bool:
        if self._sap_model.File.Save() == 0:
            self.logger.info(f"CsiBridge model has been successfully saved.")
            return True
        else:
            self.logger.warning(f"CsiBridge model has not been saved. ")
            return False

    def save_model_as(self, path: Path) -> bool:
        file_path = path.with_suffix(".sdb")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if self._sap_model.File.Save(str(file_path)) == 0:
            self.logger.info(f"CsiBridge model saved successfully in {path}.")
            return True
        else:
            self.logger.warning(f"CsiBridge model has not been saved. ")
            return False

    def unhide_ui(self) -> None:
        if self._sap_object:
            self._sap_object.Unhide()

    def has_analysis_results(self) -> bool:
        """Not yet implemented for CSI Bridge."""
        raise NotImplementedError(
            "CSIBridgeSession.has_analysis_results is not yet implemented."
        )

    def close_session(self, close_app: bool = True) -> None:
        try:
            self._bridge_modeler = None
            self._sap_model = None

            if self._sap_object is not None and close_app:
                try:
                    self._sap_object.ApplicationExit(False)
                except (OSError, comtypes.COMError) as e:
                    self.logger.warning(f"Could not close CSI Bridge application: {e}")
                finally:
                    self._sap_object = None
            else:
                self._sap_object = None

            self._helper = None

        except Exception as e:
            self.logger.error(f"Error during CSI session_manager close: {e}")
            raise

