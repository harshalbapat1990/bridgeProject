"""Export steps shared by all analytical software exporters."""

from abc import ABC, abstractmethod
from typing import List

from bda.application.interfaces.analytical_software.exporter import IExporter
from bda.domain import AnalyticalMultiModel
from bda.domain.models.submodels import GeometryGroup, MaterialBase, SectionBase
from bda.domain.units.export_units import ExportUnits
from bda.infrastructure.adapters.analytical_software.exporters.common.section_ordering import \
    order_sections_for_export
from bda.infrastructure.utils.logger import AppLogger

logger = AppLogger()


class ExporterBase(IExporter, ABC):
    """
    Export steps shared by the analytical software exporters.

    Every step reports its progress and its failure via global logger and returns whether it
    succeeded, so that the exporters can stop before the steps depending on the failed one.
    The order of the steps belongs to the exporters, as it is specific to the software they
    write to, the same as the software specific work delegated to the '_write_*' hooks.
    """

    def _prepare_model_for_export(self, amm: AnalyticalMultiModel) -> bool:
        """
        Prepare the multimodel and the model file for the export.

        Parameters
        ----------
        amm: AnalyticalMultiModel

        Returns
        -------
        bool
            True when the model was prepared.

        """

        logger.info("Preparing the model of '%s' for the export", amm.structure_name)

        try:
            self._prepare_model(amm)

        except Exception as e:
            logger.error("Export failed at model preparation: %s", e)
            return False

        return True

    def _export_materials(self, materials: List[MaterialBase], export_units: ExportUnits) -> bool:
        """
        Export materials to the analytical software.

        Parameters
        ----------
        materials: List[MaterialBase]
        export_units: ExportUnits

        Returns
        -------
        bool
            True when the materials were exported.

        """

        logger.info("Exporting materials: %s items", len(materials))

        if not materials:
            logger.warning("No materials found in the model")
            return True

        try:
            self._write_materials(materials, export_units)

        except Exception as e:
            logger.error("Export failed at materials export: %s", e)
            return False

        return True

    def _export_sections(self, sections: List[SectionBase], export_units: ExportUnits) -> bool:
        """
        Export sections to the analytical software.

        Parameters
        ----------
        sections: List[SectionBase]
        export_units: ExportUnits

        Returns
        -------
        bool
            True when the sections were exported.

        """

        logger.info("Exporting sections: %s items", len(sections))

        if not sections:
            logger.warning("No sections found in the model")
            return True

        sections_to_export = order_sections_for_export(sections)

        try:
            self._write_sections(sections_to_export, export_units)

        except Exception as e:
            logger.error("Export failed at sections export: %s", e)
            return False

        return True

    def _export_geometry(self, geometry: GeometryGroup | List[GeometryGroup],
                         export_units: ExportUnits) -> bool:
        """
        Export geometry to the analytical software.

        Parameters
        ----------
        geometry: GeometryGroup | List[GeometryGroup]
            A single geometry group or a list of them.
        export_units: ExportUnits

        Returns
        -------
        bool
            True when the geometry was exported.

        """

        geometry_groups = [geometry] if isinstance(geometry, GeometryGroup) else list(geometry)

        logger.info("Exporting geometry: %s groups", len(geometry_groups))

        if not geometry_groups:
            logger.warning("No geometry found in the model")
            return True

        try:
            self._write_geometry(geometry_groups, export_units)

        except Exception as e:
            logger.error("Export failed at geometry export: %s", e)
            return False

        return True

    @abstractmethod
    def _prepare_model(self, amm: AnalyticalMultiModel) -> None:
        """Set up everything the analytical software requires before the export."""
        pass

    @abstractmethod
    def _write_materials(self, materials: List[MaterialBase], export_units: ExportUnits) -> None:
        """Send the given materials to the analytical software."""
        pass

    @abstractmethod
    def _write_sections(self, sections: List[SectionBase], export_units: ExportUnits) -> None:
        """Send the given sections to the analytical software, in the order they are given."""
        pass

    @abstractmethod
    def _write_geometry(self, geometry_groups: List[GeometryGroup],
                        export_units: ExportUnits) -> None:
        """Send the given geometry groups to the analytical software."""
        pass
