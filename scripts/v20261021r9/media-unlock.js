/* LoonKit · 节点流媒体及 AI 地区检测
 * 手动运行；同一节点、有限并发、严格总超时。
 * 只根据服务专用接口/内容信号报告地区状态；HTTP 200 不等于解锁。
 */
(function () {
  "use strict";
  var args = (typeof $argument === "object" && $argument) || {};
  var context = (typeof $environment === "object" && $environment && $environment.params) || {};
  var nodeInfo = context.nodeInfo && typeof context.nodeInfo === "object" ? context.nodeInfo : {};
  function chosen(x) { return typeof x === "string" && x.trim() ? x.trim() : ""; }
  var node = chosen(context.node) || chosen(nodeInfo.name) || chosen(nodeInfo.tag) ||
    chosen(context.policyGroup) || chosen(args.target_policy) || "Proxy";
  var full = args.full_scan === true || args.full_scan === "true";
  var start = Date.now(), ended = false, cursor = 0, running = 0, count = 0;
  var services = [
    {id:"netflix",name:"Netflix",group:"流媒体"},
    {id:"disney",name:"Disney+",group:"流媒体"},
    {id:"youtube",name:"YouTube Premium",group:"流媒体"},
    {id:"spotify",name:"Spotify",group:"流媒体"},
    {id:"tiktok",name:"TikTok",group:"流媒体"},
    {id:"chatgpt",name:"ChatGPT",group:"AI"},
    {id:"gemini",name:"Gemini",group:"AI"},
    {id:"claude",name:"Claude",group:"AI"}
  ];
  if (full) services = services.concat([
    {id:"prime",name:"Prime Video",group:"流媒体"},
    {id:"apple",name:"Apple 地区",group:"其他"},
    {id:"bili_hk",name:"Bilibili 港澳台",group:"其他"},
    {id:"bili_cn",name:"Bilibili 大陆",group:"其他"},
    {id:"bbc",name:"BBC iPlayer",group:"其他"},
    {id:"abema",name:"Abema",group:"其他"}
  ]);
  var results = new Array(services.length);
  function finish(payload) {
    if (ended) return;
    ended = true;
    $done(payload);
  }
  if (node.length > 200 || /[\u0000-\u001f\u007f]/.test(node)) {
    finish({title:"解锁检测",content:"节点名称无效"});
    return;
  }
  function text(body) { return typeof body === "string" ? body.slice(0,150000) : ""; }
  function status(r) { return Number(r && r.status) || 0; }
  function region(v) {
    var c = String(v || "").toUpperCase();
    return /^[A-Z]{2,3}$/.test(c) ? c : "";
  }
  function tag(kind, detail) { return {kind:kind,detail:detail || ""}; }
  function value(kind, detail) {
    var labels = {
      available:"地区可用",limited:"仅部分可用",blocked:"地区受限",
      region:"地区识别",unknown:"未确认",failed:"连接失败"
    };
    return (labels[kind] || "未确认") + (detail ? " · " + detail : "");
  }
  function request(method,url,body,cb) {
    if (ended) return;
    var settled = false;
    var opts = {
      url:url,node:node,timeout:3200,
      "auto-cookie":false,"auto-redirect":false,insecure:false,
      headers:{"Accept-Language":"en-US,en;q=0.8","User-Agent":"Mozilla/5.0 (compatible; LoonKit/1.0)"}
    };
    if (method === "POST") {
      opts.body=body || "";
      opts.headers["Content-Type"]="application/json";
    }
    try {
      var client = method === "POST" ? $httpClient.post : $httpClient.get;
      client.call($httpClient,opts,function(err,response,data){
        if (settled || ended) return;
        settled = true;
        cb(err || null, response || {}, text(data));
      });
    } catch(e) {
      if (!settled && !ended) {
        settled = true;
        cb(e,null,"");
      }
    }
  }
  function get(url,cb) { request("GET",url,"",cb); }
  function deny(s) {
    return /unsupported_country|not available in your (?:country|region)|not supported in your (?:country|region)|forbidden.location|inSupportedLocation["']?\s*:\s*false/i.test(s);
  }
  function countryFrom(s,pattern) {
    var m = text(s).match(pattern);
    return m ? region(m[1]) : "";
  }
  function traceLoc(s) { return countryFrom(s,/^loc=([A-Za-z]{2})\s*$/m); }
  function countryDetail(code) { return code ? code : ""; }
  function run(service, cb) {
    var id=service.id, completed=false;
    function settle(k,d) { if (completed) return; completed=true; cb(tag(k,d)); }
    if (id === "netflix") {
      var titles=[0,0],errors=0,seen=0;
      ["81280792","70143836"].forEach(function(film,index) {
        get("https://www.netflix.com/title/"+film,function(err,r,b) {
          titles[index] = err ? -1 : status(r);
          if (err) errors++;
          seen++;
          if (seen < 2) return;
          if (titles.some(function(x){return x===200 || x===301;})) settle("available","片库");
          else if (titles[0]===404 && titles[1]===404) settle("limited","仅自制剧（推测）");
          else if (titles.some(function(x){return x===403 || x===451;})) settle("blocked","");
          else settle(errors===2?"failed":"unknown","");
        });
      });
    } else if (id === "disney") {
      // Only affirmative fields/anonymous-region errors count; a successful homepage load never counts.
      get("https://www.disneyplus.com/",function(err,r,b) {
        if (err) return settle("failed","");
        if (status(r)===451 || deny(b) || /\/(?:unavailable|preview)(?:\/|$)/i.test(String(r.url||"")))
          return settle("blocked","");
        var supported=/"inSupportedLocation"\s*:\s*(true|false)/i.exec(b);
        var country=countryFrom(b,/"countryCode"\s*:\s*"([A-Za-z]{2})"/i) ||
          countryFrom(b,/"region"\s*:\s*"([A-Za-z]{2})"/i);
        if (supported) return settle(supported[1].toLowerCase()==="true"?"available":"blocked",country);
        // A country on the generic landing page is only a location hint.
        settle(country?"region":"unknown",country);
      });
    } else if (id === "youtube") {
      get("https://www.youtube.com/premium?hl=en",function(err,r,b) {
        if (err) return settle("failed","");
        if (deny(b)) return settle("blocked","");
        var code=countryFrom(b,/"GL"\s*:\s*"([A-Za-z]{2})"/) ||
          countryFrom(b,/"countryCode"\s*:\s*"([A-Za-z]{2})"/);
        var premium=/"browseId"\s*:\s*"SPunlimited"/i.test(b) ||
          /(?:youtube premium|ad.free) is available/i.test(b);
        if (status(r)===200 && premium) settle("available",countryDetail(code));
        else settle(code?"region":"unknown",countryDetail(code));
      });
    } else if (id === "spotify") {
      get("https://www.spotify.com/api/content/v1/country-selector?platform=web&format=json",function(err,r,b) {
        if (err) return settle("failed","");
        if (status(r)===451 || deny(b)) return settle("blocked","");
        var code=countryFrom(b,/"countryCode"\s*:\s*"([A-Za-z]{2})"/i);
        if (!code) {
          var loc=String(r.url||"").match(/spotify\.com\/([a-z]{2})(?:[-/]|$)/i);
          code=loc ? region(loc[1]) : "";
        }
        settle(status(r)===200 && code ? "available":"unknown",code);
      });
    } else if (id === "tiktok") {
      get("https://www.tiktok.com/cdn-cgi/trace",function(err,r,b) {
        if (err) return settle("failed","");
        if (status(r)===451) return settle("blocked","");
        var code=traceLoc(b);
        // CDN trace identifies region, not playback. Never convert it into "unlocked".
        settle(code?"region":"unknown",code);
      });
    } else if (id === "chatgpt") {
      var parts=["未确认","未确认"],remaining=2;
      function collect(i,k) {
        parts[i]=k;
        if (--remaining!==0) return;
        if (parts[0]==="地区受限" || parts[1]==="地区受限") settle("blocked","Web / iOS："+parts.join(" / "));
        else if (parts[0]==="可用" && parts[1]==="可用") settle("available","Web + iOS");
        else settle("unknown","Web / iOS："+parts.join(" / "));
      }
      get("https://api.openai.com/compliance/cookie_requirements",function(err,r,b) {
        if (err) return collect(0,"连接失败");
        if (deny(b)) return collect(0,"地区受限");
        // A successful cookie-policy API response is not proof of account access.
        collect(0,status(r)===200 && (/^\s*\{/.test(b))?"可用":"未确认");
      });
      get("https://ios.chat.openai.com/",function(err,r,b) {
        if (err) return collect(1,"连接失败");
        var lower=b.toLowerCase();
        if (/disallowed isp|have been blocked|unsupported_country/.test(lower)) return collect(1,"地区受限");
        collect(1,lower.indexOf("request is not allowed. please try again later.")>=0?"可用":"未确认");
      });
    } else if (id === "gemini") {
      get("https://gemini.google.com/",function(err,r,b){
        if (err) return settle("failed","");
        if (status(r)===451 || deny(b)) return settle("blocked","");
        var code=countryFrom(b,/,2,1,200,"([A-Z]{3})"/);
        var disabled={CHN:1,RUS:1,BLR:1,CUB:1,IRN:1,PRK:1,SYR:1,HKG:1,MAC:1};
        settle(code ? (disabled[code]?"blocked":"region") : "unknown",code);
      });
    } else if (id === "claude") {
      get("https://claude.ai/cdn-cgi/trace",function(err,r,b) {
        if (err) return settle("failed","");
        if (status(r)===451) return settle("blocked","");
        var code=traceLoc(b);
        // Trace can be reachable even when the application is blocked.
        settle(code?"region":"unknown",code);
      });
    } else if (id === "prime") {
      get("https://www.primevideo.com/",function(err,r,b){
        if (err) return settle("failed","");
        if (/"isServiceRestricted"\s*:\s*true/i.test(b) || status(r)===451) return settle("blocked","");
        var code=countryFrom(b,/"currentTerritory"\s*:\s*"([A-Za-z]{2})"/i);
        settle(code && /"isServiceRestricted"\s*:\s*false/i.test(b)?"available":code?"region":"unknown",code);
      });
    } else if (id === "apple") {
      get("https://gspe1-ssl.ls.apple.com/pep/gcc",function(err,r,b){
        var code=region(b.trim());
        settle(!err && status(r)===200 && code.length===2?"region":err?"failed":"unknown",code);
      });
    } else if (id === "bili_hk" || id === "bili_cn") {
      var query=id==="bili_hk" ?
        "avid=18281381&cid=29892777&qn=0&type=&otype=json&ep_id=183799&fourk=1&fnver=0&fnval=16&module=bangumi" :
        "avid=82846771&qn=0&type=&otype=json&ep_id=307247&fourk=1&fnver=0&fnval=16&module=bangumi";
      get("https://api.bilibili.com/pgc/player/web/playurl?"+query,function(err,r,b){
        if (err) return settle("failed","");
        try {
          var code=JSON.parse(b).code;
          settle(code===0?"available":code===-10403?"blocked":"unknown","");
        } catch(e) { settle("unknown",""); }
      });
    } else if (id === "bbc") {
      get("https://www.bbc.co.uk/iplayer",function(err,r,b){
        if (err) return settle("failed","");
        if (status(r)===451 || /bbc iplayer only works in the uk|only available in the uk/i.test(b))
          return settle("blocked","");
        settle("unknown","");
      });
    } else if (id === "abema") {
      get("https://abema.tv/",function(err,r,b){
        if (err) return settle("failed","");
        if (status(r)===451 || /お住まいの地域では視聴できません|outside of japan/i.test(b))
          return settle("blocked","");
        settle("unknown","");
      });
    } else settle("unknown","");
  }
  function report() {
    var elapsed=Math.max(0,Math.round((Date.now()-start)/1000));
    var display=node.length>34 ? node.slice(0,32)+"…" : node;
    var lines=["节点："+display,"耗时："+elapsed+" 秒"],last="";
    services.forEach(function(item,i) {
      if (item.group!==last) {last=item.group;lines.push("", "【"+last+"】");}
      var r=results[i] || tag("unknown","");
      lines.push(item.name+"："+value(r.kind,r.detail));
    });
    lines.push("", "地区状态仅供参考，不代表账号或播放权益。");
    return {title:"解锁检测",content:lines.join("\n")};
  }
  function pump() {
    if (ended) return;
    if (count===services.length) {finish(report());return;}
    while (running<4 && cursor<services.length && !ended) {
      (function(i) {
        var released=false;
        running++;
        function release(result) {
          if (released || ended) return;
          released=true;
          results[i]=result;
          running--;count++;
          pump();
        }
        try {run(services[i],release);} catch(e) {release(tag("unknown",""));}
      })(cursor++);
    }
  }
  setTimeout(function(){ finish(report()); },full?19000:11500);
  pump();
})();