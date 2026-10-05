"""Session adapter for MIDAS Civil runtime/API lifecycle."""

from pathlib import Path
import subprocess
import time
from typing import Any, Dict, Optional, cast

from bda.application.interfaces.analytical_software.session_manager import IAnalyticalSoftwareSession
from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import MidasConfigProvider
from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import MidasAPI
from bda.infrastructure.utils.logger import AppLogger


class MidasCivilSession(IAnalyticalSoftwareSession):
    """Lifecycle owner for MIDAS Civil API configuration and process management."""

    def __init__(self, config_provider: MidasConfigProvider):
        self._config = config_provider
        self._base_url = self._config.base_url
        self._mapi_key = self._config.mapi_key
        self._program_path = self._config.program_path

        self._midas_process: Optional[subprocess.Popen] = None
        self._created_instance = False
        self.model = None

        self.logger = AppLogger()


    @property
    def software_name(self) -> str:
        return "MIDAS Civil"

    @property
    def config(self) -> Dict[str, Any]:
        return self._config

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def mapi_key(self) -> str:
        return self._mapi_key

    @property
    def program_path(self) -> str:
        return self._program_path

    @property
    def created_instance(self) -> bool:
        return self._created_instance

    @property
    def midas_process(self) -> Optional[subprocess.Popen]:
        return self._midas_process

    def api(self) -> MidasAPI:
        """Create a MidasAPI transport bound to this session_manager configuration."""
        return MidasAPI(self.base_url, self.mapi_key, False)

    def _initialize_api(self) -> None:
        try:
            self.logger.debug(f"Importing Midas libraries: MAPI_BASEURL, MAPI_KEY, Model")
            from midas_civil import MAPI_BASEURL, MAPI_KEY, Model
            MAPI_KEY(self._mapi_key)
            MAPI_BASEURL(self._base_url)
            self.model = Model
            self.logger.debug("Successfully initialized MIDAS API")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize MIDAS API: {e}.")

    def open_session(
        self,
        create_new_instance: bool,
        template_file_path: Optional[str],
    ) -> bool:
        if not create_new_instance:
            self._initialize_api()
            return self.is_active

        try:
            self._launch_midas_application(template_file_path)
            self._created_instance = True
            self._initialize_api()
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to launch MIDAS Civil: {e}")

    def _wait_for_midas_ready(self, document_mode: bool = False, timeout: int = 180) -> None:
        deadline = time.time() + timeout
        self.logger.debug("Waiting for MIDAS Civil to become ready...")
        while time.time() < deadline:
            try:
                if self.is_active:
                    self.logger.debug("MIDAS Civil is ready.")
                    if not document_mode:
                        self.create_new_model()
                    return
                else:
                    raise RuntimeError("MIDAS Civil is not ready yet...")
            except Exception:
                self.logger.debug("Waiting for MIDAS Civil to become ready...")
                time.sleep(5)
        raise RuntimeError("MIDAS Civil did not become ready in time")

    def _launch_midas_application(self, template_file_path: Optional[str]) -> None:
        if not Path(self._program_path).exists():
            raise RuntimeError(f"MIDAS executable not found: {self._program_path}")

        new_document = template_file_path is None
        cmd = [self._program_path]
        if template_file_path:
            cmd.append(template_file_path)

        # CREATE_NEW_PROCESS_GROUP exists only on Windows; keep 0 elsewhere for CI compatibility.
        creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

        self._midas_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creation_flags,
        )
        self._wait_for_midas_ready(document_mode=not new_document)

        if self._midas_process.poll() is not None:
            raise RuntimeError("MIDAS Civil process terminated unexpectedly")

    @property
    def is_active(self) -> bool:
        test_request = self.api().request("GET", "/db/UNIT")
        return test_request.status_code == 200

    def has_analysis_results(self) -> bool:
        """Return True if the open model has at least one set of analysis results.

        Probes Midas by:
          1. Reading the first static load case name from ``/db/STLD``.
          2. Reading the first element key from ``/db/ELEM``.
          3. Sending a minimal ``/post/TABLE BEAMFORCEVBM`` request for that
             element + load case.
          4. Returning True only if the response DATA list is non-empty.

        Returns False (never raises) if any step fails — the caller should
        treat that as "not yet analyzed" and report accordingly.
        """
        api = self.api()
        try:
            # Step 1: first static load case name
            stld_resp = api.request("GET", "/db/STLD")
            stld_raw = stld_resp.json()
            stld_dict = stld_raw.get("STLD", {})
            if not stld_dict:
                # Fallback: first dict-valued key
                for v in stld_raw.values():
                    if isinstance(v, dict):
                        stld_dict = v
                        break
            if not stld_dict:
                logger.warning("has_analysis_results: no static load cases found")
                return False
            first_lc_props = next(iter(stld_dict.values()))
            if isinstance(first_lc_props, dict):
                first_lc = first_lc_props.get("NAME", first_lc_props.get("LCNAME", ""))
            else:
                first_lc = str(first_lc_props)
            if not first_lc:
                logger.warning("has_analysis_results: could not read first LC name")
                return False

            # Step 2: first element key
            elem_resp = api.request("GET", "/db/ELEM")
            elem_raw = elem_resp.json()
            elem_dict = elem_raw.get("ELEM", {})
            if not elem_dict:
                for v in elem_raw.values():
                    if isinstance(v, dict):
                        elem_dict = v
                        break
            if not elem_dict:
                logger.warning("has_analysis_results: no elements found in model")
                return False
            first_elem = int(next(iter(elem_dict.keys())))

            # Step 3: minimal probe force request
            probe_body = {
                "TABLE_TYPE": "BEAMFORCEVBM",
                "UNIT": {"FORCE": "kN", "DIST": "m"},
                "STYLES": {"FORMAT": "Fixed", "PLACE": 3},
                "COMPONENTS": [
                    "Elem", "Load", "Part",
                    "Axial", "Shear-y", "Shear-z",
                    "Torsion", "Moment-y", "Moment-z",
                ],
                "NODE_ELEMS": {"KEYS": [first_elem]},
                "LOAD_CASE_NAMES": [first_lc],
                "PARTS": ["PartI"],
            }
            probe_resp = api.request("POST", "/post/TABLE", probe_body)
            probe_data = probe_resp.json()

            # Step 4: check DATA
            for val in probe_data.values():
                if isinstance(val, dict) and "DATA" in val:
                    return bool(val["DATA"])
            return False

        except Exception as exc:
            logger.warning("has_analysis_results probe failed: %s", exc)
            return False

    def create_new_model(self, name: Optional[str] = None) -> bool:
        _ = name or "new_model"
        request = self.api().request("POST", "/doc/NEW")
        return request.status_code == 200

    def open_file(self, path: str) -> bool:
        self.logger.warning("MIDAS open_file is not implemented yet: %s", path)
        return False

    def save_model(self) -> bool:
        try:
            self.model.save("")
            self.logger.info(f"MIDAS model has been successfully saved.")
            return True
        except Exception as e:
            self.logger.warning(f"MIDAS model has not been saved. {e}")
            return False

    def save_model_as(self, path: Path) -> bool:
        try:
            file_path = path.with_suffix(".mcb")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            self.model.saveAs(str(file_path))
            self.logger.info(f"MIDAS model saved successfully in {path}.")
            return True
        except Exception as e:
            self.logger.warning(f"MIDAS model has not been saved. {e}")
            return False

    def close_session(self) -> None:
        if not self._created_instance or self._midas_process is None:
            return

        try:
            self._midas_process.terminate()
            try:
                self._midas_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._midas_process.kill()
                self._midas_process.wait()
        finally:
            self._midas_process = None
            self._created_instance = False

