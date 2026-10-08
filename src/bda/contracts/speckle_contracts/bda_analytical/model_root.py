import difflib
import re
from bda.contracts.speckle_contracts.base_objects import BridgeCollection, BridgesBase
from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    MaterialIdString,
    SectionIdString,
)
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_DataObject import (
    BDA_ModelDataDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.materials.materials_collection import (
    MaterialsCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.sections.section_collection import (
    SectionsCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_bridge import (
    GeometryGroupBridge,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.boundary_conditions_collection import BoundaryConditionsCollection
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layout_collection import DeckLayoutCollection
from bda.contracts.speckle_contracts.bda_analytical.loading.loading_base import LoadingCollection
from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes


from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, ClassVar, Iterator, Literal, Optional, Union, Annotated


def _iter_models(
    root: Any,
    path: str = "$",
) -> Iterator[tuple[str, BaseModel, str | None]]:
    """Yield ``(path, model, owner)`` for every pydantic model in the tree.

    ``path`` is JSON-path-like and uses field aliases, so it matches the incoming
    payload rather than the Python attribute names. ``owner`` is the applicationId
    of the nearest enclosing object that has one -- a path of nested list indices
    alone is hard to act on, whereas the owning object's id is something the author
    recognises.

    Recurses through model fields, lists, tuples and dicts, and tracks visited ids
    so a shared object cannot cause an infinite loop.
    """
    seen: set[int] = set()

    def walk(
        value: Any,
        current: str,
        owner: str | None,
    ) -> Iterator[tuple[str, BaseModel, str | None]]:
        if isinstance(value, BaseModel):
            if id(value) in seen:
                return

            seen.add(id(value))

            yield current, value, owner

            if isinstance(value, BridgesBase) and value.applicationId:
                owner = value.applicationId

            model_fields = type(value).model_fields

            for name, child in value.__dict__.items():
                if name.startswith("_"):
                    continue

                field = model_fields.get(name)
                segment = field.alias if field is not None and field.alias else name

                yield from walk(child, f"{current}.{segment}", owner)

            for name, child in (getattr(value, "model_extra", None) or {}).items():
                yield from walk(child, f"{current}.{name}", owner)

            return

        if isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                yield from walk(item, f"{current}[{index}]", owner)

            return

        if isinstance(value, dict):
            for key, item in value.items():
                yield from walk(item, f"{current}[{key!r}]", owner)

    yield from walk(root, path, None)


# Reference parameter class -> the kind of object it points at. Adding a new kind
# of cross-reference means adding a line here, not changing the sweep below.
_REFERENCE_PARAMETERS: dict[type, str] = {
    MaterialIdString: "material",
    SectionIdString: "section",
}

# Collection class -> the kind of object its elements can be referenced as. These
# collections are the catalogues an applicationId reference resolves against.
_REFERENCE_CATALOGUES: dict[type, str] = {
    MaterialsCollection: "material",
    SectionsCollection: "section",
}


def _classify(model: BaseModel, mapping: dict[type, str]) -> str | None:
    for declared_type, kind in mapping.items():
        if isinstance(model, declared_type):
            return kind

    return None


def find_unresolved_references(root: Any) -> list[str]:
    """Return a message for every applicationId reference that does not resolve.

    Accepts any object tree -- a full ``ModelRootCollection``, a bare list of
    collections, or a partially assembled model -- so a reference sweep can be run
    before the whole root exists.

    Both sides are collected in a single walk: the catalogues (materials, sections)
    supply the valid applicationIds, and the reference parameters supply the ids
    that were asked for. The ``*IdNone`` variants hold ``provided_value=None`` and
    are not instances of the string parameters, so "no assignment" is skipped
    rather than reported as a broken reference.
    """
    available: dict[str, set[str]] = {
        kind: set() for kind in _REFERENCE_CATALOGUES.values()
    }
    usages: list[tuple[str, str, str, str | None]] = []

    for path, model, owner in _iter_models(root):
        catalogue_kind = _classify(model, _REFERENCE_CATALOGUES)

        if catalogue_kind is not None:
            for item in getattr(model, "elements", []):
                application_id = getattr(item, "applicationId", None)

                if application_id:
                    available[catalogue_kind].add(application_id)

            continue

        reference_kind = _classify(model, _REFERENCE_PARAMETERS)

        if reference_kind is not None:
            usages.append(
                (reference_kind, getattr(model, "provided_value"), path, owner)
            )

    problems: list[str] = []

    for kind, referenced, path, owner in usages:
        if referenced in available.get(kind, set()):
            continue

        candidates = sorted(available.get(kind, set()))
        location = f"{owner!r} ({path})" if owner else path
        detail = f"Unresolved {kind} reference {referenced!r} on {location}"

        suggestions = difflib.get_close_matches(
            referenced,
            candidates,
            n=3,
            cutoff=0.6,
        )

        if suggestions:
            detail += (
                f". Did you mean: {', '.join(repr(s) for s in suggestions)}?"
            )
        elif not candidates:
            detail += f". No {kind} objects are present in the model."
        else:
            detail += (
                f". Available {kind} applicationIds: "
                f"{', '.join(repr(c) for c in candidates)}"
            )

        problems.append(detail)

    return problems

RootObjects = Annotated[
    Union[
        BDA_ModelDataDataObject,
        MaterialsCollection,
        SectionsCollection,
        GeometryGroupBridge,
        BoundaryConditionsCollection,
        DeckLayoutCollection,
        LoadingCollection,
    ],
    Field(discriminator="name"),
]


class ModelRootCollection(BridgeCollection):
    COLLECTION_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^COL-ROOT$"
    )
    speckle_type: Literal[SpeckleTypes.COLLECTION.value] = Field(
        SpeckleTypes.COLLECTION.value,
        frozen=True,
    )

    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION.value
    ] = Field(
        SpeckleTypes.COLLECTION.value,
        frozen=True,
    )

    name: Literal["Model Root"] = "Model Root"

    elements: list[RootObjects] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "maxItems": 7,
            "allOf": [
                # Materials (optional)
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "const": MaterialsCollection.model_fields[
                                    "name"
                                ].default
                            }
                        },
                        "required": ["name"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                # Config (required)
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "const": BDA_ModelDataDataObject.model_fields[
                                    "name"
                                ].default
                            }
                        },
                        "required": ["name"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
                # Sections (optional)
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "const": SectionsCollection.model_fields[
                                    "name"
                                ].default
                            }
                        },
                        "required": ["name"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                # Geometry (optional)
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "const": GeometryGroupBridge.model_fields[
                                    "name"
                                ].default
                            }
                        },
                        "required": ["name"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                # Boundary Conditions (optional)
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "const": BoundaryConditionsCollection
                                .model_fields["name"]
                                .default
                            }
                        },
                        "required": ["name"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                # Deck layouts (optional)
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "const": DeckLayoutCollection.model_fields["name"].default
                            }
                        },
                        "required": ["name"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                # Loading (optional)
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "const": LoadingCollection.model_fields["name"].default
                            }
                        },
                        "required": ["name"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
            ],
        },
    )

    @model_validator(mode="after")
    def validate_material_and_section_references(self) -> "ModelRootCollection":
        """Check every geometry group's material/section id exists in the model.

        Geometry groups name their material and section by applicationId instead
        of nesting them, so nothing else can catch a typo: the model validates and
        then fails later in an exporter or in the target analysis package. Only the
        root can check this, because the referenced objects are siblings of the
        geometry rather than children of it.
        """
        problems = find_unresolved_references(self)

        if problems:
            raise ValueError(
                f"{len(problems)} unresolved applicationId reference(s):\n  "
                + "\n  ".join(problems)
            )

        return self

    @model_validator(mode="after")
    def validate_unique_application_ids(self) -> "ModelRootCollection":

        ids = set()

        def collect(obj):

            if hasattr(obj, "applicationId"):

                application_id = getattr(
                    obj,
                    "applicationId",
                    None,
                )

                if application_id:

                    if application_id in ids:
                        raise ValueError(
                            f"Duplicate applicationId detected: {application_id}"
                        )

                    ids.add(application_id)

            if hasattr(obj, "elements"):

                for child in obj.elements:
                    collect(child)

            if hasattr(obj, "properties"):

                collect(obj.properties)

        collect(self)

        return self

    @classmethod
    def create(
        cls,
        model_config: BDA_ModelDataDataObject,
        materials: Optional[MaterialsCollection] = None,
        sections: Optional[SectionsCollection] = None,
        geometry: Optional[GeometryGroupBridge] = None,
        boundary_conditions: Optional[BoundaryConditionsCollection] = None,
        application_id: str = "COL-ROOT",
        deck_layouts: Optional[DeckLayoutCollection] = None,
        loading: Optional[LoadingCollection] = None,
    ) -> "ModelRootCollection":
        elements: list[RootObjects] = [model_config]

        if materials is not None:
            elements.append(materials)

        if sections is not None:
            elements.append(sections)

        if geometry is not None:
            elements.append(geometry)
            
        if boundary_conditions is not None:
            elements.append(boundary_conditions)

        if deck_layouts is not None:
            elements.append(deck_layouts)

        if loading is not None:
            elements.append(loading)

        return cls(
            speckle_type=SpeckleTypes.COLLECTION.value,
            bda_speckle_type=SpeckleTypes.COLLECTION.value,
            applicationId=application_id,
            elements=elements,
        )

    @field_validator("applicationId")
    @classmethod
    def validate_application_id(
        cls,
        value: str,
    ):

        if not cls.COLLECTION_ID_PATTERN.match(value):
            raise ValueError(
                "Root collection applicationId must be COL-ROOT"
            )

        return value
    
if __name__ == "__main__":
        from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_enums import (
             ModelUnitSystemEnum,
             OutputSoftwareEnum,
             DesignCodesEnum,
             StructureTypeEnum
        )
        root = ModelRootCollection.create(
        model_config=BDA_ModelDataDataObject.create(
            model_unit_system=ModelUnitSystemEnum.METRIC,
            output_software=OutputSoftwareEnum.CSI_BRIDGE,
            design_code=DesignCodesEnum.AASHTO,
            structure_type=StructureTypeEnum.STEEL_COMPOSITE,
        )
    )
