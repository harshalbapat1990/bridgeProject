"""CoordinationResult — the aggregate result of one CoordinationModule run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from bda.modules_post.excel.models import CheckResult


@dataclass
class CoordinationResult:
    """Aggregate result of running all Excel modules for all structural groups.

    One ``CoordinationResult`` is produced per ``IModulePost._run()``
    invocation. It collects the ``CheckResult`` from every (module, group)
    pair plus any errors that occurred at the coordination level.

    Attributes:
        module_name:   Name of the CoordinationModule that produced this result.
        check_results: All ``CheckResult`` objects in run order.
        errors:        Coordination-level errors (not Excel-level errors, which
                       are stored inside each ``CheckResult.errors``).
    """

    module_name: str
    check_results: List[CheckResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """``True`` if no coordination errors and all check results passed."""
        return not self.errors and all(r.passed for r in self.check_results)

    def summary(self) -> str:
        """One-line human-readable summary."""
        n_pass = sum(1 for r in self.check_results if r.passed)
        n_fail = len(self.check_results) - n_pass
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] {self.module_name}: "
            f"{n_pass} passed, {n_fail} failed"
            + (f", {len(self.errors)} coordination error(s)" if self.errors else "")
        )
