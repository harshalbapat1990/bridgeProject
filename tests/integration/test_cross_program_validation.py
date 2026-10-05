"""Cross-program validation: CSI Bridge vs Midas Civil NX results.

This test module loads the *same* structural model from both CSI Bridge
and Midas Civil NX, fetches identical results, and compares them to
ensure sign conventions, axis mappings, and unit conversions are
consistent across both importers.

Requirements to run:
    1. CSI Bridge open with the validation model (API enabled).
    2. Midas Civil NX open with the same model (MAPI running).
    3. Both programs must have completed analysis.
    4. Environment variables set:
         - MIDAS_MAPI_KEY   — Midas API key
         - MIDAS_BASE_URL   — Midas base URL (default http://127.0.0.1:12101)
         - CSI_BRIDGE_RUNNING=1  — flag that CSI Bridge is available

Usage:
    pytest tests/integration/test_cross_program_validation.py -v -s

    Run with ``--tolerance=0.02`` to override the default 2% relative
    tolerance for numeric comparisons.
"""
from __future__ import annotations

import logging
import math
import os

import pytest

from bda.domain.enums.response_enums import ElementEnd
from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_set import ResultSet

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Relative tolerance for numeric comparisons (2% by default).
DEFAULT_RTOL = 0.02

# Elements and nodes to compare.  These must exist with the same domain id
# in both models.  Adjust as needed for your validation model.
VALIDATION_ELEMENT_IDS = frozenset({1, 5, 10})
VALIDATION_NODE_IDS = frozenset({1, 2, 3, 4})

# Load cases to compare.  Must have the same name in both programs.
VALIDATION_FORCE_LCS = frozenset({"Dead", "Live"})
VALIDATION_DISP_LCS = frozenset({"Dead", "Live"})

# Combination load cases — tests (CB:max)/(CB:min) handling
VALIDATION_COMBO_FORCE_LCS = frozenset({"ULS_gr5"})
VALIDATION_COMBO_DISP_LCS = frozenset({"ULS_gr5"})

# Stress load cases — TBD, both CSI and Midas stress fetchers are scaffolds
# VALIDATION_STRESS_LCS = frozenset({"Dead"})


# ---------------------------------------------------------------------------
# Skip markers
# ---------------------------------------------------------------------------

skip_no_csi = pytest.mark.skipif(
    not os.environ.get("CSI_BRIDGE_RUNNING"),
    reason="CSI Bridge not available (set CSI_BRIDGE_RUNNING=1)",
)
skip_no_midas = pytest.mark.skipif(
    not os.environ.get("MIDAS_MAPI_KEY"),
    reason="Midas not available (set MIDAS_MAPI_KEY)",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def csi_importer():
    """Connect to a running CSI Bridge instance and return its importer.

    Requires CSI Bridge to be open with the validation model and the
    API enabled (Options → Preferences → API → Active).
    """
    import comtypes.client

    raw_helper = comtypes.client.CreateObject("CSiBridge1.Helper")
    import comtypes.gen.CSiBridge1 as _csi_gen

    helper = raw_helper.QueryInterface(_csi_gen.cHelper)
    sap_object = helper.GetObject("CSI.CSiBridge.API.SapObject")
    if sap_object is None:
        sap_object = comtypes.client.GetActiveObject("CSiBridge.SapObject")
    sap_model = sap_object.SapModel

    from bda.infrastructure.adapters.analytical_software.importers import (
        CsiBridgeResultImporter,
    )
    from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession

    session = object.__new__(CSIBridgeSession)
    session._sap_model = sap_model
    importer = CsiBridgeResultImporter(session)
    yield importer


@pytest.fixture(scope="module")
def midas_importer():
    """Connect to a running Midas Civil NX instance and return its importer.

    Uses ``MidasCivilSession(MidasConfigProvider())`` to attach to a
    running MIDAS instance and passes that session_manager into the importer.

    The ``MIDAS_MAPI_KEY`` env-var is only used as a skip-gate — the
    actual credentials come from the config file.
    """
    from bda.infrastructure.adapters.analytical_software.importers import (
        MidasCivilResultImporter,
    )
    from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import \
        MidasConfigProvider
    from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import MidasCivilSession

    session = MidasCivilSession(MidasConfigProvider())
    session.open_session(create_new_instance=False, template_file_path=None)
    importer = MidasCivilResultImporter(session)
    yield importer
    session.close_session()


@pytest.fixture(scope="module")
def csi_results(csi_importer) -> ResultSet:
    """Fetch all validation results from CSI Bridge."""
    request = DataRequest(
        element_ids=VALIDATION_ELEMENT_IDS,
        node_ids=VALIDATION_NODE_IDS,
        force_loadcases=VALIDATION_FORCE_LCS | VALIDATION_COMBO_FORCE_LCS,
        disp_loadcases=VALIDATION_DISP_LCS | VALIDATION_COMBO_DISP_LCS,
    )
    return csi_importer.fetch(request)


@pytest.fixture(scope="module")
def midas_results(midas_importer) -> ResultSet:
    """Fetch all validation results from Midas Civil NX."""
    request = DataRequest(
        element_ids=VALIDATION_ELEMENT_IDS,
        node_ids=VALIDATION_NODE_IDS,
        force_loadcases=VALIDATION_FORCE_LCS | VALIDATION_COMBO_FORCE_LCS,
        disp_loadcases=VALIDATION_DISP_LCS | VALIDATION_COMBO_DISP_LCS,
    )
    return midas_importer.fetch(request)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _approx(value, *, rtol=DEFAULT_RTOL):
    """Return a ``pytest.approx`` matcher with the configured tolerance."""
    return pytest.approx(value, rel=rtol)


def _compare_force_envelopes(
    csi_results: ResultSet,
    midas_results: ResultSet,
    element_id: int,
    end: ElementEnd,
    load_case: str,
    rtol: float = DEFAULT_RTOL,
) -> None:
    """Compare force envelopes for one (element, end, load_case) pair."""
    key = (element_id, end, load_case)
    csi_env = csi_results.force_envelopes.get(key)
    midas_env = midas_results.force_envelopes.get(key)

    assert csi_env is not None, f"CSI missing force envelope for {key}"
    assert midas_env is not None, f"Midas missing force envelope for {key}"

    # Compare each ForceVector component (Fx through Mz) for both max and min
    for attr in ("Fx_max", "Fx_min", "Fy_max", "Fy_min", "Fz_max", "Fz_min",
                 "Mx_max", "Mx_min", "My_max", "My_min", "Mz_max", "Mz_min"):
        csi_fv = getattr(csi_env, attr)
        midas_fv = getattr(midas_env, attr)

        for comp in ("Fx", "Fy", "Fz", "Mx", "My", "Mz"):
            csi_val = getattr(csi_fv, comp).magnitude
            midas_val = getattr(midas_fv, comp).magnitude

            # Skip near-zero values to avoid divide-by-zero in relative checks
            if abs(csi_val) < 1e-6 and abs(midas_val) < 1e-6:
                continue

            assert midas_val == _approx(csi_val, rtol=rtol), (
                f"Force mismatch at {key}.{attr}.{comp}: "
                f"CSI={csi_val:.6f}, Midas={midas_val:.6f}"
            )


def _compare_displacement_envelopes(
    csi_results: ResultSet,
    midas_results: ResultSet,
    node_id: int,
    load_case: str,
    rtol: float = DEFAULT_RTOL,
) -> None:
    """Compare displacement envelopes for one (node, load_case) pair."""
    key = (node_id, load_case)
    csi_denv = csi_results.displacement_envelopes.get(key)
    midas_denv = midas_results.displacement_envelopes.get(key)

    assert csi_denv is not None, f"CSI missing displacement envelope for {key}"
    assert midas_denv is not None, f"Midas missing displacement envelope for {key}"

    # Compare each displacement component for both max and min
    for attr in ("UX_max", "UX_min", "UY_max", "UY_min", "UZ_max", "UZ_min",
                 "RX_max", "RX_min", "RY_max", "RY_min", "RZ_max", "RZ_min"):
        csi_nd = getattr(csi_denv, attr)
        midas_nd = getattr(midas_denv, attr)

        for comp in ("UX", "UY", "UZ", "RX", "RY", "RZ"):
            csi_val = getattr(csi_nd, comp).magnitude
            midas_val = getattr(midas_nd, comp).magnitude

            if abs(csi_val) < 1e-9 and abs(midas_val) < 1e-9:
                continue

            assert midas_val == _approx(csi_val, rtol=rtol), (
                f"Displacement mismatch at {key}.{attr}.{comp}: "
                f"CSI={csi_val:.9f}, Midas={midas_val:.9f}"
            )


# ---------------------------------------------------------------------------
# Tests — static load cases
# ---------------------------------------------------------------------------


@skip_no_csi
@skip_no_midas
class TestForceComparison:
    """Compare beam forces between CSI Bridge and Midas Civil NX."""

    @pytest.mark.parametrize("lc", sorted(VALIDATION_FORCE_LCS))
    @pytest.mark.parametrize("end", [ElementEnd.I, ElementEnd.J])
    @pytest.mark.parametrize("eid", sorted(VALIDATION_ELEMENT_IDS))
    def test_static_forces(self, csi_results, midas_results, eid, end, lc):
        """Element forces for static load cases should match."""
        _compare_force_envelopes(csi_results, midas_results, eid, end, lc)

    @pytest.mark.parametrize("lc", sorted(VALIDATION_COMBO_FORCE_LCS))
    @pytest.mark.parametrize("end", [ElementEnd.I, ElementEnd.J])
    @pytest.mark.parametrize("eid", sorted(VALIDATION_ELEMENT_IDS))
    def test_combo_forces(self, csi_results, midas_results, eid, end, lc):
        """Element forces for combination load cases should match.

        Both importers must produce compatible envelopes from
        (CB:max)/(CB:min) rows.
        """
        _compare_force_envelopes(csi_results, midas_results, eid, end, lc)


@skip_no_csi
@skip_no_midas
class TestDisplacementComparison:
    """Compare nodal displacements between CSI Bridge and Midas Civil NX."""

    @pytest.mark.parametrize("lc", sorted(VALIDATION_DISP_LCS))
    @pytest.mark.parametrize("nid", sorted(VALIDATION_NODE_IDS))
    def test_static_displacements(self, csi_results, midas_results, nid, lc):
        """Nodal displacements for static load cases should match."""
        _compare_displacement_envelopes(csi_results, midas_results, nid, lc)

    @pytest.mark.parametrize("lc", sorted(VALIDATION_COMBO_DISP_LCS))
    @pytest.mark.parametrize("nid", sorted(VALIDATION_NODE_IDS))
    def test_combo_displacements(self, csi_results, midas_results, nid, lc):
        """Nodal displacements for combination load cases should match.

        TBD: Verify that (CB:max)/(CB:min) for displacements behaves
        the same as for forces in Midas.
        """
        _compare_displacement_envelopes(csi_results, midas_results, nid, lc)


# ---------------------------------------------------------------------------
# Tests — sign convention and axis mapping
# ---------------------------------------------------------------------------


@skip_no_csi
@skip_no_midas
class TestSignConventions:
    """Verify that sign conventions are consistent between programs.

    These tests focus on known potential discrepancies:
    - Axial force sign (tension positive vs compression positive)
    - Shear force direction relative to local axes
    - Moment sign convention (sagging vs hogging)
    - Displacement sign (global axis direction)
    """

    def test_axial_sign_consistency(self, csi_results, midas_results):
        """If CSI reports tension as positive, Midas should agree.

        Pick a load case where we know the sign from first principles
        (e.g. self-weight should produce compression in columns).
        """
        # Use element 1 under Dead load as the reference
        key = (1, ElementEnd.I, "Dead")
        csi_env = csi_results.force_envelopes.get(key)
        midas_env = midas_results.force_envelopes.get(key)

        if csi_env is None or midas_env is None:
            pytest.skip("Element 1 / Dead not available in both programs")

        csi_fx = csi_env.Fx_max.Fx.magnitude
        midas_fx = midas_env.Fx_max.Fx.magnitude

        # Same sign means consistent convention
        if abs(csi_fx) > 1e-6 and abs(midas_fx) > 1e-6:
            assert math.copysign(1, csi_fx) == math.copysign(1, midas_fx), (
                f"Axial sign mismatch: CSI Fx={csi_fx}, Midas Fx={midas_fx}"
            )

    def test_moment_sign_consistency(self, csi_results, midas_results):
        """Major bending moment (Mz) should have the same sign.

        For a simply supported beam under gravity, sagging moment at
        mid-span should be positive in both programs.
        """
        key = (1, ElementEnd.I, "Dead")
        csi_env = csi_results.force_envelopes.get(key)
        midas_env = midas_results.force_envelopes.get(key)

        if csi_env is None or midas_env is None:
            pytest.skip("Element 1 / Dead not available in both programs")

        csi_mz = csi_env.Mz_max.Mz.magnitude
        midas_mz = midas_env.Mz_max.Mz.magnitude

        if abs(csi_mz) > 1e-6 and abs(midas_mz) > 1e-6:
            assert math.copysign(1, csi_mz) == math.copysign(1, midas_mz), (
                f"Moment sign mismatch: CSI Mz={csi_mz}, Midas Mz={midas_mz}"
            )

    def test_vertical_displacement_sign(self, csi_results, midas_results):
        """Vertical displacement (UZ) should have the same sign.

        Under gravity, a mid-span node should deflect downward. Both
        programs should report UZ as negative (assuming Z is upward).
        """
        key = (2, "Dead")
        csi_denv = csi_results.displacement_envelopes.get(key)
        midas_denv = midas_results.displacement_envelopes.get(key)

        if csi_denv is None or midas_denv is None:
            pytest.skip("Node 2 / Dead not available in both programs")

        csi_uz = csi_denv.UZ_max.UZ.magnitude
        midas_uz = midas_denv.UZ_max.UZ.magnitude

        if abs(csi_uz) > 1e-9 and abs(midas_uz) > 1e-9:
            assert math.copysign(1, csi_uz) == math.copysign(1, midas_uz), (
                f"UZ sign mismatch: CSI={csi_uz}, Midas={midas_uz}"
            )


# ---------------------------------------------------------------------------
# Tests — stress comparison (TBD)
# ---------------------------------------------------------------------------


@skip_no_csi
@skip_no_midas
class TestStressComparison:
    """Cross-program stress comparison — currently a placeholder.

    Both the CSI and Midas stress fetchers are scaffolds (TBD).
    Enable these tests once both are fully implemented.
    """

    @pytest.mark.skip(reason="Stress fetchers are scaffolds — TBD")
    def test_stress_basic(self, csi_results, midas_results):
        """Placeholder for stress comparison."""
        pass

    @pytest.mark.skip(reason="CB:max/CB:min for stresses — TBD")
    def test_stress_combo_envelope(self, csi_results, midas_results):
        """Placeholder for combination stress envelope comparison."""
        pass
