/* LoonKit optional, manual-only service reachability probe.
 * It tests one public endpoint through the selected service policy.
 * It does not claim login, playback, geographic access or runtime rule hits.
 */
(function () {
  "use strict";
  var catalog = {
    Spotify: {host:"open.spotify.com", path:"/favicon.ico"},
    Twitch: {host:"www.twitch.tv", path:"/favicon.ico"},
    Abema: {host:"abema.tv", path:"/favicon.ico"},
    BBC: {host:"www.bbc.com", path:"/favicon.ico"},
    Line: {host:"line.me", path:"/favicon.ico"},
    Reddit: {host:"www.reddit.com", path:"/favicon.ico"},
    Linkedin: {host:"www.linkedin.com", path:"/favicon.ico"}
  };
  var args = typeof $argument === "object" && $argument ? $argument : {};
  var raw = typeof args.service === "string" ? args.service.trim() : "Spotify";
  var selected = Object.prototype.hasOwnProperty.call(catalog, raw) ? raw : null;
  var finished = false;
  function finish(msg) {
    if (finished) return;
    finished = true;
    $done({title:"服务连通性诊断",content:msg});
  }
  if (!selected) {
    finish("不支持该服务。请从 Spotify、Twitch、Abema、BBC、Line、Reddit、Linkedin 中选择。");
    return;
  }
  var service = catalog[selected];
  var url = "https://" + service.host + service.path;
  setTimeout(function () { finish("检测超时。请检查 Loon 的请求日志与所选策略。"); }, 13000);
  try {
    $httpClient.get({
      url:url, node:selected, timeout:8500,
      "auto-redirect":false, "auto-cookie":false
    }, function (error, response) {
      if (error) {
        var message = String(error.message || error).toLowerCase();
        var reason = /timeout|timed out/.test(message) ? "连接超时"
          : /tls|ssl|certificat/.test(message) ? "TLS/证书连接失败"
          : /dns|resolv|host/.test(message) ? "域名解析或连接失败"
          : "连接失败";
        finish(selected + "（策略：" + selected + "）\n" + reason +
          "\n建议检查对应节点、DNS 和 Loon 请求日志。");
        return;
      }
      var status = Number(response && response.status);
      if (status >= 200 && status < 500) {
        finish(selected + "（策略：" + selected + "）\nHTTP " + status +
          "：检测端点已返回响应。\n这不代表登录、播放或地区权限正常。" +
          (status >= 300 ? "\n重定向或访问限制需结合实际 App 判断。" : ""));
      } else if (status >= 500 && status < 600) {
        finish(selected + "（策略：" + selected + "）\nHTTP " + status +
          "：目标站点响应异常，不能据此认定节点故障。");
      } else {
        finish(selected + "（策略：" + selected + "）\n结果未知，请查看实际请求记录。");
      }
    });
  } catch (error) {
    finish(selected + "：检测调用失败，请检查 Loon 版本及插件运行环境。");
  }
})();