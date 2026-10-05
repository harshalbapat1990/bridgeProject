from pathlib import Path

import pytest
from numpy.ma.testutils import assert_almost_equal

from bda.application.mapping.boundary_conditions.bearing_mapper import BearingMapper
from bda.domain.models.submodels.boundary_conditions.enums import DofTypeEnum
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import BearingConfigurationType, \
    ElementOrientation
from bda.infrastructure.data_providers import DataFileProvider


class TestBearingsMapper:

    @pytest.fixture
    def fixtures_path(self):
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def provider(self, fixtures_path):
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture
    def bearings(self, provider: DataFileProvider):
        return provider.get_bearing_boundary_conditions_for_project("bearing_bc.json")

    def test_bearings(self, bearings):
        result = BearingMapper.to_domain(bearings)

        assert len(result) == len(bearings)

        for para, domain in zip(bearings, result):
            assert domain.support_index == para.support_index
            assert len(domain.bearings_by_girder) == len(para.bearings_by_girder)

    def test_0(self, bearings):
        result = BearingMapper.to_domain(bearings)

        support = result[0]
        girder = support.bearings_by_girder[0]

        assert support.support_index == 0
        assert girder.girder_index == 0

    def test_1(self, bearings):
        result = BearingMapper.to_domain(bearings)

        support = result[1]
        girder = support.bearings_by_girder[1]

        assert support.support_index == 1
        assert girder.bearing_configuration_type == BearingConfigurationType.MULTIPLE
        assert_almost_equal(girder.bearing_definitions[0].bearing_stiffness_definition.sdz.stiffness.magnitude, 2000000)
        assert girder.bearing_definitions[0].orientation == ElementOrientation.ORTHOGONAL
        assert girder.bearing_definitions[0].bearing_stiffness_definition.srx.dof_type == DofTypeEnum.FREE

