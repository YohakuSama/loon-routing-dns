# LoonKit v6.3.5 维护流程

唯一正式入口：`LoonKit.lcf`。自 v6.1.0 起的 62 条补充规则记录在 `rules/service_coverage_v6.1.0.json`，随主配置分发；26 份历史固定规则未被覆盖。v6.3.0 的历史发布由 `publish-v63.yml` 处理；v6.3.5 当前配置在主分支更新，尚未宣称真机验收，旧版 `publish-v6.yml` 在活动版本变化后不再更新历史 v6.0.0 Release。唯一发布规则目录：`rules/releases/vNext-RC2/`。正式策略图标统一存放于 `icons/v20261021r1/`，正式插件位于 `release/Network_Diagnostics.plugin`。已发布的旧固定提交 URL 保持可访问，旧文件不再出现在 `main` 的活动目录。

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

正式规则固定引用 `9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4`；正式图标引用 `97c48a5d14087597dbba35119d5ee8d43b1ce537`；当前正式插件引用 `eaf6353713f10551e50ebb0c50bf8905d2e0c9f3`。改写现有仓库历史前必须先迁移这些运行时 URL 到受保护的版本引用、验证全部资源并取得单独批准。历史改写不是普通文件删除。

## 网络诊断插件固定引用

主配置中的现役插件引用 `eaf6353713f10551e50ebb0c50bf8905d2e0c9f3` 的 `release/Network_Diagnostics.plugin`。诊断脚本引用 `01e8a70ba5f7c6fe8c14ad79a1f3eba643ec801d` 的 `scripts/v20261021r3/network-diagnostics.js`；节点出口脚本引用 `db05de1c1df0648d999bf96aab292fd50dc02419`，原有插件图标仍引用 `97c48a5d14087597dbba35119d5ee8d43b1ce537`，手动服务检测脚本引用 `34ce1d17c460f503d28dd29896ae92466f7c778b` 的 `scripts/v20261021r12/media-unlock.js`。更新脚本时，应先提交版本化脚本，后提交固定脚本引用的插件，再更新正式配置中的插件提交号和 `build/release_manifest.json` 的 SHA256。不可将已发布脚本直接覆盖，也不可自动改写 DNS 或规则。


## 服务检测脚本与用户文案

当前只维护一个「网络辅助」插件；解锁检测作为第三个手动入口，一次检测所选节点。无需选择具体服务。请求必须通过检测节点或用户指定的策略发出，采用并发和总超时保护。地区限制、地区识别、超时与不确定结果均要有独立回归测试。用户可见提示优先回答当前状态和下一步操作，不显示非必要的原始协议代码、IP 地址或节点凭据。

更新脚本时先写入新的版本化目录，后更新插件固定脚本 SHA，最后更新正式配置中的插件 SHA 和 `build/release_manifest.json` 的校验值。使用包含全部固定资源提交的合并方式，避免压缩合并后资源 SHA 不在 `main` 历史内。历史版本的 Release 与其固定脚本 URL 不修改。

## 网络诊断脚本维护

现役网络诊断脚本版本为 `scripts/v20261021r3/network-diagnostics.js`，正式插件通过固定 Git Commit 引用它；旧脚本从主分支删除，但对应固定提交仍可通过历史访问，不重写已发布 Git 历史。对外诊断结论应区分连通性成功、DNS 解析成功和 DNS 传输协议元数据待确认。网络切换通知由 `$notification.post` 输出中文标题、摘要和正文；默认不启用。

## 新版 Git 历史

主线从无父提交的完整规则与图标资产开始，第二提交固定插件引用，第三提交固定正式配置。所有正式 Raw URL 均使用新历史中的祖先提交。以 `main` 为正式发布分支；功能验证过程中可以临时创建并合并 PR 分支。

## 上游候选的安全边界

质量判断分为三类：语法错误与格式不支持 → 标记来源不完整；语法合法但范围宽、涉及公共后缀/短关键字/广泛 IP 段 → 重点审阅；普通合法新增 → 常规审阅。风险高不等同语法无效，风险低不等于可自动发布。

正式规则上游审核附加 [完整安全规范](./RULE_SAFETY.md)。上游审阅除了全量新增/删除差异外，还必须输出每条新增的来源和具体风险、跨策略的 IPv4/IPv6 以及域名覆盖检查，防范 AdBlock 与登录/支付/CDN 误杀。所有候选 `*.list` 一律保留发布基线；未审核的匹配只允许存在于差异与风险 JSON 中。

每周任务下载上游快照，生成全量增删差异、规范化候选及跨策略冲突审阅报告。来源不可用、未知格式、规则数量不符均标记为不完整，不能当成可发布候选。只对同策略内的精确重复及被该策略 `DOMAIN-SUFFIX` 明确覆盖的 `DOMAIN` 作候选去重；不自动合并 IP 网段或把宽关键字猜测为精确域名。**所有来源变更均不自动修改正式规则、输入锁、策略归属或用户配置**；新规则发布需要审核与回归测试。

## 服务分流和诊断验证边界

现役网络辅助插件包含手动服务检测，引用主线历史已存在的固定提交。新增服务规则仅涉及经审阅的域名后缀，未直接引入上游的宽关键字、共享平台 IP 网段或用户代理规则。自动化执行规则、日志隐私、固定引用、哈希及发布校验；跨网络、真实账号、内容播放和地区限制仍由使用者另行验证，不能把 GitHub CI 视为真机测试结果。

## 真机验收与测速端点

自动化 CI 不能证明真实网络上的测速网址始终返回 204。正式配置当前用 `http://bing.com/generate_204` 进行代理测速，插件另对 `https://www.gstatic.com/generate_204`（代理）与 `http://wifi.vivo.com.cn/generate_204`（直连）执行探测。**发布前要在 Loon 真机和至少两种网络环境下确认这些 URL 返回预期状态**；GitHub Runner 实测中 Bing 的 HTTP 地址两次返回 301，插件的 Gstatic 与 Vivo 两次返回 204，详见 [测速记录](./PROBE_ENDPOINTS_2026-10-21.md)。使用者确认真机正常，所以保留所有现有测速 URL；只在真实客户端出现问题并有证据时单独评估替换。

插件的最低声明为 `3.5.1(983)`，而 `$dns.query` 需要 Build 988+，因此兼容性验收应分别覆盖插件加载、节点信息和 DNS 诊断。历史用户反馈与新版自动化结果分开记录，参见 [真机反馈记录](./DEVICE_TEST_STATUS.md)。

## 完整上游审计（2026-10-21）

`upstream-live-audit.yml` 使用 GitHub Actions Runner 下载全部 87 个登记来源并生成审阅附件。V2Fly 的 `include:` 受递归深度、输入格式和仓库白名单约束，额外保留引用文件快照。`URL-REGEX` 与 V2Fly 主机名 `regexp:` 不会泛化成 `DOMAIN-SUFFIX`：当前 8 条表达式有明确排除来源、哈希和理由。`verify_upstream_coverage.py` 单独检查来源分类完整性与转换完整性；发布许可永远是另一个审核步骤。参见[审计结果](./UPSTREAM_COVERAGE_2026-10-21.md)。

## 对外发布文案规范

公开页面（README、GitHub Release、版本更新记录、About）应首先说明产品功能、安装方法、实际更新和用户需要了解的限制。**内部流程和审核证据应放在维护文档，而不是在版本介绍中陈述自我验证过程或维护者的个别要求。**

例如图标文件的版本锁、CI 与真机验收证据、上游解析异常及暂不采用的规则数量，都应放在对应的依赖、审核或测试记录中；只有影响用户安装、兼容性或已知功能的事项才写入 Release。许可证文本、第三方归属与必要的法律声明仍正常保留在许可专页。

`docs/RELEASE_NOTES_v6.0.0.md` 是 v6.0.0 Release 的唯一文案源。发布工作流只在通过 Production CI 且现有 Tag、正式配置附件核对一致时同步正文，**不修改 Tag 或附件**。CI 的 `tests/test_public_copy.py` 会检查常见维护过程措辞，不能替代对公开文案的人工审阅。
