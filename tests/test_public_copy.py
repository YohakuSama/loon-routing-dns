"""Guard public-facing copy against internal maintenance narration."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = (
    "README.md",
    "docs/RELEASE_NOTES_v6.0.0.md",
    "docs/RELEASE_NOTES_v6.1.0.md",
    "docs/RELEASE_NOTES_v6.2.0.md",
    "docs/RELEASE_NOTES_v6.3.0.md",
    "docs/CHANGELOG.md",
    "docs/REPOSITORY_ABOUT.md",
    "docs/NETWORK_DIAGNOSTICS.md",
    "docs/DNS_PRIVACY.md",
    "icons/README.md",
    "rules/README.md",
)
# These patterns describe distracting promises or audit data that belong in
# technical maintenance records, not the user-facing landing/release copy.
DISALLOWED = (
    r"(?:完全|全部)?保留.{0,12}(?:原有|既有).{0,12}(?:图标|图片|PNG|SVG)",
    r"(?:原有|既有).{0,12}(?:图标|图片|PNG|SVG).{0,12}(?:保留|不替换|未更换)",
    r"(?:未转换|隔离).{0,8}\d+\s*条?(?:特殊)?正则",
    r"\d+\s*条?(?:特殊)?正则.{0,18}(?:未转换|隔离)",
    r"(?:用户|维护者).{0,8}(?:已报告|反馈).{0,8}真机",
    r"\bUSER_REPORTED_PASS\b",
    r"\bNOT_INDEPENDENTLY_REVIEWED\b",
    r"\bBLOCKED_UNTIL_EXPLICIT_APPROVAL\b",
)


class PublicCopyChecks(unittest.TestCase):
    def test_public_docs_lead_with_capabilities_not_internal_exception_logs(self):
        for name in PUBLIC:
            with self.subTest(document=name):
                text=(ROOT/name).read_text(encoding="utf-8")
                self.assertTrue(text.strip())
                for expression in DISALLOWED:
                    self.assertIsNone(re.search(expression,text,flags=re.I),
                                      f"{name}: misleading internal status in public copy: {expression}")

    def test_v6_release_is_one_reviewable_source(self):
        workflow=(ROOT/".github/workflows/publish-v6.yml").read_text(encoding="utf-8")
        notes=(ROOT/"docs/RELEASE_NOTES_v6.0.0.md").read_text(encoding="utf-8")
        self.assertIn("--notes-file docs/RELEASE_NOTES_v6.0.0.md",workflow)
        self.assertIn("gh release edit v6.0.0",workflow)
        self.assertIn('published_tag',workflow)
        self.assertIn('cmp -s LoonKit.lcf existing-release/LoonKit.lcf',workflow)
        self.assertNotIn("cat >release-output/RELEASE_NOTES.md",workflow)
        self.assertNotIn("完全保留原有",workflow)
        for heading in ("主要功能", "安装"):
            self.assertIn(heading, notes)
        self.assertIn("LoonKit.lcf",notes)

    def test_v61_release_is_reviewed_and_immutable(self):
        workflow=(ROOT/".github/workflows/publish-v61.yml").read_text(encoding="utf-8")
        notes=(ROOT/"docs/RELEASE_NOTES_v6.1.0.md").read_text(encoding="utf-8")
        for guard in ("workflow_run:", "conclusion == 'success'", "head_branch == 'main'",
                      'git rev-parse HEAD', '"$CHECKED_SHA"', 'gh release create v6.1.0',
                      'gh release view v6.1.0', 'scripts/verify_release.py --check',
                      'cmp -s LoonKit.lcf existing-release/LoonKit.lcf'):
            self.assertIn(guard, workflow)
        self.assertIn("b82fb2b61a6fc95f29dfb2b48dbf36885545c219", workflow)
        self.assertIn("19de1c36ee747ea76512af3bf5b2d62475e77175db09a2568ce8de43a82e480b", workflow)
        self.assertNotIn('test "$published_tag" = "$CHECKED_SHA"', workflow)
        self.assertIn("--notes-file docs/RELEASE_NOTES_v6.1.0.md", workflow)
        self.assertIn("## 主要功能", notes)
        self.assertIn("## 安装与升级", notes)
        self.assertIn("LoonKit.lcf", notes)
        old=(ROOT/".github/workflows/publish-v6.yml").read_text(encoding="utf-8")
        self.assertIn('if ! grep -qx "# LoonKit v6.0.0"', old)

    def test_v62_historical_release_contract(self):
        workflow=(ROOT/".github/workflows/publish-v62.yml").read_text(encoding="utf-8")
        notes=(ROOT/"docs/RELEASE_NOTES_v6.2.0.md").read_text(encoding="utf-8")
        for required in ("workflow_run:", "conclusion == 'success'", "head_branch == 'main'",
                         "head_repository.full_name == github.repository", "fetch-depth: 0",
                         "git merge-base --is-ancestor", "scripts/verify_release.py --check",
                         "gh release create v6.2.0", "gh release download v6.2.0",
                         "cmp -s LoonKit.lcf existing-release/LoonKit.lcf",
                         'sha256sum LoonKit.lcf'):
            self.assertIn(required, workflow)
        self.assertIn("## 主要更新",notes)
        self.assertIn("## 安装",notes)
        self.assertIn("一个插件",notes)
        self.assertIn("解锁检测", (ROOT/"README.md").read_text(encoding="utf-8"))

    def test_v63_official_version_and_human_readable_plugin(self):
        profile=(ROOT/"LoonKit.lcf").read_text(encoding="utf-8")
        plugin=(ROOT/"release/Network_Diagnostics.plugin").read_text(encoding="utf-8")
        workflow=(ROOT/".github/workflows/publish-v63.yml").read_text(encoding="utf-8")
        notes=(ROOT/"docs/RELEASE_NOTES_v6.3.0.md").read_text(encoding="utf-8")
        self.assertIn("# LoonKit v6.3.3",profile)
        self.assertEqual(profile.count(".plugin, enabled=true"),1)
        self.assertFalse((ROOT/"release/Service_Diagnostics.plugin").exists())
        self.assertNotIn("service = select,",plugin)
        self.assertIn('tag="节点信息"',plugin)
        self.assertIn('tag="网络检测"',plugin)
        self.assertIn('tag="解锁检测"',plugin)
        self.assertIn("scripts/v20261021r10/media-unlock.js",plugin)
        for guard in ("workflow_run:", "conclusion == 'success'", "head_branch == 'main'",
                      "head_repository.full_name == github.repository", "fetch-depth: 0",
                      "git merge-base --is-ancestor", "scripts/verify_release.py --check",
                      "gh release create v6.3.0", "gh release download v6.3.0",
                      "cmp -s LoonKit.lcf existing-release/LoonKit.lcf"):
            self.assertIn(guard,workflow)
        self.assertIn("## 更新内容",notes)
        self.assertIn("## 升级方法",notes)

    def test_landing_page_has_setup_and_support(self):
        readme=(ROOT/"README.md").read_text(encoding="utf-8")
        self.assertIn("快速开始",readme)
        self.assertIn("功能概览",readme)
        self.assertIn("问题反馈",readme)
        self.assertIn("THIRD_PARTY_NOTICES",readme)


if __name__ == "__main__":
    unittest.main()
