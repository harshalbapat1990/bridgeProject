from abc import ABC, abstractmethod


class ICheck(ABC):
   
    @abstractmethod
    def check(self, *args, **kwargs) -> bool:
        pass