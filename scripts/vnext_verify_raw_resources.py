#!/usr/bin/env python3
"""Verify every immutable RC raw GitHub URL via actual GET and SHA256."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://raw.githubusercontent.com/YohakuSama/loonkit/"
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--commit", required=True)
    p.add_argument("--json-out", type=Path, required=True)
    args = p.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        p.error("full immutable commit required")
    groups = json.loads((ROOT / "refactor/vnext/reports/phase05_diff.json").read_text())["remote_groups"]
    results = []
    for name, record in sorted(groups.items()):
        filename = ("AnimeCrazy" if name == "動畫瘋" else name) + ".list"
        url = BASE + args.commit + "/refactor/vnext/generated/" + filename
        item = {"group": name, "url": url, "expected_sha256": record["sha256"]}
        try:
            with urlopen(Request(url, headers={"User-Agent": "LoonKit-RC-Integrity/1.0"}), timeout=25) as response:
                payload = response.read(12 * 1024 * 1024)
                item["http_status"] = response.status
            item["actual_sha256"] = hashlib.sha256(payload).hexdigest()
            item["status"] = "PASS" if item["actual_sha256"] == record["sha256"] else "FAIL_HASH"
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            item["status"] = "NETWORK_UNAVAILABLE"
            item["error"] = str(exc)
        results.append(item)
    outcome = "PASS" if all(x["status"] == "PASS" for x in results) else "FAIL"
    args.json_out.write_text(json.dumps({"commit": args.commit, "result": outcome, "resources": results}, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"result": outcome, "checked": len(results), "statuses": {s: sum(x["status"] == s for x in results) for s in set(x["status"] for x in results)}}))
    if outcome != "PASS":
        raise SystemExit(1)
if __name__ == "__main__":
    main()
