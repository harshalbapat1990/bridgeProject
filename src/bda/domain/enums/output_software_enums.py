from enum import Enum

__all__ = ["OutputSoftware"]

class OutputSoftware(str, Enum):
    MIDAS = "MIDAS Civil"
    CSIBRIDGE = "CSI Bridge"