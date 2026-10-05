"""Exporter for MIDAS Civil structural analysis software."""

from typing import List

from bda.application.interfaces.analytical_software.session_manager import IAnalyticalSoftwareSession
from bda.domain import AnalyticalMultiModel
from bda.domain.enums import UnitSystem
from bda.domain.models.submodels import MaterialBase, SectionBase, GeometryGroup
from bda.domain.units.export_units import ExportUnits, get_export_units
from bda.infrastructure.adapters.analytical_software.exporters.exporter_base import ExporterBase
from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.boundary_bcs_exporter import \
    MidasBoundaryExporter
from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.geometry_exporter import \
    MidasGeometryExporter
from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.model_preparation import \
    MidasModelPreparator
from bda.infrastructure.utils.logger import AppLogger
from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import MidasCivilSession
from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.materials_exporter import MidasMaterialExporter
from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.section_exporter import MidasSectionExporter

logger = AppLogger()


class MidasCivilExporter(ExporterBase):
    """Exporter for MIDAS Civil software using an externally managed session_manager."""

    def __init__(self, session: IAnalyticalSoftwareSession):
        if not isinstance(session, MidasCivilSession):
            raise TypeError("MidasCivilExporter requires MidasCivilSession")

        self._session = session
        self.software_name = session.software_name
        from midas_civil import Model
        self.model = Model

    @property
    def api(self):
        return self._session.api()

    @property
    def mapi_key(self) -> str:
        return self._session.mapi_key

    def export(self, amm: AnalyticalMultiModel) -> None:
        """Export analytical model to MIDAS Civil."""
        exported = False

        try:
            logger.info("Starting the creation of the Midas model of '%s' to %s",
                        amm.structure_name, self.software_name)

            eu = get_export_units(amm.unit_system)
            self.set_unit_system(amm.unit_system)

            # every step depends on the previous ones, so the export stops at the first
            # step that failed instead of piling up errors on top of the original one.
            # The step itself logs what went wrong, the raised error only reports the abort.
            if not self._prepare_model_for_export(amm):
                raise RuntimeError("model preparation failed")

            if not self._export_materials(amm.get_all_materials(), eu):
                raise RuntimeError("materials export failed")

            if not self._export_sections(amm.get_all_sections(), eu):
                raise RuntimeError("sections export failed")

            if not self._export_geometry(amm, eu):
                raise RuntimeError("geometry export failed")

            if not self._export_boundaries(amm, eu):
                raise RuntimeError("boundaries export failed")

            exported = True

            logger.info(
                "Model '%s' has been successfully created.",
                amm.structure_name
            )

        except Exception as e:
            logger.error(
                "Failed to create the Midas model during '%s': %s",
                "MIDAS export orchestration", e)
            logger.warning("Midas model will be exported only partially")
            raise

        finally:
            self.model.create()
            self._session.save_model()

            if exported:
                logger.info("The Midas model has been successfully exported.")
            else:
                logger.warning("The Midas model has been exported only partially.")

    def _write_materials(self, materials: List[MaterialBase], export_units: ExportUnits) -> None:
        """Send the given materials to MIDAS Civil."""

        material_exporter = MidasMaterialExporter(export_units)
        for material in materials:
            material_exporter.export_material(material)

    def _write_sections(self, sections: List[SectionBase], export_units: ExportUnits) -> None:
        """Send the given sections to MIDAS Civil, in the order they are given."""

        section_exporter = MidasSectionExporter(export_units)
        for section in sections:
            section_exporter.export_section(section)

    def _write_geometry(self, amm: AnalyticalMultiModel, export_units: ExportUnits) -> None:
        """Send the given geometry groups to MIDAS Civil."""

        geometry_exporter = MidasGeometryExporter(export_units)
        geometry_exporter.export(amm)

    def _write_boundaries(self, amm: AnalyticalMultiModel, export_units: ExportUnits) -> None:
        """Send the boundary conditions to MIDAS Civil."""
        boundary_exporter = MidasBoundaryExporter(export_units)
        boundary_exporter.export(amm)


    def _prepare_model(self, amm: AnalyticalMultiModel) -> None:
        """
        This helper function prepares multimodel for export by setting up all areas specific to Midas Civil.

        This function include:
        - sections preparation for export by assigning materials to sections when geometry group does not exist.
            As Midas require material to be assigned to section.

        Parameters
        ----------
        amm: AnalyticalMultiModel

        Returns
        -------

        """

        MidasModelPreparator.prepare_sections_for_export(amm)

    def run_analysis(self) -> None:
        self.model.analyse()

    def set_unit_system(self, unit_system: UnitSystem) -> None:
        eu = get_export_units(unit_system)

        length_unit = str(eu.length)
        match length_unit:
            case "ft":
                midas_length = 'FT'
            case "in":
                midas_length = 'IN'
            case "m":
                midas_length = 'M'
            case "m":
                midas_length = 'CM'
            case "mm":
                midas_length = 'MM'
            case _:
                raise NotImplementedError(f"Unrecognized unit: {length_unit} for Midas Civil")

        force_unit = str(eu.force)
        match force_unit:
            case "kN":
                midas_force = 'KN'
            case "N":
                midas_force = 'N'
            case "lbf":
                midas_force = 'LBF'
            case "kip":
                midas_force = 'KIPS'
            case _:
                raise NotImplementedError(f"Unrecognized unit: {force_unit} for Midas Civil")

        temp_unit = str(eu.temperature_coef)
        match temp_unit:
            case "1/Δ°F":
                midas_temperature_coef = 'F'
            case "1/Δ°C":
                midas_temperature_coef = 'C'
            case _:
                raise NotImplementedError(f"Unrecognized unit: {temp_unit} for Midas Civil")

        self.model.units(force=midas_force, length=midas_length, temp=midas_temperature_coef)
        logger.info(f"Model units set to {midas_force}, {midas_length}, {midas_temperature_coef}")
