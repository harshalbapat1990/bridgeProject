SPECKLE_GENERIC_TYPES = (
    "Objects.Data.DataObject",
    "Speckle.Core.Models.Collections.Collection",
)


def fix_speckle_types(obj):
    "Recursively traverse a Speckle JSON-like structure and fix speckle_type values for DataObjects and Collections with original schema values which are overwritten by Speckle's generic DataObject/Collection type. This is done by looking for a custom property (bda_speckle_type) added by the sender which contains the original type information."
    if isinstance(obj, dict):

        if obj.get("speckle_type") in SPECKLE_GENERIC_TYPES:
            bda = obj.get("bda_speckle_type")

            if isinstance(bda, str):
                obj["speckle_type"] = bda

        for v in obj.values():
            fix_speckle_types(v)

    elif isinstance(obj, list):
        for item in obj:
            fix_speckle_types(item)
