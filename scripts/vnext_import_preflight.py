#!/usr/bin/env python3
"""Fail-closed, offline Loon vNext release-candidate import preflight.

Validates repository content and Loon-like structure, NOT actual Loon parsing,
node connectivity, DNS behavior, or device import.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "refactor/vnext/LoonKit.vNext.Candidate.lcf"
EXPECTED = ROOT / "refactor/vnext/reports/phase05_diff.json"
MANIFEST = ROOT / "refactor/vnext/engine_manifest.json"
REPO_RAW = "https://raw.githubusercontent.com/YohakuSama/loonkit/"
BRANCH_PREFIX = REPO_RAW + "refactor/loonkit-vnext/refactor/vnext/generated/"
SECTIONS = ("General", "Proxy", "Remote Proxy", "Remote Filter", "Proxy Group",
            "Remote Rule", "Rule", "Plugin")
DNS_AND_TUN_KEYS = {
    "dns-server", "doh-server", "hijack-dns", "ip-mode", "ipv6-vif",
    "interface-mode", "skip-proxy", "bypass-tun", "real-ip",
}
ALLOWED_KINDS = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR",
                 "IP-CIDR6", "IP-ASN", "USER-AGENT"}
BUILTIN = {"DIRECT", "REJECT", "REJECT-DROP", "REJECT-TINYGIF", "REJECT-NO-DROP"}
SHA = re.compile(r"^[0-9a-f]{40}$")


def sections(text: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        line = line.strip().lstrip("\ufeff")
        if line.startswith("[") and line.endswith("]"):
            name = line[1:-1]
            if name not in SECTIONS or name in found:
                raise ValueError("unknown/duplicate config section: " + name)
            found[name] = []
            current = name
        elif line and not line.startswith(("#", ";", "//")):
            if current is None:
                raise ValueError("non-comment text outside config section")
            found[current].append(line)
    if set(found) != set(SECTIONS):
        raise ValueError("missing required sections: " + repr(set(SECTIONS) - set(found)))
    if list(found) != list(SECTIONS):
        raise ValueError("unexpected section order")
    return found


def general_fields(lines: list[str]) -> dict[str, str]:
    out = {}
    for line in lines:
        if "=" not in line:
            raise ValueError("General entry missing assignment")
        name, value = (x.strip() for x in line.split("=", 1))
        if not name or not value or name in out:
            raise ValueError("duplicate/empty General key: " + name)
        out[name] = value
    return out


def options(parts: list[str]) -> dict[str, str]:
    result = {}
    for value in parts:
        if "=" not in value:
            raise ValueError("invalid remote option: " + value)
        k, v = (x.strip() for x in value.split("=", 1))
        if not k or not v or k in result:
            raise ValueError("duplicate or empty remote option: " + k)
        result[k] = v
    return result


def remote_rows(lines: list[str], commit: str | None = None) -> list[dict]:
    if commit is not None and not SHA.fullmatch(commit):
        raise ValueError("a complete immutable lowercase commit SHA is required")
    rows = []
    for line in lines:
        bits = [x.strip() for x in line.split(",")]
        url, opt = bits[0], options(bits[1:])
        expected_prefix = (REPO_RAW + commit + "/refactor/vnext/generated/"
                           if commit else BRANCH_PREFIX)
        if not url.startswith(expected_prefix):
            raise ValueError("remote rule must use ONLY the expected vNext ref: " + url)
        name = url[len(expected_prefix):]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*\.list", name):
            raise ValueError("unexpected remote path: " + name)
        if set(opt) != {"policy", "tag", "enabled"} or opt["enabled"] != "true":
            raise ValueError("invalid remote policy/tag/options: " + line)
        rows.append({"filename": name, "policy": opt["policy"], "tag": opt["tag"],
                     "url": url})
    if len({r["filename"] for r in rows}) != len(rows):
        raise ValueError("duplicate remote subscription")
    if len({r["tag"] for r in rows}) != len(rows):
        raise ValueError("duplicate remote tag")
    return rows


def validate_rule(line: str, allowed_policies: set[str]) -> tuple[str, str]:
    fields = [x.strip() for x in line.split(",")]
    kind = fields[0]
    if kind == "FINAL":
        if len(fields) != 2 or fields[1] not in allowed_policies:
            raise ValueError("invalid FINAL: " + line)
        return kind, fields[1]
    if len(fields) not in (3, 4) or fields[2] not in allowed_policies:
        raise ValueError("unknown rule policy/field count: " + line)
    value, policy = fields[1:3]
    flag = fields[3:] or []
    if kind == "GEOIP":
        if value != "CN" or flag != ["no-resolve"]:
            raise ValueError("unexpected GEOIP: " + line)
    elif kind in ALLOWED_KINDS:
        if kind in {"IP-CIDR", "IP-CIDR6"}:
            net = ipaddress.ip_network(value, strict=True)
            if (net.version == 6) != (kind == "IP-CIDR6"):
                raise ValueError("IP address-family mismatch: " + line)
        elif kind == "IP-ASN":
            if not re.fullmatch(r"\d+", value):
                raise ValueError("invalid ASN: " + line)
        elif kind.startswith("DOMAIN"):
            if not re.fullmatch(r"(?i)[a-z0-9*._-]+", value):
                raise ValueError("invalid domain: " + line)
        if flag != (["no-resolve"] if kind in {"IP-CIDR", "IP-CIDR6", "IP-ASN"} else []):
            raise ValueError("invalid no-resolve flag: " + line)
    else:
        raise ValueError("unsupported rule type: " + line)
    return kind, policy


def validate_remote_file(path: Path, expected_sha: str, expected_count: int) -> dict:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha:
        raise ValueError("candidate SHA256 mismatch: " + str(path))
    rows = [x.strip() for x in data.decode("utf-8-sig").splitlines()
            if x.strip() and not x.strip().startswith(("#", ";", "//"))]
    if len(rows) != expected_count or not rows:
        raise ValueError("candidate rule count mismatch: " + str(path))
    for row in rows:
        validate_rule(row + ",DIRECT" if row.count(",") in (1, 2) else row, {"DIRECT"})
        # Generated files have NO policy column. Above supplies one, retaining
        # optional IP no-resolve as a fourth field (not a policy).
    return {"path": str(path.relative_to(ROOT)), "sha256": digest,
            "rule_count": len(rows), "bytes": len(data)}


def check_repo_resource(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != "raw.githubusercontent.com":
        raise ValueError("external resource host forbidden: " + url)
    fragment = parts.path.removeprefix("/YohakuSama/loonkit/main/")
    if fragment == parts.path or not (fragment.startswith("icons/") or fragment.startswith("plugins/")):
        raise ValueError("unexpected icon/plugin resource: " + url)
    if not (ROOT / fragment).is_file():
        raise ValueError("missing icon/plugin object: " + fragment)
    return fragment


def check(config: str | None = None, commit: str | None = None) -> dict:
    content = CONFIG.read_text(encoding="utf-8") if config is None else config
    profile = sections(content)
    stable = sections((ROOT / "LoonKit.lcf").read_text(encoding="utf-8"))
    original = general_fields(stable["General"])
    candidate = general_fields(profile["General"])
    if original != candidate:
        raise ValueError("General/DNS/TUN differs from untouched production profile")
    if not DNS_AND_TUN_KEYS <= candidate.keys():
        raise ValueError("missing DNS/TUN invariants")
    if profile["Proxy"] or profile["Remote Proxy"]:
        raise ValueError("public acceptance configuration must not embed private nodes")
    filters = set()
    for line in profile["Remote Filter"]:
        if "=" not in line:
            raise ValueError("invalid remote filter")
        filters.add(line.split("=", 1)[0].strip())
    if filters != {"ALL_Filter"}:
        raise ValueError("remote filter names changed")
    groups = {}
    icons = []
    for line in profile["Proxy Group"]:
        if "=" not in line:
            raise ValueError("invalid Proxy Group line")
        name, rest = [x.strip() for x in line.split("=", 1)]
        if name in groups:
            raise ValueError("duplicate strategy group: " + name)
        tokens = [x.strip() for x in rest.split(",")]
        if tokens[0] not in {"select", "url-test", "fallback"}:
            raise ValueError("invalid group algorithm: " + name)
        groups[name] = tokens
        matches = re.findall(r"img-url\s*=\s*(https://[^,\s]+)", rest)
        if len(matches) != 1:
            raise ValueError("missing/duplicate group icon: " + name)
        icons += [check_repo_resource(matches[0])]
    if len(groups) != 33:
        raise ValueError("candidate must retain 33 strategy groups")
    allowed = set(groups) | BUILTIN
    for name, tokens in groups.items():
        refs = [token for token in tokens[1:] if "=" not in token and not token.startswith("http")]
        for target in refs:
            if target not in allowed | filters and not re.fullmatch(r"\d+", target):
                raise ValueError("unbound proxy selector: " + name + ":" + target)
    if groups["AdBlock"][:3] != ["select", "REJECT", "DIRECT"]:
        raise ValueError("AdBlock selectable modes changed")
    if groups["Final"][:5] != ["select", "Proxy", "Auto", "Fallback", "DIRECT"]:
        raise ValueError("FINAL selector choices changed")
    rows = remote_rows(profile["Remote Rule"], commit)
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))["remote_groups"]
    active = json.loads(MANIFEST.read_text(encoding="utf-8"))["active_groups"]
    if len(rows) != 26 or len(active) != 26 or set(expected) != set(active):
        raise ValueError("candidate subscriptions or engine groups changed")
    rules = {}
    actual_count = 0
    for r in rows:
        group = r["policy"]
        name = "AnimeCrazy" if group == "動畫瘋" else group
        if group not in expected or r["filename"] != name + ".list" or r["tag"] != "vNext-" + name:
            raise ValueError("incorrect subscription filename/tag/policy: " + repr(r))
        if group not in groups and group != "DIRECT":
            raise ValueError("remote references missing selector: " + group)
        # Four DIRECT lists have policy=DIRECT but are retained by active group name.
        meta = expected[group] if group in expected else None
        if meta is None:
            raise ValueError("unexpected remote group")
        path = ROOT / "refactor/vnext/generated" / r["filename"]
        rule = validate_remote_file(path, meta["sha256"], meta["rule_count"])
        rules[r["filename"]] = {**rule, "policy": group, "url": r["url"]}
        actual_count += rule["rule_count"]
    if set(rules) != {("AnimeCrazy" if g == "動畫瘋" else g) + ".list" for g in active}:
        raise ValueError("missing/extra candidate subscriptions")
    locals_ = profile["Rule"]
    if len(locals_) != 106 or locals_[-2:] != ["GEOIP,CN,DIRECT,no-resolve", "FINAL,Final"]:
        raise ValueError("local count or terminal rule order changed")
    for line in locals_:
        validate_rule(line, allowed)
    plugins = []
    for line in profile["Plugin"]:
        part = [x.strip() for x in line.split(",")]
        if len(part) != 2 or part[1] != "enabled=true":
            raise ValueError("invalid plugin line")
        plugins.append(check_repo_resource(part[0]))
    if len(plugins) != 1:
        raise ValueError("unexpected plugin count")
    if "ProxyProtect" in content:
        raise ValueError("retired ProxyProtect candidate reference")
    return {
        "schema_version": 1,
        "config_structure": "CONFIG_STRUCTURE_PASS",
        "resource_integrity": "RESOURCE_INTEGRITY_PASS",
        "private_nodes": "PRIVATE_NODE_REQUIRED",
        "loon_import": "LOON_IMPORT_NOT_EXECUTED",
        "source_ref": commit or "refactor/loonkit-vnext",
        "config_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "remote_subscription_count": len(rows),
        "remote_rule_count": actual_count,
        "proxy_group_count": len(groups),
        "local_rule_count": len(locals_),
        "icon_count": len(icons),
        "plugin_count": len(plugins),
        "rules": rules,
        "limitations": ["STATIC_CHECKS_NOT_LOON", "NO_PRIVATE_NODES", "NO_REAL_DNS_OR_IP_TEST"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", default=None)
    ap.add_argument("--config", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    result = check(args.config.read_text(encoding="utf-8") if args.config else None,
                   args.commit)
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
