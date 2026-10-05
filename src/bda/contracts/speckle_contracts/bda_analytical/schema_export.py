"""Export the JSON schema for the whole model, rooted at ModelRootCollection.

Run as a module to write the schema and a companion unit report:

    python -m bda.contracts.speckle_contracts.bda_analytical.schema_export
    python -m bda.contracts.speckle_contracts.bda_analytical.schema_export docs/schema

The schema carries the unit annotations added by ``UnitParameter``:

* ``enum`` on ``provided_unit`` -- the units a consumer may send.
* ``x-unit-dimension`` -- the physical dimension, for consumers that want to
  accept any compatible unit rather than a fixed list.
* ``x-unit-source`` -- how the enum was derived (``literal``, ``allowed-units``,
  ``dimension-catalogue``, or ``open``).
* ``readOnly`` on ``base_unit`` / ``base_value`` -- computed server-side, so a
  generated form should not prompt for them.

``unit_report`` flattens the same information into a table, which is easier to
diff in review than the nested schema.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterator

from bda.contracts.speckle_contracts.unit_parameters import UnitParameter
from bda.contracts.speckle_contracts.bda_analytical.model_root import (
    ModelRootCollection,
)


def build_root_schema() -> dict[str, Any]:
    """Return the JSON schema for the model root."""
    ModelRootCollection.model_rebuild()

    return ModelRootCollection.model_json_schema()


def _all_unit_parameter_classes() -> Iterator[type[UnitParameter]]:
    """Yield every declared UnitParameter subclass, deduplicated by name.

    Skips the synthetic classes pydantic creates when a generic is parametrised
    (``UnitParameter[Annotated[float, Strict()]]``); they are an implementation
    detail, not a contract a consumer ever sees.
    """
    seen: set[str] = set()

    def walk(cls: type) -> Iterator[type]:
        for subclass in cls.__subclasses__():
            yield subclass
            yield from walk(subclass)

    for subclass in walk(UnitParameter):
        if "[" in subclass.__name__:
            continue

        name = f"{subclass.__module__}.{subclass.__qualname__}"

        if name in seen:
            continue

        seen.add(name)
        yield subclass


def unit_report() -> list[dict[str, Any]]:
    """Flatten each parameter's published units into a sortable table."""
    rows: list[dict[str, Any]] = []

    for cls in _all_unit_parameter_classes():
        provided = cls.resolve_allowed_units("provided_unit")
        base = cls.resolve_allowed_units("base_unit")

        rows.append(
            {
                "parameter": cls.__name__,
                "module": cls.__module__,
                "dimension": cls.UNIT_DIMENSION,
                "provided_units": list(provided.units or []),
                # "enum" means only these units validate; "suggested" means any
                # dimensionally compatible unit does, and these are the offered ones.
                "enforcement": "enum" if provided.closed else "suggested",
                "source": provided.source,
                "base_unit": list(base.units or []),
            }
        )

    return sorted(rows, key=lambda row: (row["parameter"], row["module"]))


def write_schema(output_dir: Path) -> tuple[Path, Path]:
    """Write the root schema and the unit report; return both paths."""
    output_dir.mkdir(parents=True, exist_ok=True)

    schema_path = output_dir / "bda_model_root.schema.json"
    report_path = output_dir / "bda_unit_report.json"

    schema_path.write_text(
        json.dumps(build_root_schema(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    report_path.write_text(
        json.dumps(unit_report(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return schema_path, report_path


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    output_dir = Path(args[0]) if args else Path("docs") / "schema"

    schema_path, report_path = write_schema(output_dir)

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    rows = unit_report()
    enumerated = [row for row in rows if row["enforcement"] == "enum"]
    suggested = [row for row in rows if row["enforcement"] == "suggested" and row["provided_units"]]
    open_rows = [row for row in rows if not row["provided_units"]]

    print(f"schema      -> {schema_path}  ({len(schema.get('$defs', {}))} definitions)")
    print(f"unit report -> {report_path}")
    print(f"unit parameters: {len(rows)}")
    print(f"  closed enum (only listed units valid) : {len(enumerated)}")
    print(f"  suggested (any compatible unit valid) : {len(suggested)}")
    print(f"  no unit list published                : {len(open_rows)}")

    for row in open_rows:
        print(f"    - {row['parameter']} (dimension={row['dimension']!r})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
