/* Loon Routing DNS project console v1.3. Non-mutating status view. */
(function () {
  "use strict";
  var args = typeof $argument === "object" && $argument ? $argument : {};
  var LAST_AUTO = "loon-routing-dns:diag:last-auto:v1";
  var LAST_MANUAL = "loon-routing-dns:diag:last-manual:v1";
  function read(k) {
    try {
      if (typeof $persistentStore === "undefined") return null;
      var x = JSON.parse($persistentStore.read(k) || "null");
      return x && typeof x === "object" ? x : null;
    } catch (e) { return null; }
  }
  function time(t) {
    if (!t || !isFinite(Number(t))) return "暂无记录";
    try { return new Date(Number(t)).toLocaleString("zh-CN", {hour12:false}); }
    catch (e) { return "时间不可用"; }
  }
  function trim(v) {
    return String(v == null ? "" : v).replace(/[\r\n\t\u0000-\u001f]/g," ").slice(0,100);
  }
  function domain(url) {
    // Do not expose private DoH URL path/query which can contain account tokens.
    var m = /^https?:\/\/([^\/?#]+)/i.exec(String(url || ""));
    return m ? trim(m[1]) : "未设置";
  }
  var lines = ["Loon Routing DNS 控制台 v1.4（开发版）", "━━━━━━━━━━━━━━━━━━"];
  lines.push("诊断模式："+(args.auto_check === false ? "仅手动" : "网络变化自动诊断开启"));
  lines.push("正常时通知："+(args.notify_every_change === true ? "开启（建议测试完关闭）" : "关闭，仅异常通知"));
  lines.push("DoH 测试目标："+domain(args.doh_url));
  lines.push("直连探测："+domain(args.direct_probe_url));
  lines.push("代理探测："+domain(args.proxy_probe_url));
  lines.push("探测超时："+trim(args.probe_timeout || "6500")+" ms");
  lines.push("节点详情目标："+trim(args.target_policy || "Proxy"));
  lines.push("IP 情报源："+domain(args.primary_ip_url));
  lines.push("备用情报源："+(args.enable_ip_backup === false ? "关闭" : domain(args.backup_ip_url)));
  lines.push("DIRECT 出口对照："+(args.compare_direct === true ? "开启（会暴露直连公网 IP）" : "关闭（隐私默认）"));
  lines.push("精确节点短时缓存："+trim(args.cache_seconds || "0")+" 秒");
  var auto = read(LAST_AUTO), manual = read(LAST_MANUAL);
  lines.push("━━━━━━━━━━━━━━━━━━","最近网络变化检测："+time(auto && auto.time));
  if (auto) lines.push("上次状态："+trim(auto.status || "未知")+"；"+trim(auto.kind || "未分类"));
  lines.push("最近手动网络检测："+time(manual && manual.time));
  if (manual) lines.push("上次状态："+trim(manual.status || "未知"));
  lines.push("━━━━━━━━━━━━━━━━━━");
  lines.push("修改参数：Loon → 插件 → 本控制台 → 参数");
  lines.push("运行脚本：「手动网络与 DNS 诊断」「节点详情查询」「已发布规则资源检查」「广告与隐私规则诊断」。");
  lines.push("测速 URL 仅影响控制台自己的检测，不修改 Loon 原生测速与节点选择。");
  lines.push("网络变化检测正常时默认无通知，可临时开启「每次网络变化都通知」。");
  lines.push("本控制台不更改 DNS、代理模式、VPN 状态或远程规则。");
  var report=lines.join("\n");
  console.log("[Loon Routing DNS Console] "+report);
  $done({title:"Loon Routing DNS 控制台",content:report});
})();