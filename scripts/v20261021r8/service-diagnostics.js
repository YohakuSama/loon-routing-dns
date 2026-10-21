/* LoonKit · 节点服务可用性检测。
 * 所有请求使用本次检测的同一节点；不通过服务策略组分别选路。
 * 无需账号，不读取或发送任何私人数据。网页可访问不等于播放解锁。
 */
(function () {
  "use strict";
  var services = [
    {name:"Netflix",url:"https://www.netflix.com/title/81280792",kind:"netflix"},
    {name:"Disney+",url:"https://www.disneyplus.com/",kind:"disney"},
    {name:"YouTube Premium",url:"https://www.youtube.com/premium",kind:"youtube"},
    {name:"Prime Video",url:"https://www.primevideo.com/",kind:"prime"},
    {name:"Spotify",url:"https://www.spotify.com/",kind:"spotify"},
    {name:"TikTok",url:"https://www.tiktok.com/",kind:"tiktok"},
    {name:"ChatGPT",url:"https://chatgpt.com/",kind:"chatgpt"},
    {name:"Gemini",url:"https://gemini.google.com/",kind:"gemini"},
    {name:"Claude",url:"https://claude.ai/",kind:"claude"},
    {name:"Abema",url:"https://abema.tv/",kind:"abema"},
    {name:"BBC iPlayer",url:"https://www.bbc.co.uk/iplayer",kind:"bbc"},
    {name:"Twitch",url:"https://www.twitch.tv/",kind:"twitch"},
    {name:"LINE",url:"https://line.me/",kind:"line"},
    {name:"Reddit",url:"https://www.reddit.com/",kind:"reddit"},
    {name:"LinkedIn",url:"https://www.linkedin.com/",kind:"linkedin"}
  ];
  var args = (typeof $argument === "object" && $argument) || {};
  var ctx = (typeof $environment === "object" && $environment && $environment.params) || {};
  var info = ctx.nodeInfo && typeof ctx.nodeInfo === "object" ? ctx.nodeInfo : {};
  function nonempty(x) { return typeof x === "string" && x.trim() ? x.trim() : ""; }
  var route = nonempty(ctx.node) || nonempty(info.name) || nonempty(info.tag) ||
    nonempty(ctx.policyGroup) || nonempty(args.target_policy) || "Proxy";
  var completed = false, next = 0, active = 0, finished = 0;
  var results = new Array(services.length);
  function done(data) {
    if (completed) return;
    completed = true;
    $done(data);
  }
  if (route.length > 200 || /[\u0000-\u001f\u007f]/.test(route)) {
    done({title:"服务检测",content:"节点或策略名称无效。"});
    return;
  }
  var displayRoute = route.length > 72 ? route.slice(0,72) + "…" : route;
  function judge(service, error, response, body) {
    if (error) return "failed";
    var status = Number(response && response.status);
    var content = typeof body === "string" ? body.slice(0,120000).toLowerCase() : "";
    // Only explicit messages are considered regional restrictions.
    var denied = /(?:not available|unavailable|not supported|unsupported|blocked|restricted)\s+(?:in|for)\s+(?:your|this)\s+(?:country|region|location)|(?:country|region)\s+(?:is\s+)?(?:not supported|unsupported)|unsupported_country|geo.?blocked|geo.?restricted/.test(content);
    if (denied) return "restricted";
    if (status === 451) return "restricted";
    if (status === 200 && service.kind === "netflix" &&
        /(?:81280792|netflix\.com\/title)/.test(content) &&
        /netflix/.test(content)) return "likely";
    if (status === 200 && service.kind === "youtube" &&
        /(?:ispremiumavailable|is_premium_available)["']?\s*:\s*true/.test(content))
      return "likely";
    if (status >= 200 && status < 400) return "reachable";
    if (status === 403 || status === 429 || status >= 500 || !status) return "unknown";
    return "unknown";
  }
  function render() {
    var groups = {likely:[],reachable:[],restricted:[],failed:[],unknown:[]};
    services.forEach(function(service,i) {
      groups[results[i] || "unknown"].push(service.name);
    });
    var lines = ["节点/策略：" + displayRoute];
    if (groups.likely.length) lines.push("地区可能可用：" + groups.likely.join("、"));
    if (groups.reachable.length) lines.push("网页可访问：" + groups.reachable.join("、"));
    if (groups.restricted.length) lines.push("地区受限：" + groups.restricted.join("、"));
    if (groups.failed.length) lines.push("连接失败：" + groups.failed.join("、"));
    if (groups.unknown.length) lines.push("暂无法判断：" + groups.unknown.join("、"));
    lines.push("", "网页检测不代表账号、播放或完整地区解锁。");
    return {title:"节点服务检测",content:lines.join("\n")};
  }
  function pump() {
    if (completed) return;
    if (finished === services.length) { done(render()); return; }
    while (!completed && active < 4 && next < services.length) {
      (function(index) {
        var service = services[index], called = false;
        active++;
        try {
          $httpClient.get({
            url:service.url,node:route,timeout:6800,
            "auto-redirect":false,"auto-cookie":false,insecure:false
          },function(error,response,body) {
            if (called || completed) return;
            called = true;
            results[index] = judge(service,error,response,body);
            active--;
            finished++;
            pump();
          });
        } catch(ignore) {
          if (!called) {
            called = true;
            results[index] = "failed";
            active--;
            finished++;
          }
        }
      })(next++);
    }
    if (finished === services.length) done(render());
  }
  setTimeout(function () {
    if (completed) return;
    done(render());
  },33000);
  pump();
})();