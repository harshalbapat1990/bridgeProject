"""Unit tests for the export steps shared by all analytical software exporters."""

from typing import List
from unittest.mock import MagicMock

import pytest

from bda.domain import AnalyticalMultiModel
from bda.domain.enums import UnitSystem
from bda.domain.models.submodels import GeometryGroup, MaterialBase, SectionBase
from bda.domain.units.export_units import ExportUnits, get_export_units
from bda.infrastructure.adapters.analytical_software.exporters.exporter_base import ExporterBase

EU_SI = get_export_units(UnitSystem.SI)


class FakeExporter(ExporterBase):
    """Exporter recording the calls made by the shared export steps."""

    def __init__(self, failing_step: str | None = None):
        self.failing_step = failing_step
        self.calls: List[str] = []
        self.written_sections: List[SectionBase] = []
        self.written_geometry: List[GeometryGroup] = []

    def _fail_when_requested(self, step: str) -> None:
        self.calls.append(step)
        if self.failing_step == step:
            raise ValueError(f"{step} failed")

    def _prepare_model(self, amm: AnalyticalMultiModel) -> None:
        self._fail_when_requested("prepare")

    def _write_materials(self, materials: List[MaterialBase], export_units: ExportUnits) -> None:
        self._fail_when_requested("materials")

    def _write_sections(self, sections: List[SectionBase], export_units: ExportUnits) -> None:
        self._fail_when_requested("sections")
        self.written_sections = list(sections)

    def _write_geometry(self, geometry_groups: List[GeometryGroup], export_units: ExportUnits) -> None:
        self._fail_when_requested("geometry")
        self.written_geometry = list(geometry_groups)

    def export(self, amm: AnalyticalMultiModel) -> None:
        ...

    def set_unit_system(self, unit_system: UnitSystem) -> None:
        ...

    def run_analysis(self) -> None:
        ...


@pytest.fixture
def exporter() -> FakeExporter:
    return FakeExporter()


class TestSharedExportSteps:
    def test_empty_input_succeeds_without_writing_anything(self, exporter):
        assert exporter._export_materials([], EU_SI) is True
        assert exporter._export_sections([], EU_SI) is True
        assert exporter._export_geometry([], EU_SI) is True
        assert exporter.calls == [], "Nothing has to be sent to the software when there is no input"

    def test_successful_steps_return_true(self, exporter):
        amm = AnalyticalMultiModel(unit_system=UnitSystem.SI)

        assert exporter._prepare_model_for_export(amm) is True
        assert exporter._export_materials([MagicMock(spec=MaterialBase)], EU_SI) is True
        assert exporter._export_sections([MagicMock()], EU_SI) is True
        assert exporter._export_geometry([MagicMock(spec=GeometryGroup)], EU_SI) is True
        assert exporter.calls == ["prepare", "materials", "sections", "geometry"]

    @pytest.mark.parametrize("failing_step", ["prepare", "materials", "sections", "geometry"])
    def test_failed_step_returns_false_instead_of_raising(self, failing_step):
        exporter = FakeExporter(failing_step=failing_step)
        amm = AnalyticalMultiModel(unit_system=UnitSystem.SI)

        results = {
            "prepare": lambda: exporter._prepare_model_for_export(amm),
            "materials": lambda: exporter._export_materials([MagicMock(spec=MaterialBase)], EU_SI),
            "sections": lambda: exporter._export_sections([MagicMock()], EU_SI),
            "geometry": lambda: exporter._export_geometry([MagicMock(spec=GeometryGroup)], EU_SI),
        }

        assert results[failing_step]() is False, "A failed step has to be reported by its result"

    def test_single_geometry_group_is_accepted(self, exporter):
        geometry_group = MagicMock(spec=GeometryGroup)

        assert exporter._export_geometry(geometry_group, EU_SI) is True
        assert exporter.written_geometry == [geometry_group], \
            "A single geometry group has to be exported the same way as a list of them"
