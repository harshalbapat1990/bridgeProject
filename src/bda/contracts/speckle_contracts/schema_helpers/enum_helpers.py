from enum import Enum
from typing import Type, cast


def combine_enums(name: str, *enums: Type[Enum]) -> Type[Enum]:
    members = {}
    for enum in enums:
        members.update({member.name: member.value for member in enum})
    return cast(Type[Enum], Enum(name, members))