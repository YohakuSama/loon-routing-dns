# Phase 06 RC1 (UNRELEASED)

This directory documents the candidate acceptance gate. Run `python3 scripts/vnext_import_preflight.py`; CI pins `LoonKit.vNext.RC1.Test.lcf` to its own commit as an external artifact. No real device import is claimed. The public template has no private nodes. Do not publish subscriptions, credentials, server addresses or raw device logs.

## Engineering gate (2026-10-20)
Immutable tested source: `95b6e0eb02d3cc6e82fc8e6998dd130a2c5b7a98`.
Phase06 CI: https://github.com/YohakuSama/loonkit/actions/runs/39394995413 (SUCCESS).
Metadata-only follow-up CI: https://github.com/YohakuSama/loonkit/actions/runs/39395774426 (SUCCESS).
The 26 pinned raw GitHub resources passed actual HTTP GET and SHA256 verification in the immutable source CI.
The acceptance artifact is `vnext-rc1-immutable-maintainer-test` (artifact ID 12251641729).
Do not confuse the metadata HEAD with the pinned rule source commit.
Maintainer reported no obvious issues during everyday use; this is partial, unstructured observation only.
ENGINEERING_STATUS=SUCCESS for the tested source checks; DEVICE_VALIDATION=PARTIAL;
RELEASE_CANDIDATE_STATUS=READY_FOR_MAINTAINER_TEST; PRODUCTION_READINESS=NOT_READY.
Remaining release blockers are recorded in RELEASE_BLOCKERS.json and require explicit adjudication.
