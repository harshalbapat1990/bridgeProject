"""Unit-aware parameter contracts.

Each ``UnitParameter`` subclass carries a physical dimension and publishes the
units a consumer may send, so one declaration drives all three jobs:

* **UI schema** -- allowable units appear in the JSON schema as an ``enum`` on
  ``provided_unit``, so a form can render a dropdown.
* **Payload validation** -- incoming units are checked against pint for
  parseability and dimensional compatibility.
* **Python-side calculation** -- ``base_value`` is computed automatically by
  converting ``provided_value`` from ``provided_unit`` into ``base_unit``.

How allowable units are resolved
--------------------------------
For ``provided_unit`` and ``base_unit``, in precedence order:

1. A ``Literal[...]`` annotation on the field -- the narrowest, author-declared
   set. Use this when a parameter accepts only specific units.
2. ``ALLOWED_UNITS`` -- an explicit set for the class, inherited by subclasses.
3. The curated catalogue for ``UNIT_DIMENSION`` -- every unit of that dimension
   the project accepts. See ``bda.domain.units.unit_catalogue``.
4. Nothing resolvable -- the field stays an open string, still dimensionally
   validated at runtime. The schema then carries ``x-unit-dimension`` only.

Declarations are checked at *import* time by ``__pydantic_init_subclass__``: a
unit that pint cannot parse, or that does not match the class dimension, raises
immediately rather than becoming an option in a published schema that then
fails when a consumer picks it.
"""

from typing import (
    Any,
    ClassVar,
    Generic,
    Literal,
    NamedTuple,
    TypeVar,
    get_args,
    get_origin,
)

from pydantic import (
    GetJsonSchemaHandler,
    StrictFloat,
    field_validator,
    model_validator,
    Field,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema

from bda.domain.units.registry import ureg
from bda.domain.units.unit_catalogue import canonical_dimension, units_for_dimension
from bda.contracts.speckle_contracts.base_objects import Parameter

UnitParameterT = TypeVar(
    "UnitParameterT",
    float,
    list[float],
    tuple[float, ...],
)

# Fields whose allowable units are published to consumers.
_UNIT_FIELDS = ("provided_unit", "base_unit")

# ClassVar types are invariant, so every ALLOWED_UNITS override must be annotated
# with exactly this alias rather than a narrower concrete type.
AllowedUnits = frozenset[str] | tuple[str, ...] | None

# Values of the "x-unit-source" schema annotation, telling a consumer where the
# unit list came from and therefore how to treat it.
_SOURCE_LITERAL = "literal"
_SOURCE_ALLOWED_UNITS = "allowed-units"
_SOURCE_CATALOGUE = "dimension-catalogue"
_SOURCE_OPEN = "open"

# A closed source is an allowlist: only those units validate, and the schema
# publishes them as a JSON Schema "enum". An open source accepts any unit that is
# dimensionally compatible, so its units are only suggestions and go out as
# "x-suggested-units" -- an "enum" there would wrongly reject a compatible unit
# the catalogue simply has not listed.
_CLOSED_SOURCES = frozenset({_SOURCE_LITERAL, _SOURCE_ALLOWED_UNITS})


class UnitConstraint(NamedTuple):
    """What a unit field accepts, and how that was decided."""

    units: tuple[str, ...] | None
    source: str

    @property
    def closed(self) -> bool:
        """True if ``units`` is an allowlist rather than a suggestion list."""
        return self.source in _CLOSED_SOURCES


def convert_to_base(
    value: Any,
    provided_unit: str,
    base_unit: str,
) -> Any:
    """Convert a scalar or sequence from ``provided_unit`` into ``base_unit``.

    Uses a pint ``Quantity`` per element rather than a single multiplicative
    factor, because a factor is wrong for offset units: 20 degC is 68 degF, not
    20 x 33.8. Building ``1 * ureg("degC")`` to derive a factor also raises
    ``OffsetUnitCalculusError`` outright.
    """
    quantity = ureg.Quantity

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return quantity(float(value), provided_unit).to(base_unit).magnitude

    if isinstance(value, (list, tuple)):
        converted = [
            quantity(float(item), provided_unit).to(base_unit).magnitude
            if isinstance(item, (int, float)) and not isinstance(item, bool)
            else item
            for item in value
        ]

        return tuple(converted) if isinstance(value, tuple) else converted

    # Anything else is passed through unchanged.
    return value


class UnitParameter(Parameter[UnitParameterT], Generic[UnitParameterT]):
    # Class-level metadata, not model fields. These must be ClassVar so pydantic
    # treats them as configuration on the subclass rather than instance data.
    UNIT_DIMENSION: ClassVar[str | None] = None
    ALLOWED_UNITS: ClassVar[AllowedUnits] = None

    provided_unit: str
    base_unit: str

    # Computed from provided_value + the two units, so consumers never supply it.
    base_value: UnitParameterT | None = Field(default=None)

    # ------------------------------------------------------------------
    # Allowable-unit resolution
    # ------------------------------------------------------------------

    @classmethod
    def _literal_units(cls, field_name: str) -> tuple[str, ...] | None:
        field = cls.model_fields.get(field_name)

        if field is None:
            return None

        if get_origin(field.annotation) is Literal:
            return tuple(str(arg) for arg in get_args(field.annotation))

        return None

    @classmethod
    def resolve_allowed_units(cls, field_name: str) -> UnitConstraint:
        """Return the ``UnitConstraint`` that applies to a unit field.

        A ``Literal`` or ``ALLOWED_UNITS`` yields a closed allowlist. Falling
        through to the catalogue yields an open constraint: any dimensionally
        compatible unit validates, and the catalogued units are published as
        suggestions for a UI to offer.
        """
        literal_units = cls._literal_units(field_name)

        if literal_units is not None:
            return UnitConstraint(literal_units, _SOURCE_LITERAL)

        if cls.ALLOWED_UNITS:
            return UnitConstraint(
                tuple(sorted(cls.ALLOWED_UNITS)),
                _SOURCE_ALLOWED_UNITS,
            )

        catalogue_units = units_for_dimension(cls.UNIT_DIMENSION)

        if catalogue_units:
            return UnitConstraint(catalogue_units, _SOURCE_CATALOGUE)

        return UnitConstraint(None, _SOURCE_OPEN)

    # ------------------------------------------------------------------
    # Import-time correctness of the declaration itself
    # ------------------------------------------------------------------

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)

        problems: list[str] = []
        dimension = cls.UNIT_DIMENSION

        # Check the dimension first and bail out on failure: every later check
        # is expressed relative to it, so continuing would only add noise.
        if dimension is not None:
            try:
                canonical_dimension(dimension)
            except ValueError as exc:
                raise TypeError(
                    f"Invalid unit declaration on "
                    f"{cls.__module__}.{cls.__qualname__}:\n  UNIT_DIMENSION {exc}"
                ) from exc

        allowed_units = (
            frozenset(cls.ALLOWED_UNITS) if cls.ALLOWED_UNITS else None
        )

        for field_name in _UNIT_FIELDS:
            constraint = cls.resolve_allowed_units(field_name)
            units = constraint.units

            if units is None:
                continue

            for unit in units:
                try:
                    quantity = ureg.Quantity(1.0, unit)
                except Exception as exc:
                    problems.append(
                        f"{field_name}: {unit!r} is not a unit pint can parse "
                        f"({type(exc).__name__})"
                    )
                    continue

                if dimension is not None and not quantity.check(dimension):
                    problems.append(
                        f"{field_name}: {unit!r} is not compatible with "
                        f"UNIT_DIMENSION {dimension!r} "
                        f"(it is {quantity.dimensionality})"
                    )

            # A Literal must stay inside ALLOWED_UNITS, or the two disagree
            # about what the schema should publish.
            if constraint.source == _SOURCE_LITERAL and allowed_units is not None:
                outside = sorted(set(units) - allowed_units)

                if outside:
                    problems.append(
                        f"{field_name}: {outside} narrowed by Literal but not "
                        f"present in ALLOWED_UNITS {sorted(allowed_units)}"
                    )

        if problems:
            raise TypeError(
                f"Invalid unit declaration on {cls.__module__}.{cls.__qualname__}:\n  "
                + "\n  ".join(problems)
            )

    # ------------------------------------------------------------------
    # Schema publication
    # ------------------------------------------------------------------

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        schema = handler(core_schema)

        # Model schemas are emitted into $defs and referenced, so reach through
        # the $ref to annotate the definition itself.
        schema = handler.resolve_ref_schema(schema)

        properties = schema.get("properties")

        if not properties:
            return schema

        if cls.UNIT_DIMENSION:
            schema["x-unit-dimension"] = cls.UNIT_DIMENSION

        base_constraint = cls.resolve_allowed_units("base_unit")
        base_units = base_constraint.units
        base_unit_label = base_units[0] if base_units and len(base_units) == 1 else None

        for field_name in _UNIT_FIELDS:
            subschema = properties.get(field_name)

            if subschema is None:
                continue

            constraint = cls.resolve_allowed_units(field_name)

            if cls.UNIT_DIMENSION:
                subschema["x-unit-dimension"] = cls.UNIT_DIMENSION

            subschema["x-unit-source"] = constraint.source

            if not constraint.units:
                continue

            if constraint.closed:
                # A single-valued Literal renders as "const"; replace it with a
                # one-item enum so consumers read every unit field the same way.
                subschema.pop("const", None)
                subschema["enum"] = list(constraint.units)
            else:
                # Open constraint: any dimensionally compatible unit validates,
                # so these are offered rather than enforced. An "enum" here would
                # reject a compatible unit the catalogue has not listed.
                subschema["x-suggested-units"] = list(constraint.units)

        provided_unit_schema = properties.get("provided_unit")

        if provided_unit_schema is not None:
            target = (
                f" Converted into {base_unit_label} as base_value."
                if base_unit_label
                else " Converted into base_unit as base_value."
            )

            dimension_note = (
                f" Must be dimensionally compatible with {cls.UNIT_DIMENSION}."
                if cls.UNIT_DIMENSION
                else ""
            )

            provided_unit_schema.setdefault(
                "description",
                f"Unit that provided_value is expressed in.{dimension_note}{target}",
            )

        # base_unit and base_value are contract-fixed and server-computed. Mark
        # them readOnly so generated forms do not prompt for them.
        for field_name in ("base_unit", "base_value"):
            subschema = properties.get(field_name)

            if subschema is not None and "default" in subschema:
                subschema["readOnly"] = True

        base_value_schema = properties.get("base_value")

        if base_value_schema is not None:
            base_value_schema.setdefault(
                "description",
                "Computed server-side from provided_value; ignored if supplied.",
            )

        return schema

    # ------------------------------------------------------------------
    # Validation and automatic conversion
    # ------------------------------------------------------------------

    @field_validator(*_UNIT_FIELDS)
    @classmethod
    def validate_pint_unit(
        cls,
        value: str,
        info: Any,
    ) -> str:
        try:
            quantity = ureg.Quantity(1.0, value)
        except Exception:
            raise ValueError(f"Invalid Pint unit: {value}")

        constraint = cls.resolve_allowed_units(info.field_name)

        # Only a closed constraint is an allowlist. Pydantic already enforces a
        # Literal; this covers ALLOWED_UNITS, which the annotation cannot express.
        # An open constraint deliberately accepts any compatible unit, so its
        # catalogued units are not checked for membership here.
        if constraint.closed and constraint.units and value not in constraint.units:
            raise ValueError(
                f"{value} not allowed. Allowed units: {list(constraint.units)}"
            )

        if cls.UNIT_DIMENSION and not quantity.check(cls.UNIT_DIMENSION):
            raise ValueError(
                f"{value} is not compatible with {cls.UNIT_DIMENSION}"
            )

        return value

    @classmethod
    def _field_default(cls, field_name: str) -> Any:
        field = cls.model_fields.get(field_name)

        return None if field is None else field.default

    @model_validator(mode="before")
    @classmethod
    def _populate_base_value(cls, data: Any) -> Any:
        """Fill base_value before field validation so it need not be supplied.

        The parent ``Parameter`` requires a base_value whenever units are
        defined, and its after-validator runs before any declared here -- so the
        value has to exist by then.
        """
        if not isinstance(data, dict):
            return data

        provided_unit = data.get("provided_unit", cls._field_default("provided_unit"))
        base_unit = data.get("base_unit", cls._field_default("base_unit"))
        provided_value = data.get("provided_value", cls._field_default("provided_value"))

        if not (isinstance(provided_unit, str) and isinstance(base_unit, str)):
            return data

        if provided_value is None:
            return data

        try:
            converted = convert_to_base(provided_value, provided_unit, base_unit)
        except Exception:
            # Leave base_value alone; the field validators report the real
            # problem (bad unit, wrong dimension) with a clearer message.
            return data

        return {**data, "base_value": converted}

    @model_validator(mode="after")
    def _compute_base_value(self) -> "UnitParameter[UnitParameterT]":
        """Recompute base_value from the validated fields.

        Also keeps base_value correct under ``validate_assignment``, which
        re-runs after-validators but not before-validators.
        """
        converted = convert_to_base(
            self.provided_value,
            self.provided_unit,
            self.base_unit,
        )

        object.__setattr__(self, "base_value", converted)

        return self


class LengthParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[length]"
    base_unit:str = "m"


class PressureParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[pressure]"
    base_unit: str = "Pa"


class TemperatureCoefficientParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[temperature] ** -1"
    base_unit: str = "1/Δ°C"


class WeightDensityParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[force] / [length]**3"
    base_unit: str = "kN/m³"


class ForceParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[force]"
    base_unit: str = "kN"


class AreaParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[length] ** 2"
    base_unit: str = "m²"


class VolumeParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[length] ** 3"
    base_unit: str = "m³"


class MassParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[mass]"
    base_unit: str = "kg"


class DensityParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[mass] / [length] ** 3"
    base_unit: str = "kg/m³"


class TimeParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[time]"
    base_unit: str = "s"

class TemperatureParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[temperature]"
    base_unit: str = "°C"

class VelocityParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[length] / [time]"
    base_unit: str = "m/s"

class AccelerationParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[length] / [time] ** 2"
    base_unit: str = "m/s²"

class ForcePerLengthParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[force] / [length]"
    base_unit: str = "kN/m"

class AngleParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    # Pint treats angles as dimensionless, so a UNIT_DIMENSION would also admit
    # strains and ratios. An explicit set is the correct constraint here.
    ALLOWED_UNITS: ClassVar[AllowedUnits] = frozenset({"deg", "rad", "grad"})
    base_unit: str = "deg"

# Moment and energy share a dimensionality in pint, so neither can rely on the
# catalogue -- it would offer joules for a bending moment. Both declare their own.
class MomentParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[force] * [length]"
    ALLOWED_UNITS: ClassVar[AllowedUnits] = frozenset(
        {"kN*m", "N*m", "MN*m", "kip*ft", "lbf*ft"}
    )
    base_unit: str = "kN*m"


class EnergyParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[force] * [length]"
    ALLOWED_UNITS: ClassVar[AllowedUnits] = frozenset(
        {"J", "kJ", "MJ", "Wh", "kWh", "Btu"}
    )
    base_unit: str = "kJ"


class StressParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[pressure]"
    base_unit: str = "Pa"


class ElasticModulusParameter(UnitParameter[UnitParameterT],Generic[UnitParameterT]):
    UNIT_DIMENSION: ClassVar[str] = "[pressure]"
    base_unit: str = "Pa"


class StrictPressureParameter(UnitParameter[StrictFloat]):
    UNIT_DIMENSION: ClassVar[str] = "[pressure]"
    base_unit: str = "Pa"


class StrictWeightDensityParameter(UnitParameter[StrictFloat]):
    UNIT_DIMENSION: ClassVar[str] = "[force] / [length]**3"
    base_unit: str = "kN/m³"


class StrictTemperatureCoefficientParameter(UnitParameter[StrictFloat]):
    UNIT_DIMENSION: ClassVar[str] = "[temperature] ** -1"
    base_unit: str = "1/Δ°C"