# Unit Tests

## Overview

Unit tests for BDA DataModel components:
- **DataFileProvider**: Loading materials and groups from JSON fixtures
- **Exporters**: CSI Bridge and MIDAS Civil exporter implementations (mocked, no software installation required)
- **Config Providers**: Configuration loading and validation

All tests use mocked dependencies and **do not require** actual software installations (CSI Bridge, MIDAS Civil).
They can run on any CI/CD environment including GitHub Actions.

**For integration tests with real software**, see `tests/integration/README.md`

## Quick Start

Install dependencies:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock
```

Run all tests:
```bash
pytest tests/unit/ -v
```

Run specific test module:
```bash
pytest tests/unit/test_data_file_provider_materials.py -v
pytest tests/unit/test_data_file_provider_groups.py -v
pytest tests/unit/test_csi_bridge_exporter.py -v
pytest tests/unit/test_exporters.py -v
pytest tests/unit/test_config_providers.py -v
```

Run with coverage:
```bash
pytest tests/unit/ --cov=infrastructure --cov=application --cov=domain --cov-report=html --cov-report=term-missing
```

View coverage report:
```bash
# Coverage report is generated in htmlcov/index.html
# Open it in your browser to see detailed coverage
```

Run tests with verbose output and show print statements:
```bash
pytest tests/unit/ -vv -s
```

Run only specific test class:
```bash
pytest tests/unit/test_csi_bridge_exporter.py::TestCSIBridgeExporterInitialization -v
```

Run only specific test method:
```bash
pytest tests/unit/test_csi_bridge_exporter.py::TestCSIBridgeExporterInitialization::test_initialization_with_valid_config -v
```

## Test Modules

### test_data_file_provider_materials.py
Tests for `DataFileProvider.get_materials_for_project()`:
- Material loading from JSON
- Material type validation (concrete, steel)
- Material definitions (standard vs. custom)
- Error handling (file not found, invalid JSON)

**Coverage**: Material data loading and validation logic

### test_data_file_provider_groups.py
Tests for `DataFileProvider.get_groups_for_project()`:
- Group hierarchy loading
- Parent-child relationships
- Root group identification
- Nested group validation

**Coverage**: Group data loading and hierarchical structure

### test_csi_bridge_exporter.py
Tests for `CSIBridgeExporter` (100% mocked, no CSI Bridge required):
- **Initialization**: Config loading, COM helper creation, session management
- **Session Management**: Attach to instance, create new instance, close session, context manager
- **File Operations**: Open file, save model, UI control
- **Export Workflow**: Material/section export phases, logging, error handling
- **Properties**: SAP model and bridge modeler accessors

**Coverage**: Complete CSI Bridge exporter lifecycle with mocked COM objects

**Test Classes**:
- `TestCSIBridgeExporterInitialization` - 10 tests for initialization scenarios
- `TestCSIBridgeExporterSessionManagement` - 7 tests for session lifecycle
- `TestCSIBridgeExporterFileOperations` - 7 tests for file I/O
- `TestCSIBridgeExporterExport` - 9 tests for export workflow
- `TestCSIBridgeExporterProperties` - 4 tests for property accessors

**Total**: 37 comprehensive test cases covering **94% of code**

### test_exporters.py
Tests for exporter factory and implementations:
- MIDAS Civil exporter initialization and export
- CSI Bridge exporter initialization and export
- Exporter factory pattern (get_exporter, singleton behavior)

**Coverage**: Exporter factory and basic export orchestration (mocked)
**Status**: ✅ All tests passing with proper COM mocking

**Test Classes**:
- `TestMidasCivilExporter` - 4 tests for MIDAS exporter
- `TestCSIBridgeExporter` - 4 tests for CSI Bridge exporter  
- `TestExporterFactory` - 5 tests for factory pattern

**Total**: 13 tests covering exporter factory integration

### test_config_providers.py
Tests for configuration providers:
- MIDAS config provider
- CSI Bridge config provider  
- ExporterFactory integration with configs
- JSON config provider interface compliance

**Coverage**: Configuration loading, validation, and factory integration
**Status**: ✅ All tests passing with proper COM mocking

## Fixtures

Fixtures are located in `fixtures/`:
- `materials.json` - Test materials (3 entries: concrete standard, steel custom, steel standard)
- `groups.json` - Test group hierarchy (superstructure and substructure)

## CI/CD Integration

These tests run automatically on GitHub Actions for every push/PR to `main`, `master`, or `dev` branches.
See `.github/workflows/python-tests.yml` for configuration.

The CI pipeline:
1. Sets up Python 3.14 environment
2. Installs dependencies from `requirements.txt`
3. Installs testing dependencies (`pytest`, `pytest-cov`, `pytest-mock`)
4. Runs all unit tests with coverage reporting (integration tests are automatically excluded)
5. Uploads coverage reports to Codecov (optional)

**Current Status**: ✅ **93 tests passing** (all unit tests working!)
- 37 CSI Bridge exporter tests
- 28 Data provider tests (materials + groups)
- 13 Exporter factory tests (MIDAS, CSI Bridge, Factory)
- 16 Config provider tests

**Integration tests** are automatically skipped on CI/CD and only run locally with installed software.

## Testing Best Practices

- **Mocking**: All external dependencies (COM objects, file systems) are mocked
- **Isolation**: Each test is independent and can run in any order
- **Clarity**: Test names clearly describe what is being tested
- **Coverage**: Aim for high code coverage while testing meaningful scenarios
- **Fast**: All tests should complete in seconds (no real software interaction)

## Test Organization

```
tests/
├── unit/                          # Unit tests (mocked, CI/CD)
│   ├── test_csi_bridge_exporter.py    # 37 tests - CSI Bridge exporter (mocked COM)
│   ├── test_exporters.py               # 13 tests - Factory and basic exporters
│   ├── test_config_providers.py        # 16 tests - Config loading and validation
│   ├── test_data_file_provider_*.py    # 28 tests - Data providers
│   └── TEST_README.md (this file)
│
├── integration/                   # Integration tests (real software, local only)
│   ├── test_csi_bridge_integration.py  # 10 tests - Real CSI Bridge interaction
│   ├── test_midas_civil_integration.py # 15+ tests - Real MIDAS Civil interaction
│   └── README.md
│
└── conftest.py                    # Shared fixtures
```

## Related Documentation

- **Integration Tests**: See `tests/integration/README.md` for tests with real software
- **MIDAS Exporter**: See `MIDAS_EXPORTER_IMPLEMENTATION.md` for implementation details
- **Quick Start**: See `MIDAS_EXPORTER_QUICKSTART.md` for usage examples

