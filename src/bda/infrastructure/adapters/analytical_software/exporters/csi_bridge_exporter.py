"""Exporter for CSI Bridge structural analysis software."""

from typing import List

from bda.application.interfaces.analytical_software.session_manager import IAnalyticalSoftwareSession
from bda.domain import AnalyticalMultiModel
from bda.domain.enums import UnitSystem
from bda.domain.models.submodels import MaterialBase, SectionBase, GeometryGroup
from bda.domain.units.export_units import ExportUnits, get_export_units
from bda.infrastructure.adapters.analytical_software.exporters.exporter_base import ExporterBase
from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.geometry_exporter import CsiGeometryExporter
from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.model_preparation import CsiModelPraparator
from bda.infrastructure.utils.logger import AppLogger
from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession
from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.materials_exporter import CsiMaterialExporter
from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.section_exporter import CsiSectionExporter

logger = AppLogger()


class CSIBridgeExporter(ExporterBase):
    """Exporter for CSI Bridge software using an externally managed session_manager."""

    def __init__(self, session: IAnalyticalSoftwareSession):
        if not isinstance(session, CSIBridgeSession):
            raise TypeError("CSIBridgeExporter requires CSIBridgeSession")

        self._session = session
        self.software_name = session.software_name

    @property
    def sap_model(self):
        return self._session.sap_model

    @property
    def bridge_modeler(self):
        return self._session.bridge_modeler

    def export(self, amm: AnalyticalMultiModel) -> None:
        """Export analytical model to CSI Bridge."""
        exported = False

        try:
            logger.info("Starting export of '%s' to %s", amm.structure_name, self.software_name)

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

            if not self._export_geometry(amm.geometry_group or [], eu):
                raise RuntimeError("geometry export failed")

            exported = True

            logger.info("Successfully exported '%s' to %s", amm.structure_name, self.software_name)

        except Exception as e:
            logger.error("Export failed at %s: %s", "CSI Bridge export orchestration", e)
            logger.warning("CsiBridge model will be exported only partially")
            raise

        finally:
            # the model is saved also after a failed export, so that the partially
            # exported model can be inspected in the software
            self._session.save_model()

            if exported:
                logger.info("The CsiBridge model has been successfully exported.")
            else:
                logger.warning("The CsiBridge model has been exported only partially.")

    def _write_materials(self, materials: List[MaterialBase], export_units: ExportUnits) -> None:
        """Send the given materials to CSI Bridge."""

        material_exporter = CsiMaterialExporter(self.sap_model, export_units)
        for material in materials:
            material_exporter.export_material(material)

    def _write_sections(self, sections: List[SectionBase], export_units: ExportUnits) -> None:
        """Send the given sections to CSI Bridge, in the order they are given."""

        section_exporter = CsiSectionExporter(self.sap_model, export_units)
        for section in sections:
            section_exporter.export_section(section)

    def _write_geometry(self, geometry_groups: List[GeometryGroup], export_units: ExportUnits) -> None:
        """Send the given geometry groups to CSI Bridge."""

        geometry_exporter = CsiGeometryExporter(self.sap_model, export_units)
        for geometry_group in geometry_groups:
            geometry_exporter.export_geometry_group(geometry_group)

    def _prepare_model(self, amm: AnalyticalMultiModel) -> None:
        """
        This helper function prepares multimodel for export by setting up all areas specific to CsiBridge.

        This function include:
        - materials preparation for export by checking if all exported materials have unique names.
            As Csi identifies materials by their names.
        - sections preparation for export by checking if there are groups with the same section but with different material assigned.
            As Csi require material to be assigned to section.
            Sections are also checked for unique names, as Csi identifies sections by their names.

        Parameters
        ----------
        amm: AnalyticalMultiModel

        Returns
        -------

        """

        CsiModelPraparator.prepare_model_file(
            self.sap_model,
            self.get_model_units_code(
                self.get_model_units_name(amm.unit_system)))

        CsiModelPraparator.prepare_materials_for_export(amm)

        CsiModelPraparator.prepare_sections_for_export(amm)

    def run_analysis(self) -> None:
        self.sap_model.Analyze.RunAnalysis()

    def get_model_units_name(self, unit_system: UnitSystem) -> str:
        eu = get_export_units(unit_system)

        force_unit = str(eu.force)
        match force_unit:
            case "kN":
                csi_force = 'kN'
            case "N":
                csi_force = 'N'
            case "lbf":
                csi_force = 'lb'
            case "kip":
                csi_force = 'kip'
            case _:
                raise NotImplementedError(f"Unrecognized unit: {force_unit} for CsiBridge")

        length_unit = str(eu.length)
        match length_unit:
            case "ft":
                csi_length = 'ft'
            case "in":
                csi_length = 'in'
            case "m":
                csi_length = 'm'
            case "cm":
                csi_length = 'cm'
            case "mm":
                csi_length = 'mm'
            case _:
                raise NotImplementedError(f"Unrecognized unit: {length_unit} for CsiBridge")

        temp_unit = str(eu.temperature_coef)
        match temp_unit:
            case "1/Δ°F":
                csi_temperature_coef = 'F'
            case "1/Δ°C":
                csi_temperature_coef = 'C'
            case _:
                raise NotImplementedError(f"Unrecognized unit: {temp_unit} for CsiBridge")

        csi_unit_set = f"{csi_force}_{csi_length}_{csi_temperature_coef}"
        return csi_unit_set

    def get_model_units_code(self, model_units_name: str) -> int:
        """Return the CSI Bridge units code (int) for the given unit system."""

        CSI_UNITS_MAP = {
            "lb_in_F": 1,
            "lb_ft_F": 2,
            "kip_in_F": 3,
            "kip_ft_F": 4,
            "kN_mm_C": 5,
            "kN_m_C": 6,
            "kgf_mm_C": 7,
            "kgf_m_C": 8,
            "N_mm_C": 9,
            "N_m_C": 10,
            "Ton_mm_C": 11,
            "Ton_m_C": 12,
            "kN_cm_C": 13,
            "kgf_cm_C": 14,
            "N_cm_C": 15,
            "Ton_cm_C": 16,
        }

        csi_unit_value = CSI_UNITS_MAP.get(model_units_name, None)

        if csi_unit_value is None:
            raise NotImplementedError(f"Unrecognized unit set in CsiBridge: {model_units_name}")

        return csi_unit_value

    def set_unit_system(self, unit_system: UnitSystem) -> None:
        """Set the unit system in the CSI Bridge model."""
        csi_unit_set = self.get_model_units_name(unit_system)
        csi_unit_value = self.get_model_units_code(csi_unit_set)

        ret = self.sap_model.SetPresentUnits(csi_unit_value)
        if ret == 0:
            logger.info(f"Model units successfully set to {csi_unit_set}")
        else:
            logger.error(
                f"Failed to set model units to {csi_unit_set}; SetPresentUnits returned {ret}"
            )
            raise RuntimeError(
                f"Unable to set CSI Bridge model units to {csi_unit_set} (SetPresentUnits returned {ret})"
            )
