# LoonKit 测试渠道

当前正式版本为 v6.5.7，发展中的测试版为 v6.5.8-beta.1；准确版本、SHA 和资源身份以 build/beta_manifest.json 为准。

- 正式入口：https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf
- 测试入口：https://raw.githubusercontent.com/YohakuSama/loonkit/beta/beta/LoonKit.lcf
- 导入前备份个人节点与订阅；公共配置不包含私人节点或 DNS 凭据。

## 当前构建

测试版从 build/baselines/v6.5.7/LoonKit.lcf 与冻结的 foundation manifest 生成，初始有效指令和正式版一致。保留 AliDNS、LOOPBACKIP、GEOIP,CN,DIRECT,no-resolve、33 个策略组和 36 个远程资源。

routine 更新只叠加有来源的有限精确主机，先冻结资源提交，再 pin 配置。生成器保留已有 overlay、标签和数量，不能把下一轮更新退回旧 NOANSWER。版本 v6.5.5-beta.4 及其批准信息独立保存在 build/baselines/v6.5.5-beta.4/，不作为发展中 beta 的固定 SHA 要求。

```bash
python3 scripts/beta_channel.py --remote
python3 scripts/beta_effective_audit.py --output /tmp/beta-effective.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

现有 58 个静态样本与新增审计反例验证规则归属；它们不模拟设备 DNS/GeoIP、SNI/ECH、用户插件、实际节点地区或所有 App 功能。发展中的 beta 不继承历史真机使用反馈或本次正式发布请求。

## 广告开关与隐私

默认 AdBlock 为 REJECT，Proxy 表示经通用代理放行。恢复服务自己的路由时，关闭唯一的 Beta-AdBlock-Balanced 远程资源。OneSignal 通知 SDK 已放行；Cloudflare 统计脚本只按精确主机拦截，验证码等功能依赖保留。

DNS 回退与部分功能开关由 Loon App 控制，参阅 DNS_PRIVACY.md 和 LOON_APP_SETTINGS.md。未提供设备的故障回退/抓包记录，不能宣称零泄漏。

## 更新与回滚

默认分支上的上游调度比较 87 条来源和当前 beta 的 33 组有效基线。无合格增量不创建空 PR；高风险、删除、共享设施和直连规则继续人工审核。细节见 BETA_UPSTREAM_AUTOMATION.md。

发生问题可重新导入正式入口，或按 build/beta_history.json 与历史正式校验文档选择准确提交。正式发布检查和历史资源删除分开，历史 Git 对象、冻结输入与必要构建基线保留。
