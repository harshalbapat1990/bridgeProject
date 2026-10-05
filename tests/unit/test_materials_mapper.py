from pathlib import Path

import pytest

from bda.application.mapping.materials import MaterialMapper
from bda.infrastructure.data_providers import DataFileProvider


class TestMaterialsMapper:
    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    @pytest.fixture
    def fixtures_path(self):
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def provider(self, fixtures_path):
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture
    def materials(self, provider):
        return provider.get_materials_for_project("materials_from_speckle.json")

    def test_map_all_sections_from_json(self, materials):
        result = MaterialMapper.to_domain_list(materials)
        assert len(result) == len(materials)