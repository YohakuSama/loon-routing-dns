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


def _log_entries(data: bytes, *, text_mode=False):
    """Parse bounded local input without printing any input fields."""
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
    return entries


def sanitized_log_summary(data: bytes, roots: dict, *, text_mode=False):
    """Return aggregates only; no original hostname, URL, node or credential."""
    counts = Counter()
    processed = 0
    entries = _log_entries(data, text_mode=text_mode)
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



def candidate_coverage_audit(router: Router) -> dict:
    """Review staged service domains without modifying the published rules."""
    services = []
    for group in SERVICE_GROUPS:
        path = router.root / "rules" / "inputs" / (group + ".list")
        counts = Counter()
        examples = []
        for line in path.read_text(encoding="utf-8").splitlines():
            parsed = matcher(line)
            if not parsed or parsed[0] not in ("DOMAIN", "DOMAIN-SUFFIX"):
                if line.strip() and not line.lstrip().startswith("#"):
                    counts["unsupported_or_non_domain"] += 1
                continue
            kind, value = parsed
            # A public suffix without a dot is not a valid hostname query.
            if "." not in value:
                counts["unsupported_or_non_domain"] += 1
                continue
            predicted = router.match(value)["predicted_policy"]
            if predicted == group:
                label = "covered_by_service"
            elif predicted == "AdBlock":
                label = "adblock_review"
            elif predicted.startswith("Final"):
                label = "not_explicitly_routed"
            else:
                label = "routed_to_other_policy"
            counts[label] += 1
            if label != "covered_by_service" and len(examples) < 8:
                examples.append({"candidate_rule": kind + "," + value,
                                 "predicted_policy": predicted})
        services.append({"service": group,
                         "candidate_domain_rules": sum(counts[x] for x in (
                             "covered_by_service", "adblock_review",
                             "not_explicitly_routed", "routed_to_other_policy")),
                         "counts": dict(counts),
                         "review_examples": examples})
    return {
        "summary": "审核冻结上游服务域名与现役策略的差异；不自动增加规则。"
                   "覆盖统计不保证 API、登录、CDN、地域限制或真机表现。",
        "services": services,
        "publication_allowed": False,
        "warning": "其他策略、AdBlock 和共享 CDN 的命中不应自动覆盖或改成代理。"
    }


def private_triage(data: bytes, roots: dict, router: Router, *, text_mode=False):
    """Correlate redacted HTTP status, declared policy and offline rule matches.

    Aggregation explicitly discards hostnames, URLs, IPs, headers and unknown
    policy/node names. Observed HAR _policy is nonstandard and not proof of a
    Loon rule hit; it may describe a selected downstream node.
    """
    allowed = set(SERVICE_GROUPS) | {
        "DIRECT", "REJECT", "Proxy", "Auto", "Fallback", "Final",
        "AdBlock", "AI", "Google", "Microsoft", "Apple", "Netflix"
    }
    findings = Counter()
    processed = 0
    for url, status, observed in _log_entries(data, text_mode=text_mode):
        host = _host(url)
        if not host:
            continue
        processed += 1
        group = service_for(host, roots)
        predicted = router.match(host)["predicted_policy"]
        if predicted.startswith("Final"):
            predicted = "Final"
        if predicted not in allowed:
            predicted = "其他策略"
        safe_observed = observed if isinstance(observed, str) and observed in allowed else "未知"
        try:
            code = int(status)
        except (ValueError, TypeError, OverflowError):
            code = 0
        status_range = str(code // 100) + "xx" if 100 <= code <= 599 else "未知"
        if predicted == "AdBlock":
            signal = "命中 AdBlock 策略（是否拦截取决于用户选择）"
        elif group != "其他站点" and predicted == "Final":
            signal = "已识别服务使用 Final 兜底，需核对规则覆盖"
        elif group != "其他站点" and predicted not in (group, "其他策略"):
            signal = "服务流量预计进入其他策略，需人工确认"
        elif code >= 500:
            signal = "HTTP 5xx：服务端或链路异常，不能单独归咎节点"
        elif 400 <= code < 500:
            signal = "HTTP 4xx：权限、地区或请求限制待确认"
        elif code == 0:
            signal = "无有效 HTTP 状态：仅凭导出记录无法判断原因"
        elif safe_observed != "未知" and safe_observed != predicted:
            signal = "记录策略与离线预计不同，可能是下游选路或规则差异"
        else:
            signal = "未观察到明确异常"
        findings[(group, predicted, safe_observed, status_range, signal)] += 1
    rows = [
        {"service": group, "predicted_policy": predicted,
         "recorded_policy": observed, "http_status": status,
         "finding": signal, "count": count}
        for (group, predicted, observed, status, signal), count in sorted(findings.items())
    ]
    return {
        "processed_requests": processed,
        "findings": rows,
        "privacy": "仅显示服务类别、允许名单策略、状态码段、问题类型与次数；"
                   "不显示原始域名、IP、路径、查询、节点、Cookie 或令牌。",
        "warning": "离线推演不等于 Loon 真机命中；HAR 的 _policy 不是标准 Loon 字段。"
                   "HTTP 状态或单次连通性也不能证明登录、播放与地区权限。"
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("coverage", "audit", "match", "logs", "triage"):
        subparser = sub.add_parser(name)
        subparser.add_argument("--json", action="store_true")
        if name == "match":
            subparser.add_argument("hostname_or_ip")
        if name in ("logs", "triage"):
            subparser.add_argument("file", type=Path)
            subparser.add_argument("--text", action="store_true",
                                   help="text log rather than HAR JSON")
    args = parser.parse_args()
    try:
        if args.command in ("logs", "triage"):
            if args.file.stat().st_size > MAX_LOG_SIZE:
                raise ValueError("log exceeds 10 MiB")
            data = args.file.read_bytes()
            result = (sanitized_log_summary(data, known_services(), text_mode=args.text)
                      if args.command == "logs" else
                      private_triage(data, known_services(), Router(), text_mode=args.text))
        else:
            router = Router()
            result = (coverage(router) if args.command == "coverage" else
                      candidate_coverage_audit(router) if args.command == "audit" else
                      router.match(args.hostname_or_ip))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except OSError:
        parser.exit(2, "无法读取输入文件；请检查路径、权限和文件大小。\n")
    except (ValueError, KeyError, UnicodeError):
        parser.exit(2, "无法分析输入或规则资料，请检查文件格式和命令参数。\n")


if __name__ == "__main__":
    main()
