from abc import ABC, abstractmethod


class OpsExecutionError(Exception):
    pass


class OpsProvider(ABC):
    @abstractmethod
    def run(self, request_type: str, title: str, objective: str, context: dict) -> dict:
        pass
