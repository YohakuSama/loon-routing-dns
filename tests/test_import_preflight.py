"""Offline check of everything a Loon config needs to import successfully.

This checks file structure and *local* availability; it does not emulate Loon
or claim that URLs/network nodes are reachable on a particular device.
"""
from __future__ import annotations
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "LoonKit.lcf"
REVIEW = ROOT / "reviews/LoonKit_Hybrid_Review.lcf"
HOST = "raw.githubusercontent.com"


def section(source: str, name: str) -> str:
    match = re.search(r"(?m)^\[" + re.escape(name) + r"\]\s*$", source)
    if not match:
        raise AssertionError("Missing [" + name + "]")
    rest = source[match.end():]
    finish = re.search(r"(?m)^\[[^\]]+\]\s*$", rest)
    return rest[:finish.start()] if finish else rest


def entries(source: str, name: str) -> list[str]:
    return [s.strip() for s in section(source, name).splitlines()
            if s.strip() and not s.lstrip().startswith("#")]


def local_path(url: str) -> Path:
    parsed = urlsplit(url.strip())
    assert parsed.scheme == "https" and parsed.netloc == HOST, url
    parts = unquote(parsed.path).lstrip("/").split("/")
    assert len(parts) >= 5, url
    config = ACTIVE.read_text(encoding="utf-8")
    matched = re.search(r"(?m)^# GitHub:\s+https://github\.com/([^/\s]+)/([^/\s]+)\s*$", config)
    assert matched is not None, "Missing project GitHub metadata"
    assert parts[0:2] == [matched.group(1), matched.group(2)], url
    assert parts[2] == "main", url
    assert all(p and p not in (".", "..") for p in parts), url
    relative = Path(*parts[3:])
    local = ROOT / relative
    assert local.resolve().is_relative_to(ROOT), url
    return local


def icons(source: str) -> list[tuple[str, str]]:
    ret=[]
    for line in entries(source, "Proxy Group"):
        m=re.match(r"^([^=]+?)\s*=\s*(?:select|url-test|fallback),.*\bimg-url\s*=\s*(https://\S+?\.png)$",line)
        assert m, "Invalid strategy icon: " + line[:110]
        ret.append((m.group(1).strip(), m.group(2)))
    return ret


class ImportPreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main=ACTIVE.read_text(encoding="utf-8")
        cls.review=REVIEW.read_text(encoding="utf-8")
        cls.plugin=(ROOT / "plugins/Network_Diagnostics.plugin").read_text(encoding="utf-8")

    def test_active_and_review_strategy_icons_exist(self):
        main=icons(self.main)
        draft=icons(self.review)
        self.assertEqual(len(main), 33)
        self.assertEqual([x[0] for x in main], [x[0] for x in draft])
        for name,url in main+draft:
            with self.subTest(name=name, url=url):
                self.assertTrue(local_path(url).is_file(), url)

    def test_review_has_same_strategy_group_definitions(self):
        for a,b in zip(entries(self.main,"Proxy Group"),entries(self.review,"Proxy Group")):
            self.assertEqual(a.split("img-url",1)[0], b.split("img-url",1)[0])

    def test_all_remote_rules_exist_and_use_defined_policy(self):
        policy_names={name for name,_ in icons(self.main)}
        self.assertEqual(len(policy_names),33)
        for source in (self.main, self.review):
            lines=entries(source,"Remote Rule")
            self.assertEqual(len(lines),33)
            for row in lines:
                m=re.fullmatch(r"(https://[^,\s]+),\s*policy=([^,]+),\s*tag=([^,]+),\s*enabled=true",row)
                self.assertIsNotNone(m,row)
                url,policy,_=m.groups()
                with self.subTest(rule=url):
                    self.assertTrue(local_path(url).is_file(), url)
                    self.assertIn(policy,policy_names | {"DIRECT"})

    def test_active_plugin_and_its_scripts_exist(self):
        attached=entries(self.main,"Plugin")
        self.assertEqual(len(attached),1)
        url, enabled=attached[0].split(", ",1)
        self.assertEqual(enabled,"enabled=true")
        self.assertTrue(local_path(url).is_file())
        self.assertEqual(local_path(url).read_text(encoding="utf-8"),self.plugin)
        for resource in re.findall(r'script\("(https://[^"]+)"',self.plugin):
            with self.subTest(url=resource):
                self.assertTrue(local_path(resource).is_file(),resource)
        image=re.search(r"(?m)^#!icon\s*=\s*(https://\S+)",self.plugin)
        self.assertIsNotNone(image)
        self.assertTrue(local_path(image.group(1)).is_file())

    def test_old_config_filename_is_identical_compatibility_alias(self):
        alias = (ROOT / "Loon_Routing_DNS.lcf").read_text(encoding="utf-8")
        self.assertEqual(alias, self.main)

    def test_only_new_repository_paths_are_used_by_active_assets(self):
        assets = [self.main, self.review, self.plugin]
        for path in ("scripts/v20261018r11/node-intelligence.js",
                     "scripts/v20261018r11/network-diagnostics.js"):
            assets.append((ROOT / path).read_text(encoding="utf-8"))
        for content in assets:
            self.assertNotIn("YohakuSama/loon-routing-dns", content)
            self.assertNotIn("Loon Routing DNS", content)
        self.assertIn("https://github.com/YohakuSama/loonkit", self.main)
        self.assertIn("/main/plugins/v20261018r11/Network_Diagnostics.plugin", self.main)

    def test_core_rules_and_dns_are_preserved(self):
        for required in (
            "dns-server = 223.5.5.5,223.6.6.6",
            "doh-server = https://dns.alidns.com/dns-query",
            "GEOIP,CN,DIRECT,no-resolve",
            "FINAL,Final",
            "Final = select,Proxy,Auto,Fallback,DIRECT",
        ):
            with self.subTest(value=required):
                self.assertIn(required,self.main)

    def test_cdn_premerge_checks_use_commit_sha_not_unpublished_main(self):
        from scripts.validate_repo import cdn_urls_at_ref
        url = "https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf"
        sha = "a" * 40
        result = cdn_urls_at_ref([url, url], sha)
        self.assertEqual(result, [url.replace("/main/", "/" + sha + "/")])
        self.assertEqual(cdn_urls_at_ref([url], "main"), [url])
        for bad in ("../main", "refs/heads/main", "main/../../", "123"):
            with self.subTest(ref=bad):
                with self.assertRaises(ValueError):
                    cdn_urls_at_ref([url], bad)

    def test_no_broken_unversioned_icon_urls_in_review(self):
        self.assertEqual(len(icons(self.review)),33)
        self.assertFalse(any("/main/icons/" in url and "/main/icons/v" not in url
                             for _,url in icons(self.review)))


if __name__ == "__main__":
    unittest.main()
