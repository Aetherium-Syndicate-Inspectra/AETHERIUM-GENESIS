import unittest
import os
import shutil
import asyncio
from src.backend.genesis_core.vessels.workspace import WorkspaceVessel
from src.backend.genesis_core.governance.core import ActionTier

class TestWorkspaceVessel(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_root = "test_workspace"
        self.vessel = WorkspaceVessel(workspace_root=self.test_root)

    async def asyncTearDown(self):
        if os.path.exists(self.test_root):
            shutil.rmtree(self.test_root)

    def test_safe_path(self):
        self.vessel._safe_path("docs/plan.md")
        with self.assertRaises(PermissionError):
            self.vessel._safe_path("../secret.txt")

    async def test_simulate(self):
        preview = await self.vessel.simulate("write_file", {"path": "test.txt", "content": "Hello"})
        self.assertEqual(preview.risk_tier, ActionTier.TIER_1_REVERSIBLE_LOW_RISK)
        self.assertIn("Create file", preview.summary)

    async def test_execute_write_read(self):
        await self.vessel.execute("write_file", {"path": "hi.txt", "content": "Aether"})
        result = await self.vessel.execute("read_file", {"path": "hi.txt"})
        self.assertEqual(result["content"], "Aether")

if __name__ == '__main__':
    unittest.main()
