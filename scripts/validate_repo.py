#!/usr/bin/env python3
"""Static checks for LoonKit (stdlib only).

Run locally: python3 scripts/validate_repo.py
External resources: python3 scripts/validate_repo.py --check-remote
"""
import argparse
import concurrent.futures
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "LoonKit.lcf"
PLUGIN = ROOT / "plugins" / "Network_Diagnostics.plugin"
JS = [
    ROOT / "scripts" / "v20261018r11" / "network-diagnostics.js",
    ROOT / "scripts" / "v20261018r11" / "node-intelligence.js",
]
ISSUES = []


def require(ok, message):
    if not ok:
        ISSUES.append(message)


def section(content, name):
    match = re.search(r"^\[" + re.escape(name) + r"\]\s*$", content, re.M)
    if match is None:
        ISSUES.append("missing section [" + name + "]")
        return ""
    remainder = content[match.end():]
    end = re.search(r"^\[[^\]]+\]\s*$", remainder, re.M)
    return remainder[:end.start()] if end else remainder


def check_config():
    data = CONF.read_text(encoding="utf-8")
    require(data.startswith("# LoonKit v5.1.0"), "expected v5.1.0 release header")
    require("dns-server = 223.5.5.5,223.6.6.6" in data, "public DNS changed")
    require("doh-server = https://dns.alidns.com/dns-query" in data, "AliDNS DoH changed")
    require("ssid-trigger" not in data, "Wi-Fi automation must not be enabled in public config")

    groups_text = section(data, "Proxy Group")
    group_lines = re.findall(r"^([^#\s][^=\n]*?)\s*=\s*(select|url-test|fallback),", groups_text, re.M)
    groups = [name.strip() for name, _ in group_lines]
    require(len(groups) == 33, "expected 33 proxy groups (got %s)" % len(groups))
    require(len(groups) == len(set(groups)), "duplicate proxy-group names")
    known = set(groups) | {"DIRECT", "REJECT", "REJECT-DROP", "REJECT-TINYGIF", "PROXY"}
    require({"Proxy", "Auto", "Fallback", "AdBlock", "Final"} <= set(groups), "missing core groups")

    remote_text = section(data, "Remote Rule")
    remote = []
    for line in remote_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"(https://\S+?),\s*policy=([^,\s]+)", line)
        require(match is not None, "malformed remote rule: " + line[:90])
        if match:
            remote.append(match.group(1))
            require(match.group(2) in known, "undefined remote rule policy: " + match.group(2))
    require(len(remote) == 33, "expected 33 self-hosted lists (got %s)" % len(remote))
    for url in remote:
        require(url.startswith("https://raw.githubusercontent.com/YohakuSama/loonkit/main/rules/generated/"),
                "remote URL must be a self-hosted main branch rule: " + url)
        require((ROOT / "rules" / "generated" / url.rsplit("/", 1)[-1]).is_file(),
                "missing built rule: " + url)
    require(len(remote) == len(set(remote)), "duplicate remote rule URLs")

    rule_text = section(data, "Rule")
    local_count = 0
    for line in rule_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",")]
        local_count += 1
        policy = parts[1] if parts[0] == "FINAL" else (parts[2] if len(parts) >= 3 else "")
        require(policy in known, "undefined local rule policy: " + line)
    require(local_count == 3, "expected only three fallback local rules (got %s)" % local_count)
    require("GEOIP,CN,DIRECT,no-resolve" in rule_text, "CN GEOIP route missing")
    require("FINAL,Final" in rule_text, "FINAL policy missing")

    # Ensure the live config enables the current plugin.
    plugin_text = section(data, "Plugin")
    expected_plugin = "https://raw.githubusercontent.com/YohakuSama/loonkit/main/plugins/v20261018r11/Network_Diagnostics.plugin"
    entries = [line.strip() for line in plugin_text.splitlines()
               if line.strip() and not line.lstrip().startswith("#")]
    require(len(entries) == 1, "expected exactly one configured plugin")
    require(len(entries) == 1 and entries[0].startswith(expected_plugin + ",")
            and "enabled=true" in entries[0], "current plugin must be enabled")
    require("FINAL,Final" in rule_text and "Final = select,Proxy,Auto,Fallback,DIRECT" in groups_text,
            "the existing Proxy-first Final policy must remain unchanged")

    icon_urls = re.findall(r"\bimg-url\s*=\s*(https://\S+)", groups_text)
    require(len(icon_urls) == 33, "expected one icon per proxy group")
    require(len(icon_urls) == len(set(icon_urls)), "duplicate group icon URLs")
    icon_root = "https://raw.githubusercontent.com/YohakuSama/loonkit/main/icons/"
    for group, icon_url in zip(groups, icon_urls):
        expected_name = "AnimeCrazy" if group == "動畫瘋" else group
        expected_version = "v20261018r3" if group == "HBO" else "v20261018r2"
        expected_url = f"{icon_root}{expected_version}/{expected_name}.png"
        require(icon_url == expected_url, "policy icon URL/version mismatch for " + group + ": " + icon_url)
        require((ROOT / "icons" / expected_version / (expected_name + ".png")).is_file(),
                "missing versioned PNG: " + expected_name + " (" + expected_version + ")")

    print("Config: %s groups; %s remote lists; %s local rules; %s icon links"
          % (len(groups), len(remote), local_count, len(icon_urls)))
    config_url = "https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf"
    return remote + icon_urls + [expected_plugin, config_url]


def check_plugin():
    data = PLUGIN.read_text(encoding="utf-8")
    require("#!icon = https://" in data, "missing plugin icon")
    require("compare_direct = switch,false" in data, "DIRECT IP comparison must be opt-in")
    require("auto_check = switch,false" in data, "automatic checks must default off")
    pinned_plugin=ROOT / "plugins" / "v20261018r11" / "Network_Diagnostics.plugin"
    require(pinned_plugin.is_file(), "missing current versioned plugin")
    require(pinned_plugin.read_bytes() == PLUGIN.read_bytes(),
            "versioned plugin differs from current file")
    require("/main/icons/v20261018r2/Console.png" in data, "plugin icon must reference a published image")
    require((ROOT / "icons/v20261018r2/Console.png").is_file(),
            "missing current plugin image")
    require("已移除" not in data and "情报源" not in data and "安全认证" not in data,
            "public plugin metadata includes release history or unnecessary jargon")
    require("ssid-trigger" not in data and "wifi-cellular-mode" not in data,
            "unexpected Wi-Fi automation in plugin")
    arg_text = section(data, "Argument")
    names = set(re.findall(r"^([a-z_]+)\s*=", arg_text, re.M))
    expected = {"auto_check", "target_policy", "compare_direct"}
    require(names == expected, "expected exactly three lean-plugin options, got: " + str(sorted(names)))
    require("auto_check = switch,false" in data,
            "automatic network monitoring must default off")
    scripts = section(data, "Script")
    lines = [s.strip() for s in scripts.splitlines() if s.strip() and not s.lstrip().startswith("#")]
    require(len(lines) == 3, "expected 3 plugin script entries (got %d)" % len(lines))
    require(sum(s.startswith("generic then script(") for s in lines) == 2, "expected 2 manual actions")
    require(sum(s.startswith("network-changed then script(") for s in lines) == 1, "missing optional network-change hook")
    require("with enable=${auto_check}" in scripts, "network-change hook must be controlled by auto_check")
    require("dns-leak-check.js" not in scripts and "DNS 解析器泄漏检测" not in scripts,
            "removed DNS resolver leakage tool must not appear in plugin")
    require("模拟网络切换" not in scripts and "状态与设置摘要" not in scripts,
            "obsolete developer tools must not appear in the user plugin")
    for name in re.findall(r"\$\{([a-z_]+)\}", scripts):
        require(name in names, "undeclared plugin argument " + name)
    src_urls = re.findall(r'script\("(https://[^"]+)"', scripts)
    require(len(src_urls) == 3, "expected 3 script source URLs")
    for url in src_urls:
        marker = "/YohakuSama/loonkit/main/"
        require(marker in url and ("/scripts/v20261018r11/network-diagnostics.js" in url
                                   or "/scripts/v20261018r11/node-intelligence.js" in url)
                and (ROOT / url.split(marker)[1]).is_file(),
                "plugin must use versioned scripts: " + url)

    for file in JS:
        require(file.is_file(), "JS missing " + str(file))
    print("Plugin: %d arguments; %d script actions; icon supplied" % (len(names), len(lines)))
    return src_urls + [re.search(r"#!icon\s*=\s*(https://\S+)", data).group(1)]


def check_readme():
    data = (ROOT / "README.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs" / "NETWORK_DIAGNOSTICS.md").read_text(encoding="utf-8")
    for label, text in [("README", data), ("plugin guide", guide)]:
        require("Network_Diagnostics.plugin" in text, label + " missing plugin link")
        require("节点出口信息" in text and "网络与 DNS" in text,
                label + " must describe the two available tools")
    require("https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf" in data,
            "README missing full configuration import URL")
    require("直连 IP 对照" in data and "默认关闭" in data,
            "README must explain direct-IP comparison default")
    require("GEOIP,CN,DIRECT,no-resolve" not in data and "FINAL,Final" not in data,
            "README should not expose maintainer routing internals")


def check_url(url):
    # GitHub can sometimes refuse HEAD; try a small GET only for HTTP 405.
    for retry in range(2):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "Loon-Routing-DNS-CI/1.0"},
            )
            with urllib.request.urlopen(req, timeout=16) as response:
                status = response.status
            return None if status == 200 else "%s -> HTTP %s" % (url, status)
        except urllib.error.HTTPError as error:
            if error.code == 405:
                try:
                    req = urllib.request.Request(url, headers={"Range": "bytes=0-0",
                        "User-Agent": "Loon-Routing-DNS-CI/1.0"})
                    with urllib.request.urlopen(req, timeout=16) as response:
                        return None if response.status in (200, 206) else (
                            "%s -> HTTP %s" % (url, response.status))
                except Exception as inner:
                    return "%s -> %s" % (url, inner)
            if error.code not in (429, 500, 502, 503, 504) or retry > 0:
                return "%s -> HTTP %s" % (url, error.code)
        except (TimeoutError, OSError) as error:
            if retry:
                return "%s -> %s" % (url, type(error).__name__)
        time.sleep(1 + retry)
    return url + " -> request failed"


def cdn_urls_at_ref(urls, ref):
    """Use an immutable commit SHA to check PR assets before publishing to main."""
    if not re.fullmatch(r"[a-f0-9]{40}|main", ref):
        raise ValueError("--remote-ref must be main or a full commit SHA")
    prefix = "https://raw.githubusercontent.com/YohakuSama/loonkit/main/"
    for url in urls:
        if not url.startswith(prefix):
            raise ValueError("Unexpected CDN URL: " + url)
    return sorted({u.replace(prefix, prefix.replace("/main/", "/" + ref + "/"), 1)
                   for u in urls})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-remote", action="store_true",
                        help="check every rule, icon, plugin and main config URL; network required")
    parser.add_argument("--remote-ref", default="main",
                        help="git revision to check on CDN; use a PR head SHA before merging")
    args = parser.parse_args()
    urls = check_config() + check_plugin()
    check_readme()
    if args.check_remote:
        try:
            urls = cdn_urls_at_ref(urls, args.remote_ref)
        except ValueError as error:
            ISSUES.append(str(error))
        if not ISSUES:
            print("Checking %s CDN URLs (HEAD) at %s..." % (len(urls), args.remote_ref))
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            for failure in executor.map(check_url, urls):
                if failure:
                    ISSUES.append("remote: " + failure)
    if ISSUES:
        for issue in ISSUES:
            print("ERROR: " + issue, file=sys.stderr)
        print("Validation failed: %d problem(s)" % len(ISSUES), file=sys.stderr)
        sys.exit(1)
    print("All validation checks passed.")


if __name__ == "__main__":
    main()
