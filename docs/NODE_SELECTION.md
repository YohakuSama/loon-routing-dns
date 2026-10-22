# 节点选择与自动故障切换

LoonKit 使用原有的 `Proxy`、`Auto` 和 `Fallback` 三个策略组。用户可以在不修改分流规则的情况下，按照自己的订阅规模调整候选节点。

## 策略组逻辑

| 策略组 | 选择方式 | 适合的场景 |
| --- | --- | --- |
| `Proxy` | 手动选择单节点、`Auto` 或 `Fallback` | 按服务或使用习惯固定线路 |
| `Auto` | `url-test`，定期在候选节点中选延迟最低者 | 日常自动选路 |
| `Fallback` | `fallback`，按候选列表顺序取首个可用节点 | 主线路与备用线路有明确优先级 |

`Fallback` 是按可用性、**不是按延迟排名**选择节点。若要自动选择低延迟节点，请在 `Proxy` 中使用 `Auto`。

## 多订阅节点池

配置包含三个节点筛选器，而没有增加任何策略组：

- `ALL_Filter`：完整节点列表，用于手动选择。
- `Auto_Filter`：`Auto` 自动测速候选列表。
- `Fallback_Filter`：`Fallback` 有序主备候选列表。

三个筛选器默认匹配全部节点，确保导入任何机场订阅后不会因为未知命名规则而丢失节点。**默认状态不会自动剔除慢节点，也不会减少首次扫描数量。** 对于每个订阅含数十个节点的用户，可在 Loon「配置 → 筛选节点」中调整 `Auto_Filter` 和 `Fallback_Filter`，保留适合自己网络的节点；`ALL_Filter` 仍可用于访问完整列表。官方提供 `NodeSelect` 手动筛选、`NameKeyword` 和 `NameRegex` 等方式。

建议让 `Auto` 候选集合覆盖不同线路提供商和地区，避免只剩一条故障域；`Fallback` 则选择少量具有明确优先顺序的可靠主备线路。实际筛选应依据节点的真机稳定性及服务可用性，不应根据未知机场通用地排除特定名称。

## 测速参数

| 参数 | 配置 | 作用 |
| --- | --- | --- |
| `proxy-test-url` | `http://cp.cloudflare.com/generate_204` | Loon 原生节点列表测速 |
| 自动策略 `url` | 同上 | 统一 Auto 与 Fallback 的探测目标 |
| `Auto interval` | 900 秒 | 定期优选，降低大量节点下的检测频率 |
| `Auto tolerance` | 80 毫秒 | 避免微小延迟差引起频繁切换 |
| `Fallback interval` | 900 秒 | 定期检查备用节点可用性 |
| `Fallback max-timeout` | 1800 毫秒 | 超过阈值的节点不列为可用候选 |
| `test-timeout` | 5 秒 | 原生测速超时上限 |

测速 URL 使用 [Loon 官方配置文档](https://nsloon.app/docs/General/)中的例子。该地址的实际响应仍可能因用户所在网络和节点出口不同而变化；延迟数据不能直接代表视频播放速度或所有网站的连接质量。切换测速地址之前，建议对同一节点、同一网络重复测量并比较结果。

**重要：** 900 秒是定时检测间隔，而非请求耗时。对上百节点的用户，延长间隔可以减少周期性探测量，但每轮仍可能测试候选列表中的全部节点。故障切换时效和高峰测试负载需要在真实 Loon 设备中核对。

参考：[Loon 节点筛选](https://nsloon.app/docs/Node/nodefilter/) · [Loon 策略组](https://nsloon.app/docs/Policy/policygroup/) · [维护指南](./MAINTAINING.md)
