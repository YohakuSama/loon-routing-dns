# Phase 06 RC1 — engineering freeze and handoff

Date: 2026-10-20
Branch: `refactor/loonkit-vnext`
Status: **ENGINEERING_CHECKS_PASS / DEVICE_VALIDATION_PARTIAL / PRODUCTION_NOT_READY**

## Immutable candidate evidence

- Candidate source commit: `95b6e0eb02d3cc6e82fc8e6998dd130a2c5b7a98`
- Source CI: https://github.com/YohakuSama/loonkit/actions/runs/39394995413 (SUCCESS)
- 26 pinned remote rule resources: CI HTTP GET + SHA256 PASS 26/26.
- 197765 remote rule entries across 26 resources; 33 policy groups; 106 local rules, as recorded in `RC_MANIFEST.json`.
- Maintainer test artifact: `vnext-rc1-immutable-maintainer-test` (artifact ID `12251641729`), from source CI.
- Latest integrity-report CI: https://github.com/YohakuSama/loonkit/actions/runs/39397572028 (SUCCESS).
- Pinned remote rule URLs are immutable; auxiliary icons and plugin still reference `main`. Do not claim full dependency immutability.

## Device observation

Maintainer reported no obvious problems during everyday use. This is unstructured preliminary feedback, not a structured Loon import transcript or domain-by-domain validation. Never infer dedicated DNS leak, egress, IPv4/IPv6, advertising, or service-routing PASS from this observation.

## Open release gates

1. `RC-NODES`: public test profile deliberately omits private subscriptions. Keep secrets local.
2. `RC-IMPORT`: no structured Loon import evidence; daily-use feedback is positive but limited.
3. `RC-DNS`: no controlled resolver / egress comparison on a real device.
4. `RC-OVERLAPS`: 7331 non-equivalent parent/child observations; require representative runtime checks, not 7331 individual manual tests.
5. `RC-FINAL`: `FINAL,Final` uses a selectable policy group whose `DIRECT` option may cause unintended direct routing. The risk is conditional, **not** an assertion that the current configuration unconditionally uses `FINAL,DIRECT`.

## Release and rollback

- Do not modify `main`, production `.lcf` profiles, or production generated rules as part of this freeze.
- Do not create a release, promote RC1 to production, or claim full device acceptance.
- Preserve `release-candidate/phase-06/ROLLBACK_PLAN.md` and `RELEASE_BLOCKERS.json`.
- Phase 06 engineering work can be handed off; unresolved runtime checks remain explicit release gates for the next phase or maintainer acceptance.
