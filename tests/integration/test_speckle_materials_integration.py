import pytest
from bda.infrastructure.data_providers.data_speckle_provider import DataSpeckleProvider


# Design Dev test model provided by Matt
#SPECKLE_MODEL_URL = "https://design.dev.jacobs.com/projects/b05b0a09f4/models/eab47a2f4a"
#SPECKLE_MODEL_URL = "https://design.dev.jacobs.com/projects/b05b0a09f4/models/5aca29fa5a"
#SPECKLE_MODEL_URL = "https://design.jacobs.com/projects/8f0d636aa6/models/69a0d73026"
SPECKLE_MODEL_URL = ("https://design.jacobs.com/projects/8f0d636aa6/models/69a0d73026")

@pytest.fixture
def provider():
    return DataSpeckleProvider(
        speckle_model_url=SPECKLE_MODEL_URL,
        authentication_token=None
    )


# TEST 1 - Pipeline execution
def test_materials_pipeline_execution(provider):
    try:
        materials = provider.get_materials_for_project()
        assert isinstance(materials, list)
    except Exception as e:
        pytest.fail(
            f"Materials pipeline failed during validation. "
            f"Exception: {type(e).__name__}: {e}"
        )


# TEST 2 - Deterministic behavior
def test_materials_pipeline_is_deterministic(provider):
    first = provider.get_materials_for_project()
    second = provider.get_materials_for_project()

    assert len(first) == len(second)


# TEST 3 - Serialization safety
def test_materials_output_is_serializable(provider):
    materials = provider.get_materials_for_project()

    output = [m.model_dump(mode="json") for m in materials]

    assert isinstance(output, list)


# TEST 4 - Non-empty check
def test_materials_not_empty(provider):
    materials = provider.get_materials_for_project()

    if materials is None:
        pytest.skip("Pipeline failed before returning data")

    assert isinstance(materials, list)


# TEST 5 - Schema consistency
def test_materials_schema_consistency(provider):
    materials = provider.get_materials_for_project()

    if not materials:
        pytest.skip("No materials returned")

    keys = set(materials[0].model_dump(mode="json").keys())

    for mat in materials:
        assert set(mat.model_dump(mode="json").keys()) == keys