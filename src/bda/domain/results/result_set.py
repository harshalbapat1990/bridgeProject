"""ResultSet — the single normalized container for all POST-processing results.

This is a **flat** container: all results live in three dict fields keyed by
tuples, plus a fourth dict for section properties keyed by section name. There
is no nested per-element or per-node sub-object — the whole thing is one unit
that can be merged, cached, and exported together.

Design intent
-------------
- *One container per importer call.* When the coordination module fetches from
  the cache and then from the live importer it gets two ``ResultSet`` objects
  which it merges into one before running checks.
- *Flat tuple keys.* ``force_envelopes`` and ``stresses`` are keyed by
  ``(element_id, ElementEnd, load_case)``; ``displacement_envelopes`` by
  ``(node_id, load_case)``; ``section_properties`` by ``section_name``. O(1)
  lookup from any consumer.
- *Per-component independent extremes.* Force and displacement envelopes widen
  per-component (not per-row) when the same key is inserted twice. Stress still
  uses overwrite semantics pending ``StressEnvelope`` decision.
- *Section properties alongside results.* ``section_properties`` is populated
  by the importer's section-properties fetcher and shares the same container
  lifetime as the force/displacement results.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Iterator, Tuple

from bda.domain.enums.output_software_enums import OutputSoftware
from bda.domain.enums.response_enums import ElementEnd
from bda.domain.results.result_primitives import (
    ElementForceEnvelope,
    ElementStress,
    NodalDisplacementEnvelope,
)
from bda.domain.results.section_properties import SectionProperties

if TYPE_CHECKING:
    from bda.domain.models.submodels import GeometryGroupBase
    from bda.domain.models.structural_group import StructuralGroup


# ---------------------------------------------------------------------------
# Composite key type aliases
# ---------------------------------------------------------------------------

ForceKey        = Tuple[int, ElementEnd, str]   # (element_id, end, load_case)
DisplacementKey = Tuple[int, str]               # (node_id, load_case)
StressKey       = Tuple[int, ElementEnd, str]   # (element_id, end, load_case)


# ---------------------------------------------------------------------------
# ResultSet — the flat container
# ---------------------------------------------------------------------------

@dataclass
class ResultSet:
    """Single flat container holding all normalized POST-processing results.

    All three result dicts use frozen dataclasses as values, so they are
    safe to share across the pipeline. Adding a new result must go through
    the dedicated ``add_*`` helpers so envelope-merge semantics are respected.

    The ``source`` field identifies which importer produced the data
    (``OutputSoftware.CSIBRIDGE``, ``OutputSoftware.MIDAS``, ...). It is
    used only for debugging and provenance, not for routing. When two
    containers with different sources are merged, the result's source
    becomes ``"mixed"``.
    """

    force_envelopes:        Dict[ForceKey,        ElementForceEnvelope]        = field(default_factory=dict)
    displacement_envelopes: Dict[DisplacementKey, NodalDisplacementEnvelope]   = field(default_factory=dict)
    stresses:               Dict[StressKey,       ElementStress]               = field(default_factory=dict)
    section_properties:     Dict[str,             SectionProperties]           = field(default_factory=dict)
    source: OutputSoftware | str = ""

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_force_envelope(self, envelope: ElementForceEnvelope) -> None:
        """Insert or widen a force envelope at ``(element_id, end, load_case)``."""
        key: ForceKey = (envelope.element_id, envelope.end, envelope.load_case)
        existing = self.force_envelopes.get(key)
        if existing is None:
            self.force_envelopes[key] = envelope
            return
        widened = existing
        widened = widened.updated_with(envelope.Fx_max).updated_with(envelope.Fx_min)
        widened = widened.updated_with(envelope.Fy_max).updated_with(envelope.Fy_min)
        widened = widened.updated_with(envelope.Fz_max).updated_with(envelope.Fz_min)
        widened = widened.updated_with(envelope.Mx_max).updated_with(envelope.Mx_min)
        widened = widened.updated_with(envelope.My_max).updated_with(envelope.My_min)
        widened = widened.updated_with(envelope.Mz_max).updated_with(envelope.Mz_min)
        self.force_envelopes[key] = widened

    def add_displacement_envelope(self, envelope: NodalDisplacementEnvelope) -> None:
        """Insert or widen a displacement envelope at ``(node_id, load_case)``.

        Mirrors ``add_force_envelope``: for combination load cases that produce
        multiple rows (CB:max / CB:min, or CSI StepType Max/Min), per-component
        extremes are widened independently rather than overwritten.
        """
        key: DisplacementKey = (envelope.node_id, envelope.load_case)
        existing = self.displacement_envelopes.get(key)
        if existing is None:
            self.displacement_envelopes[key] = envelope
            return
        widened = existing
        widened = widened.updated_with(envelope.UX_max).updated_with(envelope.UX_min)
        widened = widened.updated_with(envelope.UY_max).updated_with(envelope.UY_min)
        widened = widened.updated_with(envelope.UZ_max).updated_with(envelope.UZ_min)
        widened = widened.updated_with(envelope.RX_max).updated_with(envelope.RX_min)
        widened = widened.updated_with(envelope.RY_max).updated_with(envelope.RY_min)
        widened = widened.updated_with(envelope.RZ_max).updated_with(envelope.RZ_min)
        self.displacement_envelopes[key] = widened

    def add_stress(self, stress: ElementStress) -> None:
        """Insert an element stress at ``(element_id, end, load_case)``. Overwrites.

        NOTE: Stresses use overwrite semantics. A ``StressEnvelope`` type should
        be introduced once cross-program stress behaviour is verified.
        """
        self.stresses[(stress.element_id, stress.end, stress.load_case)] = stress

    def add_section_properties(self, props: SectionProperties) -> None:
        """Insert or overwrite section properties keyed by ``props.name``."""
        self.section_properties[props.name] = props

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def is_empty(self) -> bool:
        """Return ``True`` if this container holds no results of any kind."""
        return (
            not self.force_envelopes
            and not self.displacement_envelopes
            and not self.stresses
            and not self.section_properties
        )

    # ------------------------------------------------------------------
    # Combination
    # ------------------------------------------------------------------

    def merge(self, other: "ResultSet") -> "ResultSet":
        """Return a new container that is the union of ``self`` and ``other``.

        Overlapping force-envelope and displacement-envelope keys are widened
        per-component; overlapping stress keys use values from ``other``;
        overlapping section-property keys use values from ``other``.
        """
        if not self.source:
            merged_source = other.source
        elif not other.source or self.source == other.source:
            merged_source = self.source
        else:
            merged_source = "mixed"

        merged = ResultSet(
            force_envelopes=dict(self.force_envelopes),
            displacement_envelopes=dict(self.displacement_envelopes),
            stresses=dict(self.stresses),
            section_properties=dict(self.section_properties),
            source=merged_source,
        )
        for env in other.force_envelopes.values():
            merged.add_force_envelope(env)
        for denv in other.displacement_envelopes.values():
            merged.add_displacement_envelope(denv)
        for stress in other.stresses.values():
            merged.add_stress(stress)
        for props in other.section_properties.values():
            merged.add_section_properties(props)
        return merged

    # ------------------------------------------------------------------
    # Views
    # ------------------------------------------------------------------

    def view_for(self, component: "GeometryGroupBase") -> "ResultSetView":
        """Return a read-only view restricted to the element/node IDs of
        ``component`` (recursively including nested groups).
        """
        element_ids = _collect_element_ids(component)
        node_ids = _collect_node_ids(component)
        return ResultSetView(
            parent=self,
            element_ids=frozenset(element_ids),
            node_ids=frozenset(node_ids),
        )

    def view_for_structural_group(self, group: "StructuralGroup") -> "ResultSetView":
        """Return a read-only view for a ``StructuralGroup`` (POST processing).

        ``StructuralGroup`` stores element/node IDs as ordered tuples; we
        convert to frozenset for O(1) lookup in the view.
        """
        return ResultSetView(
            parent=self,
            element_ids=frozenset(group.element_ids),
            node_ids=frozenset(group.node_ids),
        )


# ---------------------------------------------------------------------------
# ResultSetView — read-only slice
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResultSetView:
    """Read-only slice of a ``ResultSet`` filtered by element/node IDs.

    Calculators never see the full container — they consume a view scoped to
    their structural group, which transparently filters every lookup.
    """

    parent: ResultSet
    element_ids: frozenset
    node_ids: frozenset

    # ------------------------------------------------------------------
    # Force envelope access
    # ------------------------------------------------------------------

    def force_envelope(
        self, element_id: int, end: ElementEnd, load_case: str
    ) -> ElementForceEnvelope:
        if element_id not in self.element_ids:
            raise KeyError(f"Element {element_id} is not part of this view")
        return self.parent.force_envelopes[(element_id, end, load_case)]

    def iter_force_envelopes(self) -> Iterator[ElementForceEnvelope]:
        for (eid, _end, _lc), env in self.parent.force_envelopes.items():
            if eid in self.element_ids:
                yield env

    # ------------------------------------------------------------------
    # Displacement envelope access
    # ------------------------------------------------------------------

    def displacement_envelope(
        self, node_id: int, load_case: str
    ) -> NodalDisplacementEnvelope:
        if node_id not in self.node_ids:
            raise KeyError(f"Node {node_id} is not part of this view")
        return self.parent.displacement_envelopes[(node_id, load_case)]

    def iter_displacement_envelopes(self) -> Iterator[NodalDisplacementEnvelope]:
        for (nid, _lc), denv in self.parent.displacement_envelopes.items():
            if nid in self.node_ids:
                yield denv

    # ------------------------------------------------------------------
    # Stress access
    # ------------------------------------------------------------------

    def stress(
        self, element_id: int, end: ElementEnd, load_case: str
    ) -> ElementStress:
        if element_id not in self.element_ids:
            raise KeyError(f"Element {element_id} is not part of this view")
        return self.parent.stresses[(element_id, end, load_case)]

    def iter_stresses(self) -> Iterator[ElementStress]:
        for (eid, _end, _lc), s in self.parent.stresses.items():
            if eid in self.element_ids:
                yield s

    # ------------------------------------------------------------------
    # Section properties access (via parent — not filtered by element)
    # ------------------------------------------------------------------

    def section_properties(self, section_name: str) -> SectionProperties:
        """Look up section properties by name from the parent container."""
        try:
            return self.parent.section_properties[section_name]
        except KeyError:
            raise KeyError(
                f"Section '{section_name}' not found in ResultSet.section_properties. "
                f"Available: {list(self.parent.section_properties.keys())}"
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_element_ids(group: "GeometryGroupBase") -> set:
    ids: set = set()
    for element in group.analytical_typology.elements:
        if element.element_id is not None:
            ids.add(element.element_id)
    for nested in group.nested_groups:
        ids.update(_collect_element_ids(nested))
    return ids


def _collect_node_ids(group: "GeometryGroupBase") -> set:
    ids: set = set()
    for node in group.analytical_typology.free_nodes:
        try:
            node_id = node.node_id
        except AttributeError:
            raise AttributeError(
                f"Node object {node!r} has no 'node_id' attribute. "
                "Check the domain model definition for the correct field name."
            )
        if node_id is not None:
            ids.add(node_id)
    for nested in group.nested_groups:
        ids.update(_collect_node_ids(nested))
    return ids
