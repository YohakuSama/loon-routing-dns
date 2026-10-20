# LoonKit v6.0.0 — main publication verification

The maintainer instructed publication, and PR #39 was merged on 2026-10-20 at 12:51:29Z into commit `8e7b9a21fd2e230d4999d8f392dea860e69ebc91`.

- The two main Loon config URLs now return the v6.0.0 header and 26 Git-commit-pinned rules, with preserved per-profile General/DNS/DoH/TUN values.
- The legacy `rules/generated/` feed remains available unchanged. vNext source snapshots are segregated and locked; generated outputs do not feed back into the compiler.
- Current release assets are identical to the 26 reviewed, pinned RC2 rule blobs at commit `d405e4be28c447b6e57a4790e965c89f342d6dd6`. Config headers changed for versioning and their SHA256 values changed correspondingly.
- The phase07 engineering CI and disposable-main merge/rollback simulation were successful before publication. The post-merge main CI must be evaluated separately.
- The maintainer reports device testing with no observed problems, but no complete structured network/DNS/IPv6/region-unlock or cache-rollback evidence has been supplied. Those cells remain **NOT_EXECUTED**, not PASS.
- Full third-party license texts and historical origin catalogs are preserved. The precise reuse rights for mixed content and some icon assets have not been independently cleared; the license gate remains **BLOCKED_REVIEW**. This document does not certify legal clearance.
- GitHub Releases had no published release object or version tag at verification time; this is **publication to main and its existing raw subscription URLs**, not an independently created GitHub Release/Tag.
- The release gate status `PUBLISHED_WITH_OPEN_REVIEWS` is an explicit record of what happened, not permission to discard remaining limitations. The `--require-ready` command remains fail-closed for future merge requests without evidence.

## Confirmed import URLs

- https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf
- https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.PrivacyDNS.lcf

## Rollback

The prior main is `f19421933d2177f95e7537f1208d990b3094f1f4`. Use a normal reviewed revert PR (never force-reset main), restore the old device configuration/subscriptions and strategy selections, and refresh Loon remote resources and caches. See `release/phase-07/MIGRATION_ROLLBACK.md`.

This is a publication status record only; it does not replace third-party license obligations or device evidence.
