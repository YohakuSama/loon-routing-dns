# Beta → main release preflight: fail closed

**No actual device acceptance evidence currently exists.** The versioned template
`docs/BETA_ACCEPTANCE_TEMPLATE.json` is intentionally **not** a successful
result. CI asserts that it remains blocked and runs synthetic unit fixtures.
The tests' mock successes are not Loon observations and authorize nothing.

After real testing, a maintainer makes a separately reviewed sanitized evidence
JSON file that records the **exact** imported beta commit, configuration SHA256,
matching CI run URL, 18 device-case results, 7 risk-review decisions,
first-boot observation start/end at least seven days apart, and the rollback
pointer to formal v6.5.4. No private DNS endpoint, node credentials, device ID,
full URL, HAR or token should enter that record.

To run locally:

```sh
python3 scripts/beta_promotion_gate.py --assert-template-blocked
python3 scripts/beta_promotion_gate.py --evidence /path/to/REDACTED_VERIFIED_ACCEPTANCE.json
```

The second command **must fail** until every required field is proven and
reviewed. Even if it returns
`PREFLIGHT_READY_REQUIRES_LIVE_GITHUB_APPROVAL_AND_PR`, that is only an
offline structural preflight. A maintainer must independently check the exact
CI run against GitHub, assess the sanitized device logs/observations and open
a distinct beta → main PR according to the repository's published gate.
Never merge on an unverified JSON boolean, and do not fetch upstream changes
during promotion.

**No write-to-main automation is included.** To roll back a beta test, import
the currently verified stable entry
`https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf`,
then restore the previously selected node/subscription. Prior pinned Git
resources and the last stable commit
`87ba3f50e80ba90212a0eeba7df223949f50e32b` remain intact.

Current version `v6.5.5-beta.3`: promotion **BLOCKED** until the real device
matrix and seven days of observations are complete. Full production redundant
resource cleanup is a **separate PR after stable release**, not a prerequisite
to this preflight.
