"""POST result import runner — exercises the full result import pipeline.

Exercises the full path: config → group/calculator merge → validation →
importer → ResultSet. Supports both CSI Bridge and Midas Civil NX via
the ``--backend`` flag (or the ``backend`` field in the config JSON).

The config JSON simulates what the MultiModel + calculator requirements
registry will eventually provide:

    groups[]           element type, element IDs, node IDs
    calculator_requirements{}   element_type → {forces, displacements, stresses}

These are merged into a single DataRequest, validated against the live
model, and then fetched.

Usage (from the Project root, with the target program running):

    python modules_post/smoke_test_importer.py --backend midas
    python modules_post/smoke_test_importer.py --backend csi
    python modules_post/smoke_test_importer.py --config path/to/config.json

Exit codes:
    0  All fetches completed without error.
    1  Configuration error (bad JSON, missing keys, empty request).
    2  Connection failed.
    3  Importer raised an unexpected exception.
    5  Validation failed (elements/nodes/load cases not in model).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# Ensure the Project root is on sys.path
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent          # Project/modules_post/
_PROJECT_ROOT = _SCRIPT_DIR.parent                     # Project/
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s — %(message)s",
)
log = logging.getLogger("post_result_import_runner")


# ═══════════════════════════════════════════════════════════════════════════
# Config loading
# ═══════════════════════════════════════════════════════════════════════════


def _load_config(config_path: Path) -> dict:
    """Load and minimally validate the JSON config."""
    if not config_path.exists():
        log.error("Config file not found: %s", config_path)
        sys.exit(1)
    with config_path.open(encoding="utf-8") as fh:
        try:
            cfg = json.load(fh)
        except json.JSONDecodeError as exc:
            log.error("Invalid JSON in %s: %s", config_path, exc)
            sys.exit(1)

    if not cfg.get("groups"):
        log.error("Config has no 'groups' — nothing to do.")
        sys.exit(1)
    if not cfg.get("calculator_requirements"):
        log.error("Config has no 'calculator_requirements' — cannot determine what to fetch.")
        sys.exit(1)

    log.info("Config loaded from %s", config_path)
    return cfg


# ═══════════════════════════════════════════════════════════════════════════
# Group → DataRequest merge
# ═══════════════════════════════════════════════════════════════════════════


def _build_merged_request(cfg: dict) -> "DataRequest":
    """Merge groups with calculator requirements into one DataRequest.

    For each group, look up its ``element_type`` in
    ``calculator_requirements`` to find what load cases are needed.
    Combine the group's element/node IDs with those load cases into a
    per-group DataRequest, then merge all groups into one.
    """
    from bda.domain.results.data_request import DataRequest

    groups = cfg["groups"]
    calc_reqs = cfg["calculator_requirements"]
    per_group: List[DataRequest] = []

    for group in groups:
        name = group.get("name", "<unnamed>")
        elem_type = group.get("element_type", "")
        element_ids = group.get("element_ids", [])
        node_ids = group.get("node_ids", [])

        if elem_type not in calc_reqs:
            log.warning(
                "Group '%s' has element_type '%s' which is not in "
                "calculator_requirements — skipping.", name, elem_type
            )
            continue

        reqs = calc_reqs[elem_type]
        force_lcs = reqs.get("forces", [])
        disp_lcs = reqs.get("displacements", [])
        stress_lcs = reqs.get("stresses", [])

        dr = DataRequest(
            element_ids=frozenset(element_ids),
            node_ids=frozenset(node_ids),
            force_loadcases=frozenset(force_lcs),
            disp_loadcases=frozenset(disp_lcs),
            stress_loadcases=frozenset(stress_lcs),
        )

        log.info(
            "Group '%s' (%s): %d elements, %d nodes, "
            "forces=%s, disps=%s, stresses=%s",
            name, elem_type,
            len(element_ids), len(node_ids),
            force_lcs, disp_lcs, stress_lcs,
        )
        per_group.append(dr)

    if not per_group:
        log.error("No valid groups after merging with calculator requirements.")
        sys.exit(1)

    merged = DataRequest.merge_all(per_group)
    log.info("─" * 60)
    log.info("Merged DataRequest:")
    log.info("  element_ids      = %s", sorted(merged.element_ids))
    log.info("  node_ids         = %s", sorted(merged.node_ids))
    log.info("  force_loadcases  = %s", sorted(merged.force_loadcases))
    log.info("  disp_loadcases   = %s", sorted(merged.disp_loadcases))
    log.info("  stress_loadcases = %s", sorted(merged.stress_loadcases))
    log.info("─" * 60)
    return merged


# ═══════════════════════════════════════════════════════════════════════════
# Backend connections
# ═══════════════════════════════════════════════════════════════════════════


def _connect_csi(cfg: dict):
    """Attach to an already-open CSI Bridge session_manager. Returns the importer."""
    conn = cfg.get("csi_connection", {})
    helper_object = conn.get("helper_object", "CSiBridge1.Helper")
    program_id    = conn.get("program_id",    "CSI.CSiBridge.API.SapObject")

    try:
        import comtypes
        import comtypes.client
        import comtypes.gen
    except ImportError as exc:
        log.error("comtypes not available — are you on Windows? (%s)", exc)
        sys.exit(2)

    log.info("Creating COM helper '%s' …", helper_object)
    try:
        raw_helper = comtypes.client.CreateObject(helper_object)
        import comtypes.gen.CSiBridge1 as _csi_gen
        helper = raw_helper.QueryInterface(_csi_gen.cHelper)
    except Exception as exc:
        log.error("Failed to create COM helper: %s", exc)
        sys.exit(2)

    sap_object = None
    log.info("Attempt 1 — helper.GetObject('%s') …", program_id)
    try:
        sap_object = helper.GetObject(program_id)
        if sap_object is None:
            log.warning("  helper.GetObject returned None.")
    except Exception as exc:
        log.warning("  helper.GetObject raised: %s", exc)

    if sap_object is None:
        for rot_id in [
            "CSiBridge.SapObject", "CSiBridge1.SapObject",
            "CSI.CSiBridge.API.SapObject", "CSI.CSIBRIDGE.API.SapObject",
        ]:
            log.info("Attempt 2 — GetActiveObject('%s') …", rot_id)
            try:
                sap_object = comtypes.client.GetActiveObject(rot_id)
                if sap_object is not None:
                    log.info("  Connected via GetActiveObject('%s').", rot_id)
                    break
            except Exception as exc:
                log.warning("  GetActiveObject('%s') failed: %s", rot_id, exc)

    if sap_object is None:
        log.error(
            "Could not attach to CSI Bridge.\n"
            "  • Is CSI Bridge open with a model loaded?\n"
            "  • Is the API enabled (Options → API → Enable)?"
        )
        sys.exit(2)

    sap_model = sap_object.SapModel
    log.info("Connected to CSI Bridge.")

    from bda.modules_post.importers.csi_bridge.csi_bridge_result_importer import (
        CsiBridgeResultImporter,
    )
    from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession

    session = object.__new__(CSIBridgeSession)
    session._sap_model = sap_model
    return CsiBridgeResultImporter(session)


def _connect_midas(cfg: dict):
    """Build a MidasAPI and return the importer."""
    conn = cfg.get("midas_connection", {})
    base_url = conn.get("base_url")
    mapi_key = conn.get("mapi_key")

    # Fall back to project-level midas_config.json
    if not base_url or not mapi_key:
        midas_cfg_path = _PROJECT_ROOT / "config" / "exporters" / "midas_config.json"
        if midas_cfg_path.exists():
            log.info("Loading Midas connection from %s", midas_cfg_path)
            with midas_cfg_path.open(encoding="utf-8") as fh:
                midas_cfg = json.load(fh)
            base_url = base_url or midas_cfg.get("base_url")
            mapi_key = mapi_key or midas_cfg.get("mapi_key")

    if not base_url or not mapi_key:
        log.error(
            "Missing base_url or mapi_key. Set in smoke_test_config.json "
            "under 'midas_connection' or in config/exporters/midas_config.json."
        )
        sys.exit(2)

    from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import MidasAPI
    api = MidasAPI(base_url, mapi_key)

    log.info("Testing Midas connection to %s …", base_url)
    try:
        test_resp = api.request("GET", "/db/UNIT")
        if test_resp.status_code != 200:
            log.error("Midas connectivity failed (status %d).", test_resp.status_code)
            sys.exit(2)
        log.info("Midas connection OK.")
    except Exception as exc:
        log.error("Midas connectivity failed: %s", exc)
        sys.exit(2)

    from bda.modules_post.importers.midas_civil.midas_civil_result_importer import (
        MidasCivilResultImporter,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Temporary: print a sample of results to verify the pipeline worked
# ═══════════════════════════════════════════════════════════════════════════


def _print_sample(result_set, max_per_type: int = 3) -> None:
    """Print a small sample of each result type. TEMPORARY — will be removed
    when the downstream handoff is wired up."""
    print()
    print("=" * 70)
    print(f"ResultSet  source='{result_set.source}'")
    print(f"  force_envelopes : {len(result_set.force_envelopes)} entries")
    print(f"  disp_envelopes  : {len(result_set.displacement_envelopes)} entries")
    print(f"  stresses        : {len(result_set.stresses)} entries")
    print("=" * 70)

    # --- Force envelopes (sample) ---
    if result_set.force_envelopes:
        shown = 0
        print()
        print(f"FORCE ENVELOPES (showing first {max_per_type})")
        print("-" * 70)
        for key in sorted(result_set.force_envelopes.keys(), key=str):
            if shown >= max_per_type:
                remaining = len(result_set.force_envelopes) - shown
                print(f"  … and {remaining} more")
                break
            elem_id, end, lc = key
            env = result_set.force_envelopes[key]
            print(f"  elem={elem_id:>6}  end={end.name:<2}  lc={lc}")
            for label in ("Fx", "Fy", "Fz", "Mx", "My", "Mz"):
                try:
                    vmax = getattr(getattr(env, f"{label}_max"), label)
                    vmin = getattr(getattr(env, f"{label}_min"), label)
                    print(
                        f"    {label}: max={vmax.magnitude:>12.4f} {vmax.units:~P}"
                        f"  min={vmin.magnitude:>12.4f} {vmin.units:~P}"
                    )
                except Exception as exc:
                    print(f"    {label}: (error: {exc})")
            shown += 1

    # --- Displacement envelopes (sample) ---
    if result_set.displacement_envelopes:
        shown = 0
        print()
        print(f"DISPLACEMENT ENVELOPES (showing first {max_per_type})")
        print("-" * 70)
        for key in sorted(result_set.displacement_envelopes.keys()):
            if shown >= max_per_type:
                remaining = len(result_set.displacement_envelopes) - shown
                print(f"  … and {remaining} more")
                break
            node_id, lc = key
            denv = result_set.displacement_envelopes[key]
            print(f"  node={node_id:>6}  lc={lc}")
            for label in ("UX", "UY", "UZ", "RX", "RY", "RZ"):
                try:
                    vmax = getattr(getattr(denv, f"{label}_max"), label)
                    vmin = getattr(getattr(denv, f"{label}_min"), label)
                    print(
                        f"    {label}: max={vmax.magnitude:>12.6f} {vmax.units:~P}"
                        f"  min={vmin.magnitude:>12.6f} {vmin.units:~P}"
                    )
                except Exception as exc:
                    print(f"    {label}: (error: {exc})")
            shown += 1

    # --- Stresses (sample) ---
    if result_set.stresses:
        shown = 0
        print()
        print(f"STRESSES (showing first {max_per_type})")
        print("-" * 70)
        for key in sorted(result_set.stresses.keys(), key=str):
            if shown >= max_per_type:
                remaining = len(result_set.stresses) - shown
                print(f"  … and {remaining} more")
                break
            elem_id, end, lc = key
            stress = result_set.stresses[key]
            print(f"  elem={elem_id:>6}  end={end.name:<2}  lc={lc}  points={len(stress.points)}")
            shown += 1

    print()
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke test: groups + calculator reqs → validate → import → ResultSet."
    )
    parser.add_argument(
        "--backend",
        choices=["csi", "midas"],
        default=None,
        help="Override the backend (default: read from config JSON).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_SCRIPT_DIR / "post_result_import_config.json",
        help="Path to the JSON config file.",
    )
    args = parser.parse_args()

    # 1. Load config
    cfg = _load_config(args.config)
    backend = args.backend or cfg.get("backend", "csi")
    log.info("Backend: %s", backend)

    # 2. Merge groups with calculator requirements → single DataRequest
    merged_request = _build_merged_request(cfg)

    if merged_request.is_empty():
        log.error("Merged request is empty — nothing to fetch.")
        sys.exit(1)

    # 3. Connect to the target program and build the importer
    if backend == "csi":
        importer = _connect_csi(cfg)
    elif backend == "midas":
        importer = _connect_midas(cfg)
    else:
        log.error("Unknown backend: %s", backend)
        sys.exit(1)

    # 4. List available load cases (informational)
    log.info("Querying available load cases …")
    try:
        available = importer.available_load_cases()
        log.info("Model has %d load cases:", len(available))
        for lc in available:
            log.info("  %-30s  (%s)", lc.name, lc.load_case_type.name)
    except Exception as exc:
        log.error("Failed to list load cases: %s", exc)
        sys.exit(3)

    # 5. Validate the merged request against the live model
    from bda.modules_post.validation.request_validator import RequestValidator

    validator = RequestValidator(importer)
    report = validator.validate(merged_request)

    if not report.passed:
        log.error(
            "Validation FAILED — %d error(s). Fix the config or the model.",
            len(report.errors),
        )
        sys.exit(5)
    log.info("Validation passed.")

    # 6. Fetch results
    log.info("Fetching results via %s importer …", backend.upper())
    try:
        result_set = importer.fetch(merged_request)
    except NotImplementedError as exc:
        log.error("NotImplementedError — a stub was called: %s", exc)
        sys.exit(3)
    except Exception as exc:
        log.exception("Importer raised: %s", exc)
        sys.exit(3)

    # 7. TEMPORARY: print a sample to verify it worked
    _print_sample(result_set)

    # 8. Summary
    total = (
        len(result_set.force_envelopes)
        + len(result_set.displacement_envelopes)
        + len(result_set.stresses)
    )
    if total == 0:
        log.warning("Completed but 0 results returned — check IDs and LC names.")
    else:
        log.info("Done — %d total result entries.", total)

    # In the real pipeline, result_set is handed off here. No sys.exit(0)
    # needed — the orchestrator continues.
    sys.exit(0)


if __name__ == "__main__":
    main()
