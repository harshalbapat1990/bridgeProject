def example_from_schema(schema: dict, defs: dict | None = None):
    """
    Generate structured example variants from schema.

    Behaviour:
    ✅ Expands structural variants (oneOf, discriminators)
    ✅ Picks ONE value for enums (no combinatorial explosion)
    ✅ Picks ONE branch for anyOf (valid minimal example)
    ✅ Resolves $ref
    ✅ Handles 'contains' collections (Speckle pattern)
    ✅ Forces 'id' fields to null (backend-controlled)
    """

    if defs is None:
        defs = schema.get("$defs", {})

    def resolve_ref(s):
        if "$ref" in s:
            ref_key = s["$ref"].split("/")[-1]
            return defs[ref_key]
        return s

    def expand(s):
        s = resolve_ref(s)

        # -------------------------
        # const
        # -------------------------
        if "const" in s:
            return [s["const"]]

        # -------------------------
        # enum → PICK ONE
        # -------------------------
        if "enum" in s:
            return [s["enum"][0]]

        # -------------------------
        # anyOf → PICK FIRST VALID
        # -------------------------
        if "anyOf" in s:
            for option in s["anyOf"]:
                result = expand(option)
                if result:
                    return result
            return [None]

        # -------------------------
        # Nullable union
        # -------------------------
        if isinstance(s.get("type"), list):
            non_null = [t for t in s["type"] if t != "null"]
            if non_null:
                return expand({**s, "type": non_null[0]})
            return [None]

        # -------------------------
        # oneOf → EXPAND ALL
        # -------------------------
        if "oneOf" in s:
            results = []
            for branch in s["oneOf"]:
                results.extend(expand(branch))
            return results

        # -------------------------
        # Arrays
        # -------------------------
        if s.get("type") == "array":

            items = s.get("items", {})

            # discriminated unions
            if "discriminator" in items:
                mapping = items["discriminator"].get("mapping", {})

                variants = []
                for ref in mapping.values():
                    ref_key = ref.split("/")[-1]
                    variants.extend(expand(defs[ref_key]))

                return [variants]

            # contains pattern
            if "allOf" in s:
                collected = []

                for subschema in s["allOf"]:
                    if "contains" not in subschema:
                        continue

                    contains = subschema["contains"]

                    speckle_type = (
                        contains.get("properties", {})
                        .get("speckle_type", {})
                        .get("const")
                    )

                    items = s.get("items", {})
                    discriminator = items.get("discriminator", {})
                    mapping = discriminator.get("mapping", {})

                    if speckle_type in mapping:
                        ref_key = mapping[speckle_type].split("/")[-1]
                        collected.extend(expand(defs[ref_key]))

                return [collected]

            # normal array
            item_vals = expand(items)
            return [[item_vals[0]]]

        # -------------------------
        # Objects
        # -------------------------
        if s.get("type") == "object":
            props = s.get("properties", {})
            result = {}

            for k, v in props.items():
                # ✅ FORCE id to null
                if k == "id":
                    result[k] = None
                    continue

                expanded = expand(v)
                result[k] = expanded[0] if expanded else None

            return [result]

        # -------------------------
        # Primitives
        # -------------------------
        if s.get("type") == "string":
            return ["string"]
        if s.get("type") == "integer":
            return [0]
        if s.get("type") == "number":
            return [0.0]
        if s.get("type") == "boolean":
            return [True]

        return [None]

    return expand(schema)
