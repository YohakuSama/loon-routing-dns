# LoonKit 测速端点实测记录（2026-10-21）

本次在 GitHub Actions 的 Ubuntu 托管 Runner 上，使用 `curl` **不跟随重定向**、绕过 Runner 代理环境变量，对正式配置和插件使用的三个 `generate_204` 地址各请求两次，记录了：

| 用途 | 目标 | 第 1 次 | 第 2 次 |
| --- | --- | ---: | ---: |
| 配置的代理测速（含 Auto / Fallback） | `http://bing.com/generate_204` | **301** | **301** |
| 插件的代理网络检测 | `https://www.gstatic.com/generate_204` | **204** | **204** |
| 插件的直连网络检测 | `http://wifi.vivo.com.cn/generate_204` | **204** | **204** |

[查看此次 GitHub Actions 运行日志](https://github.com/YohakuSama/loonkit/actions/runs/39556464369)。

**结论与边界：** 301 表示在该 Runner 的网络中 URL 被重定向，不能据此认定 Loon 上的节点测速异常。Loon 可能使用不同网络路径或不同的重定向处理方式。使用者此前明确表示已在真机测试无问题，因此**保持上述三个配置地址完全不变**。

若以后真的出现 URL-Test / Fallback 选路异常，应优先收集 Loon 在受影响网络中的 HTTP 结果，再在独立的 PR 中评估是否替换测速端点；不要仅根据一次 GitHub Runner 的观测而更改已验收的正式配置。注意：测速端点当前可用不等于长期可用。

[维护说明](./MAINTAINING.md) · [真机验收记录](./DEVICE_TEST_STATUS.md)
