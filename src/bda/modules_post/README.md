# Post-Processing Module

The `modules_post` package imports analysis results from structural engineering
software, normalizes them into a program-agnostic `ResultSet`, and feeds them
to downstream calculators (girder checks, etc.).

## Importer Architecture

Every source program has a concrete importer behind the `IResultImporter`
interface. Calculators never see source-specific types — they consume
`ResultSet` objects containing pint-Quantity values in canonical units
(kN, m, kN*m, MPa, radians).

```
IResultImporter
  ├── CsiBridgeResultImporter   — CSI Bridge via COM (comtypes, Windows-only)
  └── MidasCivilResultImporter  — Midas Civil NX via REST API (cross-platform)
```

Both importers share the same internal structure:

```
Importer (IResultImporter)
  ├── IdMapper            — validates element/node ids against the live model
  ├── LoadCaseResolver    — classifies load cases (static, combination, envelope)
  ├── ForcesFetcher       — beam forces → ElementForceEnvelope
  ├── DisplacementsFetcher — nodal displacements → NodalDisplacement
  └── StressesFetcher     — element stresses → ElementStress
```

### Lifecycle

1. Caller constructs the importer with an open connection (COM proxy or REST API).
2. Calculators declare needs as `DataRequest`; the orchestrator merges them.
3. `importer.fetch(request)` returns a normalized `ResultSet`.
4. `importer.close()` releases importer-internal resources (not the program).

### Domain Primitives

All defined in `domain/results/result_primitives.py` with binding conventions:

- `ForceVector` — Fx (axial), Fy/Fz (shear), Mx (torsion), My/Mz (moments) in local axes.
- `ElementForceEnvelope` — per-component independent min/max, widened by `ResultSet.put_force_envelope`.
- `NodalDisplacement` — UX/UY/UZ/RX/RY/RZ in global axes; rotations enforced as radians.
- `NodalDisplacementEnvelope` — per-component independent min/max (mirrors `ElementForceEnvelope`),
  widened by `ResultSet.put_displacement_envelope`. This prevents data loss when combination
  load cases produce multiple rows (CB:max/CB:min or StepType Max/Min).
- `ElementStress` — list of `StressPoint(y, z, sigma)` tuples.

> **Note — stress envelope:** Stresses currently use overwrite semantics (`put_stress`).
> If combination load cases produce per-component independent stress extremes (as forces
> and displacements do), a `StressEnvelope` type should be introduced following the same
> pattern. This needs live verification against both CSI Bridge and Midas Civil NX.

---

## CSI Bridge Importer

Located in `importers/csi_bridge/`. Communicates via COM automation (comtypes).

### Connection

Uses `CSIBridgeConfigProvider` which reads from `config/exporters/csi_bridge_config.json`.

The importer requires a live `sap_model` COM proxy. It wraps each fetch
in a `CsiUnitsContext` that calls `SetPresentUnits()` to force kN-m-C
before reading, then restores the original units.

> **Note — unit handling amendment planned:** The current approach of
> switching units in the file is a design mistake. A future amendment
> should read the model's current units via `GetPresentUnits()` and
> convert, rather than mutating model state. This does not affect Midas.

### Key files

| File | Purpose |
|------|---------|
| `csi_bridge_result_importer.py` | Orchestrator — implements `IResultImporter` |
| `csi_forces_fetcher.py` | Beam forces via `FrameObj.GetResults()` |
| `csi_displacements_fetcher.py` | Nodal displacements |
| `csi_stresses_fetcher.py` | Element stresses (scaffold) |
| `csi_id_mapper.py` | Maps domain ids ↔ CSI string labels |
| `csi_load_case_resolver.py` | Classifies cases, manages output selection |
| `csi_units_context.py` | `SetPresentUnits` / restore context manager |

---

## Midas Civil NX Importer

Located in `importers/midas_civil/`. Communicates via the Midas REST API.

### Connection

Reads `base_url` and `mapi_key` from `config/exporters/midas_config.json` —
the same config file used by the Midas exporter.

```python
from src.modules_post.importers.midas_civil.midas_civil_result_importer import (
    MidasCivilResultImporter,
)

# Preferred — reads from midas_config.json
importer = MidasCivilResultImporter.from_config()

# Alternative — manual API for testing
from src.infrastructure.adapters.exporters.midas_helpers.MidasAPI import MidasAPI

api = MidasAPI("http://127.0.0.1:12101", "YOUR_MAPI_KEY")
importer = MidasCivilResultImporter(api)
```

### REST Endpoints

| Purpose | Method | Endpoint | TABLE_TYPE | Status |
|---------|--------|----------|------------|--------|
| Element ids | GET | /db/elem | — | Confirmed |
| Node ids/coords | GET | /db/node | — | Confirmed |
| Static LCs | GET | /db/STCT | — | Confirmed |
| Combinations | GET | /db/LDCOMB | — | Confirmed |
| Beam forces | POST | /post/table | BEAMFORCEVBM | Confirmed |
| Displacements | POST | /post/table | NODEDISP | TBD |
| Stresses | POST | /post/table | BEAMSTRESS | TBD |

### Unit Handling

Midas accepts per-request units in the POST body (`"UNIT": {"FORCE": "kN", "DIST": "m"}`),
so the importer always requests results in canonical units without switching model state.

### Envelope Handling (CB:max / CB:min)

Combination and envelope load cases produce rows suffixed with `(CB:max)` and
`(CB:min)`. The fetchers strip this suffix and feed both rows into `ResultSet`,
where `put_force_envelope` widens the per-component envelope. Confirmed for
forces; behavior for displacements and stresses is TBD.

### Key files

| File | Purpose |
|------|---------|
| `midas_civil_result_importer.py` | Orchestrator — `IResultImporter` + `from_config()` |
| `midas_forces_fetcher.py` | Beam forces via `BEAMFORCEVBM` |
| `midas_displacements_fetcher.py` | Nodal displacements via `NODEDISP` (TBD) |
| `midas_stresses_fetcher.py` | Element stresses via `BEAMSTRESS` (scaffold) |
| `midas_id_mapper.py` | Validates element/node ids via `/db/elem`, `/db/node` |
| `midas_load_case_resolver.py` | Classifies cases from `/db/STCT`, `/db/LDCOMB` |

### Known TBD Items

1. Displacement TABLE_TYPE — `"NODEDISP"` is the candidate; may need adjustment.
2. Stress TABLE_TYPE — `"BEAMSTRESS"` is the candidate; column layout TBD.
3. Rotation units — if Midas returns degrees, enable `math.radians()` in `_build_displacement()`.
4. Stress point coordinates — scaffold currently places a single point at centroid.
5. CB:max/CB:min for stresses — needs live verification. Displacements now use
   `NodalDisplacementEnvelope` (same pattern as forces).
6. Non-CB combination types (moving-load envelopes, construction-stage, time-history)
   may use different suffix conventions. The triple-send fallback (bare + CB:max + CB:min)
   for unknown load case types works but is wasteful. Needs live verification and
   tightening.
7. Static load case behaviour may differ across analysis types (linear static vs.
   nonlinear static vs. staged construction). Needs live verification.
8. Cross-program validation: the same model must be imported from both CSI Bridge and
   Midas Civil NX, and forces/displacements/stresses compared for sign-convention
   consistency. This test exists as a placeholder in `test_cross_program_validation.py`
   and must be run against real data. May also be extended to additional programs in
   the future.

---

## Key Differences Between Importers

| Concern | CSI Bridge | Midas Civil NX |
|---------|-----------|----------------|
| Transport | COM (comtypes, Windows-only) | REST (requests, cross-platform) |
| Connection object | `sap_model` COM proxy | `MidasAPI` (base_url + mapi_key) |
| Config file | `csi_bridge_config.json` | `midas_config.json` |
| Id encoding | String names ("F12") | Integer keys directly |
| Output selection | Must call `SetComboSelectedForOutput` | Not needed — LC names in POST body |
| Unit switching | Changes model units (context manager) | Per-request in POST body |
| Envelope convention | Multiple rows per (elem, lc) | Explicit `(CB:max)`/`(CB:min)` suffixes |
| End classification | Station distance = 0 or L | `"PartI"` / `"PartJ"` field |
| Error handling | COM exceptions + return codes | HTTP status codes + JSON bodies |
| `close()` | Restores output selection state | No-op |

---

## Tests

### Unit tests (no live connections)

```bash
# All unit tests
pytest tests/unit/ -v

# Midas importer only (44 tests, 6 classes)
pytest tests/unit/test_midas_importer.py -v
```

All tests use mocked API/COM responses and run anywhere.

### Integration tests (require installed software)

```bash
# All integration tests
pytest tests/integration/ -v

# CSI Bridge only
pytest tests/integration/test_csi_bridge_integration.py -v

# Midas Civil only
pytest tests/integration/test_midas_civil_integration.py -v

# By marker
pytest -v -m "integration and csi_bridge"
pytest -v -m "integration and midas_civil"
```

Integration tests auto-skip when the required software is not installed or
when running on CI/CD.

### Prerequisites

For CSI Bridge tests: CSI Bridge 26 installed, valid license, Windows.

For Midas Civil tests: Midas Civil NX installed, MAPI access configured in
`config/exporters/midas_config.json`, Windows.

### Cross-program validation

Compares results from both programs on the same structural model:

```bash
CSI_BRIDGE_RUNNING=1 MIDAS_MAPI_KEY=1 pytest tests/integration/test_cross_program_validation.py -v -s
```

Tests forces, displacements, and sign conventions across importers. Stress
tests are placeholders pending both fetchers being fully implemented.

### Test markers

- `@pytest.mark.integration` — all integration tests (skipped on CI)
- `@pytest.mark.csi_bridge` — CSI Bridge specific
- `@pytest.mark.midas_civil` — Midas Civil specific
- `@pytest.mark.slow` — long-running tests

### Troubleshooting

CSI Bridge: ensure all instances are closed before running tests; check
license availability; if COM errors occur, restart Windows to clear the cache.

Midas Civil: verify `base_url` and `mapi_key` in `midas_config.json`; check
that MAPI is enabled in Midas (Tools > MAPI); kill orphaned `CVLw.exe`
processes if tests fail to clean up.
