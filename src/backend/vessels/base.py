from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ActionPreview:
    plan: str
    diff: str
    tools: list[str]
    evidence: Dict[str, Any]


class ExecutionVessel(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def preview(self, action: str, params: Dict[str, Any]) -> ActionPreview:
        raise NotImplementedError

    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
