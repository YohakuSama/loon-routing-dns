# v6.5.5 post-release cleanup

## Verified publication
- Release PR: https://github.com/YohakuSama/loonkit/pull/119
- Release main commit: `7c7ca4f67180437c962c3bc7eae07c6042e519d6`
- Immutable production configuration SHA256: `d97984a42e313e5b4fc81c26ce760fd4d1163275ad7278e3930cbce69dcf9f03`
- Tested beta configuration SHA256: `fd1a01c6f8363a5dffaa1db9dbf044014c711fa48ea46e34a7c107180acbe0b7`
- Post-merge successful production CI: https://github.com/YohakuSama/loonkit/actions/runs/40097998603

## Read-only inventory and archival proof
- Inventory: https://github.com/YohakuSama/loonkit/actions/runs/40098353235
- Verified all 11 historical fixed commit URLs with actual downloadable bytes and matching SHA256: https://github.com/YohakuSama/loonkit/actions/runs/40098505066
- Protected active resources: **36** (including all v6.5.5 formal rule URLs).
- No stable or beta profile directive, frozen source, release checksum, license or historical metadata is deleted.

## Deleted working-tree duplicates

Only the following retired historical working-tree copies were removed. Every path is preserved at its listed immutable commit URL with verified SHA256 and remains reachable by historical clients.

| Removed working-tree path | Archive SHA256 | Preserved rollback resource |
| --- | --- | --- |
| `rules/beta/v6.5.5-beta.1/RoutingAdBlock.list` | `712afa25c2ca6ec603bc296d195a6a82af01c1a58aea61ddcd6fceabb81320ab` | [fixed commit](https://raw.githubusercontent.com/YohakuSama/loonkit/26a24c86b58b133b2d094956f0f615680275a1b0/rules/beta/v6.5.5-beta.1/RoutingAdBlock.list) |
| `rules/beta/v6.5.5-beta.1/SteamCN.list` | `45e0ccb6848cf49773fddec26962c8508d692d778de6f47ce0cb29f5e6550526` | [fixed commit](https://raw.githubusercontent.com/YohakuSama/loonkit/26a24c86b58b133b2d094956f0f615680275a1b0/rules/beta/v6.5.5-beta.1/SteamCN.list) |
| `rules/beta/v6.5.5-beta.1/SteamGlobal.list` | `1a6e5296f61e91c30de8d978848cc918a7cb9a07ebc10cf42db7bd6e5a7b2a0f` | [fixed commit](https://raw.githubusercontent.com/YohakuSama/loonkit/26a24c86b58b133b2d094956f0f615680275a1b0/rules/beta/v6.5.5-beta.1/SteamGlobal.list) |
| `rules/beta/v6.5.5-beta.1/Service-Spotify.list` | `f25bd281e6b2c230ab54477a88355986d15cf4edce761507d502ddf576c1fcea` | [fixed commit](https://raw.githubusercontent.com/YohakuSama/loonkit/26a24c86b58b133b2d094956f0f615680275a1b0/rules/beta/v6.5.5-beta.1/Service-Spotify.list) |
| `rules/beta/v6.5.5-beta.1/Service-Twitch.list` | `c20e138ba791bd9b95d7bd0a7eb97502ce85067ffe7092f2618b29723fff8d32` | [fixed commit](https://raw.githubusercontent.com/YohakuSama/loonkit/26a24c86b58b133b2d094956f0f615680275a1b0/rules/beta/v6.5.5-beta.1/Service-Twitch.list) |
| `rules/beta/v6.5.5-beta.1/Service-BBC.list` | `fd77987c0a38f126ffded997e15012bb46e429cfb2d2137d6724153e6f731fb5` | [fixed commit](https://raw.githubusercontent.com/YohakuSama/loonkit/26a24c86b58b133b2d094956f0f615680275a1b0/rules/beta/v6.5.5-beta.1/Service-BBC.list) |
| `rules/beta/v6.5.5-beta.1/Service-Line.list` | `5ea83d6c33ffb66315878b761361499776d946e612cd838d7d2de04a87a64395` | [fixed commit](https://raw.githubusercontent.com/YohakuSama/loonkit/26a24c86b58b133b2d094956f0f615680275a1b0/rules/beta/v6.5.5-beta.1/Service-Line.list) |
| `rules/beta/v6.5.5-beta.1/Service-Reddit.list` | `aa66c24708a107bee9709c69e499c7b1f9f53e3a5c17dd9145078ca0d176f34f` | [fixed commit](https://raw.githubusercontent.com/YohakuSama/loonkit/26a24c86b58b133b2d094956f0f615680275a1b0/rules/beta/v6.5.5-beta.1/Service-Reddit.list) |
| `rules/beta/v6.5.5-beta.1/Service-Linkedin.list` | `efb9d832a9d6dd7a0268abe128fe7e2bff7cb988481b1bc65881fc00b7d5d34e` | [fixed commit](https://raw.githubusercontent.com/YohakuSama/loonkit/26a24c86b58b133b2d094956f0f615680275a1b0/rules/beta/v6.5.5-beta.1/Service-Linkedin.list) |
| `rules/beta/v6.5.5-beta.1/AIScoped.list` | `25869eeb05134296ea083f8d68095f7723a08dec25f1372ceb0a698a299d1e25` | [fixed commit](https://raw.githubusercontent.com/YohakuSama/loonkit/26a24c86b58b133b2d094956f0f615680275a1b0/rules/beta/v6.5.5-beta.1/AIScoped.list) |
| `rules/beta/v6.5.5-beta.3/ChinaDirect.list` | `bdeafed6ce861f1f72e1f891c798257687123a8f29867ae4e7a89b007001b68a` | [fixed commit](https://raw.githubusercontent.com/YohakuSama/loonkit/2f4980593843dbe28d4b983c309de6713913b8c9/rules/beta/v6.5.5-beta.3/ChinaDirect.list) |

## Explicitly retained
- Entire current `rules/beta/v6.5.5-beta.4/` used by main and beta.
- All original `rules/releases/vNext-RC2/`, frozen `rules/inputs/` and `rules/custom/` and v6.5.4 baseline template.
- `build/beta_history.json`, manifest and original device feedback, v6.5.2–v6.5.5 public checksums, rules/sources.json and all third-party license records.
- Stable/rollback commit URLs and standalone beta update channels.
