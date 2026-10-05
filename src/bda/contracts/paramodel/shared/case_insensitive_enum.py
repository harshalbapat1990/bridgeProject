from enum import Enum


class CaseInsensitiveEnum(str, Enum):
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.lower()
            for member in cls:
                if member.value.lower() == value:
                    return member
        return None
