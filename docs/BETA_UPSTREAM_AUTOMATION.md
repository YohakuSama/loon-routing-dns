# 测试版自动上游更新

## 实际链路

.github/workflows/beta-upstream-update.yml 必须安装到默认分支 main，才能按周一 02:40 UTC（台北 10:40）定时运行。也支持选择 main 手动运行；仅在 beta 中存在的 YAML 不会形成独立的 GitHub 定时任务。

已通过 [PR #116](https://github.com/YohakuSama/loonkit/pull/116) 安装到 main。[2026-10-24 首次线上运行](https://github.com/YohakuSama/loonkit/actions/runs/40093458478)成功：来源完整，已比较 33 个实际 beta 服务组，本轮没有合格新增，未创建空 PR。首轮写入 job 被跳过，真实自动 PR 权限与 CI dispatch 仍需在首次合格增量出现时核实；事务和连续更新测试均通过，不冒充真实写入结果。

1. 只读 job checkout 精确 beta 版本，验证资源与回归。
2. 复用 upstream_review 解析器拉取现有 87 条来源，和当前 beta 的 33 个来源组比较；保留快照、UTC、HTTP ETag/Last-Modified、哈希、完整差异与风险报告。
3. 对来源完整、该组无损解析、无移除/共享设施/跨归属冲突、数量受限的精确 DOMAIN 新增做候选筛选。无关广告来源的已记录正则排除不会永久冻结一个无损的视频服务来源。
4. 与当前有效规则再比对：同组已有覆盖不重复添加，其他组已经拥有的主机隔离审阅。
5. 独立写 job 只运行 main 受信任代码，将实际新增编成累计的服务 overlay：先创建资源提交，再创建引用该 SHA 的配置、manifest、验收模板提交。
6. 创建唯一、可重复运行的 automation/beta-upstream-* 草稿 PR，目标 beta；不覆盖人工分支、不强推、不自动合并。
7. 显式 dispatch beta-ci.yml 检查该分支。GITHUB_TOKEN 创建的 PR 不会自然触发 pull_request Actions，不能省略这一步。
8. 维护者审查并合并 beta 后再观察；正式入口不自动跟随。

每轮生成结果保留已有服务的不可变引用，按确定次序插入累计 overlay，并同步下一轮审阅的来源组标签/数量。可复现生成器已覆盖连续三轮跨服务及同服务累计更新，避免“草稿已创建，但配置重建清空规则或回退版本”的死路。

没有合格新增时不创建空 PR。来源不完整会保留现役资源、上传证据并报告失败。广告、直连、AI、Apple、Microsoft、支付、宽后缀/IP/ASN、删除、异常数量与来源翻译不确定性继续需要审核。

## 权限和部署

默认分支的基础设施安装包括调度工作流、受信任的 beta_upstream_delivery.py / beta_github.py、其 REST 事务测试，以及供显式 dispatch 识别的 beta-ci.yml；不改变正式版的 .lcf、DNS、规则或图标。

只读 job 不携带写权限。写 job 具有 contents、pull-requests、actions 写权限，用途限定为测试版草稿 PR 和明确的 CI dispatch。仓库还必须允许 GitHub Actions 创建 PR；若 GitHub 返回权限错误，工作流明确失败，不能宣称已经完成自动 PR。

现有正式版周一只读审计保持独立。Beta 上的 beta-upstream-candidate.yml 继续提供手动/代码变更时的审阅产物，不负责默认分支调度，也不代替真正的草稿 PR 更新流程。

## 运行边界

- 运行版本不直接引用上游可变地址。
- 计划绑定准确 beta SHA、当前配置哈希、来源目录和 24 小时有效窗口；beta 已移动就拒绝发布。
- 不自动应用来源移除，也不重新引入已排除的 .cn、UA、证书误杀或 AI 共享接口。
- 正式发布仍受设备和观察门禁约束。
- CI 事务测试使用虚构主机，无测试规则会被推入真实运行配置。

## 本轮发布准备与下一轮 beta

发布候选 PR #119 没有修改或重新生成已验收的 beta 运行配置。独立冻结 v6.5.4 模板使得根目录正式入口升级之后，当前 beta 仍可确定性重建。发布基础设施只有合入 main 并同步 beta 后才算默认分支已生效；本段不冒充新的定时线上验证。下一次出现合格上游增量时仍必须验证资源先提交、配置后 pin 与准确 CI；此前首次实际运行没有触发写入 job。
