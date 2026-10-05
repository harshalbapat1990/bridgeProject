"""JSONContext — Route B structural context read from a JSON run-spec file.

Run-spec schema
---------------
::

    {
        "bridge_type": "psc_box",
        "groups": [
            {
                "id": "Girder_1",
                "element_ids": [1, 2, 3, 4, 5],
                "node_ids": [10, 11, 12, 13, 14, 15]
            }
        ],
        "load_cases": {
            "force":        ["ULS_gr5", "SLS_gr1"],
            "displacement": ["SLS_gr1"],
            "stress":       []
        }
    }

``bridge_type`` must match a ``BridgeType`` enum value (e.g. ``"psc_box"``).

``load_cases`` is informational — individual modules declare their own data
requirements via ``data_requirements()``. The orchestrator can merge the two
if the user wants to force additional load cases.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from bda.application.interfaces.structural_context.i_structural_context import IStructuralContext
from bda.domain.enums.bridge_type_enums import BridgeType
from bda.domain.models.structural_group import StructuralGroup

logger = logging.getLogger(__name__)


class JSONContext(IStructuralContext):
    """Reads structural metadata from a JSON run-spec file.

    Prefer the ``from_file()`` factory over direct construction.
    """

    def __init__(
        self,
        bridge_type: BridgeType,
        groups: List[StructuralGroup],
        raw_spec: Dict[str, Any] | None = None,
    ) -> None:
        self._bridge_type = bridge_type
        self._groups = groups
        self._raw_spec = raw_spec or {}

    # ── Factory ────────────────────────────────────────────────────────────────

    @classmethod
    def from_file(cls, path: Path) -> "JSONContext":
        """Parse a JSON run-spec file and return a ``JSONContext``.

        Args:
            path: Absolute or relative path to the JSON run-spec.

        Raises:
            FileNotFoundError: If *path* does not exist.
            ValueError:        If the JSON is invalid or required keys are missing.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Run-spec not found: {path}")

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in run-spec {path}: {exc}") from exc

        return cls._from_dict(raw)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JSONContext":
        """Construct directly from a dict (useful for tests)."""
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "JSONContext":
        # -- bridge_type -------------------------------------------------------
        bt_raw = data.get("bridge_type")
        if not bt_raw:
            raise ValueError("Run-spec missing required key 'bridge_type'.")
        try:
            bridge_type = BridgeType(bt_raw)
        except ValueError:
            valid = [e.value for e in BridgeType]
            raise ValueError(
                f"Unknown bridge_type {bt_raw!r}. Valid values: {valid}"
            ) from None

        # -- groups ------------------------------------------------------------
        raw_groups = data.get("groups")
        if not raw_groups:
            raise ValueError("Run-spec missing required key 'groups' (or empty list).")

        groups: List[StructuralGroup] = []
        for i, g in enumerate(raw_groups):
            group_id = g.get("id")
            if not group_id:
                raise ValueError(f"Group at index {i} is missing required field 'id'.")
            groups.append(
                StructuralGroup(
                    id=str(group_id),
                    element_ids=[int(x) for x in g.get("element_ids", [])],
                    node_ids=[int(x) for x in g.get("node_ids", [])],
                )
            )

        return cls(bridge_type=bridge_type, groups=groups, raw_spec=data)

    # ── IStructuralContext ────────────────────────────────────────────────────

    @property
    def bridge_type(self) -> BridgeType:
        return self._bridge_type

    def groups(self) -> List[StructuralGroup]:
        return list(self._groups)

    # ── Extra accessors ───────────────────────────────────────────────────────

    @property
    def raw_spec(self) -> Dict[str, Any]:
        """The original parsed JSON dict (read-only copy)."""
        return dict(self._raw_spec)

    def load_cases_for(self, result_type: str) -> List[str]:
        """Return load case names declared for *result_type*.

        Args:
            result_type: One of ``"force"``, ``"displacement"``, ``"stress"``.

        Returns:
            List of load case name strings, or empty list if not declared.
        """
        lc_block = self._raw_spec.get("load_cases", {})
        return list(lc_block.get(result_type, []))

    def module_inputs_for(self, module_key: str) -> Dict[str, Any]:
        """Return the full inputs block for a specific module.

        Used to retrieve module-specific geometry and scalar inputs that are
        not derivable from the FEM results (e.g. the ``module_07`` block for
        ``GirderFlexureCheck``).

        Args:
            module_key: Key in the run-spec, e.g. ``"module_07"``.

        Returns:
            The dict at ``raw_spec[module_key]``, or ``{}`` if not present.
        """
        return dict(self._raw_spec.get(module_key, {}))

    def materials(self) -> Dict[str, Dict[str, Any]]:
        """Return the materials dict from the run-spec.

        Keys are material instance names (e.g. ``"A416"``, ``"C6000 grade"``,
        ``"A615 Gr60"``).  Values are property dicts with metadata keys
        (those starting with ``_``) stripped out, so callers only see
        ``{"f_pu": 1861.58, "f_pe": ..., ...}`` etc.

        When the AMM is available, the coordinator will source material
        properties from AMM instead; this accessor is the Route B fallback.

        Returns:
            Dict of material property dicts, or ``{}`` if no ``"materials"``
            key is present in the run-spec.
        """
        raw = self._raw_spec.get("materials", {})
        return {
            name: {k: v for k, v in props.items() if not k.startswith("_")}
            for name, props in raw.items()
            if isinstance(props, dict)
        }

    def module_load_cases_for(self, module_key: str) -> dict:
        """Return the load case mapping for a specific Excel check module.

        The ``module_load_cases`` block in the run-spec maps module keys to
        dicts of named load cases. Keys are module-specific (e.g. ``"force"``,
        ``"force_stage1"``); values are load case name strings.

        Args:
            module_key: Short module identifier declared as ``MODULE_KEY`` on
                        the ``IExcelCheckModule`` subclass, e.g. ``"girder_flexure"``.

        Returns:
            Dict of load case names for the module, or ``{}`` if not declared.
        """
        return dict(self._raw_spec.get("module_load_cases", {}).get(module_key, {}))

    def module_spec_for(self, run_spec_key: str) -> "Optional[Any]":
        """Return a ``JsonModuleSpec`` if the module block contains a ``"spec"`` sub-key.

        Parses ``run_spec[run_spec_key]["spec"]`` into a ``JsonModuleSpec`` and
        injects ``run_spec_key`` so the coordinator can trace back to the data
        block.  Returns ``None`` if the block or the ``"spec"`` sub-key is absent,
        or if the spec fails validation (with a warning logged).

        Args:
            run_spec_key: Top-level key in the run-spec, e.g. ``"module_07"``.

        Returns:
            Parsed ``JsonModuleSpec`` with ``run_spec_key`` set, or ``None``.
        """
        # Lazy import — avoids a circular dependency at import time.
        from bda.modules_post.excel.json_module_spec import JsonModuleSpec

        block = self._raw_spec.get(run_spec_key, {})
        spec_data = block.get("spec")
        if not spec_data:
            return None

        try:
            spec = JsonModuleSpec.model_validate(spec_data)
            spec.run_spec_key = run_spec_key
            return spec
        except Exception as exc:
            logger.warning(
                "JSONContext.module_spec_for(%r): failed to parse spec -- %s",
                run_spec_key, exc,
            )
            return None
