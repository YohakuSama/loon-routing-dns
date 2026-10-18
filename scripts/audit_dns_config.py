#!/usr/bin/env python3
"""Conservative static DNS configuration risk audit; not a DNS leak detector."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "Loon_Routing_DNS.lcf"


def section(text, name):
    match = re.search(r"(?m)^\[" + re.escape(name) + r"\]\s*$", text)
    if not match:
        raise ValueError("missing [" + name + "]")
    tail = text[match.end():]
    end = re.search(r"(?m)^\[[^]]+\]\s*$", tail)
    return tail[:end.start()] if end else tail


def inspect(text):
    settings = {}
    for raw in section(text, "General").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith(("#", ";")) or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        settings[key.strip().lower()] = value.strip()
    warnings = []
    doh = settings.get("doh-server", "")
    if not doh:
        warnings.append("No DoH server configured; encrypted DNS is not established by configuration")
    elif not all(x.strip().lower().startswith("https://") for x in doh.split(",")):
        warnings.append("DoH server includes a non-HTTPS endpoint")
    plain = settings.get("dns-server", "")
    if plain:
        warnings.append("Plain DNS fallback configured; verify actual resolver selection in Loon")
    hijack = settings.get("hijack-dns", "")
    if not hijack:
        warnings.append("No DNS hijack setting; external port 53 requests may bypass Loon")
    elif "*:53" not in [x.strip() for x in hijack.split(",")]:
        warnings.append("DNS hijack is not global for port 53")
    bypass = settings.get("bypass-tun", "")
    if bypass and any(x.strip() in ("0.0.0.0/0", "::/0") for x in bypass.split(",")):
        warnings.append("Default route bypasses TUN; review routing")
    return warnings


def main():
    text = CONFIG.read_text(encoding="utf-8")
    warnings = inspect(text)
    print("DNS static risk audit (configuration only; cannot prove DNS leaks)")
    for warning in warnings:
        print("REVIEW:", warning)
    print("PASS: configuration parsed; %d review item(s)" % len(warnings))


if __name__ == "__main__":
    main()
