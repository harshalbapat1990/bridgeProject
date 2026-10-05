"""Gateway smoke test — verify MidasAPI connectivity end-to-end.

Tests that:
    1. ``midas_config.json`` is found and contains valid fields.
    2. ``MidasConfigProvider`` loads the correct values.
    3. ``MidasAPI`` can be constructed from config without error.
    4. ``MidasAPI.is_connected()`` returns True against a live Midas session_manager.
    5. ``MidasCivilResultImporter(session_manager)`` completes initialization
       (id mapper + load case resolver queries succeed).

Run with Midas Civil NX open and MAPI enabled:

    pytest tests/integration/test_midas_gateway.py -v -s

No environment variables needed — everything comes from midas_config.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import MidasConfigProvider


# =====================================================================
# Tests that always run (no live Midas needed)
# =====================================================================


class TestMidasConfigFile:
    """Verify midas_config.json exists and has the required fields."""


    def test_config_has_base_url(self):
        data = MidasConfigProvider().config
        assert "base_url" in data, "midas_config.json missing 'base_url'"
        assert isinstance(data["base_url"], str)
        assert len(data["base_url"]) > 0, "base_url is empty"

    def test_config_has_mapi_key(self):
        data = MidasConfigProvider().config
        assert "mapi_key" in data, "midas_config.json missing 'mapi_key'"
        assert isinstance(data["mapi_key"], str)
        assert len(data["mapi_key"]) > 0, "mapi_key is empty"

    def test_config_has_program_path(self):
        data = MidasConfigProvider().config
        assert "program_path" in data, "midas_config.json missing 'program_path'"


class TestMidasConfigProvider:
    """Verify MidasConfigProvider loads the config correctly."""

    def test_provider_loads_without_error(self):
        from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import \
            MidasConfigProvider
        cfg = MidasConfigProvider()
        assert cfg is not None

    def test_provider_returns_base_url(self):
        from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import \
            MidasConfigProvider
        cfg = MidasConfigProvider()
        base_url = cfg.get_config_value("base_url")
        assert base_url is not None
        assert base_url.startswith("http")

    def test_provider_returns_mapi_key(self):
        from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import \
            MidasConfigProvider
        cfg = MidasConfigProvider()
        mapi_key = cfg.get_config_value("mapi_key")
        assert mapi_key is not None
        assert len(mapi_key) > 10, "mapi_key looks too short to be valid"


class TestMidasAPIConstruction:
    """Verify MidasAPI can be built from config values."""

    def test_api_construction_from_config(self):
        from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import \
            MidasConfigProvider
        from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import (
            MidasAPI,
        )

        cfg = MidasConfigProvider()
        base_url = cfg.get_config_value("base_url")
        mapi_key = cfg.get_config_value("mapi_key")

        api = MidasAPI(base_url, mapi_key)
        assert api.baseURL == base_url
        assert api.mapiKey == mapi_key

    def test_api_rejects_empty_base_url(self):
        from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import (
            MidasAPI,
        )
        with pytest.raises(AssertionError, match="Base URL"):
            MidasAPI("", "some_key")

    def test_api_rejects_empty_mapi_key(self):
        from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import (
            MidasAPI,
        )
        with pytest.raises(AssertionError, match="MAPI-Key"):
            MidasAPI("http://localhost", "")


# =====================================================================
# Tests that need a live Midas session_manager
# =====================================================================


def _build_api():
    """Helper: build MidasAPI from config."""
    from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import \
        MidasConfigProvider
    from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import (
        MidasAPI,
    )

    cfg = MidasConfigProvider()
    return MidasAPI(
        cfg.get_config_value("base_url"),
        cfg.get_config_value("mapi_key"),
    )


def _build_session():
    """Helper: build a Midas session_manager from config and attach to a running instance."""
    from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import \
        MidasConfigProvider
    from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import MidasCivilSession

    session = MidasCivilSession(MidasConfigProvider())
    session.open_session(create_new_instance=False, template_file_path=None)
    return session


def _midas_is_reachable() -> bool:
    """Return True if Midas responds to a simple GET."""
    try:
        api = _build_api()
        return api.is_connected()
    except Exception:
        return False


skip_no_midas = pytest.mark.skipif(
    not _midas_is_reachable(),
    reason="Midas Civil NX not reachable (is it running with MAPI enabled?)",
)


@skip_no_midas
class TestMidasLiveConnection:
    """Tests that hit the live Midas REST API."""

    def test_is_connected(self):
        api = _build_api()
        assert api.is_connected() is True

    def test_test_connection_returns_200(self):
        api = _build_api()
        resp = api.test_connection()
        assert resp is not None
        assert resp.status_code == 200

    def test_get_db_unit(self):
        """GET /db/unit should return the model's unit system."""
        api = _build_api()
        resp = api.request("GET", "/db/unit")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_get_db_elem(self):
        """GET /db/elem should return element data (model must have elements)."""
        api = _build_api()
        resp = api.request("GET", "/db/elem")
        assert resp.status_code == 200
        data = resp.json()
        assert "ELEM" in data, f"Unexpected response keys: {list(data.keys())}"

    def test_get_db_node(self):
        """GET /db/node should return node data."""
        api = _build_api()
        resp = api.request("GET", "/db/node")
        assert resp.status_code == 200
        data = resp.json()
        assert "NODE" in data, f"Unexpected response keys: {list(data.keys())}"

    def test_get_db_stld(self):
        """GET /db/STLD should return static load cases."""
        api = _build_api()
        resp = api.request("GET", "/db/STLD")
        assert resp.status_code == 200
        data = resp.json()
        assert "STLD" in data, f"Unexpected response keys: {list(data.keys())}"
        print(f"\n  Static load cases: {data['STLD']}")

    def test_get_db_lcom_gen(self):
        """GET /db/LCOM-GEN should return load combinations."""
        api = _build_api()
        resp = api.request("GET", "/db/LCOM-GEN")
        assert resp.status_code == 200
        data = resp.json()
        assert "LCOM-GEN" in data, f"Unexpected response keys: {list(data.keys())}"
        print(f"\n  Load combinations: {data['LCOM-GEN']}")


@skip_no_midas
class TestMidasImporterWithSession:
    """Verify the full session_manager -> importer initialization pipeline."""

    def test_session_initializes_importer(self):
        """Session-based constructor should build the importer without errors.

        This exercises:
        - Config file reading
        - MidasAPI construction
        - MidasIdMapper (GET /db/elem + /db/node)
        - MidasLoadCaseResolver (GET /db/STLD + /db/LCOM-GEN)
        """

        from bda.infrastructure.adapters.analytical_software.importers import MidasCivilResultImporter

        session = _build_session()
        importer = MidasCivilResultImporter(session)
        assert importer is not None
        session.close_session()

    def test_session_has_load_cases(self):
        """The model should expose at least one load case."""
        from bda.infrastructure.adapters.analytical_software.importers import MidasCivilResultImporter

        session = _build_session()
        importer = MidasCivilResultImporter(session)
        lcs = importer.available_load_cases()
        assert len(lcs) > 0, "No load cases found — is the model empty?"
        print(f"\n  Available load cases ({len(lcs)}):")
        for lc in lcs:
            print(f"    - {lc.name} ({lc.load_case_type.value})")
        session.close_session()

    def test_session_has_elements(self):
        """The id mapper should find elements in the model."""
        from bda.infrastructure.adapters.analytical_software.importers import MidasCivilResultImporter

        session = _build_session()
        importer = MidasCivilResultImporter(session)
        elem_count = len(importer._id_mapper.element_ids)
        node_count = len(importer._id_mapper.node_ids)
        assert elem_count > 0, "No elements found — is the model empty?"
        assert node_count > 0, "No nodes found — is the model empty?"
        print(f"\n  Model: {elem_count} elements, {node_count} nodes")
        session.close_session()
