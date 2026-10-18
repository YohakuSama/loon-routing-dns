#!/usr/bin/env python3
"""Offline review safety and complete-config lint; independent of old v4.4.8 validator."""
from pathlib import Path
import re
import json
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "Loon_Routing_DNS.lcf"
BASE = ROOT / "releases" / "v4.4.8" / "Loon_Routing_DNS.lcf"
CATALOG = ROOT / "rules" / "sources.json"
GENERATED = ROOT / "rules" / "generated"

def section(body, name):
    match = re.search(r"(?m)^\[" + re.escape(name) + r"\]\s*$", body)
    assert match, "missing " + name
    tail = body[match.end():]
    end = re.search(r"(?m)^\[[^\]]+\]\s*$", tail)
    return tail[:end.start()] if end else tail

def active(body):
    return [line.strip() for line in body.splitlines()
            if line.strip() and not line.lstrip().startswith("#")]

def validate(check_generated=False):
    original = BASE.read_text(encoding="utf-8")
    conf = CONFIG.read_text(encoding="utf-8")
    assert conf.startswith("# Loon Routing DNS v5.1.0")
    assert section(conf, "General") == section(original, "General"), "DNS/general changed unexpectedly"
    plugin = active(section(conf, "Plugin"))
    assert len(plugin) == 1
    assert plugin[0].startswith(
        "https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/plugins/v20261018r4/Network_Diagnostics.plugin,")
    assert section(conf, "Remote Proxy") == section(original, "Remote Proxy"), "personal proxies not preserved"
    groups = [line.split("=",1)[0].strip() for line in active(section(conf, "Proxy Group"))
              if " = " in line]
    assert len(groups) == len(set(groups)) == 33, f"strategy group count {len(groups)}"
    assert "HelloBike" not in groups
    assert any(s.startswith("AdBlock = select,REJECT,") for s in active(section(conf, "Proxy Group")))
    remote = active(section(conf, "Remote Rule"))
    assert len(remote) == 33
    urls = set()
    policies = set(groups) | {"DIRECT", "REJECT"}
    for line in remote:
        match = re.fullmatch(r"(https://[^,]+),\s*policy=([^,]+),\s*tag=([^,]+),\s*enabled=true", line)
        assert match, "invalid remote line: " + line
        u, policy, _ = match.groups()
        assert policy in policies
        assert urlparse(u).netloc == "raw.githubusercontent.com"
        assert urlparse(u).path.startswith(
            "/YohakuSama/loon-routing-dns/main/rules/generated/"
        )
        assert u not in urls, "duplicate rule source: " + u
        urls.add(u)
        if check_generated:
            local = GENERATED / u.rsplit("/", 1)[-1]
            assert local.is_file() and local.stat().st_size > 50, str(local)
    assert all(not u.startswith("https://raw.githubusercontent.com/blackmatrix7") for u in urls)
    local = active(section(conf, "Rule"))
    assert local == [
        "DOMAIN-SUFFIX,raw.githubusercontent.com,Proxy",
        "GEOIP,CN,DIRECT,no-resolve",
        "FINAL,Final",
    ], "duplicate local service rules or lost final routing"
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    sources = [x for x in catalog["sources"] if x.get("enabled")]
    assert len(sources) == 87
    assert len({x["id"] for x in sources}) == len(sources)
    assert any(x["id"] == "local-hellobike" and x["group"] == "DomesticCore"
               and x["policy"] == "DIRECT" for x in sources)
    names = {x["group"].replace("動畫瘋", "AnimeCrazy") + ".list" for x in sources}
    assert "HelloBike.list" not in names
    assert names == {u.rsplit("/", 1)[-1] for u in urls}, "staged output group not referenced"
    if check_generated:
        actual = {p.name for p in GENERATED.glob("*.list")}
        assert actual == names, "orphaned generated rule files"
    # Reviewed routing must match. Versions of icons and plugin URLs can vary.
    reviewer = (ROOT / "reviews" / "Loon_Routing_DNS_Hybrid_Review.lcf").read_text(encoding="utf-8")
    assert section(conf, "Remote Rule") == section(reviewer, "Remote Rule"), "review routing order diverged"
    assert active(section(conf, "Rule")) == active(section(reviewer, "Rule")), "review local routing diverged"
    print("PASS: 87 sources, 33 generated service groups, all self-hosted, General/DNS unchanged")

if __name__ == "__main__":
    import sys
    validate(check_generated="--generated" in sys.argv)
