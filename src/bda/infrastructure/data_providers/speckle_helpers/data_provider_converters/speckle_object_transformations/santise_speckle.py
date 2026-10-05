SPECKLE_STRIP_FIELDS = {
    "totalChildrenCount"
}

def strip_speckle_metadata(obj):
    if isinstance(obj, dict):

        # ✅ remove keys in-place
        for key in list(obj.keys()):
            if key in SPECKLE_STRIP_FIELDS:
                del obj[key]

        # ✅ recurse
        for v in obj.values():
            strip_speckle_metadata(v)

    elif isinstance(obj, list):
        for item in obj:
            strip_speckle_metadata(item)