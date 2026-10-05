"""Abstract base class for POST-processing CoordinationModules.

A CoordinationModule orchestrates one check domain (e.g. all girder checks
for a PT Box bridge). It is the direct child of a Profile and the direct
parent of a set of ``IExcelCheckModule`` implementations.

Design notes
------------
- ``IModulePost`` does NOT inherit ``IModule``. PRE modules mutate an AMM;
  POST CoordinationModules read a context and produce check results. The
  contracts are different enough that inheritance would be misleading.
- The ``context`` parameter replaces the old ``AnalyticalMultiModel`` arg.
  Both Route A (AMM) and Route B (JSON) satisfy ``IStructuralContext``, so
  ``_run()`` is identical regardless of which route was used.
- ``run_folder`` is supplied by the entry point (UI layer), not created here.
  CoordinationModules must call ``run_folder.sub_folder(self.module_name)``
  to get an isolated working directory for this check domain.
- ``cache`` is optional. When provided, the orchestrator checks it before
  calling the importer and stores new results in it after fetching.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from bda.application.interfaces.logging import IAppLogger, NullLogger
from bda.application.interfaces.structural_context.i_structural_context import IStructuralContext
from bda.application.interfaces.analytical_software.importer import IResultImporter
from bda.modules_post.interfaces.i_result_cache import IResultCache


class IModulePost(ABC):
    """Contract for a top-level POST-processing CoordinationModule.

    Args:
        context:    Structural metadata (bridge type + groups).
                    Either ``AMMContext`` or ``JSONContext``.
        importer:   FEM result importer (CSI Bridge or Midas Civil NX).
        run_folder: Per-run working directory manager supplied by the UI.
                    CoordinationModules call ``run_folder.sub_folder(name)``
                    to avoid file conflicts between concurrent section types.
        logger:     Optional application logger; defaults to NullLogger.
        cache:      Optional result cache. When provided, the coordinator
                    checks it before importing and stores results after.
    """

    def __init__(
        self,
        context: IStructuralContext,
        importer: IResultImporter,
        run_folder: "RunFolder",  # noqa: F821 — forward ref, avoid circular import
        logger: Optional[IAppLogger] = None,
        cache: Optional[IResultCache] = None,
    ) -> None:
        self.context = context
        self.importer = importer
        self.run_folder = run_folder
        self.logger = logger or NullLogger()
        self.cache = cache

    @property
    @abstractmethod
    def module_name(self) -> str:
        """Short human-readable name, e.g. ``"PTBox_GirderCoordination"``."""
        ...

    @abstractmethod
    def _run(self) -> None:
        """Execute the full check pipeline for this CoordinationModule.

        Implementation pattern::

            def _run(self) -> None:
                # 1. Aggregate DataRequest from all Excel module classes
                merged = DataRequest.merge_all(
                    cls.data_requirements() for cls in self.EXCEL_MODULES
                )

                # 2. Check cache; only fetch what is missing
                if self.cache:
                    cached_req = self.cache.available(merged, model_hash)
                    cached_rs  = self.cache.load(cached_req, model_hash)
                    fetch_req  = merged.difference(cached_req)
                else:
                    cached_rs = ResultSet()
                    fetch_req = merged

                # 3. Fetch from FEM importer (may be empty if fully cached)
                live_rs = self.importer.fetch(fetch_req) if not fetch_req.is_empty() else ResultSet()
                result_set = cached_rs.merge(live_rs)

                # 4. Store new results in cache
                if self.cache and not live_rs.is_empty():
                    self.cache.store(live_rs, model_hash)

                # 5. Create per-module subfolder to avoid file conflicts
                mod_folder = self.run_folder.sub_folder(self.module_name)

                # 6. Run all Excel modules for each structural group
                for group in self.context.groups():
                    view = result_set.view_for_structural_group(group)
                    for module_cls in self.EXCEL_MODULES:
                        module_cls().execute(
                            view,
                            run_folder=mod_folder,
                            component_id=group.id,
                        )
        """
        ...

    def run(self) -> bool:
        """Public entry point. Wraps ``_run()`` with logging and error handling.

        Returns:
            ``True`` only if ``_run()`` completed without exception AND the
            stored ``CoordinationResult`` (if any) reports ``passed=True``.
            ``False`` if ``_run()`` raised, or if any check result failed.
        """
        self.logger.info("Starting CoordinationModule: '%s'", self.module_name)
        try:
            self._run()
        except Exception as exc:
            self.logger.error(
                "Exception in CoordinationModule '%s': %s", self.module_name, exc
            )
            return False
        self.logger.info("Finished CoordinationModule: '%s'", self.module_name)
        # If _run() stored a CoordinationResult, honour its pass/fail verdict.
        last = getattr(self, "_last_result", None)
        if last is not None:
            return last.passed
        return True
