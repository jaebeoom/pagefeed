from __future__ import annotations

import unittest
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "update-feed.yml"


class WorkflowTest(unittest.TestCase):
    def test_configure_pages_can_enable_pages_site(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("uses: actions/configure-pages@v5", workflow)
        self.assertIn("enablement: true", workflow)

    def test_notify_runs_for_any_incomplete_update(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "if: ${{ always() && (needs.build.result != 'success' || needs.deploy.result != 'success' || inputs.send_test_alert) }}",
            workflow,
        )
        self.assertIn("BUILD_RESULT: ${{ needs.build.result }}", workflow)
        self.assertIn("DEPLOY_RESULT: ${{ needs.deploy.result }}", workflow)
        self.assertIn("SEND_TEST_ALERT: ${{ inputs.send_test_alert }}", workflow)
        self.assertIn(
            "pagefeed update did not complete. build=${BUILD_RESULT}, deploy=${DEPLOY_RESULT}. Check: ${RUN_URL}",
            workflow,
        )
        self.assertIn(
            "pagefeed alert test succeeded. build=${BUILD_RESULT}, deploy=${DEPLOY_RESULT}. Check: ${RUN_URL}",
            workflow,
        )
        self.assertIn("Telegram alert failed with HTTP ${http_status}:", workflow)


if __name__ == "__main__":
    unittest.main()
