"""Post-processing interface contracts."""

from bda.modules_post.interfaces.i_calculator import ICalculator
from bda.modules_post.interfaces.i_check import ICheck
from bda.modules_post.interfaces.i_result_cache import IResultCache

__all__ = [
	"ICalculator",
	"ICheck",
	"IResultCache",
	"IResultImporter",
]

