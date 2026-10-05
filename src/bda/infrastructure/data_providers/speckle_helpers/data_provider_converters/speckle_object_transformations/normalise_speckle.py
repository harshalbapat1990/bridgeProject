def fix_speckle_types(obj):
    "Recursively traverse a Speckle JSON-like structure and fix speckle_type values for DataObjects with original schema values which are overwritten by Speckle's generic DataObject type. This is done by looking for a custom property added by the sender which contains the original type information."
    if isinstance(obj, dict):

        if obj.get("speckle_type") == "Objects.Data.DataObject":
            props = obj.get("properties", {})
            bda = props.get("bda_speckle_type")

            if isinstance(bda, dict):
                pv = bda.get("provided_value")
                if isinstance(pv, str):
                    obj["speckle_type"] = pv

        for v in obj.values():
            fix_speckle_types(v)

    elif isinstance(obj, list):
        for item in obj:
            fix_speckle_types(item)
