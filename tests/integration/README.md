# Integration Tests

## WARNING
These tests require real software installations and are intended for local Windows environments.
They are skipped on CI/CD and when required software is not available.

## Prerequisites

### CSI Bridge
1. CSI Bridge 26 installed (default path: `C:\Program Files\Computers and Structures\CSI Bridge 26`)
2. Valid CSI Bridge license
3. Windows OS (COM automation)

### MIDAS Civil
1. MIDAS Civil NX installed (default path: `C:\Program Files\MIDAS\MIDAS CIVIL NX\MIDAS CIVIL NX`)
2. Valid MIDAS Civil license
3. Windows OS
4. MAPI configuration in `config/exporters/midas_config.json`

## Folder Structure

`tests/integration/`
- `csi/` - CSI Bridge integration scenarios
  - `pre/materials/` - pre-export checks for materials
  - `pre/sections/` - pre-export checks for sections
- `midas/` - MIDAS Civil integration scenarios
  - `pre/materials/` - pre-export checks for materials
  - `pre/sections/` - pre-export checks for sections

## Running Tests

```bash
# all integration tests
pytest tests/integration/ -v

# CSI Bridge integration tests
pytest tests/integration/csi/ -v

# MIDAS Civil integration tests
pytest tests/integration/midas/ -v

# CSI pre-export tests
pytest tests/integration/csi/pre/materials/ -v
pytest tests/integration/csi/pre/sections/ -v

# MIDAS pre-export tests
pytest tests/integration/midas/pre/materials/ -v
pytest tests/integration/midas/pre/sections/ -v
```

## Markers

Defined in `pytest.ini`:
- `integration`
- `csi_bridge`
- `midas_civil`
- `slow`

Examples:

```bash
pytest -v -m integration
pytest -v -m "integration and csi_bridge"
pytest -v -m "integration and midas_civil"
pytest -v -m "integration and not slow"
```

## Notes

- Integration tests verify real interaction with installed tools.
- Unit tests (`tests/unit/`) remain the default for CI/CD.
- Temporary files created during test runs should not be committed.

