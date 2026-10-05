"""
Shared fixtures for integration tests.

Key design goal: **do not churn the user's live CSI Bridge instance**.

Previously each CSI integration test either created a new CSI Bridge
process (``create_new_instance=True``) or attached its own ``CSIBridgeExporter``
and closed it in teardown, calling ``ApplicationExit`` in the process.
When dozens of tests ran back-to-back, the user's originally-open CSI
Bridge session_manager had its "Active API instance" flag flipped off — the
API-facing CSI that all subsequent attach-based tests depended on was
effectively lost, and every export test below that point skipped with
"CSI Bridge is not running".

The fixtures below solve this by:

1. Attaching **once** per test session_manager to the running CSI Bridge.
2. Yielding the same ``CSIBridgeExporter`` (and its ``sap_model``) to every
   test that needs it.
3. On teardown, releasing COM references via
   ``close_session(close_app=False)`` so the user's CSI instance is left
   running and API-active.

Tests that *must* spawn their own CSI process (the ones verifying the
create / attach / close lifecycle itself) are marked
``@pytest.mark.destructive`` and excluded from the default run. Opt in
with ``pytest -m destructive`` when you actually want to exercise those.

------------------------------------------------------------
WARNING: ``csi_fresh_model`` calls ``InitializeNewModel`` + ``File.NewBlank``
on the attached CSI session_manager, which **wipes whatever the user currently
has open in CSI Bridge**. Save your work before running the integration
suite. This is deliberate — material/section export tests need a
known-empty state.
------------------------------------------------------------
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from bda.infrastructure.adapters.analytical_software.config_providers.csi_config_provider import CSIBridgeConfigProvider
from bda.infrastructure.adapters.analytical_software.exporters.csi_bridge_exporter import CSIBridgeExporter
from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession


# ---------------------------------------------------------------------------
# CSI Bridge install detection (shared across files)
# ---------------------------------------------------------------------------

def _csi_install_dir() -> str:
    """Installation directory of CSI Bridge, derived from the configured
    program_path. Falls back to the conventional default."""
    try:
        config = CSIBridgeConfigProvider().load_config()
        exe_path = config.get("program_path")
        if exe_path:
            return str(Path(exe_path).parent)
    except Exception:
        pass
    return r"C:\Program Files\Computers and Structures\CSiBridge 26"


CSI_INSTALL_DIR = _csi_install_dir()


def csi_is_installed() -> bool:
    """True if a CSI Bridge install is present at the configured path."""
    return os.path.exists(CSI_INSTALL_DIR)


# ---------------------------------------------------------------------------
# Session-scoped CSI Bridge fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def csi_config_provider() -> CSIBridgeConfigProvider:
    """Real CSI Bridge configuration provider (session-scoped)."""
    return CSIBridgeConfigProvider()


@pytest.fixture(scope="session")
def csi_exporter(csi_config_provider):
    """Attach once to the running CSI Bridge for the whole test session.

    - Skips every dependent test if CSI Bridge is not installed.
    - Skips every dependent test if no CSI Bridge instance is running
      with an Active API flag (attach fails).
    - On teardown, releases COM references via ``close_session(close_app=False)``
      so the user's CSI Bridge process stays alive.

    Yields:
        CSIBridgeExporter attached to the running instance.
    """
    if not csi_is_installed():
        pytest.skip(f"CSI Bridge not installed at configured path: {CSI_INSTALL_DIR}")

    session = CSIBridgeSession(csi_config_provider)

    try:
        session.open_session(create_new_instance=False, template_file_path=None)
        exporter = CSIBridgeExporter(session)
    except RuntimeError as exc:
        pytest.skip(
            "CSI Bridge is not running with an Active API instance. "
            "Launch CSI Bridge manually, ensure the Active API flag is on, "
            "then rerun. If a prior test run killed the Active API flag, "
            f"restart CSI Bridge. Underlying error: {exc}"
        )

    try:
        yield exporter
    finally:
        # Release COM refs but leave the user's CSI process alive.
        try:
            session.close_session(close_app=False)
        except Exception:
            # Even if teardown fails, never raise from a session_manager-scoped
            # fixture — it would mask the real test failure.
            pass


@pytest.fixture
def csi_sap_model(csi_exporter):
    """SapModel pulled from the session_manager-scoped attached exporter.

    Function-scoped for ergonomics, but the underlying CSI session_manager is shared.
    Does NOT reset the model state — use ``csi_fresh_model`` for that.
    """
    return csi_exporter.sap_model


@pytest.fixture
def csi_fresh_model(csi_exporter):
    """Reset the attached CSI session_manager to a blank model before the test.

    Wipes the user's currently-open model. Tests that need a known-empty
    CSI state depend on this fixture; tests that just need to read
    something should depend on ``csi_sap_model`` instead.

    Yields:
        The same SapModel as ``csi_sap_model``, but after
        ``InitializeNewModel`` + ``File.NewBlank``.
    """
    sap_model = csi_exporter.sap_model
    try:
        ret1 = sap_model.InitializeNewModel()
        ret2 = sap_model.File.NewBlank()
    except Exception as exc:  # noqa: BLE001 - includes _ctypes.COMError
        # CSI Bridge process died (closed, crashed, or "RPC server is
        # unavailable"). Skip the rest of the dependent tests cleanly
        # instead of producing a wall of identical setup errors.
        pytest.skip(
            "CSI Bridge COM connection lost mid-suite "
            "(likely process closed or crashed). "
            "Restart CSI Bridge and rerun the failing batch. "
            f"Underlying error: {exc}"
        )
    if ret1 != 0 or ret2 != 0:
        pytest.fail(
            f"Failed to reset CSI Bridge to blank model "
            f"(InitializeNewModel={ret1}, NewBlank={ret2})"
        )
    yield sap_model


@pytest.fixture
def csi_exporter_fresh(csi_exporter, csi_fresh_model):
    """Session-attached exporter with its model reset to blank state.

    Use this when a test needs to call exporter-level helper methods
    like ``_export_materials`` or ``_export_sections`` against a clean
    CSI state.
    """
    return csi_exporter
