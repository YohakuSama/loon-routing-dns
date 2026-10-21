# v6.0.0 配置文件的 SHA256 校验

[获取 v6.0.0 Release 配置](https://github.com/YohakuSama/loonkit/releases/download/v6.0.0/LoonKit.lcf)

原始版本附件的配置哈希已与 GitHub Release API 返回的文件摘要核对：

```text
00a5a313d7bca674286e545569edacf31b1b44bcacb3bacd10d293a71c7f124e  LoonKit.lcf
```

将 `LoonKit.lcf` 和仓库提供的 [可直接使用的 SHA256SUMS](../release/SHA256SUMS.v6.0.0) 下载到**同一文件夹**，运行：

```bash
sha256sum -c SHA256SUMS.v6.0.0
```

原先 v6.0.0 Release 中的 `SHA256SUMS` 附件记录了构建时的 `release-output/` 路径。哈希值本身正确，但直接在下载目录运行 `sha256sum -c SHA256SUMS` 会提示文件路径找不到。此仓库内的可移植校验文件解决这一问题；未来发布工作流改成只记录文件名 `LoonKit.lcf`，防止再次出现路径前缀。

此修复不影响已经发布的 v6.0.0 配置、Tag、原图标和固定规则。GitHub Release 的**原始附件仍保留**；本文不会误称它已被替换。
