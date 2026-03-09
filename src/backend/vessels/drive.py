from typing import Any, Dict

from src.backend.vessels.base import ActionPreview, ExecutionVessel


class DriveVessel(ExecutionVessel):
    """Draft/update abstraction for remote drive providers."""

    def __init__(self):
        super().__init__(name="drive")

    def preview(self, action: str, params: Dict[str, Any]) -> ActionPreview:
        return ActionPreview(
            plan=f"Drive action {action} on {params.get('doc_id', 'new_doc')}",
            diff=params.get("content", "")[:120],
            tools=["drive.api"],
            evidence={"provider": params.get("provider", "generic")},
        )

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "draft_only", "action": action, "message": "Drive execution adapter pending provider binding"}
