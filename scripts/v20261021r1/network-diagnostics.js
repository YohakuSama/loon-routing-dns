/* LoonKit · network/DNS diagnostics.
 * Inspect the resolver used by the native Loon DNS stack. This cannot prove
 * that browsers or other apps do not use independent encrypted DNS.
 * No routing, DNS, policy, or VPN settings are modified. */
(function () {
  "use strict";
  var name = (typeof $script === "object" && $script && $script.name) || "";
  var automatic = name === "网络切换异常监测";
  var DIRECT_URL = "http://wifi.vivo.com.cn/generate_204";
  var PROXY_URL = "https://www.gstatic.com/generate_204";
  var ALERT_KEY = "loonkit:v4:network-alert";
  var COOLDOWN = 30 * 60 * 1000;
  var finished = false;

  setTimeout(function () {
    finish("检测超时：请检查 Loon 的请求日志和 DNS 日志。");
  }, 34000);

  function finish(message) {
    if (finished) return;
    finished = true;
    // Loon does not guarantee a clearTimeout API. Guard against late callbacks.
    if (automatic) $done();
    else $done({title:"网络与 DNS 诊断",content:message});
  }
  function errorText(error) {
    var msg = String(error && (error.message || error) || "").toLowerCase();
    if (/timeout|timed out/.test(msg)) return "超时";
    if (/certificat|tls|ssl/.test(msg)) return "TLS 错误";
    if (/dns|resolv|host/.test(msg)) return "域名解析失败";
    return "连接失败";
  }
  function httpProbe(label, url, policy, cb) {
    var start=Date.now(), called=false;
    function done(ok, detail) {
      if (called) return;
      called=true;
      cb({label:label,ok:ok,detail:detail,ms:Date.now()-start});
    }
    try {
      $httpClient.get({url:url,node:policy,timeout:6500,
        "auto-redirect":false,"auto-cookie":false},function(error,response){
        if (error) return done(false,errorText(error));
        var status=Number(response && response.status);
        if (status===204) return done(true,"HTTP 204");
        // This is a generate_204 endpoint. HTTP 200 might be a captive portal.
        if (status===200) return done(null,"HTTP 200（目标未返回预期 204，可能为认证页面）");
        // A redirect proves a response, not a broken proxy; do not follow it.
        if (status>=300 && status<400)
          return done(null,"HTTP "+status+"（目标重定向，代理状态待确认）");
        if (status>=400 && status<=599)
          return done(null,"HTTP "+status+"（目标站点响应，不代表代理故障）");
        done(null,"HTTP "+(status || "未知")+"（无法确认）");
      });
    } catch (error) {done(false,errorText(error));}
  }
  function nativeDns(cb) {
    var label="DNS 解析";
    if (typeof $dns === "undefined" || !$dns || typeof $dns.query !== "function") {
      cb({label:label,ok:null,detail:"当前 Loon 不支持 DNS 查询 API（需 Build 988+）"});
      return;
    }
    var called=false;
    try {
      $dns.query({domain:"example.com",protocol:"auto",timeout:6500},function(error,reply){
        if (called) return;
        called=true;
        if (error || !reply) {
          cb({label:label,ok:false,detail:"查询失败："+errorText(error)});
          return;
        }
        var answers=Array.isArray(reply.answers)?reply.answers:[];
        if (!answers.some(function(item){return item && (item.type==="A" || item.type==="AAAA") && item.value;})) {
          cb({label:label,ok:false,detail:"未获得有效的 A/AAAA 地址"});
          return;
        }

        var protocol=String(reply.protocol || "unknown").toLowerCase().trim();
        var server=String(reply.server || "").trim().slice(0,180);
        // A cache hit confirms resolution, but makes no fresh transport request.
        if (reply.fromCache===true) {
          cb({label:label,ok:true,detail:"解析成功（缓存）",
            notice:"本次使用缓存，没有发生新的 DNS 查询。"});
          return;
        }

        // Loon documents protocol=auto as choosing the transport by server scheme.
        // A *complete* HTTPS resolver URL can identify configured DoH. A bare
        // "https://" is incomplete and must never be called verified encryption.
        var httpsUrl=/^https:\/\/[^\s\/?#]+(?:[\/?#]|$)/i.test(server);
        var expected=/^https:\/\/dns\.alidns\.com\/dns-query(?:[?#]|$)/i.test(server);
        if ((protocol==="auto" || protocol==="doh") && expected) {
          cb({label:label,ok:true,detail:"解析成功 · DoH（AliDNS）"});
        } else if ((protocol==="auto" || protocol==="doh") && httpsUrl) {
          cb({label:label,ok:true,detail:"解析成功 · DoH",
            notice:"DNS 地址不是配置的 AliDNS，请确认是否为预期设置。"});
        } else if (protocol==="udp" || protocol==="system" ||
                   (protocol==="auto" && (/^system$/i.test(server) ||
                     /^[\d.]+(?::\d+)?$/.test(server) || /^\[[0-9a-f:]+\](?::\d+)?$/i.test(server)))) {
          cb({label:label,ok:true,detail:"解析成功 · 普通 DNS",
            notice:"本次解析未使用配置的 DoH，请检查 DNS 回退设置。"});
        } else if (protocol==="doh" || protocol==="doh3" || protocol==="quic") {
          cb({label:label,ok:true,detail:"解析成功 · Loon 报告加密 DNS",
            notice:"返回的服务器信息不足以核对是否为配置的 AliDNS。"});
        } else {
          cb({label:label,ok:true,detail:"解析成功",
            notice:"Loon 返回的 DNS 协议信息不完整，无法判断加密方式。"});
        }
      });
    } catch (error) {
      if (!called) cb({label:label,ok:false,detail:"DNS API 调用异常"});
    }
  }
  function resultLine(value) {
    return (value.ok===null?"—":value.ok?"✓":"✗")+" "+value.label+"："+value.detail+
      (typeof value.ms==="number"?"（"+value.ms+" ms）":"");
  }
  function manual() {
    var pending=2, results={};
    function collect(key,result) {
      if (results[key]) return;
      results[key]=result;
      if (--pending!==0) return;
      nativeDns(function(dns){
        var all=[results.direct,results.proxy,dns];
        var failure=all.some(function(x){return x.ok===false;});
        var unknown=all.some(function(x){return x.ok===null;});
        var summary=failure?"结果：检测到连接或解析失败"
          :unknown?"结果：部分检测尚未确认"
          :"结果：网络连接与 DNS 解析正常";
        var notes=[];
        if (dns.notice) notes.push("提示："+dns.notice);
        if (dns.ok===false) notes.push("建议检查 Loon 的 DNS 日志及回退设置。");
        finish([summary].concat(all.map(resultLine),notes).join("\n"));
      });
    }
    httpProbe("直连网络",DIRECT_URL,"DIRECT",function(x){collect("direct",x);});
    httpProbe("代理策略 Proxy",PROXY_URL,"Proxy",function(x){collect("proxy",x);});
  }
  function notify(result) {
    if (finished || result.ok !== false) return;
    var last=null;
    try {last=JSON.parse($persistentStore.read(ALERT_KEY)||"null");}catch(e){}
    if (last && Date.now()-Number(last.at||0)<COOLDOWN) return;
    try {$persistentStore.write(JSON.stringify({at:Date.now()}),ALERT_KEY);}catch(e){}
    try {$notification.post("Loon 网络切换提醒","直连连接连续失败",
      "网络切换后两次检测均未成功，请检查当前网络连接。此结果不能判断 DNS 是否泄漏。");}catch(e){}
  }
  if (!automatic) {manual();return;}
  // Never send unsolicited DNS requests to an unrelated public resolver.
  setTimeout(function(){
    httpProbe("直连网络",DIRECT_URL,"DIRECT",function(first){
      if (first.ok!==false) return finish(first.ok===true?"网络已恢复":"网络检查结果待确认");
      setTimeout(function(){
        httpProbe("直连网络",DIRECT_URL,"DIRECT",function(second){
          notify(second);
          finish("网络变化检查完成");
        });
      },2200);
    });
  },1600);
})();