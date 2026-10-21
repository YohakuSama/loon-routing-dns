# LoonKit v6.0.0 维护流程

唯一正式入口：`LoonKit.lcf`。唯一发布规则目录：`rules/releases/vNext-RC2/`。正式策略图标统一存放于 `icons/v20261021r2/`，正式插件位于 `release/Network_Diagnostics.plugin`。已发布的旧固定提交 URL 保持可访问，旧文件不再出现在 `main` 的活动目录。

## 构建

`rules/inputs/`（33）+ `rules/custom/`（10）→ `build/engine_manifest.json` + `build/sources.lock.json` → `scripts/rule_engine.py` → 26 份正式规则。

执行：

```bash
python3 scripts/source_lock.py --check
python3 scripts/verify_release.py --check
python3 scripts/license_audit.py --check
python3 -m unittest discover -s tests -p 'test_production.py' -v
```

`scripts/upstream_review.py` 拉取公开上游来源、解析格式，在仓库**外**生成规范化候选、完整差异、来源快照和风险审阅报告。`rules-update.yml` 每周执行；`scripts/review_source.py` 与 `scripts/prepare_release.py` 保留为手动审核及冻结构建工具。`ci.yml` 校验正式资源和候选安全回归测试；正式发布仍需审核确认，不自动发布。

## 兼容性清理

维护者确认不再需要旧 DNSPod 完整配置、旧 v5 生成规则、ProxyProtect 和独立插件别名，已移除。原订阅这些已删除路径的用户会得到 404。现有标准配置引用的固定版本资源不变。

## Git 历史

正式规则固定引用 `9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4`；正式图标引用 `d9333b47b1a0361d911fc57e3dc5808683d416d5`，节点出口脚本仍引用 `97c48a5d14087597dbba35119d5ee8d43b1ce537`；正式插件引用 `5b115b5dd02836620597b2212b2b49c18c646bb7`。改写现有仓库历史前必须先迁移这些运行时 URL 到受保护的版本引用、验证全部资源并取得单独批准。历史改写不是普通文件删除。

## 网络诊断插件固定引用

主配置中的现役插件引用 `5b115b5dd02836620597b2212b2b49c18c646bb7` 的 `release/Network_Diagnostics.plugin`。诊断脚本引用 `af78ebb6b75bdbb341996db446d87cb2be719af4` 的 `scripts/v20261021r2/network-diagnostics.js`；节点出口脚本仍引用 `97c48a5d14087597dbba35119d5ee8d43b1ce537`，插件和各策略图标引用 `d9333b47b1a0361d911fc57e3dc5808683d416d5`。更新脚本时，应先提交版本化脚本，后提交固定脚本引用的插件，再更新正式配置中的插件提交号和 `build/release_manifest.json` 的 SHA256。不可将已发布脚本直接覆盖，也不可自动改写 DNS 或规则。


## 网络诊断脚本维护

现役诊断脚本版本为 `scripts/v20261021r2/network-diagnostics.js`，正式插件通过固定 Git Commit 引用它；旧脚本从主分支删除，但对应固定提交仍可通过历史访问，不重写已发布 Git 历史。对外诊断结论应区分连通性成功、DNS 解析成功和 DNS 传输协议元数据待确认。网络切换通知由 `$notification.post` 输出中文标题、摘要和正文；默认不启用。

## 新版 Git 历史

主线从无父提交的完整规则与图标资产开始，第二提交固定插件引用，第三提交固定正式配置。所有正式 Raw URL 均使用新历史中的祖先提交。以 `main` 为正式发布分支；功能验证过程中可以临时创建并合并 PR 分支。

## 上游候选的安全边界

质量判断分为三类：语法错误与格式不支持 → 标记来源不完整；语法合法但范围宽、涉及公共后缀/短关键字/广泛 IP 段 → 重点审阅；普通合法新增 → 常规审阅。风险高不等同语法无效，风险低不等于可自动发布。

正式规则上游审核附加 [完整安全规范](./RULE_SAFETY.md)。上游审阅除了全量新增/删除差异外，还必须输出每条新增的来源和具体风险、跨策略的 IPv4/IPv6 以及域名覆盖检查，防范 AdBlock 与登录/支付/CDN 误杀。所有候选 `*.list` 一律保留发布基线；未审核的匹配只允许存在于差异与风险 JSON 中。

每周任务下载上游快照，生成全量增删差异、规范化候选及跨策略冲突审阅报告。来源不可用、未知格式、规则数量不符均标记为不完整，不能当成可发布候选。只对同策略内的精确重复及被该策略 `DOMAIN-SUFFIX` 明确覆盖的 `DOMAIN` 作候选去重；不自动合并 IP 网段或把宽关键字猜测为精确域名。**所有来源变更均不自动修改正式规则、输入锁、策略归属或用户配置**；新规则发布需要审核与回归测试。

## 真机验收与测速端点

自动化 CI 不能证明真实网络上的测速网址始终返回 204。正式配置当前用 `http://bing.com/generate_204` 进行代理测速，插件另对 `https://www.gstatic.com/generate_204`（代理）与 `http://wifi.vivo.com.cn/generate_204`（直连）执行探测。**发布前要在 Loon 真机和至少两种网络环境下确认这些 URL 返回预期状态**；若返回重定向、门户页面或其他状态，先记录响应和运行环境，再在独立版本变更中替换，避免只凭某一时刻的网页抓取结果大范围改变测速行为。

插件的最低声明为 `3.5.1(983)`，而 `$dns.query` 需要 Build 988+，因此兼容性验收应分别覆盖插件加载、节点出口和 DNS 诊断。现有 `build/release_manifest.json` 的 `device_test` 仍为 `NOT_EXECUTED`，不应把 CI 绿灯描述为已完成真机验收。

## 完整上游审计（2026-10-21）

`upstream-live-audit.yml` 使用 GitHub Actions Runner 下载全部 87 个登记来源并生成审阅附件。V2Fly 的 `include:` 受递归深度、输入格式和仓库白名单约束，额外保留引用文件快照。`URL-REGEX` 与 V2Fly 主机名 `regexp:` 不会泛化成 `DOMAIN-SUFFIX`：当前 8 条表达式有明确排除来源、哈希和理由。`verify_upstream_coverage.py` 单独检查来源分类完整性与转换完整性；发布许可永远是另一个审核步骤。参见[审计结果](./UPSTREAM_COVERAGE_2026-10-21.md)。
