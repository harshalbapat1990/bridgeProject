from pathlib import Path
from datetime import datetime, timezone
from typing import Type, Optional
import json
from pydantic import BaseModel


from pathlib import Path
from datetime import datetime, timezone
from typing import Type
import json
import re
from pydantic import BaseModel


def _kebab_case(name: str) -> str:
    """
    Convert CamelCase / snake_case to kebab-case.
    """
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    name = name.replace("_", "-")
    return name.lower()


def export_json_schema(
    *,
    target_dir: Path,
    model: Type[BaseModel],
    schema_family: str,
    version: str,
    description: str,
    namespace: str = "bda",
    overwrite: bool = False,
) -> Path:
    """
    Generate a JSON Schema from a Pydantic model, automatically
    derive the filename and schema ID, inject metadata, and save it.

    Parameters
    ----------
    target_dir : Path
        Directory where the schema will be written (e.g. schemas/x/1.0.0)
    model : Type[BaseModel]
        Pydantic model to generate the schema from
    schema_family : str
        Logical schema family (e.g. "bda-analytical-model")
    version : str
        Semantic version (e.g. "1.0.0")
    description : str
        Human-readable description
    namespace : str
        Namespace for URN generation (default: "bda")
    overwrite : bool
        Whether to overwrite an existing file

    Returns
    -------
    Path
        Path to the written schema file
    """

    schema_name = _kebab_case(model.__name__.removesuffix("Model").removesuffix("Collection"))
    file_name = f"{schema_name}.schema.json"
    target_path = target_dir / file_name

    if target_path.exists() and not overwrite:
        raise FileExistsError(
            f"Schema already exists at {target_path}. "
            f"Refusing to overwrite without overwrite=True."
        )

    schema_id = (
        f"urn:{namespace}:schema:{schema_family}:{schema_name}:{version}"
    )

    schema = model.model_json_schema()

    schema.update(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": schema_id,
            "schema_family": schema_family,
            "schema_name": schema_name,
            "version": version,
            "description": description,
            "generated_at": (
                datetime.now(timezone.utc)
                .isoformat(timespec="seconds")
                .replace("+00:00", "Z")
            ),
            "source_model": f"{model.__module__}.{model.__qualname__}",
        }
    )

    target_dir.mkdir(parents=True, exist_ok=True)

    target_path.write_text(
        json.dumps(schema, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return target_path

if __name__ == "__main__":
    from pathlib import Path
    from bda.contracts.speckle_contracts.bda_analytical.model_root import ModelRootCollection

    export_json_schema(
        target_dir=Path("src/bda/contracts/ui_schemas/bda-analytical-model/1.0.5"),
        model=ModelRootCollection,
        schema_family="bda-analytical-model",
        version="1.0.5",
        description="BDA Analytical Model Root schema including Materials, Sections and Model Configuration. Model upadted to reflect alterations to the schema to simplify enum handling and remove redundant UI fields. This is a breaking change from 1.0.4.",
    )