#!/usr/bin/env python3
"""Validate the active historically verified profile and independent staged rules."""
from pathlib import Path
import re
import json
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "LoonKit.lcf"
CATALOG = ROOT / "rules/sources.json"
BASELINE = ROOT / "rules/verified-routing-baseline.json"
GENERATED = ROOT / "rules/generated"


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
    conf = CONFIG.read_text(encoding="utf-8")
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert conf.startswith("# LoonKit v5.10.0")
    assert not (ROOT / "Loon_Routing_DNS.lcf").exists(), "deprecated config must be removed"
    assert "dns-server = 223.5.5.5,223.6.6.6" in conf
    assert "doh-server = https://dns.alidns.com/dns-query" in conf
    assert "[Host]" not in conf, "DoH hostname mapping must not be forced"
    assert "ip-mode = dual" in conf and "ipv6-vif = auto" in conf

    plugin = active(section(conf, "Plugin"))
    assert len(plugin) == 1
    assert plugin[0].startswith(
        "https://raw.githubusercontent.com/YohakuSama/loonkit/main/plugins/v20261018r11/Network_Diagnostics.plugin,")

    groups = [line.split("=", 1)[0].strip() for line in active(section(conf, "Proxy Group"))
              if " = " in line]
    assert len(groups) == len(set(groups)) == 33
    assert "HelloBike" not in groups
    assert any(s.startswith("AdBlock = select,REJECT,")
               for s in active(section(conf, "Proxy Group")))

    remote = active(section(conf, "Remote Rule"))
    assert remote == baseline["remote_rules"], "active remote rules/order have drifted from working baseline"
    assert len(remote) == 28
    policies = set(groups) | {"DIRECT", "REJECT"}
    urls = set()
    for line in remote:
        match = re.fullmatch(
            r"(https://[^,]+),\s*policy=([^,]+),\s*tag=([^,]+),\s*enabled=true",
            line)
        assert match, "invalid remote rule: " + line
        url, policy, _ = match.groups()
        assert policy in policies
        parsed = urlparse(url)
        assert parsed.netloc == "raw.githubusercontent.com"
        assert parsed.path.startswith("/blackmatrix7/ios_rule_script/master/rule/Loon/")
        assert url not in urls
        urls.add(url)

    local = active(section(conf, "Rule"))
    guarded = json.loads((ROOT / "rules/routing_guardrails.json").read_text(encoding="utf-8"))["protected_proxy_domains"]
    protected = ["DOMAIN-SUFFIX," + domain + ",Proxy" for domain in guarded]
    assert len(protected) == 17
    assert local == protected + baseline["local_rules"], (
        "active local Proxy rules must exactly cover the protected domains before the baseline")
    assert len(local) == 66 + len(protected)
    assert local[-2:] == ["GEOIP,CN,DIRECT,no-resolve", "FINAL,Final"]
    assert any(x.startswith("DOMAIN-SUFFIX,openai.com,AI") for x in local)
    assert any(x.startswith("DOMAIN-SUFFIX,whatsapp.com,Whatsapp") for x in local)
    assert not any("jmssub.net" in line or "members/getsub.php" in line
                   for line in conf.splitlines()), "private subscription leaked into public config"

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    sources = [x for x in catalog["sources"] if x.get("enabled")]
    assert len(sources) == 87
    assert len({x["id"] for x in sources}) == len(sources)
    assert any(x["id"] == "local-hellobike" and x["group"] == "DomesticCore"
               and x["policy"] == "DIRECT" for x in sources)
    names = {x["group"].replace("動畫瘋", "AnimeCrazy") + ".list" for x in sources}
    assert len(names) == 33 and "HelloBike.list" not in names
    assert not any("/rules/generated/" in line for line in remote), "staged rule lists must not be enabled"
    if check_generated:
        actual = {p.name for p in GENERATED.glob("*.list")}
        assert actual == names, "unexpected staged rule file set"
        for name in names:
            assert (GENERATED / name).stat().st_size > 50, name
    assert not (ROOT / "reviews/LoonKit_Hybrid_Review.lcf").exists()
    print("PASS: v5.10.0 routing 28/66 + 17 protected-domain Proxy overrides, staged composite 33 lists, AliDNS baseline")


if __name__ == "__main__":
    import sys
    validate(check_generated="--generated" in sys.argv)
