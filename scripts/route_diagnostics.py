#!/usr/bin/env python3
"""Offline LoonKit routing approximation, seven-service coverage and private log summary.

No network requests. Do not treat this as Loon's actual runtime match log.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
RAW_RULE = re.compile(
    r"^https://raw\.githubusercontent\.com/YohakuSama/loonkit/"
    r"[0-9a-f]{40}/(rules/releases/vNext-RC2/[A-Za-z0-9_-]+\.list)$"
)
VALID_HOST = re.compile(r"^(?=.{1,253}$)[a-z0-9-]+(?:\.[a-z0-9-]+)+$", re.I)
KINDS = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6"}
SERVICE_GROUPS = ("Spotify", "Twitch", "Abema", "BBC", "Line", "Reddit", "Linkedin")
MAX_LOG_SIZE = 10 * 1024 * 1024
MAX_LOG_ENTRIES = 10000


def profile_sections(profile: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    active = None
    for raw in profile.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            active = line[1:-1]
            sections[active] = []
        elif active and line and not line.startswith(("#", ";", "//")):
            sections[active].append(line)
    return sections


def matcher(raw: str):
    fields = [f.strip() for f in raw.split(",")]
    if len(fields) < 2 or fields[0].upper() not in KINDS:
        return None
    kind, value = fields[0].upper(), fields[1].lower()
    if kind in ("IP-CIDR", "IP-CIDR6"):
        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError:
            return None
        if (network.version == 6) != (kind == "IP-CIDR6"):
            return None
        return kind, str(network)
    if kind == "DOMAIN-KEYWORD":
        return (kind, value) if value and len(value) <= 253 else None
    if kind == "DOMAIN-SUFFIX" and re.fullmatch(r"[a-z0-9-]{2,63}", value):
        return kind, value
    return (kind, value) if VALID_HOST.fullmatch(value) else None


def known_services(root=ROOT):
    manifest = json.loads((root / "build/engine_manifest.json").read_text(encoding="utf-8"))
    data = manifest["reviewed_overseas_inline_minimal"]
    if set(SERVICE_GROUPS) != set(data):
        raise ValueError("seven-service reviewed roots changed; re-audit")
    return {group: tuple(sorted(set(values))) for group, values in data.items()}


class Router:
    """Documented subset of Loon's matching grammar; no DNS, GEOIP or ASN lookup."""

    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.profile = (self.root / "LoonKit.lcf").read_text(encoding="utf-8")
        self.sections = profile_sections(self.profile)
        self.exact = defaultdict(list)
        self.suffix = defaultdict(list)
        self.keyword = []
        self.ips = []
        self.subscriptions = []
        self.count = 0
        for line in self.sections["Rule"]:
            cols = [x.strip() for x in line.split(",")]
            if len(cols) >= 3:
                self._add(",".join(cols[:2]), cols[2], "本地规则")
        for entry in self.sections["Remote Rule"]:
            parts = [x.strip() for x in entry.split(",")]
            hit = RAW_RULE.fullmatch(parts[0])
            if not hit:
                raise ValueError("untrusted or unfrozen subscription: " + parts[0][:90])
            settings = dict((key.strip(), value.strip()) for x in parts[1:] if "=" in x
                            for key, value in (x.split("=", 1),))
            policy = settings.get("policy", "").strip()
            if not policy or settings.get("enabled", "true").strip().lower() == "false":
                continue
            rel = hit.group(1)
            self.subscriptions.append(rel)
            for raw in (self.root / rel).read_text(encoding="utf-8").splitlines():
                self._add(raw, policy, rel)

    def _add(self, line: str, policy: str, origin: str):
        parsed = matcher(line)
        if not parsed:
            return
        kind, value = parsed
        self.count += 1
        item = (self.count, policy, origin, kind + "," + value)
        if kind == "DOMAIN":
            self.exact[value].append(item)
        elif kind == "DOMAIN-SUFFIX":
            self.suffix[value].append(item)
        elif kind == "DOMAIN-KEYWORD":
            self.keyword.append((value, item))
        else:
            self.ips.append((ipaddress.ip_network(value), item))

    def match(self, value: str) -> dict:
        target = value.lower().rstrip(".")
        if target.startswith(("http://", "https://")):
            raise ValueError("enter a hostname or IP only; URLs might contain private tokens")
        try:
            ip = ipaddress.ip_address(target)
        except ValueError:
            ip = None
        hits = []
        if ip is not None:
            for network, item in self.ips:
                if ip.version == network.version and ip in network:
                    hits.append(item)
        else:
            if not VALID_HOST.fullmatch(target):
                raise ValueError("expected a valid public-style hostname or IP address")
            hits += self.exact.get(target, [])
            parts = target.split(".")
            for i in range(len(parts)):
                hits.extend(self.suffix.get(".".join(parts[i:]), []))
            for keyword, item in self.keyword:
                if keyword in target:
                    hits.append(item)
        hits.sort(key=lambda item: item[0])
        chosen = hits[0] if hits else None
        return {
            "target": target,
            "predicted_policy": chosen[1] if chosen else "Final (subject to GEOIP/ASN/runtime)",
            "first_match": ({"rule":chosen[3], "source":chosen[2]} if chosen else None),
            "other_match_count": max(0, len(hits)-1),
            "other_policies": sorted({item[1] for item in hits[1:]}),
            "warning": ("离线规则推演；无法确认真机实际命中、GEOIP、IP-ASN、"
                        "DNS 解析、插件插入规则及节点实际可用性。"),
        }


def coverage(router: Router) -> dict:
    service_roots = known_services(router.root)
    groups = []
    for group, roots in service_roots.items():
        checks = []
        for root in roots:
            result = router.match(root)
            checks.append({"root": root, "predicted_policy": result["predicted_policy"],
                           "pass": result["predicted_policy"] == group})
        groups.append({"service": group, "declared_root_count": len(roots),
                       "reviewed_roots_match": all(x["pass"] for x in checks),
                       "roots": checks})
    return {"summary": "只检查已登记的主域名；不代表 App 登录/API/CDN 已完整覆盖。",
            "all_reviewed_roots_match": all(g["reviewed_roots_match"] for g in groups),
            "services": groups}


def service_for(host: str, roots: dict) -> str:
    for group, values in roots.items():
        if any(host == root or host.endswith("." + root) for root in values):
            return group
    return "其他站点"


def _host(url: str):
    if not isinstance(url, str) or len(url) > 4096:
        return None
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https"):
            return None
        host = parsed.hostname
    except ValueError:
        return None
    if host and VALID_HOST.fullmatch(host):
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return host.lower()
        return None
    return None


def sanitized_log_summary(data: bytes, roots: dict, *, text_mode=False):
    """Only counts by known service, status bucket, and public policy group.

    Never output raw URL, path, query, node, hostname, cookie, token or IP.
    """
    if len(data) > MAX_LOG_SIZE:
        raise ValueError("log exceeds 10 MiB")
    counts = Counter()
    processed = 0
    if text_mode:
        entries = []
        for line in data.decode("utf-8-sig").splitlines():
            found = re.search(r"https?://[^\s<>\"']{1,4096}", line)
            if not found:
                continue
            status = re.search(r"(?:HTTP\s*|status\s*[=:]\s*)([1-5]\d\d)\b", line, re.I)
            entries.append((found.group(0), int(status.group(1)) if status else 0, ""))
            if len(entries) >= MAX_LOG_ENTRIES:
                break
    else:
        obj = json.loads(data)
        entries = []
        if not isinstance(obj, dict) or not isinstance(obj.get("log"), dict):
            raise ValueError("expected a HAR object with log.entries")
        har_entries = obj["log"].get("entries", [])
        if not isinstance(har_entries, list):
            raise ValueError("invalid HAR entries")
        for record in har_entries[:MAX_LOG_ENTRIES]:
            if not isinstance(record, dict):
                continue
            request, response = record.get("request"), record.get("response")
            if not isinstance(request, dict):
                continue
            status = response.get("status", 0) if isinstance(response, dict) else 0
            policy = record.get("_policy", "")
            entries.append((request.get("url"), status, policy))
    allowed_policies = set(SERVICE_GROUPS) | {"DIRECT", "REJECT", "Proxy", "Auto",
                                               "Fallback", "Final", "AdBlock", "AI",
                                               "Google", "Microsoft", "Apple", "Netflix"}
    for url, status, policy in entries:
        host = _host(url)
        if not host:
            continue
        processed += 1
        group = service_for(host, roots)
        try:
            code = int(status)
        except (ValueError, TypeError, OverflowError):
            code = 0
        bucket = str(code // 100) + "xx" if 100 <= code <= 599 else "未知"
        safe_policy = policy if isinstance(policy, str) and policy in allowed_policies else "未知"
        counts[(group, bucket, safe_policy)] += 1
    result = [{"service":group, "http_status":status, "policy":policy, "count":count}
              for (group, status, policy), count in sorted(counts.items())]
    return {"processed_requests": processed, "groups": result,
            "privacy": "只输出服务类别/状态码范围/公开策略名及计数；不输出节点、域名、URL、请求路径、令牌或原始日志。",
            "warning": "分析的是本地提供的记录；没有日志就无法确认真机匹配。未知主机被合并为其他站点。"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("coverage", "match", "logs"):
        subparser = sub.add_parser(name)
        subparser.add_argument("--json", action="store_true")
        if name == "match":
            subparser.add_argument("hostname_or_ip")
        if name == "logs":
            subparser.add_argument("file", type=Path)
            subparser.add_argument("--text", action="store_true",
                                   help="text log rather than HAR JSON")
    args = parser.parse_args()
    try:
        if args.command == "logs":
            if args.file.stat().st_size > MAX_LOG_SIZE:
                raise ValueError("log exceeds 10 MiB")
            result = sanitized_log_summary(args.file.read_bytes(), known_services(),
                                           text_mode=args.text)
        else:
            router = Router()
            result = coverage(router) if args.command == "coverage" else router.match(args.hostname_or_ip)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except OSError:
        parser.exit(2, "无法读取输入文件；请检查路径、权限和文件大小。\n")
    except (ValueError, KeyError, UnicodeError):
        parser.exit(2, "无法分析输入或规则资料，请检查文件格式和命令参数。\n")


if __name__ == "__main__":
    main()
