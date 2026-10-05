"""Fetch section geometric properties from Midas Civil NX.

Uses two confirmed-working endpoints:

    1. GET /db/SECT
       Returns section definitions (name, type, raw dimensions).
       Used to build the list of section names.

    2. POST /post/TABLE  body: {"TABLE_TYPE": "SECTIONALL"}
       Triggers Midas to export computed section properties to a file
       at the configured results_dir (EXPORT_PATH on the Midas host).
       The response body does NOT contain the data.

    3. Parse the exported file from results_dir.
       Columns (confirmed from Midas API testing 2026-04-xx):
       SectName, Area, Asy, Asz, Ixx, Iyy, Izz, Czp, Czm, Cyp, Cym,
       Qyb, Qzb, Peri.(Out), Peri.(In)

Important:
    SECTIONALL writes to a file — the response body is empty/irrelevant.
    The fetcher reads the file from results_dir after triggering the export.
    results_dir must be accessible from the machine running BDA (i.e., if
    Midas is local or the results folder is a network/OneDrive share).

    /ope/SECTPROP is broken (404 always).
    SECT_PROP_LAST_STAGE always errors. Do not use either.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Optional

from bda.contracts.result_models.section_properties_result_model import SectionPropertiesResultModel
from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import MidasAPI
from bda.infrastructure.utils import CANONICAL_UNIT_SYSTEM

logger = logging.getLogger(__name__)

# The file name Midas writes when TABLE_TYPE = "SECTIONALL"
_SECTIONALL_FILENAME = "SECTIONALL.csv"

# Canonical unit spec for the POST body.
MIDAS_CANONICAL_UNIT = {"FORCE": "kN", "DIST": "m"}


class MidasSectionPropertiesFetcher:
    """Fetch and parse section geometric properties from Midas Civil NX.

    Args:
        api: Bound MidasAPI transport.
        results_dir: Path to the directory on the Midas host where
            /post/TABLE writes its output files. Must be accessible
            from the machine running BDA (e.g. a shared/OneDrive folder).
    """

    def __init__(self, api: MidasAPI, results_dir: str) -> None:
        self._api = api
        self._results_dir = Path(results_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self) -> list[SectionPropertiesResultModel]:
        """Trigger the SECTIONALL export and return parsed section properties.

        Returns:
            List of `SectionPropertiesResultModel`, one per section defined
            in the Midas model.

        Raises:
            RuntimeError: If the API call fails or the export file cannot
                be found or parsed.
        """
        self._trigger_export()
        return self._parse_export_file()

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    def _trigger_export(self) -> None:
        """POST /post/TABLE with TABLE_TYPE=SECTIONALL to write the file."""
        body = {
            "TABLE_TYPE": "SECTIONALL",
            "UNIT": MIDAS_CANONICAL_UNIT,
        }
        try:
            resp = self._api.request("POST", "/post/TABLE", body)
            logger.info(
                "SECTIONALL export triggered — HTTP %d. "
                "File will be at: %s",
                resp.status_code,
                self._results_dir / _SECTIONALL_FILENAME,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to trigger SECTIONALL export from Midas: {exc}"
            ) from exc

    def _parse_export_file(self) -> list[SectionPropertiesResultModel]:
        """Read and parse the CSV file written by Midas."""
        export_path = self._results_dir / _SECTIONALL_FILENAME

        if not export_path.exists():
            raise RuntimeError(
                f"SECTIONALL export file not found at '{export_path}'. "
                "Check that results_dir in midas_config.json is correct and "
                "accessible from this machine."
            )

        results: list[SectionPropertiesResultModel] = []
        with export_path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    rm = SectionPropertiesResultModel(
                        section_name=row["SectName"].strip(),
                        area=float(row["Area"]),
                        shear_area_y=float(row["Asy"]),
                        shear_area_z=float(row["Asz"]),
                        torsional_inertia=float(row["Ixx"]),
                        moment_inertia_y=float(row["Iyy"]),
                        moment_inertia_z=float(row["Izz"]),
                        czp=float(row["Czp"]),
                        czm=float(row["Czm"]),
                        cyp=float(row["Cyp"]),
                        cym=float(row["Cym"]),
                        unit_system=CANONICAL_UNIT_SYSTEM,
                    )
                    results.append(rm)
                except (KeyError, ValueError) as exc:
                    logger.warning(
                        "Skipping malformed SECTIONALL row %r — %s", row, exc
                    )

        logger.info(
            "MidasSectionPropertiesFetcher: parsed %d sections from '%s'",
            len(results), export_path,
        )
        return results
