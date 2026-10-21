/* LoonKit · 手动服务检测。
 * 仅检查指定服务的两个 HTTPS 地址和本机 DNS 解析。
 * 不收集账号信息，不更改 Loon 配置，不自动执行。
 */
(function () {
  "use strict";
  var catalog = {
    "Spotify（音乐）": {policy:"Spotify", name:"Spotify 音乐", hosts:["open.spotify.com","i.scdn.co"]},
    "Twitch（直播）": {policy:"Twitch", name:"Twitch 直播", hosts:["www.twitch.tv","static.twitchcdn.net"]},
    "Abema（视频）": {policy:"Abema", name:"Abema 视频", hosts:["abema.tv","api.abema.io"]},
    "BBC（资讯）": {policy:"BBC", name:"BBC 资讯", hosts:["www.bbc.com","static.bbci.co.uk"]},
    "LINE（通讯）": {policy:"Line", name:"LINE 通讯", hosts:["line.me","access.line.me"]},
    "Reddit（社区）": {policy:"Reddit", name:"Reddit 社区", hosts:["www.reddit.com","www.redditstatic.com"]},
    "LinkedIn（职场）": {policy:"Linkedin", name:"LinkedIn 职场", hosts:["www.linkedin.com","static.licdn.com"]}
  };
  var args = (typeof $argument === "object" && $argument) || {};
  var selected = typeof args.service === "string" ? args.service.trim() : "";
  var item = Object.prototype.hasOwnProperty.call(catalog, selected) ? catalog[selected] : null;
  var finished = false, checks = [], dnsState = "pending", nextIndex = 0;
  function finish(title, content) {
    if (finished) return;
    finished = true;
    $done({title:title, content:content});
  }
  if (!item) {
    finish("服务检测", "请先在「网络辅助」设置中选择要检测的服务。");
    return;
  }
  function errorLabel(error) {
    var text = String(error && (error.message || error) || "").toLowerCase();
    if (/timed? ?out|timeout/.test(text)) return "连接超时";
    if (/certificat|tls|ssl/.test(text)) return "安全连接失败";
    if (/dns|resolv|host/.test(text)) return "连接失败";
    return "连接失败";
  }
  function httpLabel(error, response) {
    if (error) return {state:"failed", detail:errorLabel(error)};
    var status = Number(response && response.status);
    if (status >= 200 && status < 500)
      return {state:"ok", detail:"可连接"};
    if (status >= 500 && status < 600)
      return {state:"server", detail:"响应异常（HTTP " + status + "）"};
    return {state:"unknown", detail:"暂未确认"};
  }
  function render() {
    var first = checks[0] || {state:"unknown", detail:"检测未完成"};
    var second = checks[1] || {state:"unknown", detail:"检测未完成"};
    var failed = first.state === "failed" || second.state === "failed";
    var server = first.state === "server" || second.state === "server";
    var unclear = first.state === "unknown" || second.state === "unknown";
    var titleState = dnsState === "failed" ? "DNS 检查异常"
      : failed ? "部分连接失败"
      : server ? "服务响应异常"
      : unclear ? "检查未完成"
      : dnsState === "ok" ? "连接正常" : "已连接";
    var dnsLabel = dnsState === "ok" ? "正常"
      : dnsState === "failed" ? "解析失败"
      : dnsState === "noapi" ? "当前版本不支持检测"
      : "暂未确认";
    var lines = [
      "网站：" + first.detail,
      "相关资源：" + second.detail,
      "DNS 解析：" + dnsLabel
    ];
    if (dnsState === "failed")
      lines.push("建议：查看 Loon 的 DNS 日志，必要时重试。");
    else if (failed)
      lines.push("建议：检查所选策略的节点及 Loon 请求记录。");
    else if (server)
      lines.push("建议：稍后重试，并与其他节点对比。");
    else if (unclear)
      lines.push("建议：稍后重新检测。");
    return {title:"服务检测 · " + item.name + " · " + titleState, content:lines.join("\n")};
  }
  function maybeDone() {
    if (finished || checks.length !== 2 || dnsState === "pending") return;
    var out = render();
    finish(out.title, out.content);
  }
  function dnsProbe() {
    if (typeof $dns === "undefined" || !$dns || typeof $dns.query !== "function") {
      dnsState = "noapi";
      maybeDone();
      return;
    }
    var called = false;
    try {
      $dns.query({domain:item.hosts[0],protocol:"auto",timeout:6000},function(error,reply) {
        if (called || finished) return;
        called = true;
        if (error || !reply) dnsState = "failed";
        else {
          var answers = Array.isArray(reply.answers) ? reply.answers : [];
          dnsState = answers.some(function(record) {
            return record && (record.type === "A" || record.type === "AAAA") && record.value;
          }) ? "ok" : "unknown";
        }
        maybeDone();
      });
    } catch(ignore) {
      dnsState = "unknown";
      maybeDone();
    }
  }
  function httpNext() {
    if (finished) return;
    if (nextIndex >= 2) { maybeDone(); return; }
    var index = nextIndex++;
    var called = false;
    try {
      $httpClient.get({
        url:"https://" + item.hosts[index] + "/favicon.ico",
        node:item.policy, timeout:6500,
        "auto-redirect":false, "auto-cookie":false, insecure:false
      },function(error,response) {
        if (called || finished) return;
        called = true;
        checks.push(httpLabel(error,response));
        httpNext();
      });
    } catch(ignore) {
      checks.push({state:"failed",detail:"连接失败"});
      httpNext();
    }
  }
  setTimeout(function() {
    if (finished) return;
    while (checks.length < 2) checks.push({state:"unknown",detail:"检测超时"});
    if (dnsState === "pending") dnsState = "unknown";
    var out = render();
    finish(out.title,out.content);
  },19500);
  dnsProbe();
  httpNext();
})();
