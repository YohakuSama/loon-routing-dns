#!/usr/bin/env python3
"""Audit App Store icon candidates without silently replacing brand artwork.

Usage: python scripts/audit_appstore_icons.py
Requires: Python 3 standard library only.
Produces: appstore-icon-audit.json (not committed).
Review each candidate's app name, seller and country before approving artwork.
"""
import json
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRANDS = {
    "Google": "Google", "Microsoft": "Microsoft 365", "Apple": "Apple",
    "YouTube": "YouTube", "Netflix": "Netflix", "Disney": "Disney+",
    "PrimeVideo": "Amazon Prime Video", "Spotify": "Spotify",
    "TikTok": "TikTok", "Twitch": "Twitch", "HBO": "HBO Max",
    "Abema": "ABEMA", "AnimeCrazy": "動畫瘋", "Dazn": "DAZN",
    "BBC": "BBC iPlayer", "Bilibili": "bilibili",
    "Telegram": "Telegram Messenger", "Whatsapp": "WhatsApp Messenger",
    "Instagram": "Instagram", "Facebook": "Facebook",
    "Twitter": "X", "Discord": "Discord", "Line": "LINE",
    "Reddit": "Reddit", "Linkedin": "LinkedIn",
    "Steam": "Steam Mobile", "Paypal": "PayPal",
}
CUSTOM = ["Proxy", "Auto", "Fallback", "AdBlock", "Final", "AI"]
COUNTRIES = ["us", "cn", "jp", "tw", "gb"]
def lookup(term, country):
    query = urllib.parse.urlencode({"term": term, "entity": "software", "country": country, "limit": 8})
    request = urllib.request.Request("https://itunes.apple.com/search?" + query, headers={"User-Agent": "loon-routing-dns-icon-audit/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response)
    return [{"trackId": r.get("trackId"), "trackName": r.get("trackName"),
             "sellerName": r.get("sellerName"), "bundleId": r.get("bundleId"),
             "artworkUrl512": r.get("artworkUrl512"), "trackViewUrl": r.get("trackViewUrl")}
            for r in data.get("results", []) if r.get("artworkUrl512")]
def main():
    report = {"policy": "Candidates only; verify app identity, seller and artwork before replacing any icons.",
              "brand_candidates": {}, "custom_icons_keep_original": CUSTOM,
              "plugin_icon_keep_original": "Network Diagnostics"}
    for name, term in BRANDS.items():
        report["brand_candidates"][name] = {}
        for country in COUNTRIES:
            try:
                report["brand_candidates"][name][country] = lookup(term, country)
            except Exception as exc:
                report["brand_candidates"][name][country] = {"error": str(exc)}
            time.sleep(.12)
    target = ROOT / "appstore-icon-audit.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", target)
    print("Brand groups:", len(BRANDS), "Custom groups:", len(CUSTOM), "Plugin: 1")
    print("No icons were replaced; manual identity verification is required.")
if __name__ == "__main__":
    main()
