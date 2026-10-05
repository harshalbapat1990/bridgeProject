"""Unit tests for the CSI Bridge result importer (mocked COM).

Mirrors the pattern of test_midas_importer.py: all COM calls are
replaced with unittest.mock so these tests run without CSI Bridge
installed.

Covers:
    - CsiIdMapper: name↔id parsing (prefixed and unprefixed)
    - CsiForcesFetcher: station classification, force vector construction,
      envelope widening via ResultSet, load-case filtering
    - CsiDisplacementsFetcher: displacement construction, envelope
      deposit, load-case filtering
    - CsiLoadCaseResolver: index building, resolve, enable_for_output
    - CsiUnitsContext: enter/exit unit switching
    - CsiBridgeResultImporter.fetch: end-to-end with mocked COM
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bda.domain.enums import OutputSoftware
from bda.infrastructure.utils import (
    CSI_UNIT_CODE_KN_M_C,
)
from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession
from bda.domain.enums.load_case_enums import LoadCaseType
from bda.domain.enums.response_enums import ElementEnd
from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_set import ResultSet


# =====================================================================
# Mock helpers
# =====================================================================


def _make_mock_sap_model(
    frame_names=("F1", "F2"),
    point_names=("J1", "J2", "J3"),
    section_names=("S1",),
    material_names=("M1",),
    case_names=("Dead", "Live"),
    combo_names=("ULS_gr5",),
    combo_types=None,
) -> MagicMock:
    """Build a mock SapModel with GetNameList stubs for the id mapper,
    load case resolver, and results endpoints.

    combo_types: dict mapping combo name → type code (1=envelope, 0=linear)
    """
    if combo_types is None:
        combo_types = {"ULS_gr5": 1}  # default: envelope

    sap = MagicMock()

    # FrameObj.GetNameList → (count, names_tuple)
    sap.FrameObj.GetNameList.return_value = (len(frame_names), frame_names)
    # PointObj.GetNameList → (count, names_tuple)
    sap.PointObj.GetNameList.return_value = (len(point_names), point_names)
    # PropFrame.GetNameList
    sap.PropFrame.GetNameList.return_value = (len(section_names), section_names)
    # PropMaterial.GetNameList
    sap.PropMaterial.GetNameList.return_value = (len(material_names), material_names)

    # LoadCases.GetNameList
    sap.LoadCases.GetNameList.return_value = (len(case_names), case_names)
    # RespCombo.GetNameList
    sap.RespCombo.GetNameList.return_value = (len(combo_names), combo_names)
    # RespCombo.GetTypeOAPI — returns tuple with type code
    sap.RespCombo.GetTypeOAPI.side_effect = lambda name: (combo_types.get(name, 0),)

    # Results.Setup — capture/restore calls
    sap.Results.Setup.GetCaseSelectedForOutput.return_value = False
    sap.Results.Setup.GetComboSelectedForOutput.return_value = False
    sap.Results.Setup.SetCaseSelectedForOutput.return_value = None
    sap.Results.Setup.SetComboSelectedForOutput.return_value = None
    sap.Results.Setup.DeselectAllCasesAndCombosForOutput.return_value = None

    # GetPresentUnits / SetPresentUnits for CsiUnitsContext
    sap.GetPresentUnits.return_value = 1  # some non-canonical code
    sap.SetPresentUnits.return_value = None

    return sap


def _make_csi_session_with_sap(sap: MagicMock) -> CSIBridgeSession:
    session = object.__new__(CSIBridgeSession)
    session._sap_model = sap
    return session


def _mock_frame_force_response(
    element_name: str,
    rows: list[dict],
) -> tuple:
    """Build the tuple that sap_model.Results.FrameForce returns.

    Each row dict has keys: station, load_case, step_type,
    fx, fy, fz, mx, my, mz.
    """
    count = len(rows)
    obj_names = [element_name] * count
    obj_stations = [r.get("obj_station", r["station"]) for r in rows]
    elm_names = [element_name] * count
    elm_stations = [r["station"] for r in rows]
    load_cases = [r["load_case"] for r in rows]
    step_types = [r.get("step_type", "") for r in rows]
    step_nums = [0.0] * count
    fx = [r["fx"] for r in rows]
    fy = [r["fy"] for r in rows]
    fz = [r["fz"] for r in rows]
    mx = [r["mx"] for r in rows]
    my = [r["my"] for r in rows]
    mz = [r["mz"] for r in rows]
    ret = 0

    return (
        count,           # [0]
        obj_names,       # [1]
        obj_stations,    # [2] ObjSta
        elm_names,       # [3]
        elm_stations,    # [4] ElmSta — used for I/J classification
        load_cases,      # [5]
        step_types,      # [6]
        step_nums,       # [7]
        fx,              # [8]  P
        fy,              # [9]  V2
        fz,              # [10] V3
        mx,              # [11] T
        my,              # [12] M2
        mz,              # [13] M3
        ret,             # [14]
    )


def _mock_joint_displ_response(
    node_name: str,
    rows: list[dict],
) -> tuple:
    """Build the tuple that sap_model.Results.JointDispl returns.

    Each row dict has keys: load_case, step_type,
    ux, uy, uz, rx, ry, rz.
    """
    count = len(rows)
    obj_names = [node_name] * count
    elm_names = [node_name] * count
    load_cases = [r["load_case"] for r in rows]
    step_types = [r.get("step_type", "") for r in rows]
    step_nums = [0.0] * count
    ux = [r["ux"] for r in rows]
    uy = [r["uy"] for r in rows]
    uz = [r["uz"] for r in rows]
    rx = [r["rx"] for r in rows]
    ry = [r["ry"] for r in rows]
    rz = [r["rz"] for r in rows]
    ret = 0

    return (
        count,           # [0]
        obj_names,       # [1]
        elm_names,       # [2]
        load_cases,      # [3]  ← confirmed at index 3
        step_types,      # [4]
        step_nums,       # [5]
        ux,              # [6]
        uy,              # [7]
        uz,              # [8]
        rx,              # [9]
        ry,              # [10]
        rz,              # [11]
        ret,             # [12]
    )


def _mock_get_points(i_name: str, j_name: str):
    """Build the return value for FrameObj.GetPoints."""
    return (i_name, j_name, 0)


def _mock_get_coord(x: float, y: float, z: float):
    """Build the return value for PointObj.GetCoordCartesian."""
    return (x, y, z, 0)


# =====================================================================
# TestCsiIdMapper
# =====================================================================


class TestCsiIdMapper:
    """Tests for CsiIdMapper — name<->id parsing from CSI."""

    def test_prefixed_names(self):
        """Standard exporter names like F1, J2 should parse correctly."""
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiIdMapper

        sap = _make_mock_sap_model(
            frame_names=("F1", "F10", "F99"),
            point_names=("J1", "J5"),
        )
        mapper = CsiIdMapper(sap)

        assert mapper.element_name(1) == "F1"
        assert mapper.element_name(10) == "F10"
        assert mapper.element_id("F99") == 99
        assert mapper.node_name(1) == "J1"
        assert mapper.node_name(5) == "J5"
        assert mapper.node_id("J5") == 5

    def test_unprefixed_names(self):
        """Models built directly in CSI may have plain integer names."""
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiIdMapper

        sap = _make_mock_sap_model(
            frame_names=("1", "2", "10"),
            point_names=("1", "2"),
        )
        mapper = CsiIdMapper(sap)

        assert mapper.element_name(1) == "1"
        assert mapper.element_name(10) == "10"
        assert mapper.node_name(1) == "1"

    def test_missing_element_raises(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiIdMapper

        sap = _make_mock_sap_model(frame_names=("F1",))
        mapper = CsiIdMapper(sap)

        with pytest.raises(KeyError):
            mapper.element_name(999)

    def test_missing_node_raises(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiIdMapper

        sap = _make_mock_sap_model(point_names=("J1",))
        mapper = CsiIdMapper(sap)

        with pytest.raises(KeyError):
            mapper.node_name(999)

    def test_section_and_material_lookups(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiIdMapper

        sap = _make_mock_sap_model(
            section_names=("S5", "S10"),
            material_names=("M1", "M3"),
        )
        mapper = CsiIdMapper(sap)

        assert mapper.section_name(5) == "S5"
        assert mapper.section_id("S10") == 10
        assert mapper.material_name(1) == "M1"
        assert mapper.material_id("M3") == 3


# =====================================================================
# TestCsiUnitsContext
# =====================================================================


class TestCsiUnitsContext:
    """Tests for CsiUnitsContext — enter/exit unit switching."""

    def test_enter_sets_canonical(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiUnitsContext

        sap = MagicMock()
        sap.GetPresentUnits.return_value = 1

        ctx = CsiUnitsContext(sap)
        ctx.__enter__()

        sap.SetPresentUnits.assert_called_with(CSI_UNIT_CODE_KN_M_C)

    def test_exit_restores_previous(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiUnitsContext

        sap = MagicMock()
        sap.GetPresentUnits.return_value = 42  # some arbitrary previous code

        ctx = CsiUnitsContext(sap)
        ctx.__enter__()
        sap.SetPresentUnits.reset_mock()
        ctx.__exit__(None, None, None)

        sap.SetPresentUnits.assert_called_with(42)

    def test_context_manager_protocol(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiUnitsContext

        sap = MagicMock()
        sap.GetPresentUnits.return_value = 1

        with CsiUnitsContext(sap) as ctx:
            assert ctx is not None

        # Should have called SetPresentUnits twice: canonical + restore
        assert sap.SetPresentUnits.call_count == 2


# =====================================================================
# TestCsiForcesFetcher
# =====================================================================


class TestCsiForcesFetcher:
    """Tests for CsiForcesFetcher with mocked COM responses."""

    def _make_fetcher(self, sap=None, frame_names=("F1",), point_names=("J1", "J2")):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiIdMapper
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiLoadCaseResolver
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiForcesFetcher

        if sap is None:
            sap = _make_mock_sap_model(
                frame_names=frame_names,
                point_names=point_names,
            )

        mapper = CsiIdMapper(sap)
        resolver = CsiLoadCaseResolver(sap)
        fetcher = CsiForcesFetcher(sap, mapper, resolver)
        return fetcher, sap

    def test_station_classification_i_end(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiForcesFetcher

        assert CsiForcesFetcher._classify_station(0.0, 10.0) == ElementEnd.I
        assert CsiForcesFetcher._classify_station(1e-5, 10.0) == ElementEnd.I

    def test_station_classification_j_end(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiForcesFetcher

        assert CsiForcesFetcher._classify_station(10.0, 10.0) == ElementEnd.J
        assert CsiForcesFetcher._classify_station(9.99995, 10.0) == ElementEnd.J

    def test_station_classification_mid(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiForcesFetcher

        assert CsiForcesFetcher._classify_station(5.0, 10.0) is None

    def test_fetch_into_single_load_case(self):
        """Single static load case produces one envelope per end."""
        fetcher, sap = self._make_fetcher()

        # Mock GetPoints and GetCoordCartesian for element length calc
        sap.FrameObj.GetPoints.return_value = _mock_get_points("J1", "J2")
        sap.PointObj.GetCoordCartesian.side_effect = [
            _mock_get_coord(0.0, 0.0, 0.0),  # J1
            _mock_get_coord(10.0, 0.0, 0.0),  # J2 → length = 10
        ]

        # Mock FrameForce result — I end and J end rows
        sap.Results.FrameForce.return_value = _mock_frame_force_response(
            "F1",
            [
                {"station": 0.0, "load_case": "Dead", "fx": 100, "fy": 50,
                 "fz": 10, "mx": 5, "my": 20, "mz": 300},
                {"station": 10.0, "load_case": "Dead", "fx": -100, "fy": -50,
                 "fz": -10, "mx": -5, "my": -20, "mz": -300},
            ],
        )

        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"Dead"}),
        )
        rs = ResultSet()
        fetcher.fetch_into(request, rs)

        # Should have two envelopes: (1, I, Dead) and (1, J, Dead)
        assert (1, ElementEnd.I, "Dead") in rs.force_envelopes
        assert (1, ElementEnd.J, "Dead") in rs.force_envelopes

        env_i = rs.force_envelopes[(1, ElementEnd.I, "Dead")]
        assert env_i.Fx_max.Fx.magnitude == pytest.approx(100)
        assert env_i.Mz_max.Mz.magnitude == pytest.approx(300)

        env_j = rs.force_envelopes[(1, ElementEnd.J, "Dead")]
        assert env_j.Fx_max.Fx.magnitude == pytest.approx(-100)

    def test_fetch_into_skips_unrequested_lc(self):
        """Load cases not in the request should be skipped."""
        fetcher, sap = self._make_fetcher()

        sap.FrameObj.GetPoints.return_value = _mock_get_points("J1", "J2")
        sap.PointObj.GetCoordCartesian.side_effect = [
            _mock_get_coord(0.0, 0.0, 0.0),
            _mock_get_coord(10.0, 0.0, 0.0),
        ]

        sap.Results.FrameForce.return_value = _mock_frame_force_response(
            "F1",
            [
                {"station": 0.0, "load_case": "Dead", "fx": 100, "fy": 0,
                 "fz": 0, "mx": 0, "my": 0, "mz": 0},
                {"station": 0.0, "load_case": "Live", "fx": 200, "fy": 0,
                 "fz": 0, "mx": 0, "my": 0, "mz": 0},
            ],
        )

        # Only request "Dead" — "Live" should be skipped
        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"Dead"}),
        )
        rs = ResultSet()
        fetcher.fetch_into(request, rs)

        assert (1, ElementEnd.I, "Dead") in rs.force_envelopes
        assert (1, ElementEnd.I, "Live") not in rs.force_envelopes

    def test_fetch_into_skips_mid_stations(self):
        """Intermediate stations should be discarded."""
        fetcher, sap = self._make_fetcher()

        sap.FrameObj.GetPoints.return_value = _mock_get_points("J1", "J2")
        sap.PointObj.GetCoordCartesian.side_effect = [
            _mock_get_coord(0.0, 0.0, 0.0),
            _mock_get_coord(10.0, 0.0, 0.0),
        ]

        sap.Results.FrameForce.return_value = _mock_frame_force_response(
            "F1",
            [
                {"station": 0.0, "load_case": "Dead", "fx": 100, "fy": 0,
                 "fz": 0, "mx": 0, "my": 0, "mz": 0},
                {"station": 5.0, "load_case": "Dead", "fx": 150, "fy": 0,
                 "fz": 0, "mx": 0, "my": 0, "mz": 0},  # mid station
                {"station": 10.0, "load_case": "Dead", "fx": -100, "fy": 0,
                 "fz": 0, "mx": 0, "my": 0, "mz": 0},
            ],
        )

        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"Dead"}),
        )
        rs = ResultSet()
        fetcher.fetch_into(request, rs)

        # Only I and J ends, no mid station
        assert len(rs.force_envelopes) == 2

    def test_envelope_widening_from_multiple_rows(self):
        """Combination LCs produce multiple rows that should widen the envelope."""
        fetcher, sap = self._make_fetcher()

        sap.FrameObj.GetPoints.return_value = _mock_get_points("J1", "J2")
        sap.PointObj.GetCoordCartesian.side_effect = [
            _mock_get_coord(0.0, 0.0, 0.0),
            _mock_get_coord(10.0, 0.0, 0.0),
        ]

        # Two rows at station 0 for same LC — simulates StepType Max/Min
        sap.Results.FrameForce.return_value = _mock_frame_force_response(
            "F1",
            [
                {"station": 0.0, "load_case": "ULS_gr5", "step_type": "Max",
                 "fx": 200, "fy": 50, "fz": 10, "mx": 5, "my": 20, "mz": 500},
                {"station": 0.0, "load_case": "ULS_gr5", "step_type": "Min",
                 "fx": -100, "fy": -30, "fz": -5, "mx": -2, "my": -10, "mz": -200},
            ],
        )

        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"ULS_gr5"}),
        )
        rs = ResultSet()
        fetcher.fetch_into(request, rs)

        env = rs.force_envelopes[(1, ElementEnd.I, "ULS_gr5")]
        assert env.Fx_max.Fx.magnitude == pytest.approx(200)
        assert env.Fx_min.Fx.magnitude == pytest.approx(-100)
        assert env.Mz_max.Mz.magnitude == pytest.approx(500)
        assert env.Mz_min.Mz.magnitude == pytest.approx(-200)

    def test_zero_rows_does_not_crash(self):
        """If FrameForce returns 0 rows, no envelope is deposited."""
        fetcher, sap = self._make_fetcher()

        sap.FrameObj.GetPoints.return_value = _mock_get_points("J1", "J2")
        sap.PointObj.GetCoordCartesian.side_effect = [
            _mock_get_coord(0.0, 0.0, 0.0),
            _mock_get_coord(10.0, 0.0, 0.0),
        ]

        sap.Results.FrameForce.return_value = (0, [], [], [], [], [], [], [], [], [], [], [], [], [], 0)

        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"Dead"}),
        )
        rs = ResultSet()
        fetcher.fetch_into(request, rs)

        assert len(rs.force_envelopes) == 0


# =====================================================================
# TestCsiDisplacementsFetcher
# =====================================================================


class TestCsiDisplacementsFetcher:
    """Tests for CsiDisplacementsFetcher with mocked COM responses."""

    def _make_fetcher(self, sap=None):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiIdMapper
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiDisplacementsFetcher

        if sap is None:
            sap = _make_mock_sap_model()

        mapper = CsiIdMapper(sap)
        fetcher = CsiDisplacementsFetcher(sap, mapper)
        return fetcher, sap

    def test_fetch_into_single_load_case(self):
        fetcher, sap = self._make_fetcher()

        sap.Results.JointDispl.return_value = _mock_joint_displ_response(
            "J1",
            [
                {"load_case": "Dead", "ux": 0.001, "uy": 0.002,
                 "uz": -0.005, "rx": 0.0001, "ry": 0.0002, "rz": 0.0003},
            ],
        )

        request = DataRequest(
            node_ids=frozenset({1}),
            disp_loadcases=frozenset({"Dead"}),
        )
        rs = ResultSet()
        fetcher.fetch_into(request, rs)

        assert (1, "Dead") in rs.displacement_envelopes
        denv = rs.displacement_envelopes[(1, "Dead")]
        assert denv.UX_max.UX.magnitude == pytest.approx(0.001)
        assert denv.UZ_max.UZ.magnitude == pytest.approx(-0.005)

    def test_fetch_into_skips_unrequested_lc(self):
        fetcher, sap = self._make_fetcher()

        sap.Results.JointDispl.return_value = _mock_joint_displ_response(
            "J1",
            [
                {"load_case": "Dead", "ux": 0.001, "uy": 0, "uz": 0,
                 "rx": 0, "ry": 0, "rz": 0},
                {"load_case": "Live", "ux": 0.002, "uy": 0, "uz": 0,
                 "rx": 0, "ry": 0, "rz": 0},
            ],
        )

        request = DataRequest(
            node_ids=frozenset({1}),
            disp_loadcases=frozenset({"Dead"}),
        )
        rs = ResultSet()
        fetcher.fetch_into(request, rs)

        assert (1, "Dead") in rs.displacement_envelopes
        assert (1, "Live") not in rs.displacement_envelopes

    def test_envelope_widening_from_steptype(self):
        """StepType Max/Min rows should widen the displacement envelope."""
        fetcher, sap = self._make_fetcher()

        sap.Results.JointDispl.return_value = _mock_joint_displ_response(
            "J1",
            [
                {"load_case": "ULS_gr5", "step_type": "Max",
                 "ux": 0.005, "uy": 0.001, "uz": -0.001,
                 "rx": 0.001, "ry": 0.001, "rz": 0.001},
                {"load_case": "ULS_gr5", "step_type": "Min",
                 "ux": -0.003, "uy": -0.001, "uz": -0.008,
                 "rx": -0.001, "ry": -0.001, "rz": -0.001},
            ],
        )

        request = DataRequest(
            node_ids=frozenset({1}),
            disp_loadcases=frozenset({"ULS_gr5"}),
        )
        rs = ResultSet()
        fetcher.fetch_into(request, rs)

        denv = rs.displacement_envelopes[(1, "ULS_gr5")]
        assert denv.UX_max.UX.magnitude == pytest.approx(0.005)
        assert denv.UX_min.UX.magnitude == pytest.approx(-0.003)
        assert denv.UZ_max.UZ.magnitude == pytest.approx(-0.001)
        assert denv.UZ_min.UZ.magnitude == pytest.approx(-0.008)

    def test_zero_rows_does_not_crash(self):
        fetcher, sap = self._make_fetcher()

        sap.Results.JointDispl.return_value = (0, [], [], [], [], [], [], [], [], [], [], [], 0)

        request = DataRequest(
            node_ids=frozenset({1}),
            disp_loadcases=frozenset({"Dead"}),
        )
        rs = ResultSet()
        fetcher.fetch_into(request, rs)

        assert len(rs.displacement_envelopes) == 0

    def test_multiple_nodes(self):
        """Fetcher should iterate over all requested node ids."""
        fetcher, sap = self._make_fetcher()

        def joint_displ_side_effect(node_name, item_type):
            if node_name == "J1":
                return _mock_joint_displ_response(
                    "J1",
                    [{"load_case": "Dead", "ux": 0.001, "uy": 0, "uz": 0,
                      "rx": 0, "ry": 0, "rz": 0}],
                )
            elif node_name == "J2":
                return _mock_joint_displ_response(
                    "J2",
                    [{"load_case": "Dead", "ux": 0.002, "uy": 0, "uz": 0,
                      "rx": 0, "ry": 0, "rz": 0}],
                )
            return (0, [], [], [], [], [], [], [], [], [], [], [], 0)

        sap.Results.JointDispl.side_effect = joint_displ_side_effect

        request = DataRequest(
            node_ids=frozenset({1, 2}),
            disp_loadcases=frozenset({"Dead"}),
        )
        rs = ResultSet()
        fetcher.fetch_into(request, rs)

        assert (1, "Dead") in rs.displacement_envelopes
        assert (2, "Dead") in rs.displacement_envelopes


# =====================================================================
# TestCsiLoadCaseResolver
# =====================================================================


class TestCsiLoadCaseResolver:
    """Tests for CsiLoadCaseResolver — index building and resolution."""

    def test_available(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiLoadCaseResolver

        sap = _make_mock_sap_model(
            case_names=("Dead", "Live"),
            combo_names=("ULS_gr5",),
            combo_types={"ULS_gr5": 1},
        )
        resolver = CsiLoadCaseResolver(sap)

        lcs = resolver.available()
        names = {lc.name for lc in lcs}
        assert "Dead" in names
        assert "Live" in names
        assert "ULS_gr5" in names

    def test_resolve_valid(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiLoadCaseResolver

        sap = _make_mock_sap_model()
        resolver = CsiLoadCaseResolver(sap)

        resolved = resolver.resolve(["Dead", "ULS_gr5"])
        assert len(resolved) == 2
        assert resolved[0].name == "Dead"
        assert resolved[0].kind == LoadCaseType.SINGLE_VALUED
        assert resolved[1].name == "ULS_gr5"
        assert resolved[1].kind == LoadCaseType.ENVELOPE

    def test_resolve_unknown_raises(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiLoadCaseResolver

        sap = _make_mock_sap_model()
        resolver = CsiLoadCaseResolver(sap)

        with pytest.raises(KeyError, match="not found in CSI model"):
            resolver.resolve(["NonExistent"])

    def test_enable_for_output_calls_correct_api(self):
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiLoadCaseResolver

        sap = _make_mock_sap_model(
            case_names=("Dead",),
            combo_names=("ULS_gr5",),
            combo_types={"ULS_gr5": 1},
        )
        resolver = CsiLoadCaseResolver(sap)

        resolver.enable_for_output(["Dead", "ULS_gr5"])

        sap.Results.Setup.SetCaseSelectedForOutput.assert_called_with("Dead", True)
        sap.Results.Setup.SetComboSelectedForOutput.assert_called_with("ULS_gr5", True)

    def test_combo_classification_linear_additive(self):
        """Type code 0 should classify as COMBINATION (linear additive)."""
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiLoadCaseResolver

        sap = _make_mock_sap_model(
            combo_names=("SLS_freq",),
            combo_types={"SLS_freq": 0},
        )
        resolver = CsiLoadCaseResolver(sap)

        resolved = resolver.resolve(["SLS_freq"])
        assert resolved[0].kind == LoadCaseType.COMBINATION


# =====================================================================
# TestCsiBridgeResultImporter (end-to-end with mocked COM)
# =====================================================================


class TestCsiBridgeResultImporter:
    """End-to-end test of CsiBridgeResultImporter.fetch with mocked COM."""

    def test_fetch_forces_and_displacements(self):
        """fetch() should produce a ResultSet with forces and displacements."""
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import (
            CsiBridgeResultImporter,
        )

        sap = _make_mock_sap_model(
            frame_names=("F1",),
            point_names=("J1", "J2"),
            case_names=("Dead",),
            combo_names=(),
        )

        # Mock element length
        sap.FrameObj.GetPoints.return_value = _mock_get_points("J1", "J2")
        sap.PointObj.GetCoordCartesian.side_effect = [
            _mock_get_coord(0.0, 0.0, 0.0),
            _mock_get_coord(10.0, 0.0, 0.0),
        ]

        # Mock FrameForce
        sap.Results.FrameForce.return_value = _mock_frame_force_response(
            "F1",
            [
                {"station": 0.0, "load_case": "Dead", "fx": 100, "fy": 50,
                 "fz": 10, "mx": 5, "my": 20, "mz": 300},
                {"station": 10.0, "load_case": "Dead", "fx": -100, "fy": -50,
                 "fz": -10, "mx": -5, "my": -20, "mz": -300},
            ],
        )

        # Mock JointDispl
        def joint_displ_side_effect(node_name, item_type):
            if node_name == "J1":
                return _mock_joint_displ_response(
                    "J1",
                    [{"load_case": "Dead", "ux": 0.0, "uy": 0.0, "uz": 0.0,
                      "rx": 0.0, "ry": 0.0, "rz": 0.0}],
                )
            elif node_name == "J2":
                return _mock_joint_displ_response(
                    "J2",
                    [{"load_case": "Dead", "ux": 0.001, "uy": 0.0, "uz": -0.005,
                      "rx": 0.0001, "ry": 0.0, "rz": 0.0}],
                )
            return (0, [], [], [], [], [], [], [], [], [], [], [], 0)

        sap.Results.JointDispl.side_effect = joint_displ_side_effect

        importer = CsiBridgeResultImporter(_make_csi_session_with_sap(sap))
        request = DataRequest(
            element_ids=frozenset({1}),
            node_ids=frozenset({1, 2}),
            force_loadcases=frozenset({"Dead"}),
            disp_loadcases=frozenset({"Dead"}),
        )
        result = importer.fetch(request)

        assert result.source == OutputSoftware.CSIBRIDGE
        assert len(result.force_envelopes) == 2  # I and J ends
        assert len(result.displacement_envelopes) == 2  # nodes 1 and 2

        env_i = result.force_envelopes[(1, ElementEnd.I, "Dead")]
        assert env_i.Fx_max.Fx.magnitude == pytest.approx(100)

        denv_2 = result.displacement_envelopes[(2, "Dead")]
        assert denv_2.UZ_max.UZ.magnitude == pytest.approx(-0.005)

    def test_fetch_skips_stresses(self):
        """Stress fetcher raises NotImplementedError — fetch should handle
        the case where stress_loadcases is empty (no stress fetch attempted)."""
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import (
            CsiBridgeResultImporter,
        )

        sap = _make_mock_sap_model(
            frame_names=("F1",),
            point_names=("J1",),
            case_names=("Dead",),
            combo_names=(),
        )

        sap.FrameObj.GetPoints.return_value = _mock_get_points("J1", "J1")
        sap.PointObj.GetCoordCartesian.side_effect = [
            _mock_get_coord(0.0, 0.0, 0.0),
            _mock_get_coord(0.0, 0.0, 0.0),
        ]
        sap.Results.FrameForce.return_value = (0, [], [], [], [], [], [], [], [], [], [], [], [], [], 0)
        sap.Results.JointDispl.return_value = (0, [], [], [], [], [], [], [], [], [], [], [], 0)

        importer = CsiBridgeResultImporter(_make_csi_session_with_sap(sap))
        # No stress_loadcases → stress fetcher should NOT be called
        request = DataRequest(
            element_ids=frozenset({1}),
            node_ids=frozenset({1}),
            force_loadcases=frozenset({"Dead"}),
            disp_loadcases=frozenset({"Dead"}),
        )
        result = importer.fetch(request)
        assert len(result.stresses) == 0
