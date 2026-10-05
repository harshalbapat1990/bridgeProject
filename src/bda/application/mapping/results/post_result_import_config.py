"""Configuration for the POST-pipeline result import stage.

Holds settings that are needed to locate and read FEM result data but are
not specific to a particular analytical software package.  Keeping this
here separates run-environment paths from software connection details
(API keys, base URLs) which live in the software-specific config providers.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PostResultImportConfig:
    """Settings required by the POST result import stage.

    Attributes
    ----------
    results_dir:
        Directory on the FEM host where file-based result exports are
        written (e.g. the Midas ``EXPORT_PATH`` used by ``/post/TABLE``
        for ``SECTIONALL``).  Must be accessible from the machine running
        BDA.  Empty string disables file-based import paths.
    """

    results_dir: str = field(default="")
