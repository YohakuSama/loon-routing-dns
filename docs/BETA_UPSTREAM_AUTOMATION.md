# 测试版自动上游更新

## 实际链路

.github/workflows/beta-upstream-update.yml 必须安装到默认分支 main，才能按周一 02:40 UTC（台北 10:40）定时运行。也支持选择 main 手动运行；仅在 beta 中存在的 YAML 不会形成独立的 GitHub 定时任务。

1. 只读 job checkout 精确 beta 版本，验证资源与回归。
2. 复用 upstream_review 解析器拉取现有 87 条来源，和当前 beta 的 33 个来源组比较；保留快照、UTC、HTTP ETag/Last-Modified、哈希、完整差异与风险报告。
3. 对来源完整、该组无损解析、无移除/共享设施/跨归属冲突、数量受限的精确 DOMAIN 新增做候选筛选。无关广告来源的已记录正则排除不会永久冻结一个无损的视频服务来源。
4. 与当前有效规则再比对：同组已有覆盖不重复添加，其他组已经拥有的主机隔离审阅。
5. 独立写 job 只运行 main 受信任代码，将实际新增编成累计的服务 overlay：先创建资源提交，再创建引用该 SHA 的配置、manifest、验收模板提交。
6. 创建唯一、可重复运行的 automation/beta-upstream-* 草稿 PR，目标 beta；不覆盖人工分支、不强推、不自动合并。
7. 显式 dispatch beta-ci.yml 检查该分支。GITHUB_TOKEN 创建的 PR 不会自然触发 pull_request Actions，不能省略这一步。
8. 维护者审查并合并 beta 后再观察；正式入口不自动跟随。

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
