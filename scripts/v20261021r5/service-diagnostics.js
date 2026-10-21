/* LoonKit optional manual reachability checks.
 * Two public endpoints through the selected policy; no runtime rule introspection.
 * HTTP response is transport evidence, not proof of login, streaming or region.
 */
(function () {
  "use strict";
  var catalog = {
    Spotify: ["open.spotify.com", "accounts.spotify.com"],
    Twitch: ["www.twitch.tv", "id.twitch.tv"],
    Abema: ["abema.tv", "api.abema.io"],
    BBC: ["www.bbc.com", "www.bbc.co.uk"],
    Line: ["line.me", "access.line.me"],
    Reddit: ["www.reddit.com", "oauth.reddit.com"],
    Linkedin: ["www.linkedin.com", "static.licdn.com"]
  };
  var args = typeof $argument === "object" && $argument ? $argument : {};
  var raw = typeof args.service === "undefined" ? "Spotify"
    : (typeof args.service === "string" ? args.service.trim() : "");
  var selected = Object.prototype.hasOwnProperty.call(catalog, raw) ? raw : null;
  var finished = false, results = [], index = 0;
  function done(content) {
    if (finished) return;
    finished = true;
    $done({title: "服务连通性诊断", content: content});
  }
  if (!selected) {
    done("不支持该服务。请在插件参数中选择列出的服务。");
    return;
  }
  function classify(error, response) {
    if (error) {
      var message = String(error.message || error).toLowerCase();
      if (/timeout|timed out/.test(message)) return "超时";
      if (/tls|ssl|certificat/.test(message)) return "TLS/证书失败";
      if (/dns|resolv|host/.test(message)) return "解析或连接失败";
      return "连接失败";
    }
    var status = Number(response && response.status);
    if (status >= 200 && status < 500) {
      return "HTTP " + status + "（端点已响应）";
    }
    if (status >= 500 && status < 600) {
      return "HTTP " + status + "（服务端或链路异常）";
    }
    return "响应状态未知";
  }
  function summary() {
    var responded = 0, failed = 0, server = 0;
    for (var i = 0; i < results.length; i++) {
      if (results[i].kind === "responded") responded++;
      else if (results[i].kind === "server") server++;
      else failed++;
    }
    var status = responded === 2 ? "两个端点都有 HTTP 响应"
      : responded ? "部分端点有响应，需进一步检查"
      : "未确认端点连通，需检查节点、DNS 与 Loon 日志";
    return selected + "（所选策略：" + selected + "）\n" + status +
      "\n主站：" + results[0].text +
      "\n关联端点：" + (results[1] ? results[1].text : "未完成检测") +
      "\n端点仅用于连通性参考，不读取实际规则命中；"
      + "HTTP 4xx、重定向或单个端点响应不代表登录、播放与地区权限正常。"
      + (failed || server ? "\n请结合 Loon 实际请求日志定位原因。" : "");
  }
  function probeNext() {
    if (finished) return;
    if (index >= 2) { done(summary()); return; }
    var step = index++;
    var url = "https://" + catalog[selected][step] + "/favicon.ico";
    var settled = false;
    try {
      $httpClient.get({
        url: url, node: selected, timeout: 7000,
        "auto-redirect": false, "auto-cookie": false, insecure: false
      }, function (error, response) {
        if (settled || finished) return;
        settled = true;
        var value = classify(error, response);
        var status = Number(response && response.status);
        results.push({
          kind: !error && status >= 200 && status < 500 ? "responded"
            : !error && status >= 500 && status < 600 ? "server" : "failed",
          text: value
        });
        probeNext();
      });
    } catch (error) {
      results.push({kind: "failed", text: "检测 API 调用失败"});
      probeNext();
    }
  }
  setTimeout(function () {
    if (finished) return;
    while (results.length < 2) results.push({kind: "failed", text: "检测未完成或超时"});
    done(summary());
  }, 18000);
  probeNext();
})();
