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
        if (status===204 || status===200) return done(true,"HTTP "+status);
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
    var label="Loon 原生 DNS";
    if (typeof $dns === "undefined" || !$dns || typeof $dns.query !== "function") {
      cb({label:label,ok:null,detail:"不支持 $dns.query（需要 Loon Build 988+）"});
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
        if (!answers.some(function(item){return item && (item.type==="A" || item.type==="AAAA");})) {
          cb({label:label,ok:false,detail:"没有有效 A/AAAA 答案"});
          return;
        }
        var protocol=String(reply.protocol || "unknown").toLowerCase();
        var server=String(reply.server || "unknown").slice(0,180);
        var cache=reply.fromCache===true?"（缓存命中，未验证本次网络传输）":"";
        var detail=protocol+" / "+server+cache;
        // Cache metadata is not evidence of any network request made now.
        if (reply.fromCache===true) {
          cb({label:label,ok:null,detail:"缓存解析成功；本次没有可验证的 DNS 传输："+detail});
        } else if (protocol==="udp" || protocol==="system") {
          cb({label:label,ok:false,detail:"本次使用普通 DNS 查询："+detail});
        } else if (protocol==="doh" && server.indexOf("https://dns.alidns.com/dns-query")===0) {
          cb({label:label,ok:true,detail:"本次使用配置的 DoH："+detail});
        } else if (protocol==="doh" || protocol==="doh3" || protocol==="quic") {
          cb({label:label,ok:null,detail:"使用加密 DNS，非当前配置预期地址："+detail});
        } else if (protocol==="auto") {
          cb({label:label,ok:null,detail:"解析成功；Loon 返回 auto，未提供可验证的实际传输协议："+detail});
        } else {
          cb({label:label,ok:null,detail:"解析成功，但协议无法判定："+detail});
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
        finish([(failure?"结果：存在异常项目":unknown?"结果：部分项目不可用":"结果：所测项目正常")]
          .concat(all.map(resultLine)).concat([
            "如需确认 DNS 实际传输，请查看 Loon 的 DNS 日志及明文 DNS 回退设置。",
            "仅反映单次 Loon DNS 查询；DoH 加密不代表使用代理节点出口。",
            "UDP/53 劫持不能拦截浏览器或 App 自行使用的 DoH/DoT。"
          ]).join("\n"));
      });
    }
    httpProbe("直连网络",DIRECT_URL,"DIRECT",function(x){collect("direct",x);});
    httpProbe("代理策略 Proxy",PROXY_URL,"Proxy",function(x){collect("proxy",x);});
  }
  function notify(result) {
    if (finished || result.ok) return;
    var last=null;
    try {last=JSON.parse($persistentStore.read(ALERT_KEY)||"null");}catch(e){}
    if (last && Date.now()-Number(last.at||0)<COOLDOWN) return;
    try {$persistentStore.write(JSON.stringify({at:Date.now()}),ALERT_KEY);}catch(e){}
    try {$notification.post("Loon 网络异常提醒","直连探测连续失败",
      "网络切换后的 HTTP 探测失败；这不是 DNS 泄漏的证据。");}catch(e){}
  }
  if (!automatic) {manual();return;}
  // Never send unsolicited DNS requests to an unrelated public resolver.
  setTimeout(function(){
    httpProbe("直连网络",DIRECT_URL,"DIRECT",function(first){
      if (first.ok) return finish("网络已恢复");
      setTimeout(function(){
        httpProbe("直连网络",DIRECT_URL,"DIRECT",function(second){
          notify(second);
          finish("网络变化检查完成");
        });
      },2200);
    });
  },1600);
})();