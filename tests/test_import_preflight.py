"""Offline check of everything a Loon config needs to import successfully.

This checks file structure and *local* availability; it does not emulate Loon
or claim that URLs/network nodes are reachable on a particular device.
"""
from __future__ import annotations
import re
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "LoonKit.lcf"
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
        cls.plugin=(ROOT / "plugins/Network_Diagnostics.plugin").read_text(encoding="utf-8")

    def test_active_strategy_icons_exist(self):
        main=icons(self.main)
        self.assertEqual(len(main), 33)
        for name,url in main:
            with self.subTest(name=name,url=url):
                self.assertTrue(local_path(url).is_file(),url)

    def test_all_remote_rules_exist_and_use_defined_policy(self):
        policy_names={name for name,_ in icons(self.main)}
        self.assertEqual(len(policy_names),33)
        lines=entries(self.main,"Remote Rule")
        baseline=json.loads((ROOT / "rules/verified-routing-baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(lines,baseline["remote_rules"])
        self.assertEqual(len(lines),28)
        for row in lines:
            m=re.fullmatch(r"(https://[^,\s]+),\s*policy=([^,]+),\s*tag=([^,]+),\s*enabled=true",row)
            self.assertIsNotNone(m,row)
            url,policy,_=m.groups()
            with self.subTest(rule=url):
                parsed=urlsplit(url)
                self.assertEqual(parsed.scheme,"https")
                self.assertEqual(parsed.netloc,"raw.githubusercontent.com")
                self.assertTrue(parsed.path.startswith("/blackmatrix7/ios_rule_script/master/rule/Loon/"))
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

    def test_deprecated_config_copies_removed(self):
        self.assertFalse((ROOT / "Loon_Routing_DNS.lcf").exists())
        self.assertFalse((ROOT / "reviews/LoonKit_Hybrid_Review.lcf").exists())

    def test_only_new_repository_paths_are_used_by_active_assets(self):
        assets = [self.main, self.plugin]
        for path in ("scripts/v20261018r11/node-intelligence.js",
                     "scripts/v20261018r11/network-diagnostics.js"):
            assets.append((ROOT / path).read_text(encoding="utf-8"))
        for content in assets:
            self.assertNotIn("YohakuSama/loon-routing-dns", content)
            self.assertNotIn("Loon Routing DNS", content)
        self.assertIn("https://github.com/YohakuSama/loonkit", self.main)
        self.assertIn("/main/plugins/v20261018r11/Network_Diagnostics.plugin", self.main)

    def test_local_rule_order_matches_verified_baseline(self):
        baseline=json.loads((ROOT / "rules/verified-routing-baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(entries(self.main,"Rule"),["DOMAIN-SUFFIX,browserleaks.com,Proxy",
             "DOMAIN-SUFFIX,whatismyip.com,Proxy",
             "DOMAIN-SUFFIX,stripe.com,Proxy"] + baseline["local_rules"])
        self.assertEqual(len(baseline["local_rules"]),66)
        self.assertEqual(entries(self.main,"Rule")[:3],["DOMAIN-SUFFIX,browserleaks.com,Proxy",
             "DOMAIN-SUFFIX,whatismyip.com,Proxy",
             "DOMAIN-SUFFIX,stripe.com,Proxy"])
        self.assertNotIn("/rules/generated/",section(self.main,"Remote Rule"))
        self.assertNotIn("members/getsub.php",self.main)

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
        upstream = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/YouTube/YouTube.list"
        self.assertEqual(cdn_urls_at_ref([url,upstream],sha),sorted([
            url.replace("/main/","/"+sha+"/"),upstream]))
        for bad in ("../main", "refs/heads/main", "main/../../", "123"):
            with self.subTest(ref=bad):
                with self.assertRaises(ValueError):
                    cdn_urls_at_ref([url], bad)

    def test_no_unversioned_icon_urls_in_active_profile(self):
        self.assertEqual(len(icons(self.main)),33)
        self.assertFalse(any("/main/icons/" in url and "/main/icons/v" not in url
                             for _,url in icons(self.main)))


if __name__ == "__main__":
    unittest.main()
