# LoonKit 测速端点实测记录（2026-10-21）

以下结果来自 2026-10-21 GitHub Actions Ubuntu Runner 的两轮 `curl` 请求（未跟随重定向，排除 Runner 代理环境变量）：

| 用途 | 目标 | 第 1 次 | 第 2 次 |
| --- | --- | ---: | ---: |
| 配置的代理测速（含 Auto / Fallback） | `http://bing.com/generate_204` | **301** | **301** |
| 插件的代理网络检测 | `https://www.gstatic.com/generate_204` | **204** | **204** |
| 插件的直连网络检测 | `http://wifi.vivo.com.cn/generate_204` | **204** | **204** |

[查看此次 GitHub Actions 运行日志](https://github.com/YohakuSama/loonkit/actions/runs/39556464369)。

**结果说明**：`bing.com` 地址在该 Runner 网络下返回 HTTP 301；其他两个地址返回 HTTP 204。实际设备可能采用不同网络路径及重定向处理方式，因此这些观测用于排查参考，正式探测地址保持不变。

若后续出现 URL-Test 或 Fallback 异常，可先收集受影响网络中的 Loon 请求记录，再通过独立 PR 评估端点调整。

[维护说明](./MAINTAINING.md) · [真机验收记录](./DEVICE_TEST_STATUS.md)
