"""PTBoxGirderCoordination — CoordinationModule for PT Box girder checks.

Orchestrates all Excel check modules for PT Box girders across every
structural group supplied by the context. For each group it:

1. Creates an isolated per-group subfolder inside the run folder.
2. Builds a ``ResultSetView`` scoped to the group's element/node IDs.
3. Runs every Excel module in ``EXCEL_MODULES`` and collects results.

Result caching
--------------
If ``self.cache`` is provided (injected via ``IModulePost.__init__``), this
module checks the cache before fetching and stores fresh results in it
afterward. The model hash is derived from the importer's connection identity
(a simple string label for now; replace with a real fingerprint once the AMM
exposes one).
"""
from __future__ import annotations

import logging
import math
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type

from bda.application.interfaces.module.i_module_post import IModulePost
from bda.domain.enums.response_enums import ElementEnd
from bda.domain.models.structural_group import StructuralGroup
from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_set import ResultSet
from bda.modules_post.excel.models import UnitSystemSpec
from bda.modules_post.excel.base import IExcelCheckModule
from bda.modules_post.modules.pt_box.girder_flexure import GirderFlexureCheck
# Parked modules — re-enable once templates and load-case names are confirmed:
# from bda.modules_post.modules.pt_box.end_block import EndBlockCheck
# from bda.modules_post.modules.pt_box.girder_shear import GirderShearCheck
# from bda.modules_post.modules.pt_box.girder_strand_stresses import StrandStressesCheck
# from bda.modules_post.modules.pt_box.girder_temporary_stresses import ConcreteTemporaryStressesCheck
from bda.modules_post.result_models.coordination_result import CoordinationResult

logger = logging.getLogger(__name__)


class PTBoxGirderCoordination(IModulePost):
    """CoordinationModule for all girder checks on a PT Box bridge.

    ``EXCEL_MODULES`` lists the static (hand-coded) module classes that run
    unconditionally.  At runtime ``_all_module_classes()`` extends this list
    with dynamically generated classes for any module whose run-spec block
    contains a ``"spec"`` sub-object, replacing the static class where both
    exist.

    To park a module, comment it out here.  To add a new check, either add a
    static class or drop a ``"spec"`` block into the run-spec JSON — no other
    Python changes are needed for the JSON-driven path.
    """

    EXCEL_MODULES: ClassVar[Tuple[Type[IExcelCheckModule], ...]] = (
        # Module 07 is driven by the JSON spec in run_spec.module_07.spec.
        # GirderFlexureCheck is kept here as the fallback when no spec is found.
        GirderFlexureCheck,
        # -- Parked — re-enable once templates / load-case names are confirmed --
        # GirderShearCheck,
        # ConcreteTemporaryStressesCheck,
        # StrandStressesCheck,
        # EndBlockCheck,
    )

    @property
    def module_name(self) -> str:
        return "PTBox_GirderCoordination"

    def _module_load_cases(self, module_cls) -> dict:
        """Return load case names for *module_cls* from the context run-spec.

        Falls back to an empty dict if the context does not implement
        ``module_load_cases_for`` (e.g. Route A / AMMContext).
        """
        key = getattr(module_cls, "MODULE_KEY", None)
        if key and hasattr(self.context, "module_load_cases_for"):
            return self.context.module_load_cases_for(key)
        return {}

    def _module_scalar_inputs(
        self,
        module_cls,
        pre_computed: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return the scalar_inputs dict for *module_cls* from the run-spec.

        For ``GirderFlexureCheck`` (INPUTS_SPEC_KEY = ``"module_07"``):
        - Reads ``module_07.scalar_inputs`` from the run-spec.
        - Overrides ``h`` with the **maximum section depth** across all nodes
          (taken from ``pre_computed["node_h_"]`` when available, giving the
          correct value for tapered spans).  Falls back to the sections dict
          when pre_computed is not yet available.

        Returns ``{}`` for modules that have no inputs block defined.

        Args:
            module_cls:   The module class being executed.
            pre_computed: Per-node pre-computed dict from ``_prepare_node_data``.
                          Used to derive the per-span h_max scalar for B10.
        """
        key = getattr(module_cls, "INPUTS_SPEC_KEY", None)
        if not key or not hasattr(self.context, "module_inputs_for"):
            return {}

        block = self.context.module_inputs_for(key)
        si = dict(block.get("scalar_inputs", {}))

        sections = {
            k: v for k, v in block.get("sections", {}).items()
            if not k.startswith("_")
        }

        # h = max section depth over all nodes (B10 in the template).
        # Priority: per-node heights from pre_computed (covers tapered spans) >
        #           fallback from sections dict (constant sections only).
        h_set = False
        if pre_computed:
            h_vals = pre_computed.get("node_h_", [])
            numeric = [v for v in h_vals if isinstance(v, (int, float))]
            if numeric:
                si["h"] = max(numeric)
                h_set = True

        if not h_set and sections:
            h_candidates = []
            for sec in sections.values():
                for field in ("h_end", "h_start", "h"):
                    if field in sec:
                        h_candidates.append(float(sec[field]))
                        break
            if h_candidates:
                si["h"] = max(h_candidates)

        si = self._resolve_material_refs(si, sections_data=sections)
        return si

    def _all_module_classes(self) -> list:
        """Return the effective list of module classes/types to run.

        For each entry in ``EXCEL_MODULES``:
        - If the entry carries an ``INPUTS_SPEC_KEY`` and the context provides a
          ``JsonModuleSpec`` for that key (via ``module_spec_for()``), the static
          class is **replaced** by a ``DynamicExcelModule`` subclass built from
          the JSON spec.
        - Otherwise the static class is used unchanged.

        This means:  dropping a ``"spec"`` block into ``run_spec.module_07``
        automatically switches Module 07 to JSON-driven execution with no
        further code changes.

        Returns:
            List of ``Type[IExcelCheckModule]`` in the same order as
            ``EXCEL_MODULES``, with dynamic replacements applied.
        """
        if not hasattr(self.context, "module_spec_for"):
            return list(self.EXCEL_MODULES)

        from bda.modules_post.excel.dynamic_module import make_dynamic_module_class

        result = []
        for cls in self.EXCEL_MODULES:
            spec_key = getattr(cls, "INPUTS_SPEC_KEY", None)
            if spec_key:
                json_spec = self.context.module_spec_for(spec_key)
                if json_spec is not None:
                    dynamic_cls = make_dynamic_module_class(json_spec)
                    self.logger.debug(
                        "[%s] Module %r replaced by %s (spec found for key %r).",
                        self.module_name, cls.__name__,
                        dynamic_cls.__name__, spec_key,
                    )
                    result.append(dynamic_cls)
                    continue
            result.append(cls)
        return result

    def _resolve_material_refs(
        self,
        scalar_inputs: Dict[str, Any],
        sections_data: Optional[Dict[str, Dict]] = None,
    ) -> Dict[str, Any]:
        """Resolve ``{"$ref": "<context>.<type>.<property>"}`` values in *scalar_inputs*.

        Two ``$ref`` contexts are supported:

        ``section.<type>.<property>``
            Resolves the material type (``concrete``, ``rebar``, ``tendon``) from
            the first section's ``materials`` sub-block, maps it to a top-level
            material instance name, then reads the property from that instance.

            Example: ``"section.tendon.f_pu"`` -> sections["PSC1"]["materials"]["tendon"]
            -> ``"A416"`` -> materials["A416"]["f_pu"]`` -> ``1861.58``

        ``materials.<instance>.<property>``
            Direct lookup into the top-level ``materials`` block by instance name.
            Useful for explicit one-off overrides; generally prefer ``section.*``.

        Entries whose keys start with ``"_"`` (``_notes``, ``_comment``, etc.) are
        stripped so they never reach the Excel engine.

        Graceful fallback: if a reference cannot be resolved a warning is logged
        and the value is set to ``None`` (the Excel engine writes an empty cell
        rather than raising).

        When the AMM is wired up, replace ``context.materials()`` with a lookup
        against the AMM's material registry -- no other changes are needed here.
        """
        # -- Load material library ---------------------------------------------
        materials: Dict[str, Dict[str, Any]] = {}
        if hasattr(self.context, "materials"):
            try:
                materials = self.context.materials()
            except Exception as exc:
                self.logger.warning(
                    "[%s] context.materials() failed (%s) -- all $refs will be None.",
                    self.module_name, exc,
                )

        # -- Build section-level type -> instance name map from first section --
        # If all sections use the same material grades (typical) the first section
        # is authoritative.  For mixed-grade bridges a per-node resolution would
        # be needed; that is deferred until a real case requires it.
        section_mat_map: Dict[str, str] = {}
        if sections_data:
            first_sec = next(iter(sections_data.values()), {})
            section_mat_map = first_sec.get("materials", {})
            if not section_mat_map:
                self.logger.warning(
                    "[%s] First section has no 'materials' sub-block -- "
                    "'section.*' $refs will fail.",
                    self.module_name,
                )

        # -- Resolve -----------------------------------------------------------
        resolved: Dict[str, Any] = {}
        for key, value in scalar_inputs.items():
            if key.startswith("_"):          # strip _notes, _comment, etc.
                continue
            if isinstance(value, dict) and "$ref" in value:
                ref_path: str = value["$ref"]
                try:
                    context_key, mat_type, prop = ref_path.split(".", 2)
                    if context_key == "section":
                        instance_name = section_mat_map[mat_type]
                        resolved[key] = materials[instance_name][prop]
                    elif context_key == "materials":
                        # Direct instance lookup: materials.<instance>.<prop>
                        resolved[key] = materials[mat_type][prop]
                    else:
                        raise ValueError(
                            f"Unknown $ref context {context_key!r}. "
                            f"Expected 'section' or 'materials'."
                        )
                except (ValueError, KeyError) as exc:
                    self.logger.warning(
                        "[%s] Cannot resolve $ref %r for scalar_input %r: %s "
                        "-- value set to None.",
                        self.module_name, ref_path, key, exc,
                    )
                    resolved[key] = None
            else:
                resolved[key] = value
        return resolved

    def _run(self) -> None:
        # -- 0. Save a copy of the run-spec into inputs/ for traceability -------
        # This lets anyone re-open the run folder later and see exactly which
        # parameters were active when the calculations were executed.
        if hasattr(self.context, "raw_spec"):
            try:
                self.run_folder.save_spec(self.context.raw_spec)
                self.logger.info(
                    "[%s] run_spec.json saved to %s",
                    self.module_name,
                    self.run_folder.inputs_dir / "run_spec.json",
                )
            except Exception as exc:
                self.logger.warning(
                    "[%s] Could not save run_spec to inputs folder: %s",
                    self.module_name, exc,
                )

        # Resolve the effective module list once for this run — static classes
        # are replaced by dynamic equivalents where a JSON spec is present.
        _module_classes = self._all_module_classes()

        # -- 1. Aggregate DataRequest from all Excel module classes ------------
        merged_from_modules = DataRequest.merge_all(
            cls.data_requirements(self._module_load_cases(cls))
            for cls in _module_classes
        )

        # Merge in the group element/node IDs from context so the importer
        # knows which elements/nodes to fetch (needed for "governing" paths
        # that don't pin a specific element id in the result_path string).
        group_ids = DataRequest(
            element_ids=frozenset(
                eid
                for group in self.context.groups()
                for eid in group.element_ids
            ),
            node_ids=frozenset(
                nid
                for group in self.context.groups()
                for nid in group.node_ids
            ),
        )
        full_request = merged_from_modules.merge(group_ids)

        # -- 2. Cache check — skip fetching what is already available ---------
        model_hash = self._model_hash()
        cached_result_set = ResultSet()
        fetch_request = full_request

        if self.cache is not None:
            try:
                cached_sub = self.cache.available(full_request, model_hash)
                if not cached_sub.is_empty():
                    self.logger.info(
                        "[%s] Loading %d element(s) / %d node(s) from cache.",
                        self.module_name,
                        len(cached_sub.element_ids),
                        len(cached_sub.node_ids),
                    )
                    cached_result_set = self.cache.load(cached_sub, model_hash)
                    fetch_request = full_request.difference(cached_sub)
            except Exception as exc:
                self.logger.warning(
                    "[%s] Cache check failed (%s) -- falling back to full fetch.",
                    self.module_name, exc,
                )

        # -- 3. Fetch live results ---------------------------------------------
        if not fetch_request.is_empty():
            self.logger.info(
                "[%s] Fetching %d force LC(s) / %d disp LC(s) from importer.",
                self.module_name,
                len(fetch_request.force_loadcases),
                len(fetch_request.disp_loadcases),
            )
            live_result_set = self.importer.fetch(fetch_request)
        else:
            self.logger.info("[%s] All results served from cache.", self.module_name)
            live_result_set = ResultSet()

        result_set = cached_result_set.merge(live_result_set)

        # -- 4. Store fresh results in cache -----------------------------------
        if self.cache is not None and not live_result_set.force_envelopes and \
                not live_result_set.displacement_envelopes and \
                not live_result_set.stresses:
            pass  # nothing new to store
        elif self.cache is not None:
            try:
                self.cache.store(live_result_set, model_hash)
            except Exception as exc:
                self.logger.warning(
                    "[%s] Failed to store results in cache: %s", self.module_name, exc
                )

        # -- 5. Run all Excel modules for each structural group ----------------
        coordination_result = CoordinationResult(module_name=self.module_name)

        for group in self.context.groups():
            self.logger.info(
                "[%s] Processing group '%s'.", self.module_name, group.id
            )
            view = result_set.view_for_structural_group(group)

            # Pre-compute per-node governing values for column-injection modules.
            # pre_computed is also used to derive the h_max scalar for B10.
            pre_computed = self._prepare_node_data(result_set, group, _module_classes)

            # Each group gets its own subfolder to avoid file conflicts
            grp_folder = self.run_folder.sub_folder(self.module_name, group.id)

            for module_cls in _module_classes:
                module_name = module_cls.__name__
                self.logger.debug(
                    "[%s] Running %s for group '%s'.",
                    self.module_name, module_name, group.id,
                )
                try:
                    check_result = module_cls().execute(
                        view,
                        run_folder=grp_folder,
                        component_id=group.id,
                        unit_system=UnitSystemSpec.SI,
                        pre_computed=pre_computed,
                        load_cases=self._module_load_cases(module_cls),
                        # Pass pre_computed so h_max can be derived from node heights
                        scalar_inputs=self._module_scalar_inputs(
                            module_cls, pre_computed=pre_computed
                        ),
                    )
                    coordination_result.check_results.append(check_result)

                    if not check_result.passed:
                        self.logger.warning(
                            "[%s] %s / '%s': %d error(s).",
                            self.module_name, module_name, group.id,
                            len(check_result.errors),
                        )
                        for err in check_result.errors:
                            self.logger.warning("[%s]   %s", self.module_name, err)
                except Exception as exc:
                    msg = (
                        f"Exception in {module_name} for group '{group.id}': {exc}"
                    )
                    self.logger.error("[%s] %s", self.module_name, msg)
                    coordination_result.errors.append(msg)

        self.logger.info(
            "[%s] %s", self.module_name, coordination_result.summary()
        )
        self._last_result = coordination_result

    # ── Private ───────────────────────────────────────────────────────────────

    def _model_hash(self) -> str:
        """Return a simple model identity string for cache keying.

        TODO: Replace with a real model fingerprint once the AMM or importer
        exposes one (e.g. model file mtime + load case list hash).
        """
        return f"{self.module_name}:default"

    def _governing_per_node(
        self,
        result_set: ResultSet,
        group: StructuralGroup,
        component: str,
        load_case: str,
    ) -> list:
        """Return per-node governing scalar values for *component* under *load_case*.

        For each node in ``group.node_ids`` (in span order), the governing value
        is derived from the adjacent element end:

        - Node ``i`` (0-indexed, not the last): I-end of element ``i``.
        - Last node: J-end of element ``i-1``.

        "Governing" means the value with the largest absolute magnitude across
        the ``_max`` and ``_min`` envelope halves -- appropriate for design checks
        that need the worst-case demand regardless of sign.

        Supported components (case-sensitive, matching ForceVector field names):
            ``Mz``, ``Fy``, ``Fx``, ``Fz``, ``Mx``, ``My``

        Returns a ``list[float]`` in canonical units (kN*m for moments, kN for
        forces) with ``len == len(group.node_ids)``.  Missing envelope entries
        produce ``0.0`` with a debug-level warning.
        """
        ordered_nodes = group.node_ids
        ordered_elements = group.element_ids
        n = len(ordered_nodes)
        values: list = []

        for i in range(n):
            # Pick adjacent element end
            if i < len(ordered_elements):
                eid = ordered_elements[i]
                end = ElementEnd.I
            else:
                eid = ordered_elements[i - 1]
                end = ElementEnd.J

            key = (eid, end, load_case)
            env = result_set.force_envelopes.get(key)
            if env is None:
                self.logger.debug(
                    "[%s] No force envelope for key (%d, %s, %r) -- using 0.0.",
                    self.module_name, eid, end.value, load_case,
                )
                values.append(0.0)
                continue

            # Extract max and min Quantity for the requested component
            max_fv = getattr(env, f"{component}_max", None)
            min_fv = getattr(env, f"{component}_min", None)
            if max_fv is None or min_fv is None:
                self.logger.warning(
                    "[%s] Component %r not found on ElementForceEnvelope -- using 0.0.",
                    self.module_name, component,
                )
                values.append(0.0)
                continue

            val_max = float(getattr(max_fv, component).magnitude)
            val_min = float(getattr(min_fv, component).magnitude)
            governing = val_max if abs(val_max) >= abs(val_min) else val_min
            values.append(governing)

        return values

    def _prepare_node_data(
        self,
        result_set: ResultSet,
        group: StructuralGroup,
        module_classes: Optional[list] = None,
    ) -> dict:
        """Pre-compute per-node values for all column-injection inputs.

        Two categories:

        1. **FEM force/moment columns** — ``(component, load_case)`` pairs where
           ``load_case`` is non-empty.  Resolved via ``_governing_per_node()``.

        2. **Geometry / static columns** — ``(component, "")`` pairs where the
           load_case is empty.  Resolved from node coordinates and the run-spec
           ``module_07`` block (populated once per call, reused by all
           geometry-keyed mappings).

        Args:
            result_set:     Full ``ResultSet`` for the current run.
            group:          Structural group being processed.
            module_classes: Effective module class list (from ``_all_module_classes()``).
                            Defaults to ``self.EXCEL_MODULES`` if not supplied.

        Returns:
            Dict keyed by ``f"node_{component}_{load_case}"`` with ``list[float]``
            (or ``list[int]`` for NODE_ID, ``list[str]`` for SECTION_NAME) of
            length ``len(group.node_ids)``.
        """
        classes = module_classes if module_classes is not None else list(self.EXCEL_MODULES)
        required: set = set()
        for cls in classes:
            lcs = self._module_load_cases(cls)
            if lcs and hasattr(cls, "make_spec"):
                spec_si, spec_imp = cls.make_spec(lcs)
            else:
                spec_si, spec_imp = cls.SPEC_SI, cls.SPEC_IMP
            for spec in (spec_si, spec_imp):
                for file_spec in spec.files:
                    for tc_inp in file_spec.table_column_inputs:
                        required.add((tc_inp.component, tc_inp.load_case))

        # -- Pre-populate geometry columns (load_case == "") ------------------
        geo_required = {comp for comp, lc in required if not lc}
        pre_computed: dict = {}
        if geo_required:
            self._populate_geometry_columns(group, pre_computed, geo_required)

        # -- FEM force/moment columns (load_case != "") -----------------------
        for component, load_case in required:
            if not load_case:
                continue  # already handled above
            values = self._governing_per_node(result_set, group, component, load_case)
            pre_computed[f"node_{component}_{load_case}"] = values
            self.logger.debug(
                "[%s] pre_computed key='node_%s_%s' -- %d node(s).",
                self.module_name, component, load_case, len(values),
            )
        return pre_computed

    def _populate_geometry_columns(
        self,
        group: StructuralGroup,
        pre_computed: dict,
        required_components: set,
    ) -> None:
        """Fill geometry-keyed entries in *pre_computed* for *group*.

        Geometry keys use an empty load_case, so their pre_computed key is
        ``f"node_{component}_"``.

        Components handled:
            ``NODE_ID``      -- integer node ids in span order.
            ``DISTANCE``     -- cumulative chord distance from the first node [m].
            ``SECTION_NAME`` -- section name string at each node (from section_profile).
            ``h``            -- section height [m]; interpolated for tapered sections.
            ``Aps``          -- area of prestressing steel [cm2], per section.
            ``bw``           -- web width [m], per section.
            ``dp``           -- depth to tendon CG from top [m], per section.
            ``bot_As``       -- bottom flange rebar area [mm2], per section.
            ``bot_ds``       -- bottom flange rebar depth [m], per section.
            ``bot_hf``       -- bottom flange thickness [m], per section.
            ``top_As``       -- top flange rebar area [mm2], per section.
            ``top_ds``       -- top flange rebar depth [m], per section.
            ``top_hf``       -- top flange thickness [m], per section.
            ``top_b``        -- top flange effective width [m], per section.
        """
        ordered_nodes = group.node_ids
        ordered_elements = group.element_ids
        n_nodes = len(ordered_nodes)

        # All components that come from section data (including new string/h cols)
        section_geom_keys = {
            "Aps", "bw", "dp",
            "bot_As", "bot_ds", "bot_hf",
            "top_As", "top_ds", "top_hf", "top_b",
            "SECTION_NAME", "h",
        }
        needed_section_cols = required_components & section_geom_keys

        # -- Node IDs ---------------------------------------------------------
        if "NODE_ID" in required_components:
            pre_computed["node_NODE_ID_"] = list(ordered_nodes)

        # -- Fetch node coordinates (needed for DISTANCE, h-tapered, section cols) --
        node_coords: Dict[int, tuple] = {}
        if "DISTANCE" in required_components or needed_section_cols:
            try:
                node_coords = self.importer.fetch_node_geometry(list(ordered_nodes))
            except Exception as exc:
                self.logger.warning(
                    "[%s] fetch_node_geometry failed (%s) -- distances will be 0.",
                    self.module_name, exc,
                )

        # -- Cumulative distances (for DISTANCE column and tapered h) ---------
        # Compute whenever DISTANCE is required OR h is needed (for taper interp).
        distances_list: Optional[List[float]] = None
        if node_coords and (
            "DISTANCE" in required_components or "h" in needed_section_cols
        ):
            distances_list = self._cumulative_distances(ordered_nodes, node_coords)

        if "DISTANCE" in required_components:
            pre_computed["node_DISTANCE_"] = (
                distances_list if distances_list is not None
                else [0.0] * n_nodes
            )

        # -- Section geometry + SECTION_NAME + h ------------------------------
        if needed_section_cols:
            self._populate_section_columns(
                group, ordered_nodes, ordered_elements, n_nodes,
                needed_section_cols, pre_computed,
                distances=distances_list,
            )

    def _cumulative_distances(
        self,
        ordered_nodes: tuple,
        node_coords: Dict[int, tuple],
    ) -> List[float]:
        """Compute cumulative chord distances from the first node [m]."""
        distances: List[float] = [0.0]
        for i in range(1, len(ordered_nodes)):
            nid_prev = ordered_nodes[i - 1]
            nid_curr = ordered_nodes[i]
            if nid_prev in node_coords and nid_curr in node_coords:
                x0, y0, z0 = node_coords[nid_prev]
                x1, y1, z1 = node_coords[nid_curr]
                dl = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2)
            else:
                dl = 0.0
                self.logger.warning(
                    "[%s] No coordinates for node pair (%d, %d) -- distance increment = 0.",
                    self.module_name, nid_prev, nid_curr,
                )
            distances.append(distances[-1] + dl)
        return distances

    def _fetch_midas_section_geometry(self) -> Dict[str, Dict]:
        """Return model-derived geometry for all sections (Midas only).

        Calls ``importer.fetch_section_geometry()`` if available; returns
        an empty dict for importers that do not support this method (e.g.
        CSI Bridge) or if the call fails.

        Returns:
            ``{section_name: {h|h_start/h_end, top_hf, bw, bot_hf}}``
            with all values in metres.  Empty dict on failure.
        """
        if not hasattr(self.importer, "fetch_section_geometry"):
            return {}
        try:
            geom = self.importer.fetch_section_geometry()
            self.logger.info(
                "[%s] Loaded model geometry for %d section(s) from importer.",
                self.module_name, len(geom),
            )
            return geom
        except Exception as exc:
            self.logger.warning(
                "[%s] fetch_section_geometry failed (%s) -- "
                "geometric dims will fall back to run-spec values.",
                self.module_name, exc,
            )
            return {}

    def _populate_section_columns(
        self,
        group: StructuralGroup,
        ordered_nodes: tuple,
        ordered_elements: tuple,
        n_nodes: int,
        needed_cols: set,
        pre_computed: dict,
        distances: Optional[List[float]] = None,
    ) -> None:
        """Look up per-section geometry data and populate per-node column lists.

        For each node, the adjacent element (element[i] for all but the last
        node; element[i-1] for the last node) determines the section.

        Section geometry sources (merged in priority order):
        1. **Model geometry** (``importer.fetch_section_geometry``) — provides
           ``h`` / ``h_start`` / ``h_end``, ``top_hf``, ``bw``, ``bot_hf``
           directly from the Midas ``/db/sect`` raw data.  Overrides any
           matching keys present in the run-spec ``sections`` dict.
        2. **Run-spec ``module_07.sections`` dict** — supplies design inputs
           (``Aps``, ``dp``, ``top_b``, ``bot_As``, ``bot_ds``, ``top_As``,
           ``top_ds``) and the ``materials`` reference block.  Also acts as
           the sole source when model geometry is unavailable (e.g. CSI Bridge).

        Element-to-section assignment priority:
        1. ``module_07.section_profile`` in run-spec (explicit element ranges).
        2. FEM importer ``fetch_element_section_names`` (model-derived).
        3. Fallback: first section in ``sections`` dict for all elements.

        Special columns:
        - ``SECTION_NAME``: the section name string (not a numeric property).
        - ``h``: section height [m]; linearly interpolated between ``h_start``
          and ``h_end`` for tapered sections when ``distances`` is provided.

        Args:
            distances: Cumulative node distances [m] from ``_cumulative_distances``.
                       Required for tapered section height interpolation.

        TODO: generalise the ``"module_07"`` hard-code once multiple modules
        with different section data are in play.
        """
        n_elements = len(ordered_elements)

        # ── 1. Load sections data and section_profile from run-spec ──────────
        runspec_sections: Dict[str, Dict] = {}
        section_profile: list = []
        if hasattr(self.context, "module_inputs_for"):
            m07 = self.context.module_inputs_for("module_07")
            runspec_sections = {
                k: v for k, v in m07.get("sections", {}).items()
                if not k.startswith("_")
            }
            # Only keep entries that have an explicit "section" key
            section_profile = [
                e for e in m07.get("section_profile", [])
                if isinstance(e, dict) and "section" in e
            ]

        # ── 2. Fetch model geometry and merge with run-spec ───────────────────
        # Model geometry (h, top_hf, bw, bot_hf) takes priority over any
        # matching values in the run-spec sections dict.
        # Design inputs (Aps, dp, top_b, rebar) are always from the run-spec.
        midas_geom = self._fetch_midas_section_geometry()

        all_section_names = set(runspec_sections.keys()) | set(midas_geom.keys())
        sections_data: Dict[str, Dict] = {}
        for sec_name in all_section_names:
            merged: Dict = dict(runspec_sections.get(sec_name, {}))
            if sec_name in midas_geom:
                # Midas geometric dims always override run-spec dims
                merged.update(midas_geom[sec_name])
            sections_data[sec_name] = merged

        if not sections_data:
            self.logger.warning(
                "[%s] No section geometry available (run-spec nor model) -- "
                "section columns will be 0 / empty.",
                self.module_name,
            )

        # ── 3. Build element → section name map ───────────────────────────────
        if section_profile:
            # Use explicit mapping from run-spec (overrides FEM-derived names)
            elem_sec_map: Dict[int, str] = {}
            for entry in section_profile:
                sec_name = entry.get("section", "")
                if "element_range" in entry:
                    try:
                        e_start = int(entry["element_range"][0])
                        e_end   = int(entry["element_range"][1])
                        for eid in range(e_start, e_end + 1):
                            elem_sec_map[eid] = sec_name
                    except (TypeError, IndexError, ValueError) as exc:
                        self.logger.warning(
                            "[%s] section_profile entry has invalid element_range: %r (%s).",
                            self.module_name, entry, exc,
                        )
                elif "elements" in entry:
                    for eid in entry["elements"]:
                        elem_sec_map[int(eid)] = sec_name
            self.logger.debug(
                "[%s] section_profile mapped %d element(s) to sections.",
                self.module_name, len(elem_sec_map),
            )
        else:
            # Fall back to FEM importer
            try:
                elem_sec_map = self.importer.fetch_element_section_names(
                    list(ordered_elements)
                )
            except Exception as exc:
                self.logger.warning(
                    "[%s] fetch_element_section_names failed (%s) -- "
                    "section columns will use first section as fallback.",
                    self.module_name, exc,
                )
                elem_sec_map = {}

        # ── 4. Build section groups for tapered height interpolation ──────────
        # A section group = maximal run of consecutive elements with the same section.
        # Each group spans node indices [grp_node_start .. grp_node_end] inclusive,
        # where grp_node_end = (last element index in group) + 1.
        #
        # Node index i maps to element ordered_elements[min(i, n_elements-1)].
        # So element group [e_start..e_end] (0-based) covers nodes [e_start..e_end+1].
        section_groups: List[Tuple[str, int, int]] = []
        if "h" in needed_cols and distances is not None:
            prev_sec: Optional[str] = None
            grp_start = 0
            for idx, eid in enumerate(ordered_elements):
                sec_name = elem_sec_map.get(eid, "")
                if sec_name != prev_sec:
                    if prev_sec is not None:
                        section_groups.append((prev_sec, grp_start, idx))
                    prev_sec = sec_name
                    grp_start = idx
            if prev_sec is not None:
                # Last group ends at the last node (node index = n_elements)
                section_groups.append((prev_sec, grp_start, n_elements))

        # ── 5. Build per-node column lists ────────────────────────────────────
        col_lists: Dict[str, list] = {col: [] for col in needed_cols}
        first_sec_name = next(iter(sections_data), "") if sections_data else ""
        first_sec_data = sections_data.get(first_sec_name, {})

        for i in range(n_nodes):
            # Element that determines the section for this node
            elem_idx = i if i < n_elements else n_elements - 1
            eid = ordered_elements[elem_idx]
            # display_sec_name: always the name from elem_sec_map; shown in SECTION_NAME
            # column and used for tapered interpolation group matching.
            display_sec_name = elem_sec_map.get(eid, "")
            sec_data = sections_data.get(display_sec_name)

            # Fallback to first section's DATA only when geometry is not available.
            # IMPORTANT: display_sec_name is preserved so SECTION_NAME still shows
            # the correct section name (TAP-PSC:1 etc.) even when data is missing.
            if not sec_data:
                if display_sec_name and sections_data:
                    self.logger.warning(
                        "[%s] Section %r not in merged sections -- "
                        "using %r data as numeric fallback (node idx %d). "
                        "Add Aps/dp/top_b for this section to run_spec.json.",
                        self.module_name, display_sec_name, first_sec_name, i,
                    )
                sec_data = first_sec_data

            for col in needed_cols:
                if col == "SECTION_NAME":
                    # Always use the actual section name, not the fallback name
                    col_lists[col].append(display_sec_name)

                elif col == "h":
                    col_lists[col].append(
                        self._height_at_node(
                            i, display_sec_name, sec_data,
                            section_groups, distances,
                        )
                    )

                else:
                    # Numeric section property (design input or geometric scalar)
                    val = sec_data.get(col, 0.0)
                    col_lists[col].append(
                        float(val) if not isinstance(val, dict) else 0.0
                    )

        # ── 6. Write to pre_computed ──────────────────────────────────────────
        for col, values in col_lists.items():
            pre_computed[f"node_{col}_"] = values
            self.logger.debug(
                "[%s] pre_computed key='node_%s_' -- %d node(s), "
                "sample: %r",
                self.module_name, col, len(values),
                values[:3] if values else [],
            )

    def _height_at_node(
        self,
        node_idx: int,
        sec_name: str,
        sec_data: dict,
        section_groups: List[Tuple[str, int, int]],
        distances: Optional[List[float]],
    ) -> float:
        """Return the section height at *node_idx*.

        For **constant** sections (``sec_data["h"]`` only): returns that value.

        For **tapered** sections (``sec_data["h_start"]`` / ``sec_data["h_end"]``):
        interpolates between h_start and h_end using the variation law stored
        in ``sec_data["z_var"]`` (sourced from the Midas ``Z_VAR`` field):

            z_var == 1  (linear):     h(t) = h_start + (h_end - h_start) * t
            z_var == 2  (parabolic):  h(t) = h_start + (h_end - h_start) * t**2

        where ``t`` is the normalised position within the section group
        (0 at the I-end / first node of the group, 1 at the J-end / last node),
        derived from cumulative chord distances.

        The parabolic formula produces a haunch that deepens slowly near the
        midspan end and rapidly near the pier — consistent with Midas Z_VAR=2.

        Args:
            node_idx:       0-based index into the ordered_nodes tuple.
            sec_name:       Name of the section at this node.
            sec_data:       Section property dict (merged Midas + run-spec).
                            Expected for tapered: ``h_start``, ``h_end``,
                            ``z_var`` (default 1 if absent).
            section_groups: List of ``(sec_name, node_start_idx, node_end_idx)``
                            built by ``_populate_section_columns``.
            distances:      Cumulative node distances [m]; ``None`` disables
                            tapered interpolation (returns h_start).

        Returns:
            Height in metres.
        """
        h_start = float(sec_data.get("h_start", sec_data.get("h", 0.0)))
        h_end   = float(sec_data.get("h_end",   sec_data.get("h", h_start)))
        z_var   = int(sec_data.get("z_var", 1))   # 1=linear, 2=parabolic

        # Constant section or no distance data: no interpolation needed
        if h_start == h_end or not section_groups or distances is None:
            return h_start

        # Find the section group that contains this node
        for grp_sec, grp_start, grp_end in section_groups:
            if grp_sec == sec_name and grp_start <= node_idx <= grp_end:
                d_start = distances[grp_start]
                d_end   = distances[grp_end] if grp_end < len(distances) else distances[-1]
                if d_end <= d_start:
                    return h_start
                t = (distances[node_idx] - d_start) / (d_end - d_start)
                t = max(0.0, min(1.0, t))   # clamp to [0, 1]
                if z_var == 2:
                    # Parabolic: Midas Z_VAR=2 — deepens slowly then rapidly
                    return h_start + (h_end - h_start) * (t ** 2)
                else:
                    # Linear: Midas Z_VAR=1 (default)
                    return h_start + (h_end - h_start) * t

        return h_start
