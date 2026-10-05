"""Unit tests for the Midas Civil NX result importer.

All tests use mocked ``MidasAPI`` responses — no live Midas session_manager
required. Tests can run on any CI/CD environment.

Test Classes:
    - TestMidasIdMapper           — id validation, node coordinates
    - TestMidasLoadCaseResolver   — case classification, validation
    - TestMidasForcesFetcher      — force parsing, envelopes, edge cases
    - TestMidasDisplacementsFetcher — displacement parsing
    - TestMidasStressesFetcher    — stress parsing (scaffold)
    - TestMidasCivilResultImporter — orchestration, full pipeline
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest

from bda.domain.enums import OutputSoftware
# Ensure project root is on path (conftest.py handles this).
from bda.domain.enums.load_case_enums import LoadCaseType
from bda.domain.enums.response_enums import ElementEnd
from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_set import ResultSet
from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import MidasConfigProvider


# =====================================================================
# Test helpers
# =====================================================================


class FakeResponse:
    """Minimal stand-in for ``requests.Response``."""

    def __init__(self, data: Dict[str, Any], status_code: int = 200):
        self._data = data
        self.status_code = status_code

    def json(self) -> Dict[str, Any]:
        return self._data


def make_mock_api(responses: Optional[Dict[str, FakeResponse]] = None):
    """Build a mock ``MidasAPI`` that returns canned responses.

    ``responses`` maps ``(method, command)`` tuples (as ``"METHOD command"``)
    to ``FakeResponse`` objects.
    """
    api = MagicMock()
    if responses is None:
        responses = {}

    def mock_request(method, command, body=None):
        key = f"{method} {command}"
        if key in responses:
            return responses[key]
        # Default: empty success
        return FakeResponse({}, 200)

    api.request = MagicMock(side_effect=mock_request)
    return api


# =====================================================================
# Canned API responses
# =====================================================================


ELEM_RESPONSE = {
    "ELEM": {
        "1": {"NODE": [1, 2], "MATL": 1, "SECT": 1, "ANGLE": 0, "STYPE": "BEAM"},
        "5": {"NODE": [3, 4], "MATL": 1, "SECT": 2, "ANGLE": 0, "STYPE": "BEAM"},
        "10": {"NODE": [5, 6], "MATL": 2, "SECT": 1, "ANGLE": 0, "STYPE": "BEAM"},
    }
}

NODE_RESPONSE = {
    "NODE": {
        "1": {"X": 0.0, "Y": 0.0, "Z": 0.0},
        "2": {"X": 10.0, "Y": 0.0, "Z": 0.0},
        "3": {"X": 10.0, "Y": 0.0, "Z": 0.0},
        "4": {"X": 20.0, "Y": 0.0, "Z": 0.0},
        "5": {"X": 20.0, "Y": 0.0, "Z": 0.0},
        "6": {"X": 30.0, "Y": 0.0, "Z": 0.0},
    }
}

STLD_RESPONSE = {
    "STLD": {
        "1": {"NAME": "Dead"},
        "2": {"NAME": "Live"},
    }
}

LCOM_GEN_RESPONSE = {
    "LCOM-GEN": {
        "1": {"NAME": "ULS_gr5", "iTYPE": 0},
        "2": {"NAME": "SLS_char", "iTYPE": 0},
        "3": {"NAME": "ULS_ENV", "iTYPE": 1},
    }
}


def _standard_api_responses() -> Dict[str, FakeResponse]:
    """Return the standard mock API responses for a basic 3-element model."""
    return {
        "GET /db/elem": FakeResponse(ELEM_RESPONSE),
        "GET /db/node": FakeResponse(NODE_RESPONSE),
        "GET /db/STLD": FakeResponse(STLD_RESPONSE),
        "GET /db/LCOM-GEN": FakeResponse(LCOM_GEN_RESPONSE),
    }


# =====================================================================
# TestMidasIdMapper
# =====================================================================


class TestMidasIdMapper:
    """Tests for ``MidasIdMapper``."""

    def _make_mapper(self, responses=None):
        if responses is None:
            responses = _standard_api_responses()
        api = make_mock_api(responses)
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import MidasIdMapper
        return MidasIdMapper(api)

    def test_loads_element_ids(self):
        mapper = self._make_mapper()
        assert mapper.element_ids == {1, 5, 10}

    def test_loads_node_ids(self):
        mapper = self._make_mapper()
        assert mapper.node_ids == {1, 2, 3, 4, 5, 6}

    def test_validate_element_valid(self):
        mapper = self._make_mapper()
        mapper.validate_element(1)  # should not raise

    def test_validate_element_invalid(self):
        mapper = self._make_mapper()
        with pytest.raises(KeyError, match="Element 99"):
            mapper.validate_element(99)

    def test_validate_node_valid(self):
        mapper = self._make_mapper()
        mapper.validate_node(3)

    def test_validate_node_invalid(self):
        mapper = self._make_mapper()
        with pytest.raises(KeyError, match="Node 99"):
            mapper.validate_node(99)

    def test_node_coordinates(self):
        mapper = self._make_mapper()
        coords = mapper.node_coordinates(2)
        assert coords == (10.0, 0.0, 0.0)

    def test_node_coordinates_invalid(self):
        mapper = self._make_mapper()
        with pytest.raises(KeyError, match="Node 99"):
            mapper.node_coordinates(99)

    def test_empty_model(self):
        responses = {
            "GET /db/elem": FakeResponse({"ELEM": {}}),
            "GET /db/node": FakeResponse({"NODE": {}}),
        }
        mapper = self._make_mapper(responses)
        assert mapper.element_ids == set()
        assert mapper.node_ids == set()

    def test_api_failure_raises(self):
        api = MagicMock()
        api.request = MagicMock(side_effect=Exception("Connection refused"))
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import MidasIdMapper
        with pytest.raises(RuntimeError, match="Cannot build element map"):
            MidasIdMapper(api)


# =====================================================================
# TestMidasLoadCaseResolver
# =====================================================================


class TestMidasLoadCaseResolver:
    """Tests for ``MidasLoadCaseResolver``."""

    def _make_resolver(self, responses=None):
        if responses is None:
            responses = _standard_api_responses()
        api = make_mock_api(responses)
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import (
            MidasLoadCaseResolver,
        )
        return MidasLoadCaseResolver(api)

    def test_loads_static_cases(self):
        resolver = self._make_resolver()
        names = {lc.name for lc in resolver.available()}
        assert "Dead" in names
        assert "Live" in names

    def test_loads_combinations(self):
        resolver = self._make_resolver()
        names = {lc.name for lc in resolver.available()}
        assert "ULS_gr5" in names
        assert "SLS_char" in names
        assert "ULS_ENV" in names

    def test_static_case_classification(self):
        resolver = self._make_resolver()
        assert resolver.classify("Dead") == LoadCaseType.SINGLE_VALUED

    def test_combination_classification(self):
        resolver = self._make_resolver()
        assert resolver.classify("ULS_gr5") == LoadCaseType.COMBINATION

    def test_envelope_classification(self):
        resolver = self._make_resolver()
        assert resolver.classify("ULS_ENV") == LoadCaseType.ENVELOPE

    def test_is_combination_true(self):
        resolver = self._make_resolver()
        assert resolver.is_combination("ULS_gr5") is True
        assert resolver.is_combination("ULS_ENV") is True

    def test_is_combination_false_for_static(self):
        resolver = self._make_resolver()
        assert resolver.is_combination("Dead") is False

    def test_resolve_valid_names(self):
        resolver = self._make_resolver()
        resolved = resolver.resolve(["Dead", "ULS_gr5"])
        assert len(resolved) == 2
        assert resolved[0].name == "Dead"
        assert resolved[1].name == "ULS_gr5"

    def test_resolve_invalid_name_raises(self):
        resolver = self._make_resolver()
        with pytest.raises(KeyError, match="NONEXISTENT"):
            resolver.resolve(["Dead", "NONEXISTENT"])

    def test_classify_invalid_name_raises(self):
        resolver = self._make_resolver()
        with pytest.raises(KeyError, match="NONEXISTENT"):
            resolver.classify("NONEXISTENT")


# =====================================================================
# TestMidasForcesFetcher
# =====================================================================


class TestMidasForcesFetcher:
    """Tests for ``MidasForcesFetcher``."""

    def _make_fetcher_and_result_set(
        self, force_response_data=None, responses=None
    ):
        if responses is None:
            responses = _standard_api_responses()
        if force_response_data is not None:
            responses["POST /post/TABLE"] = FakeResponse(force_response_data)
        api = make_mock_api(responses)

        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import MidasIdMapper
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import (
            MidasLoadCaseResolver,
        )
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import (
            MidasForcesFetcher,
        )

        mapper = MidasIdMapper(api)
        resolver = MidasLoadCaseResolver(api)
        fetcher = MidasForcesFetcher(api, mapper, resolver)
        result_set = ResultSet(source="midas_civil_nx")
        return fetcher, result_set, api

    def test_basic_force_fetch(self):
        """Single element, single LC, I and J ends."""
        force_data = {
            "Empty": {
                "DATA": [
                    [0, "1", "ULS_gr5(CB:max)", "PartI", "Comp",
                     "100.0", "50.0", "10.0", "5.0", "200.0", "300.0"],
                    [1, "1", "ULS_gr5(CB:max)", "PartJ", "Comp",
                     "100.0", "-50.0", "-10.0", "-5.0", "-200.0", "-300.0"],
                    [2, "1", "ULS_gr5(CB:min)", "PartI", "Comp",
                     "-80.0", "-40.0", "-8.0", "-4.0", "-180.0", "-250.0"],
                    [3, "1", "ULS_gr5(CB:min)", "PartJ", "Comp",
                     "-80.0", "40.0", "8.0", "4.0", "180.0", "250.0"],
                ]
            }
        }

        fetcher, result_set, _ = self._make_fetcher_and_result_set(force_data)
        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"ULS_gr5"}),
        )
        fetcher.fetch_into(request, result_set)

        # Should have 2 envelopes: (1, I, ULS_gr5) and (1, J, ULS_gr5)
        assert len(result_set.force_envelopes) == 2
        assert (1, ElementEnd.I, "ULS_gr5") in result_set.force_envelopes
        assert (1, ElementEnd.J, "ULS_gr5") in result_set.force_envelopes

    def test_envelope_widening(self):
        """CB:max and CB:min rows should widen the envelope."""
        force_data = {
            "Empty": {
                "DATA": [
                    [0, "1", "ULS_gr5(CB:max)", "PartI", "Comp",
                     "100.0", "50.0", "10.0", "5.0", "200.0", "300.0"],
                    [1, "1", "ULS_gr5(CB:min)", "PartI", "Comp",
                     "-80.0", "-40.0", "-8.0", "-4.0", "-180.0", "-250.0"],
                ]
            }
        }

        fetcher, result_set, _ = self._make_fetcher_and_result_set(force_data)
        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"ULS_gr5"}),
        )
        fetcher.fetch_into(request, result_set)

        envelope = result_set.force_envelopes[(1, ElementEnd.I, "ULS_gr5")]
        # Fx_max should be from the CB:max row (100 kN)
        assert envelope.Fx_max.Fx.magnitude == pytest.approx(100.0)
        # Fx_min should be from the CB:min row (-80 kN)
        assert envelope.Fx_min.Fx.magnitude == pytest.approx(-80.0)

    def test_skips_unrequested_load_cases(self):
        """Only requested LCs are kept."""
        force_data = {
            "Empty": {
                "DATA": [
                    [0, "1", "ULS_gr5(CB:max)", "PartI", "Comp",
                     "100.0", "50.0", "10.0", "5.0", "200.0", "300.0"],
                    [1, "1", "SLS_char(CB:max)", "PartI", "Comp",
                     "50.0", "25.0", "5.0", "2.5", "100.0", "150.0"],
                ]
            }
        }

        fetcher, result_set, _ = self._make_fetcher_and_result_set(force_data)
        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"ULS_gr5"}),  # Only ULS
        )
        fetcher.fetch_into(request, result_set)

        assert len(result_set.force_envelopes) == 1
        assert (1, ElementEnd.I, "ULS_gr5") in result_set.force_envelopes
        assert (1, ElementEnd.I, "SLS_char") not in result_set.force_envelopes

    def test_skips_invalid_elements(self):
        """Elements not in the Midas model are skipped."""
        force_data = {"Empty": {"DATA": []}}
        fetcher, result_set, _ = self._make_fetcher_and_result_set(force_data)
        request = DataRequest(
            element_ids=frozenset({999}),  # Does not exist
            force_loadcases=frozenset({"ULS_gr5"}),
        )
        fetcher.fetch_into(request, result_set)
        assert len(result_set.force_envelopes) == 0

    def test_empty_response(self):
        """No data returned from API."""
        force_data = {"Empty": {"DATA": []}}
        fetcher, result_set, _ = self._make_fetcher_and_result_set(force_data)
        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"ULS_gr5"}),
        )
        fetcher.fetch_into(request, result_set)
        assert len(result_set.force_envelopes) == 0

    def test_multiple_elements(self):
        """Forces for multiple elements in one request."""
        force_data = {
            "Empty": {
                "DATA": [
                    [0, "1", "Dead", "PartI", "Comp",
                     "50.0", "25.0", "5.0", "2.5", "100.0", "150.0"],
                    [1, "5", "Dead", "PartI", "Comp",
                     "60.0", "30.0", "6.0", "3.0", "120.0", "180.0"],
                ]
            }
        }

        fetcher, result_set, _ = self._make_fetcher_and_result_set(force_data)
        request = DataRequest(
            element_ids=frozenset({1, 5}),
            force_loadcases=frozenset({"Dead"}),
        )
        fetcher.fetch_into(request, result_set)

        assert (1, ElementEnd.I, "Dead") in result_set.force_envelopes
        assert (5, ElementEnd.I, "Dead") in result_set.force_envelopes

    def test_strip_combo_suffix(self):
        """Test the suffix-stripping helper."""
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import (
            MidasForcesFetcher,
        )

        assert MidasForcesFetcher._strip_combo_suffix("ULS_gr5(CB:max)") == "ULS_gr5"
        assert MidasForcesFetcher._strip_combo_suffix("ULS_gr5(CB:min)") == "ULS_gr5"
        assert MidasForcesFetcher._strip_combo_suffix("Dead") == "Dead"
        assert MidasForcesFetcher._strip_combo_suffix("") == ""

    def test_classify_part(self):
        """Test the part classification helper."""
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import (
            MidasForcesFetcher,
        )

        assert MidasForcesFetcher._classify_part("PartI") == ElementEnd.I
        assert MidasForcesFetcher._classify_part("PartJ") == ElementEnd.J
        assert MidasForcesFetcher._classify_part("I") == ElementEnd.I
        assert MidasForcesFetcher._classify_part("J") == ElementEnd.J
        assert MidasForcesFetcher._classify_part("PARTI") == ElementEnd.I
        assert MidasForcesFetcher._classify_part("Unknown") is None

    def test_force_vector_units(self):
        """Verify that force vectors have correct pint units."""
        force_data = {
            "Empty": {
                "DATA": [
                    [0, "1", "Dead", "PartI", "Comp",
                     "100.0", "50.0", "10.0", "5.0", "200.0", "300.0"],
                ]
            }
        }

        fetcher, result_set, _ = self._make_fetcher_and_result_set(force_data)
        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"Dead"}),
        )
        fetcher.fetch_into(request, result_set)

        envelope = result_set.force_envelopes[(1, ElementEnd.I, "Dead")]
        fv = envelope.Fx_max
        assert fv.Fx.check("[force]")
        assert fv.Fy.check("[force]")
        assert fv.Mx.check("[force] * [length]")
        assert fv.Mz.check("[force] * [length]")

    def test_api_error_raises_runtime(self):
        """API failure should raise RuntimeError."""
        responses = _standard_api_responses()
        api = make_mock_api(responses)

        # Make the POST call fail
        original_side_effect = api.request.side_effect

        def fail_on_post(method, command, body=None):
            if method == "POST":
                raise ConnectionError("Server down")
            return original_side_effect(method, command, body)

        api.request.side_effect = fail_on_post

        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import MidasIdMapper
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import (
            MidasForcesFetcher,
        )

        mapper = MidasIdMapper(api)
        fetcher = MidasForcesFetcher(api, mapper)
        result_set = ResultSet(source="midas_civil_nx")
        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"Dead"}),
        )

        with pytest.raises(RuntimeError, match="Failed to fetch forces"):
            fetcher.fetch_into(request, result_set)


# =====================================================================
# TestMidasDisplacementsFetcher
# =====================================================================


class TestMidasDisplacementsFetcher:
    """Tests for ``MidasDisplacementsFetcher``."""

    def _make_fetcher_and_result_set(self, disp_response_data=None):
        responses = _standard_api_responses()
        if disp_response_data is not None:
            responses["POST /post/TABLE"] = FakeResponse(disp_response_data)
        api = make_mock_api(responses)

        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import MidasIdMapper
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import (
            MidasLoadCaseResolver,
        )
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import (
            MidasDisplacementsFetcher,
        )

        mapper = MidasIdMapper(api)
        resolver = MidasLoadCaseResolver(api)
        fetcher = MidasDisplacementsFetcher(api, mapper, resolver)
        result_set = ResultSet(source="midas_civil_nx")
        return fetcher, result_set

    def test_basic_displacement_fetch(self):
        """Single node, single LC."""
        disp_data = {
            "Empty": {
                "DATA": [
                    [0, "1", "Dead",
                     "0.001", "0.002", "-0.005",
                     "0.0001", "0.0002", "0.0003"],
                ]
            }
        }

        fetcher, result_set = self._make_fetcher_and_result_set(disp_data)
        request = DataRequest(
            node_ids=frozenset({1}),
            disp_loadcases=frozenset({"Dead"}),
        )
        fetcher.fetch_into(request, result_set)

        assert len(result_set.displacement_envelopes) == 1
        denv = result_set.displacement_envelopes[(1, "Dead")]
        # For a single row, max and min are the same degenerate envelope
        assert denv.UX_max.UX.magnitude == pytest.approx(0.001)
        assert denv.UZ_max.UZ.magnitude == pytest.approx(-0.005)
        assert denv.RX_max.RX.magnitude == pytest.approx(0.0001)

    def test_displacement_units(self):
        """Verify pint unit dimensions."""
        disp_data = {
            "Empty": {
                "DATA": [
                    [0, "1", "Dead",
                     "0.001", "0.002", "-0.005",
                     "0.0001", "0.0002", "0.0003"],
                ]
            }
        }

        fetcher, result_set = self._make_fetcher_and_result_set(disp_data)
        request = DataRequest(
            node_ids=frozenset({1}),
            disp_loadcases=frozenset({"Dead"}),
        )
        fetcher.fetch_into(request, result_set)

        denv = result_set.displacement_envelopes[(1, "Dead")]
        # Check units via the max envelope member
        assert denv.UX_max.UX.check("[length]")
        assert denv.RX_max.RX.check("radian")

    def test_combo_suffix_stripping(self):
        """CB:max/CB:min suffixes are stripped from displacement LCs."""
        disp_data = {
            "Empty": {
                "DATA": [
                    [0, "1", "ULS_gr5(CB:max)",
                     "0.005", "0.010", "-0.020",
                     "0.001", "0.002", "0.003"],
                ]
            }
        }

        fetcher, result_set = self._make_fetcher_and_result_set(disp_data)
        request = DataRequest(
            node_ids=frozenset({1}),
            disp_loadcases=frozenset({"ULS_gr5"}),
        )
        fetcher.fetch_into(request, result_set)

        assert (1, "ULS_gr5") in result_set.displacement_envelopes

    def test_empty_response(self):
        disp_data = {"Empty": {"DATA": []}}
        fetcher, result_set = self._make_fetcher_and_result_set(disp_data)
        request = DataRequest(
            node_ids=frozenset({1}),
            disp_loadcases=frozenset({"Dead"}),
        )
        fetcher.fetch_into(request, result_set)
        assert len(result_set.displacement_envelopes) == 0

    def test_skips_invalid_nodes(self):
        disp_data = {"Empty": {"DATA": []}}
        fetcher, result_set = self._make_fetcher_and_result_set(disp_data)
        request = DataRequest(
            node_ids=frozenset({999}),
            disp_loadcases=frozenset({"Dead"}),
        )
        fetcher.fetch_into(request, result_set)
        assert len(result_set.displacement_envelopes) == 0


# =====================================================================
# TestMidasStressesFetcher
# =====================================================================


class TestMidasStressesFetcher:
    """Tests for ``MidasStressesFetcher`` (scaffold — response format TBD)."""

    def _make_fetcher_and_result_set(self, stress_response_data=None):
        responses = _standard_api_responses()
        if stress_response_data is not None:
            responses["POST /post/TABLE"] = FakeResponse(stress_response_data)
        api = make_mock_api(responses)

        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import MidasIdMapper
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import (
            MidasLoadCaseResolver,
        )
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import (
            MidasStressesFetcher,
        )

        mapper = MidasIdMapper(api)
        resolver = MidasLoadCaseResolver(api)
        fetcher = MidasStressesFetcher(api, mapper, resolver)
        result_set = ResultSet(source="midas_civil_nx")
        return fetcher, result_set

    def test_basic_stress_fetch(self):
        """Scaffold test — verifies the structural skeleton works."""
        stress_data = {
            "Empty": {
                "DATA": [
                    [0, "1", "Dead", "PartI", "150.0"],
                ]
            }
        }

        fetcher, result_set = self._make_fetcher_and_result_set(stress_data)
        request = DataRequest(
            element_ids=frozenset({1}),
            stress_loadcases=frozenset({"Dead"}),
        )
        fetcher.fetch_into(request, result_set)

        assert len(result_set.stresses) == 1
        stress = result_set.stresses[(1, ElementEnd.I, "Dead")]
        assert len(stress.points) == 1
        assert stress.points[0].sigma.check("[pressure]")

    def test_empty_response(self):
        stress_data = {"Empty": {"DATA": []}}
        fetcher, result_set = self._make_fetcher_and_result_set(stress_data)
        request = DataRequest(
            element_ids=frozenset({1}),
            stress_loadcases=frozenset({"Dead"}),
        )
        fetcher.fetch_into(request, result_set)
        assert len(result_set.stresses) == 0

    def test_no_data_key_in_response(self):
        """API returns unexpected response structure."""
        stress_data = {"unexpected": "format"}
        fetcher, result_set = self._make_fetcher_and_result_set(stress_data)
        request = DataRequest(
            element_ids=frozenset({1}),
            stress_loadcases=frozenset({"Dead"}),
        )
        fetcher.fetch_into(request, result_set)
        assert len(result_set.stresses) == 0


# =====================================================================
# TestMidasCivilResultImporter
# =====================================================================


class TestMidasCivilResultImporter:
    """Tests for the ``MidasCivilResultImporter`` orchestrator."""

    def _make_importer(self, force_data=None, disp_data=None, stress_data=None):
        """Build an importer with canned responses for all three fetchers.

        For simplicity, the POST /post/TABLE response is shared. In a
        real scenario each fetcher would call the endpoint with different
        TABLE_TYPE; here we just return whatever data is needed for the
        test.
        """
        responses = _standard_api_responses()

        # Combine all data into one response (fetchers will filter by LC)
        combined_data = []
        if force_data:
            combined_data.extend(force_data)
        if disp_data:
            combined_data.extend(disp_data)
        # For stresses, we need a separate response since format differs

        responses["POST /post/TABLE"] = FakeResponse(
            {"Empty": {"DATA": combined_data}}
        )

        api = make_mock_api(responses)

        from bda.infrastructure.adapters.analytical_software.importers.midas_civil_result_importer import (
            MidasCivilResultImporter)
        from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import (
            MidasCivilSession)

        class _InlineMidasConfigProvider:
            def load_config(self):
                return {
                    "base_url": "http://127.0.0.1:12101",
                    "mapi_key": "test-key",
                    "program_path": "",
                }

        session = MidasCivilSession(MidasConfigProvider())
        session.api = MagicMock(return_value=api)
        return MidasCivilResultImporter(session)

    def test_fetch_forces_only(self):
        """Request with only force load cases."""
        force_rows = [
            [0, "1", "ULS_gr5(CB:max)", "PartI", "Comp",
             "100.0", "50.0", "10.0", "5.0", "200.0", "300.0"],
            [1, "1", "ULS_gr5(CB:min)", "PartI", "Comp",
             "-80.0", "-40.0", "-8.0", "-4.0", "-180.0", "-250.0"],
        ]
        importer = self._make_importer(force_data=force_rows)
        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"ULS_gr5"}),
        )
        result = importer.fetch(request)

        assert result.source == OutputSoftware.MIDAS
        assert len(result.force_envelopes) == 1

    def test_fetch_returns_empty_for_no_data(self):
        """Empty request returns empty ResultSet."""
        importer = self._make_importer(force_data=[])
        request = DataRequest()
        result = importer.fetch(request)

        assert result.source == OutputSoftware.MIDAS
        assert len(result.force_envelopes) == 0
        assert len(result.displacement_envelopes) == 0
        assert len(result.stresses) == 0

    def test_available_load_cases(self):
        """Verify that available_load_cases returns all known cases."""
        importer = self._make_importer()
        lcs = importer.available_load_cases()
        names = {lc.name for lc in lcs}
        assert "Dead" in names
        assert "ULS_gr5" in names
        assert "ULS_ENV" in names

    def test_invalid_load_case_raises(self):
        """Requesting an unknown load case should fail fast."""
        importer = self._make_importer(force_data=[])
        request = DataRequest(
            element_ids=frozenset({1}),
            force_loadcases=frozenset({"NONEXISTENT_LC"}),
        )
        with pytest.raises(KeyError, match="NONEXISTENT_LC"):
            importer.fetch(request)

    def test_result_set_source(self):
        """ResultSet should have source='midas_civil_nx'."""
        importer = self._make_importer(force_data=[])
        request = DataRequest()
        result = importer.fetch(request)
        assert result.source == OutputSoftware.MIDAS
