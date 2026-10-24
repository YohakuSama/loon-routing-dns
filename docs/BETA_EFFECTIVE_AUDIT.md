# Effective routing precedence and targeted block validation

Status: **static domain simulation only; Loon device has not been tested**.
CI executes `scripts/beta_effective_audit.py` against **all actually referenced** local
and immutable remote list files, plus the pinned diagnostics plugin. It checks exact
Git commit URL refs and beta overlay checksums. The plugin has scripts only, no
`[Rule]`/`[Host]`/`[Rewrite]` sections. Unlisted personal third-party plugins
can invalidate this model; no user traffic or credentials are read.

Usage outside checkout:

```sh
python3 scripts/beta_effective_audit.py --output /tmp/loonkit-effective.json
python3 -m unittest tests/test_beta_effective_audit.py -v
```

The report emits `verified_synthetic_routes` for 15 known-risk domains and
includes independent naïve-membership cross-checks of all referenced subscriptions.
The `loon_adblock_disabled` prediction skips **both** AdBlock subscriptions,
not just the primary one and not by selecting DIRECT. Precise matches for Apple
OCSP, Microsoft login, Spotify, Meta telemetry, Copilot, domestic/TLD fallback,
Steam global families and mainland CDN are asserted.

**Open risks are deliberately not converted into guessed fixes:**

- `tenant-unknown.apis.google.com` may still match an AI-owned Google APIs suffix.
  It is shared infrastructure, not evidence that every tenant belongs to AI.
- `wechat.com`, `wechatapp.com`, `servicewechat.com` still match historical direct
  rules with unknown physical deployment/registration. Need more than the brand
  to change policy safely.
- `configuration.apple.com` and other AppleOTA includes are not simply firmware
  downloads: the 82 frozen rules include cert/service endpoints. Do not
  drop them without system-functional evidence.

The report intentionally does not decide Loon's exact internal tie-breaking for
multiple same-owner matching strings, SNI/ECH visibility, DNS-vs-IP matches,
CDN geolocation, UDP, user-added plugin routing or policy-group UI selections.
CI passing does not confirm these runtime effects or guarantee zero misblocking.
