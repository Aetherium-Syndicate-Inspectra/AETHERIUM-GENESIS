from typing import Any, Dict

from src.backend.vessels.base import ActionPreview, ExecutionVessel


class SlackVessel(ExecutionVessel):
    def __init__(self):
        super().__init__(name="slack")

    def preview(self, action: str, params: Dict[str, Any]) -> ActionPreview:
        return ActionPreview(
            plan=f"{action} message to {params.get('channel', '#general')}",
            diff=params.get("text", "")[:200],
            tools=["slack.api"],
            evidence={"mode": "draft"},
        )

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "draft_only", "channel": params.get("channel"), "action": action}
