"""Route B POST-pipeline entry point — Midas Civil NX.

Runs the full POST-processing pipeline against an already-open Midas Civil NX
session. No PRE workflow, no export, no analysis — the model must already be
analysed and the Midas API server must be running.

Usage
-----
From the project root (with Midas open and the API server running)::

    python src/bda/modules_post/run_post_midas.py
    python src/bda/modules_post/run_post_midas.py --spec path/to/run_spec.json
    python src/bda/modules_post/run_post_midas.py --spec src/bda/modules_post/run_spec.json --runs-dir D:/output/runs

Arguments
---------
--spec      Path to the JSON run-spec file (default: ``run_spec.json`` in the
            same directory as this script).
--runs-dir  Root directory for run output folders (default: ``tests/runs/``
            under the project root). Each run creates a timestamped sub-folder here.
--project   Short label used in the run-folder name (default: derived from the
            spec filename stem, e.g. ``run_spec``).

Run-spec format
---------------
See ``run_spec.json`` for a full example. Minimal structure::

    {
        "bridge_type": "psc_box",
        "groups": [
            {
                "id": "Girder_1",
                "element_ids": [1, 2, 3, ..., 54],
                "node_ids":    [1, 2, 3, ..., 55]
            }
        ],
        "load_cases": {
            "force":        ["ULS"],
            "displacement": [],
            "stress":       []
        }
    }

Exit codes
----------
0  Pipeline completed without error.
1  Configuration or spec error.
2  Midas connection failed.
3  Pipeline raised an unexpected exception.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure ``src/`` is on sys.path so ``bda.*`` imports work when running the
# script directly (without ``pip install -e .``).
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent          # src/bda/modules_post
_SRC  = _HERE.parent.parent                      # src/
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# ---------------------------------------------------------------------------
# Logging — console only until the RunFolder is ready; then we can add a
# file handler if needed.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
# Temporarily enable DEBUG for the Midas forces fetcher to diagnose empty responses.
logging.getLogger(
    "bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_forces_fetcher"
).setLevel(logging.DEBUG)
log = logging.getLogger("run_post_midas")


# ═══════════════════════════════════════════════════════════════════════════
# Argument parsing
# ═══════════════════════════════════════════════════════════════════════════

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Route B POST-pipeline: run_spec.json + live Midas → Excel checks."
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=_HERE / "run_spec.json",
        help="Path to run_spec.json (default: ./run_spec.json).",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=_HERE.parent.parent.parent / "tests" / "runs",
        help="Root directory for run output folders (default: tests/runs/ under project root).",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Short project label for the run-folder name (default: spec filename stem).",
    )
    return parser.parse_args()


# ═══════════════════════════════════════════════════════════════════════════
# Step 1 — Load run spec → JSONContext
# ═══════════════════════════════════════════════════════════════════════════

def _load_context(spec_path: Path):
    """Parse the run-spec JSON and return a JSONContext."""
    from bda.infrastructure.adapters.structural_context.json_context import JSONContext

    log.info("Loading run spec: %s", spec_path)
    if not spec_path.exists():
        log.error("Run spec not found: %s", spec_path)
        sys.exit(1)

    try:
        ctx = JSONContext.from_file(spec_path)
    except (ValueError, FileNotFoundError) as exc:
        log.error("Failed to parse run spec: %s", exc)
        sys.exit(1)

    log.info(
        "Context loaded — bridge_type=%s, groups=%d",
        ctx.bridge_type.value,
        len(ctx.groups()),
    )
    for group in ctx.groups():
        log.info(
            "  Group '%s': %d elements, %d nodes",
            group.id,
            len(group.element_ids),
            len(group.node_ids),
        )
    return ctx


# ═══════════════════════════════════════════════════════════════════════════
# Step 2 — Connect to Midas → build importer
# ═══════════════════════════════════════════════════════════════════════════

def _build_importer():
    """Connect to the running Midas Civil NX session and return an importer."""
    from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import (
        MidasConfigProvider,
    )
    from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import (
        MidasCivilSession,
    )
    from bda.infrastructure.adapters.analytical_software.importers.midas_civil_result_importer import (
        MidasCivilResultImporter,
    )

    log.info("Loading Midas configuration …")
    try:
        config_provider = MidasConfigProvider()
    except (FileNotFoundError, ValueError) as exc:
        log.error("Midas config error: %s", exc)
        sys.exit(1)

    log.info("  base_url = %s", config_provider.base_url)

    # Build the session (no open_session() call — Midas is already running).
    session = MidasCivilSession(config_provider)

    # Smoke-test the connection before handing it to the importer.
    log.info("Testing Midas API connection …")
    try:
        api = session.api()
        resp = api.request("GET", "/db/UNIT")
        if resp.status_code != 200:
            log.error(
                "Midas API responded with HTTP %d. "
                "Is the model open and the API server running?",
                resp.status_code,
            )
            sys.exit(2)
    except Exception as exc:
        log.error(
            "Cannot reach Midas API at %s: %s\n"
            "  → Make sure Midas Civil NX is open, a model is loaded,\n"
            "    and the API server is running (Tools → MIDAS API Server).",
            config_provider.base_url,
            exc,
        )
        sys.exit(2)

    log.info("Midas connection OK.")

    try:
        importer = MidasCivilResultImporter(session)
    except Exception as exc:
        log.error("Failed to build importer: %s", exc)
        sys.exit(3)

    return importer


# ═══════════════════════════════════════════════════════════════════════════
# Step 3 — Create RunFolder
# ═══════════════════════════════════════════════════════════════════════════

def _build_run_folder(runs_dir: Path, project_name: str):
    """Create and return a RunFolder rooted at runs_dir."""
    from bda.modules_post.excel.run_folder import RunFolder

    runs_dir.mkdir(parents=True, exist_ok=True)
    run_folder = RunFolder(base_dir=runs_dir, project_name=project_name)
    log.info("Run folder: %s", run_folder.run_dir)
    return run_folder


# ═══════════════════════════════════════════════════════════════════════════
# Step 4 — Discover and run POST coordination modules
# ═══════════════════════════════════════════════════════════════════════════

def _run_pipeline(ctx, importer, run_folder) -> bool:
    """Discover POST modules for the bridge type and run each one."""
    from bda.bootstrap.bridge_module_factory import BridgeModuleFactory
    from bda.domain.enums import ProcessingStage
    from bda.infrastructure.utils.logger import AppLogger

    app_logger = AppLogger(console=True, log_file=False)

    log.info("Discovering POST modules for bridge_type='%s' …", ctx.bridge_type.value)
    try:
        module_types = BridgeModuleFactory.get_module_types(
            ctx.bridge_type, ProcessingStage.POST
        )
    except ValueError as exc:
        log.error("No POST modules registered for this bridge type: %s", exc)
        sys.exit(1)

    log.info("Found %d coordination module(s):", len(module_types))
    for mt in module_types:
        log.info("  %s", mt.__name__)

    all_passed = True
    for module_type in module_types:
        log.info("─" * 60)
        log.info("Running: %s", module_type.__name__)
        module = module_type(
            context=ctx,
            importer=importer,
            run_folder=run_folder,
            logger=app_logger,
        )
        passed = module.run()
        if not passed:
            log.error("Module '%s' reported failure.", module_type.__name__)
            all_passed = False

    return all_passed


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    args = _parse_args()

    spec_path: Path  = args.spec.resolve()
    runs_dir: Path   = args.runs_dir.resolve()
    project_name: str = args.project or spec_path.stem  # e.g. "run_spec"

    log.info("=" * 60)
    log.info("BDA Route B — POST pipeline (Midas Civil NX)")
    log.info("  spec       : %s", spec_path)
    log.info("  runs dir   : %s", runs_dir)
    log.info("  project    : %s", project_name)
    log.info("=" * 60)

    # 1. Parse run spec
    ctx = _load_context(spec_path)

    # 2. Connect to Midas
    importer = _build_importer()

    # 3. Create run folder
    run_folder = _build_run_folder(runs_dir, project_name)

    # 4. Copy spec into run folder inputs for traceability
    run_folder.save_spec({"spec_path": str(spec_path)})

    # 5. Run POST modules
    log.info("=" * 60)
    log.info("Starting POST pipeline …")
    try:
        success = _run_pipeline(ctx, importer, run_folder)
    except Exception as exc:
        log.exception("Unhandled exception in POST pipeline: %s", exc)
        sys.exit(3)

    log.info("=" * 60)
    if success:
        log.info("Pipeline COMPLETE. Outputs: %s", run_folder.run_dir)
        sys.exit(0)
    else:
        log.error("Pipeline finished with errors. Check logs above.")
        sys.exit(3)


if __name__ == "__main__":
    main()
