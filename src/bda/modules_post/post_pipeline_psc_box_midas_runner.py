"""POST pipeline runner — runs PTBoxGirderCoordination against a live Midas session via Route B.

Usage (from the project root, with .venv active):

    python src/bda/modules_post/post_pipeline_psc_box_midas_runner.py
    python src/bda/modules_post/post_pipeline_psc_box_midas_runner.py --spec path/to/run_spec.json --out path/to/outputs

Prerequisites:
    - Midas Civil NX is running with a model open and analysis results available.
    - midas_config.json has the correct base_url and mapi_key.
    - run_spec.json has element/node IDs and load case names that match the model.

The script connects to the already-running Midas instance (does NOT launch a new one),
fetches results for the groups declared in run_spec.json, runs the registered Excel
check modules, and prints a summary of the CoordinationResult.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# ── Add src/ to path so the script works without `pip install -e .` ──────────
_HERE = Path(__file__).resolve().parent          # src/bda/modules_post
sys.path.insert(0, str(_HERE.parent.parent))     # src/

from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import MidasConfigProvider
from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import MidasCivilSession
from bda.infrastructure.adapters.analytical_software.importers.midas_civil_result_importer import MidasCivilResultImporter
from bda.infrastructure.adapters.structural_context.json_context import JSONContext
from bda.modules_post.coordination_modules.pt_box.pt_box_girder_coordination import PTBoxGirderCoordination
from bda.modules_post.excel.run_folder import RunFolder
from bda.infrastructure.utils.logger import AppLogger

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
_DEFAULT_SPEC = _HERE / "run_spec.json"
_DEFAULT_OUT  = _HERE.parent.parent.parent / "tests" / "post_pipeline_outputs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PSC Box POST pipeline runner — Route B (JSONContext) against live Midas.")
    p.add_argument(
        "--spec",
        type=Path,
        default=_DEFAULT_SPEC,
        help=f"Path to run_spec.json (default: {_DEFAULT_SPEC})",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=_DEFAULT_OUT,
        help=f"Base directory for run outputs (default: {_DEFAULT_OUT})",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    log = AppLogger(console=True, log_file=False)
    log.info("=== BDA PSC Box POST pipeline — Route B (Midas) ===")

    # ── 1. Load run spec ──────────────────────────────────────────────────────
    log.info("Loading run spec: %s", args.spec)
    context = JSONContext.from_file(args.spec)
    log.info(
        "Context: bridge_type=%s, %d group(s)",
        context.bridge_type.value,
        len(context.groups()),
    )
    for g in context.groups():
        log.info(
            "  Group '%s': %d elements, %d nodes",
            g.id, len(g.element_ids), len(g.node_ids),
        )

    # ── 2. Connect to Midas (already running) ─────────────────────────────────
    log.info("Connecting to Midas Civil NX …")
    config_provider = MidasConfigProvider()
    session = MidasCivilSession(config_provider)

    if not session.is_active:
        log.error(
            "Midas is not reachable at %s — is Civil NX running with MAPIserver active?",
            config_provider.base_url,
        )
        return 1

    log.info("Midas connection OK  (base_url=%s)", config_provider.base_url)

    if not session.has_analysis_results():
        log.warning(
            "Analysis pre-check returned negative — model may not be analyzed, "
            "or the probe failed. Continuing; a real fetch failure will confirm."
        )

    # ── 3. Build importer ─────────────────────────────────────────────────────
    importer = MidasCivilResultImporter(session)

    # Optionally list load cases available in the model to help with debugging.
    try:
        available_lcs = importer.available_load_cases()
        log.info("Available load cases (%d):", len(available_lcs))
        for lc in available_lcs:
            log.info("  %s", lc)
    except Exception as exc:
        log.warning("Could not list load cases: %s", exc)

    # ── 4. Set up run folder ──────────────────────────────────────────────────
    run_folder = RunFolder(args.out, project_name="smoke_test")
    log.info("Run folder: %s", run_folder.run_dir)

    # ── 5. Run coordination module ────────────────────────────────────────────
    # ── 4b. Quick force fetch to verify results exist ─────────────────────────
    # Ask for one element, one LC. If we get 0 envelopes back the model
    # almost certainly hasn't been analyzed — fail fast with a clear message.
    spec_groups = context.groups()
    probe_lcs = context.load_cases_for("force")
    if spec_groups and probe_lcs:
        from bda.domain.results.data_request import DataRequest
        probe_request = DataRequest(
            element_ids=frozenset([spec_groups[0].element_ids[0]]),
            force_loadcases=frozenset([probe_lcs[0]]),
        )
        probe_result = importer.fetch(probe_request)
        if probe_result.is_empty():
            log.error(
                "Zero results returned for element %d / LC '%s' — "
                "model is not analyzed. Run the analysis in Midas first.",
                spec_groups[0].element_ids[0], probe_lcs[0],
            )
            return 1
        log.info(
            "Analysis confirmed: got %d envelope(s) for probe element %d / LC '%s'.",
            len(probe_result.force_envelopes),
            spec_groups[0].element_ids[0], probe_lcs[0],
        )

    log.info("Starting PTBoxGirderCoordination …")
    coord = PTBoxGirderCoordination(
        context=context,
        importer=importer,
        run_folder=run_folder,
        logger=log,
        cache=None,
    )
    success = coord.run()

    # ── 6. Print summary ──────────────────────────────────────────────────────
    log.info("")
    last = getattr(coord, "_last_result", None)
    if last is not None:
        log.info("=== CoordinationResult: %s ===", last.summary())
        for cr in last.check_results:
            status = "PASS" if cr.passed else "FAIL"
            log.info("  [%s] %s / %s", status, cr.check_name, cr.component_id)
            for err in cr.errors:
                log.error("        %s", err)
        for err in last.errors:
            log.error("  [COORDINATION ERROR] %s", err)
    else:
        log.info("=== Result: %s ===", "PASSED" if success else "FAILED")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
