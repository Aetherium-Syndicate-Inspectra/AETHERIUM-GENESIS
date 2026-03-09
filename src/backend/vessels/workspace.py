import os
from typing import Any, Dict

from src.backend.vessels.base import ActionPreview, ExecutionVessel


class WorkspaceVessel(ExecutionVessel):
    def __init__(self, workspace_root: str = "workspace_runtime"):
        super().__init__(name="workspace")
        self.root = os.path.abspath(workspace_root)
        os.makedirs(self.root, exist_ok=True)

    def _safe_path(self, path: str) -> str:
        resolved = os.path.abspath(os.path.join(self.root, path))
        if not resolved.startswith(self.root):
            raise PermissionError("Path escapes workspace sandbox")
        return resolved

    def preview(self, action: str, params: Dict[str, Any]) -> ActionPreview:
        path = params.get("path", "")
        if action == "write_file":
            return ActionPreview(
                plan=f"Write file at {path}",
                diff=f"+ {params.get('content', '')[:80]}",
                tools=["workspace.fs"],
                evidence={"path": path},
            )
        return ActionPreview(plan=f"Run {action}", diff="", tools=["workspace.fs"], evidence={})

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        target = self._safe_path(params.get("path", ""))
        if action == "write_file":
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(params.get("content", ""))
            return {"status": "ok", "path": target}
        if action == "read_file":
            with open(target, "r", encoding="utf-8") as handle:
                return {"status": "ok", "content": handle.read()}
        raise ValueError(f"Unsupported workspace action: {action}")
