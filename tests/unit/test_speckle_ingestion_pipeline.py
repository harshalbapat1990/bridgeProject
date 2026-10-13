import json

from bda.infrastructure.data_providers.speckle_helpers.data_provider_converters.speckle_object_transformations.speckle_ingestion_pipeline import (
    canonicalise_speckle_payload,
)


def test_canonicalise_restores_custom_bda_types_after_speckle_serialization(monkeypatch):
    payload = {
        "speckle_type": "Objects.Data.DataObject",
        "bda_speckle_type": "Objects.Data.DataObject:BDA_Load_Example",
        "elements": [
            {
                "speckle_type": "Speckle.Core.Models.Collections.Collection",
                "bda_speckle_type": "Speckle.Core.Models.Collections.Collection:BDA_Loading",
                "totalChildrenCount": 1,
            }
        ],
    }
    monkeypatch.setattr(
        "bda.infrastructure.data_providers.speckle_helpers.data_provider_converters.speckle_object_transformations.speckle_ingestion_pipeline.operations.serialize",
        lambda _obj: json.dumps(payload),
    )

    canonical = canonicalise_speckle_payload(object())

    assert canonical["speckle_type"] == canonical["bda_speckle_type"]
    child = canonical["elements"][0]
    assert child["speckle_type"] == child["bda_speckle_type"]
    assert "totalChildrenCount" not in child
