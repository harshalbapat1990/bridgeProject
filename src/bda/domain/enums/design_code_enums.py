from enum import Enum

__all__ = ["DesignCode"]

class DesignCode(str, Enum):
    AASHTO = "AASHTO"
    EUROCODE = "EUROCODE"