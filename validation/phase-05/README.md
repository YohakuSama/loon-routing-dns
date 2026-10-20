# Phase 05 real-device acceptance package

This directory is a **test plan**, not proof of real-world Loon behavior. All status values start UNKNOWN/NOT_EXECUTED.

## Procedure
1. Freeze one refactor commit SHA and generate a copy of the candidate using `python3 scripts/vnext_pin_candidate.py --commit <FULL_SHA> --output /tmp/LoonKit.vNext.Pinned.lcf`. Never use a moving branch URL during acceptance.
2. Test HISTORICAL, PRODUCTION, and VNEXT on the same device, client version, network and node configuration.
3. Keep DNS/DoH/TUN, IPv4/IPv6 and transport settings identical. Restore each strategy selector state deliberately.
4. Record rule, selector, actual egress, resolver observations and masked logs. Unknown values stay UNKNOWN.
5. Run `python3 scripts/validate_device_results.py validation/phase-05/RESULT_TEMPLATE.json` after entering anonymized observations.
6. Compare each case with the corresponding old profile and vNext candidate; log behavior changes and any device-specific limitations.

Never upload private node subscriptions. The validator checks schema/evidence and does **not** run Loon or attest a PASS.
