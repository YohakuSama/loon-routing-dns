/* Loon Routing DNS — published rule artifact health check v1.0.
 * Reads public GitHub tree metadata; does not inspect Loon's live rule hits.
 * No MITM, no direct-IP query, no configuration mutation.
 */
(function () {
  "use strict";
  var URL = "https://api.github.com/repos/YohakuSama/loon-routing-dns/git/trees/main?recursive=1";
  var expected = "DomesticCore AI AppleOTA SteamCN YouTube Netflix Disney PrimeVideo Spotify TikTok Twitch HBO Abema BBC Bilibili AnimeCrazy Dazn Telegram Whatsapp Instagram Facebook Twitter Discord Line Reddit Linkedin Google Microsoft Apple Steam Paypal AdBlock ChinaDirect".split(" ");
  var finished = false;
  function done(message) {
    if (finished) return;
    finished = true;
    console.log("[Rule Health] " + message);
    $done({title:"规则资源健康检查",content:message});
  }
  try {
    $httpClient.get({url:URL,node:"DIRECT",timeout:12000,
      headers:{"Accept":"application/vnd.github+json","User-Agent":"Loon-Routing-DNS"},
      "auto-cookie":false,"auto-redirect":false},function(err,response,body){
      if(err) return done("无法获取 GitHub 规则目录："+String(err).slice(0,100)+"\n请检查 DIRECT 网络及 GitHub API 连通性。");
      if(!response || response.status!==200) return done("GitHub API 返回 HTTP "+String(response&&response.status)+"。\n请稍后重试；可能遇到 API 限流。");
      var data;
      try { data=JSON.parse(body); } catch(e) {return done("GitHub API 返回内容无法解析。");}
      if(!data || !Array.isArray(data.tree) || data.truncated===true) return done("规则目录数据不完整，不能判定资源健康。");
      var files={};
      data.tree.forEach(function(item){
        if(item.type==="blob" && /^rules\/generated\/[^/]+\.list$/.test(item.path)) {
          files[item.path.slice("rules/generated/".length,-5)]=item.size;
        }
      });
      var missing=[],empty=[],small=[],total=0;
      expected.forEach(function(name){
        if(!Object.prototype.hasOwnProperty.call(files,name)) missing.push(name);
        else if(!Number.isFinite(files[name]) || files[name]===0) empty.push(name);
        else {total++;if(files[name]<40) small.push(name);}
      });
      var unexpected=Object.keys(files).filter(function(name){return expected.indexOf(name)<0;});
      var ok=!missing.length&&!empty.length&&!small.length;
      var lines=["检查目标：GitHub main 已发布规则文件（非 Loon 本地订阅状态）",
        "预期："+expected.length+" 组；存在且非空："+total+" 组",
        "缺失："+(missing.join(", ")||"无"),
        "空文件："+(empty.join(", ")||"无"),
        "异常偏小（<40B）："+(small.join(", ")||"无"),
        "其他规则文件："+(unexpected.join(", ")||"无"),
        "结论："+(ok?"远程文件结构检查通过":"存在需要检查的规则文件"),
        "注意：无法证明 Loon 已下载、规则命中正确或广告已被拦截。",
        "排查实际分流请使用 Loon 请求日志与远程规则更新状态。"];
      done(lines.join("\n"));
    });
  } catch(e) {done("规则目录检查未执行："+String(e).slice(0,100));}
})();
