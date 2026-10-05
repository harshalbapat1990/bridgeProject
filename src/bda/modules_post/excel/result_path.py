"""result_path — resolve dotted path strings to pint.Quantity values.

Path syntax
-----------
Four patterns are supported:

    forces.element[{id}].{I|J}.{lc}.{axis}_{max|min}
        Single-element force envelope for element *id*, end *I* or *J*,
        load case *lc*. Returns the governing scalar for the requested
        extreme (e.g. ``My_max`` → ``envelope.My_max.My``).

    forces.governing.{I|J}.{lc}.{axis}_{max|min}
        Governing extreme across **all elements** visible in the view.
        Returns the max (for ``*_max``) or min (for ``*_min``) scalar.

    displacements.node[{id}].{lc}.{axis}_{max|min}
        Single-node displacement envelope.
        ``{axis}`` is one of ``UX UY UZ RX RY RZ``.

    previous_outputs.{name}
        Value already computed by an earlier ``ExcelFileSpec`` in the same
        check, carried forward in the ``outputs_so_far`` dict. Enables
        multi-file chaining (e.g. file 2 reads section properties from
        file 1's output).

All resolved values are returned as ``pint.Quantity``.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

import pint

from bda.domain.enums.response_enums import ElementEnd
from bda.domain.results.result_set import ResultSetView


def resolve(
    path: str,
    view: ResultSetView,
    outputs_so_far: Optional[Dict[str, Any]] = None,
) -> pint.Quantity:
    """Resolve *path* against *view* and return a ``pint.Quantity``.

    Args:
        path:            Dotted result-path string (see module docstring).
        view:            ``ResultSetView`` scoped to the current structural group.
        outputs_so_far:  Scalar outputs produced by earlier ``ExcelFileSpec``
                         runs in the same check execution.

    Returns:
        Resolved ``pint.Quantity``.

    Raises:
        ValueError: If *path* does not match any recognised pattern.
        KeyError:   If the requested element/node/output does not exist in *view*.
    """
    if outputs_so_far is None:
        outputs_so_far = {}

    # ── previous_outputs.{name} ───────────────────────────────────────────────
    m = re.match(r"^previous_outputs\.(\w+)$", path)
    if m:
        name = m.group(1)
        if name not in outputs_so_far:
            raise KeyError(
                f"previous_outputs.{name!r} not found in outputs_so_far. "
                f"Available: {list(outputs_so_far.keys())}"
            )
        value = outputs_so_far[name]
        if isinstance(value, pint.Quantity):
            return value
        raise TypeError(
            f"previous_outputs.{name!r} is not a pint.Quantity: {type(value)}"
        )

    # ── forces.element[id].end.lc.component ───────────────────────────────────
    m = re.match(r"^forces\.element\[(\d+)\]\.([IJ])\.(\w+)\.(\w+)$", path)
    if m:
        element_id = int(m.group(1))
        end = ElementEnd[m.group(2)]
        load_case = m.group(3)
        component = m.group(4)   # e.g. "My_max"
        envelope = view.force_envelope(element_id, end, load_case)
        return _extract_force_component(envelope, component, path)

    # ── forces.governing.end.lc.component ─────────────────────────────────────
    m = re.match(r"^forces\.governing\.([IJ])\.(\w+)\.(\w+)$", path)
    if m:
        end = ElementEnd[m.group(1)]
        load_case = m.group(2)
        component = m.group(3)   # e.g. "My_max"
        is_max = component.endswith("_max")
        best: Optional[pint.Quantity] = None

        for env in view.iter_force_envelopes():
            if env.end != end or env.load_case != load_case:
                continue
            try:
                qty = _extract_force_component(env, component, path)
            except (KeyError, AttributeError):
                continue
            if best is None:
                best = qty
            elif is_max and qty.magnitude > best.magnitude:
                best = qty
            elif not is_max and qty.magnitude < best.magnitude:
                best = qty

        if best is None:
            raise KeyError(
                f"No force envelopes found for end={end.name}, "
                f"load_case={load_case!r} in view. "
                "Check that the importer fetched the required load case."
            )
        return best

    # ── displacements.node[id].lc.component ───────────────────────────────────
    m = re.match(r"^displacements\.node\[(\d+)\]\.(\w+)\.(\w+)$", path)
    if m:
        node_id = int(m.group(1))
        load_case = m.group(2)
        component = m.group(3)   # e.g. "UZ_max"
        denv = view.displacement_envelope(node_id, load_case)
        return _extract_displacement_component(denv, component, path)

    raise ValueError(
        f"Unrecognised result path: {path!r}\n"
        "Supported patterns:\n"
        "  forces.element[{id}].{I|J}.{lc}.{axis}_{max|min}\n"
        "  forces.governing.{I|J}.{lc}.{axis}_{max|min}\n"
        "  displacements.node[{id}].{lc}.{axis}_{max|min}\n"
        "  previous_outputs.{name}"
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_force_component(
    envelope: Any, component: str, path: str
) -> pint.Quantity:
    """Extract a scalar Quantity from a force envelope field.

    *component* is ``"{axis}_{extreme}"`` (e.g. ``"My_max"``).
    ``extreme`` selects the ``ForceVector`` on the envelope;
    ``axis`` selects the scalar field on that vector.
    """
    m = re.match(r"^(Fx|Fy|Fz|Mx|My|Mz)_(max|min)$", component)
    if not m:
        raise ValueError(
            f"Unrecognised force component {component!r} in {path!r}. "
            "Expected: {{Fx|Fy|Fz|Mx|My|Mz}}_{{max|min}}"
        )
    axis = m.group(1)
    extreme = m.group(2)
    envelope_field = f"{axis}_{extreme}"

    force_vector = getattr(envelope, envelope_field, None)
    if force_vector is None:
        raise AttributeError(
            f"Envelope has no field {envelope_field!r} (path: {path!r})"
        )
    qty = getattr(force_vector, axis, None)
    if qty is None:
        raise AttributeError(
            f"ForceVector has no field {axis!r} (path: {path!r})"
        )
    return qty


def _extract_displacement_component(
    denv: Any, component: str, path: str
) -> pint.Quantity:
    """Extract a scalar Quantity from a displacement envelope field.

    *component* is ``"{axis}_{extreme}"`` (e.g. ``"UZ_max"``).
    """
    m = re.match(r"^(UX|UY|UZ|RX|RY|RZ)_(max|min)$", component)
    if not m:
        raise ValueError(
            f"Unrecognised displacement component {component!r} in {path!r}. "
            "Expected: {{UX|UY|UZ|RX|RY|RZ}}_{{max|min}}"
        )
    axis = m.group(1)
    extreme = m.group(2)
    envelope_field = f"{axis}_{extreme}"

    nodal_disp = getattr(denv, envelope_field, None)
    if nodal_disp is None:
        raise AttributeError(
            f"NodalDisplacementEnvelope has no field {envelope_field!r} (path: {path!r})"
        )
    qty = getattr(nodal_disp, axis, None)
    if qty is None:
        raise AttributeError(
            f"NodalDisplacement has no field {axis!r} (path: {path!r})"
        )
    return qty
