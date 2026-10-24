# 测试版有效分流审计

scripts/beta_effective_audit.py 从实际 beta/LoonKit.lcf 读取本地、固定插件与全部远程来源，使用不可变资源的实际字节验证 manifest。

当前配置保留 4 条本地域名规则、36 个固定远程资源、一个不包含拦截规则的网络辅助插件。58 个独立预期样本覆盖广告开关、关键功能反例、国内补充、AI/共享 API、Steam 和现有各服务。

    python3 scripts/beta_effective_audit.py --output /tmp/beta-effective.json

- 单个 Beta-AdBlock-Balanced 资源关闭时，Spotify/Facebook 等依照服务规则，而不是强制 DIRECT。
- crl.microsoft.com、ocsp.godaddy.com 不再命中 AdBlock。
- 共享 Google APIs 跟随 Google；通用 Statsig/LiveKit 不再被全数标为 AI。
- 微信国内已知目标保持直连，两个国际父域不再无条件直连。
- Apple 更新/证书规则跟随 Apple 策略组。
- 索引实现与独立朴素匹配器交叉检查；同一资源内展示的匹配细节不声称完全复制 Loon 内部数据结构。

本工具不会采集或上传访问日志，不解析 DNS，不模拟 SNI/ECH、GeoIP/ASN、真实 IP/Fake IP、当前用户节点选择和其他安装插件。报告是离线预测，不能作为零泄漏或所有功能已通过的证据。
