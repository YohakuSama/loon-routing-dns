# LoonKit v6.0.0 维护流程

唯一正式入口：`LoonKit.lcf`。唯一发布规则目录：`rules/releases/vNext-RC2/`。正式图标仍保留固定 Git Raw URL；网络辅助插件更新时使用新的固定版本路径，旧插件路径保留兼容。

## 构建

`rules/inputs/`（33）+ `rules/custom/`（10）→ `build/engine_manifest.json` + `build/sources.lock.json` → `scripts/rule_engine.py` → 26 份正式规则。

执行：

```bash
python3 scripts/source_lock.py --check
python3 scripts/verify_release.py --check
python3 scripts/license_audit.py --check
python3 -m unittest discover -s tests -p 'test_production.py' -v
```

`scripts/review_source.py` 只生成上游差异；`scripts/prepare_release.py` 只在工作区外生成新候选。GitHub Actions 的 `ci.yml` 校验正式资源，`rules-update.yml` 生成上游审核附件，`release.yml` 供人工准备发布候选；不自动推送发布。

## 兼容性清理

维护者确认不再需要旧 DNSPod 完整配置、旧 v5 生成规则、ProxyProtect 和独立插件别名，已移除。原订阅这些已删除路径的用户会得到 404。现有标准配置引用的固定版本资源不变。

## Git 历史

正式配置中的规则、图标及脚本固定引用 `9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4`；插件本体固定引用 `a2409b2d470e36ad0fa92f1fe424c37ae9543927`。改写现有仓库历史前必须先迁移这些运行时 URL 到受保护的版本引用、验证全部资源并取得单独批准。历史改写不是普通文件删除。

## 网络诊断插件固定引用

主配置中的现役插件引用 `a43e28aff0a4512964f5bbed7c7d8112bd856d0f` 的 `release/phase-08/assets/Network_Diagnostics.plugin`。插件内的网络与 DNS 诊断引用 `080a60897afd24c8c3c9387c25500615a6ec4145` 的 `scripts/v20261021r1/network-diagnostics.js`；节点出口脚本和图标仍固定引用 `9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4`。更新脚本时，应先提交版本化脚本，后提交固定脚本引用的插件，再更新正式配置中的插件提交号和 `build/release_manifest.json` 的 SHA256。不可将已发布脚本直接覆盖，也不可自动改写 DNS 或规则。


## 网络诊断脚本维护

现役诊断脚本版本为 `scripts/v20261021r1/network-diagnostics.js`，正式插件通过固定 Git Commit 引用它；旧脚本保留以免破坏旧固定 URL。对外诊断结论应区分连通性成功、DNS 解析成功和 DNS 传输协议元数据待确认。网络切换通知由 `$notification.post` 输出中文标题、摘要和正文；默认不启用。

## 新版 Git 历史

主线从无父提交的完整规则与图标资产开始，第二提交固定插件引用，第三提交固定正式配置。所有正式 Raw URL 均使用新历史中的祖先提交。当前公开分支仅保留 `main`。
