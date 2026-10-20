# LoonKit v6.0.0 维护流程

唯一正式入口：`LoonKit.lcf`。唯一发布规则目录：`rules/releases/vNext-RC2/`。正式图标和插件仍保留它们在配置里固定的 Git Raw URL 原路径。

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

当前仍引用固定提交 `d405e4be28c447b6e57a4790e965c89f342d6dd6`（规则和插件）以及 `95b6e0eb02d3cc6e82fc8e6998dd130a2c5b7a98`（图标及脚本）。改写现有仓库历史前必须先迁移这些运行时 URL 到受保护的版本引用、验证全部资源并取得单独批准。历史改写不是普通文件删除。
