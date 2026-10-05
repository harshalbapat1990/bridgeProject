from enum import Enum

__all__ = ["ProcessingStage"]


class ProcessingStage(str, Enum):
    PRE = "pre"
    POST = "post"
