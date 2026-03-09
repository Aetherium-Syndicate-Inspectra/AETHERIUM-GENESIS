from typing import Any, Dict

from src.backend.vessels.base import ActionPreview, ExecutionVessel


class DatabaseVessel(ExecutionVessel):
    def __init__(self):
        super().__init__(name="database")

    def preview(self, action: str, params: Dict[str, Any]) -> ActionPreview:
        table = params.get("table", "unknown")
        return ActionPreview(
            plan=f"Database action {action} on table {table}",
            diff=str(params.get("patch", {}))[:120],
            tools=["database.client"],
            evidence={"transactional": True},
        )

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "dry_run", "action": action, "table": params.get("table")}
