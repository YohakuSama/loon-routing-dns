/* LoonKit · manual seven-service diagnostics in the existing network plugin.
 * HTTPS and Loon-native DNS observations, never login/playback/geo validation.
 * No credentials, cookies, redirects, TLS bypass or automatic background checks.
 */
(function () {
  "use strict";
  var services = {
    Spotify: ["open.spotify.com", "i.scdn.co", "播放与账号"],
    Twitch: ["www.twitch.tv", "static.twitchcdn.net", "直播与登录"],
    Abema: ["abema.tv", "api.abema.io", "播放与地区"],
    BBC: ["www.bbc.com", "static.bbci.co.uk", "iPlayer 与地区"],
    Line: ["line.me", "access.line.me", "消息与登录"],
    Reddit: ["www.reddit.com", "www.redditstatic.com", "登录与社区操作"],
    Linkedin: ["www.linkedin.com", "static.licdn.com", "账号与动态"]
  };
  var options = typeof $argument === "object" && $argument ? $argument : {};
  var wanted = typeof options.service === "undefined" ? "Spotify" :
    (typeof options.service === "string" ? options.service.trim() : "");
  var service = Object.prototype.hasOwnProperty.call(services, wanted) ? wanted : "";
  var finished = false, http = [], dnsText = "DNS：未检查", dnsReady = false;
  var step = 0, dnsDomain;
  function finish(message) {
    if (finished) return;
    finished = true;
    $done({title: "服务诊断", content: message});
  }
  if (!service) {
    finish("请选择插件设置中列出的服务。");
    return;
  }
  dnsDomain = services[service][0];
  function reason(error) {
    var text = String(error && (error.message || error) || "").toLowerCase();
    if (/timeout|timed out/.test(text)) return "超时";
    if (/certificat|tls|ssl/.test(text)) return "TLS/证书错误";
    if (/dns|resolv|host/.test(text)) return "解析或连接失败";
    return "连接失败";
  }
  function classify(error, response) {
    if (error) return {kind:"failed", text:reason(error)};
    var status = Number(response && response.status);
    if (status >= 200 && status < 400)
      return {kind:"reachable", text:"可连接（HTTP " + status + "）"};
    if (status >= 400 && status < 500)
      return {kind:"reachable", text:"有响应（HTTP " + status + "，仅是检测地址的结果）"};
    if (status >= 500 && status < 600)
      return {kind:"server", text:"HTTP " + status + "（对端异常，不能判定节点故障）"};
    return {kind:"unknown", text:"HTTP 响应未确认"};
  }
  function render() {
    var failed = http.some(function(x){return x.kind==="failed";});
    var server = http.some(function(x){return x.kind==="server";});
    var unknown = http.some(function(x){return x.kind==="unknown";});
    var summary = failed ? "部分连接失败，请核对 DNS、节点和 Loon 请求日志"
      : server ? "收到服务器异常响应，不能判定节点故障"
      : unknown ? "连通性尚未确认"
      : "两个 HTTPS 端点均有响应";
    var lines = [
      service + " · " + summary,
      "主站：" + http[0].text,
      "关联服务：" + http[1].text,
      dnsText
    ];
    lines.push("仅检测连接，" + services[service][2] + "请在 App 内验证。");
    if (failed) lines.push("网络相关故障需结合 Loon 请求/DNS 日志确认，无法直接检测 UDP。");
    return lines.join("\n");
  }
  function maybeDone() {
    if (finished || http.length !== 2 || !dnsReady) return;
    finish(render());
  }
  function nativeDns() {
    if (typeof $dns === "undefined" || !$dns || typeof $dns.query !== "function") {
      dnsText = "DNS：当前版本不支持原生查询（Build 988+）";
      dnsReady = true; maybeDone(); return;
    }
    var called = false;
    try {
      $dns.query({domain:dnsDomain, protocol:"auto", timeout:6000}, function (error, reply) {
        if (called || finished) return;
        called = true;
        if (error || !reply) {
          dnsText = "DNS：查询失败（请查看 DNS 日志）";
        } else {
          var answers = Array.isArray(reply.answers) ? reply.answers : [];
          var a = 0, aaaa = 0;
          answers.forEach(function(item) {
            if (item && item.value && item.type === "A") a++;
            if (item && item.value && item.type === "AAAA") aaaa++;
          });
          dnsText = a + aaaa > 0 ?
            "DNS：有解析结果（A " + a + " / AAAA " + aaaa + "）" :
            "DNS：未收到 A/AAAA 记录";
        }
        dnsReady = true; maybeDone();
      });
    } catch (ignore) {
      dnsText = "DNS：当前环境不支持此项查询";
      dnsReady = true; maybeDone();
    }
  }
  function next() {
    if (finished) return;
    if (step >= 2) { maybeDone(); return; }
    var index = step++;
    var called = false;
    try {
      $httpClient.get({
        url:"https://" + services[service][index] + "/favicon.ico",
        node:service, timeout:6500,
        "auto-redirect":false, "auto-cookie":false, insecure:false
      }, function (error, response) {
        if (called || finished) return;
        called = true;
        http.push(classify(error, response));
        next();
      });
    } catch (ignore) {
      http.push({kind:"failed", text:"请求接口不可用"});
      next();
    }
  }
  setTimeout(function() {
    if (finished) return;
    while (http.length < 2) http.push({kind:"unknown", text:"检测超时"});
    if (!dnsReady) {dnsText = "DNS：查询未完成";dnsReady = true;}
    finish(render());
  }, 19500);
  nativeDns();
  next();
})();
