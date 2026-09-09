import re
import unittest
from pathlib import Path

from local_beta.constants import TOOL_VERSION


ROOT = Path(__file__).resolve().parents[1]


class ReleaseContractTests(unittest.TestCase):
    def test_changelog_top_version_matches_tool_version(self):
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.search(r"^## ([0-9.]+)\b", changelog, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), TOOL_VERSION)

    def test_readme_current_version_matches_tool_version(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        versions = re.findall(r"(?:当前版本|Current version) \*\*([0-9.]+)", readme)
        self.assertEqual(versions, [TOOL_VERSION, TOOL_VERSION])
        self.assertIn(f"当前 **{TOOL_VERSION} 公开测试版", readme)
        self.assertIn(f"Current **{TOOL_VERSION} Public Beta", readme)

    def test_release_workflow_publishes_mac_package(self):
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("runs-on: macos-15", workflow)
        self.assertIn("./script/build_and_run.sh --build-only", workflow)
        self.assertIn("EUDAMED_Local_Beta_Mac_arm64.zip", workflow)
        self.assertIn("EUDAMED_Local_Beta_Windows.zip", workflow)
        self.assertIn("Create final SHA-256 manifest", workflow)
        self.assertIn("needs: build-macos", workflow)
        self.assertIn("actions/download-artifact@v8", workflow)


if __name__ == "__main__":
    unittest.main()
