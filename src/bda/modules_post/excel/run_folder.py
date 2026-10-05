"""RunFolder — per-run working directory manager for Excel check execution.

The entry point (UI layer) constructs a ``RunFolder`` with a base directory
chosen by the user and passes it to every ``IModulePost`` invocation.
CoordinationModules call ``run_folder.sub_folder(module_name)`` to get an
isolated working directory for their check domain, preventing file conflicts
when multiple section types run in the same pipeline execution.

Directory structure
-------------------
::

    <base_dir>/
    └── <project>_<YYYYMMDD>_<NNN>/     ← RunFolder root (one per run)
        ├── inputs/                       ← run_spec.json, logs
        ├── calcs/
        │   ├── PTBox_GirderCoordination/ ← sub_folder per CoordinationModule
        │   │   ├── Girder_1/             ← sub_folder per structural group
        │   │   │   ├── Module_GirderFlexure.xlsx
        │   │   │   └── Module_GirderShear.xlsx
        │   │   └── Girder_2/
        │   └── ...
        └── run_log.json
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path


class RunFolder:
    """Manage the file structure for one pipeline run.

    Args:
        base_dir:     Root directory supplied by the UI. A new timestamped
                      subdirectory is created here for each run.
        project_name: Short label included in the folder name, e.g. the
                      model file stem. Must be safe for filesystem use.
    """

    def __init__(self, base_dir: Path, project_name: str) -> None:
        self._base = Path(base_dir)
        self._project = project_name
        self._created = datetime.now()
        self._run_id = self._next_run_id()
        self._run_dir = self._base / self._folder_name()
        self._run_dir.mkdir(parents=True, exist_ok=True)
        self._inputs_dir = self._run_dir / "inputs"
        self._inputs_dir.mkdir(exist_ok=True)
        self._calcs_dir = self._run_dir / "calcs"
        self._calcs_dir.mkdir(exist_ok=True)

    # ── Public interface ──────────────────────────────────────────────────────

    @property
    def run_id(self) -> int:
        """Sequential run identifier for today (1, 2, 3, …)."""
        return self._run_id

    @property
    def run_dir(self) -> Path:
        """Root directory of this run."""
        return self._run_dir

    @property
    def inputs_dir(self) -> Path:
        """``<run>/inputs/`` — for run-spec JSON and run logs."""
        return self._inputs_dir

    @property
    def calcs_dir(self) -> Path:
        """``<run>/calcs/`` — root for all Excel working copies."""
        return self._calcs_dir

    def sub_folder(self, *parts: str) -> "RunFolder":
        """Return an isolated working directory for one check domain.

        Typical call sites::

            mod_folder = run_folder.sub_folder(self.module_name)
            # → <run>/calcs/PTBox_GirderCoordination/

            grp_folder = mod_folder.sub_folder(group.id)
            # → <run>/calcs/PTBox_GirderCoordination/Girder_1/

        The returned ``RunFolder`` shares the same ``run_id`` but uses the
        new subdirectory as its ``calcs_dir``. Templates copied into it will
        not conflict with copies in sibling directories.

        Args:
            *parts: Path components appended under ``calcs_dir``.
        """
        sub_dir = self._calcs_dir
        for part in parts:
            sub_dir = sub_dir / part
        sub_dir.mkdir(parents=True, exist_ok=True)
        return _SubRunFolder(root=self, calcs_dir=sub_dir)

    def copy_template(self, template_path: Path, dest_name: str | None = None) -> Path:
        """Copy *template_path* into ``calcs_dir`` and return the destination path.

        Args:
            template_path: Absolute path to the source Excel template.
            dest_name:     Filename for the copy. Defaults to the template's
                           own filename.

        Returns:
            Absolute path to the copied file in ``calcs_dir``.
        """
        dest_name = dest_name or template_path.name
        dest = self._calcs_dir / dest_name
        shutil.copy2(template_path, dest)
        return dest

    def save_spec(self, spec_dict: dict) -> None:
        """Write *spec_dict* to ``inputs/run_spec.json``."""
        with (self._inputs_dir / "run_spec.json").open("w", encoding="utf-8") as fh:
            json.dump(spec_dict, fh, indent=2)

    def save_log(self, log_dict: dict) -> None:
        """Write *log_dict* to ``run_log.json`` at the run root."""
        with (self._run_dir / "run_log.json").open("w", encoding="utf-8") as fh:
            json.dump(log_dict, fh, indent=2)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _folder_name(self) -> str:
        date_str = self._created.strftime("%Y%m%d")
        return f"{self._project}_{date_str}_{self._run_id:03d}"

    def _next_run_id(self) -> int:
        """Scan ``base_dir`` for existing today-folders and return the next id."""
        today_str = datetime.now().strftime("%Y%m%d")
        pattern = f"{self._project}_{today_str}_*"
        existing = list(self._base.glob(pattern))
        ids = []
        for d in existing:
            if d.is_dir():
                try:
                    ids.append(int(d.name.split("_")[-1]))
                except (ValueError, IndexError):
                    pass
        return max(ids, default=0) + 1


class _SubRunFolder(RunFolder):
    """Internal: a RunFolder view scoped to a subdirectory.

    Created by ``RunFolder.sub_folder()`` — never construct directly.
    """

    def __init__(self, root: RunFolder, calcs_dir: Path) -> None:
        # Bypass __init__: we share the root's state but override calcs_dir.
        self._base = root._base
        self._project = root._project
        self._created = root._created
        self._run_id = root._run_id
        self._run_dir = root._run_dir
        self._inputs_dir = root._inputs_dir
        self._calcs_dir = calcs_dir
