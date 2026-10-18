/* Loon Routing DNS · Network Check v2.0 — manual and opt-in network change.
 * Independent probes are NOT proof of DNS-leak freedom or all rules working.
 * No DNS, routing, policy or VPN mutation. */
(function () {
  "use strict";
  var args = (typeof $argument === "object" && $argument) || {};
  var name = (typeof $script === "object" && $script && $script.name) || "";
  var automatic = name === "网络切换异常监测";
  var DIRECT_URL = "http://wifi.vivo.com.cn/generate_204";
  var PROXY_URL = "http://cp.cloudflare.com/generate_204";
  var DOH_URL = "https://dns.alidns.com/dns-query";
  var ALERT_KEY = "loon-routing-dns:v2:network-alert";
  var COOLDOWN = 30 * 60 * 1000;
  var finished = false;
  var watchdog = setTimeout(function () {
    finish("检测未完成：部分请求未在脚本时限内返回。请检查 Loon 脚本日志。");
  }, automatic ? 34000 : 34000);

  function finish(text) {
    if (finished) return;
    finished = true;
    clearTimeout(watchdog);
    if (automatic) $done();
    else $done({title: "网络与 DNS 诊断", content: text});
  }
  function errorText(err) {
    var s = String(err || "").toLowerCase();
    if (/timeout|timed out/.test(s)) return "超时";
    if (/certificat|tls|ssl/.test(s)) return "TLS 连接失败";
    if (/dns|resolv|unknown host/.test(s)) return "域名解析失败";
    return "连接失败";
  }
  function httpProbe(label, url, policy, cb) {
    var start = Date.now(), called = false;
    function done(ok, detail) {
      if (called) return;
      called = true;
      cb({label: label, ok: ok, detail: detail, ms: Date.now()-start});
    }
    try {
      $httpClient.get({url:url, node:policy, timeout:6500,
        "auto-redirect":false, "auto-cookie":false}, function (err, response) {
        if (err) return done(false, errorText(err));
        var status = Number(response && response.status);
        done(status === 200 || status === 204,
          status === 200 || status === 204 ? "HTTP " + status : "探测站返回 HTTP " + (status || "未知"));
      });
    } catch (e) { done(false, errorText(e)); }
  }
  function dnsQuery() {
    return new Uint8Array([0,0,1,0,0,1,0,0,0,0,0,0,7,101,120,97,109,112,108,101,3,99,111,109,0,0,1,0,1]);
  }
  function validDnsAnswer(raw) {
    if (!(raw instanceof Uint8Array) || raw.length < 33) return false;
    if (raw[0] !== 0 || raw[1] !== 0 || !(raw[2] & 128) || (raw[2] & 2) ||
        (raw[3] & 15) || raw[4] !== 0 || raw[5] !== 1 || raw[6] + raw[7] === 0) return false;
    var query=dnsQuery();
    for (var i=12; i<query.length; i++) if (raw[i] !== query[i]) return false;
    var off=query.length, count=(raw[6] << 8)|raw[7];
    for (var n=0; n<count; n++) {
      var steps=0;
      while (true) {
        if (++steps > 128 || off >= raw.length) return false;
        var len=raw[off++];
        if ((len & 192) === 192) {
          if (off >= raw.length) return false;
          off++; break;
        }
        if (len & 192) return false;
        if (len === 0) break;
        if (off+len > raw.length) return false;
        off+=len;
      }
      if (off+10 > raw.length) return false;
      var type=(raw[off]<<8)|raw[off+1], klass=(raw[off+2]<<8)|raw[off+3];
      var size=(raw[off+8]<<8)|raw[off+9];
      off+=10;
      if (off+size > raw.length) return false;
      if (klass===1 && ((type===1 && size===4) || (type===28 && size===16))) return true;
      off+=size;
    }
    return false;
  }
  function dohProbe(cb) {
    var start=Date.now(), called=false;
    function done(ok,detail) {
      if(called) return;
      called=true;
      cb({label:"DoH 服务（DIRECT）",ok:ok,detail:detail,ms:Date.now()-start});
    }
    try {
      $httpClient.post({url:DOH_URL,node:"DIRECT",timeout:6500,
        headers:{"Accept":"application/dns-message","Content-Type":"application/dns-message"},
        body:dnsQuery(),"binary-mode":true,"auto-redirect":false,"auto-cookie":false,insecure:false},
        function(err,response,data) {
          if (err) return done(false,errorText(err));
          if (Number(response && response.status)!==200) return done(false,"DoH HTTP "+String(response && response.status || "未知"));
          done(validDnsAnswer(data),validDnsAnswer(data)?"DNS A/AAAA 响应有效":"DNS 响应无效或缺少 A/AAAA 记录");
        });
    } catch (e) { done(false,errorText(e)); }
  }
  function nativeDns(cb) {
    if (typeof $dns === "undefined" || !$dns || typeof $dns.query !== "function") {
      cb({label:"Loon 原生 DNS",ok:null,detail:"当前版本不支持此接口（需 Build 988+）"});
      return;
    }
    var called=false;
    try {
      $dns.query({domain:"example.com",protocol:"auto",timeout:6500},function(err,reply){
        if (called) return;
        called=true;
        if (err || !reply) return cb({label:"Loon 原生 DNS",ok:false,detail:"查询失败"});
        var answers=Array.isArray(reply.answers)?reply.answers:[];
        var valid=answers.some(function(a){return a && (a.type==="A"||a.type==="AAAA");});
        cb({label:"Loon 原生 DNS",ok:valid,detail:valid?"获得 A/AAAA 解析记录":"未获得 A/AAAA 记录"});
      });
    } catch(e) { if(!called) cb({label:"Loon 原生 DNS",ok:false,detail:"查询接口异常"}); }
  }
  function batch(includeProxy,done) {
    var todo=includeProxy?3:2, out={};
    function collect(key,val) { if (out[key]) return; out[key]=val; if(--todo===0) done(out); }
    httpProbe("直连网络",DIRECT_URL,"DIRECT",function(v){collect("direct",v);});
    dohProbe(function(v){collect("doh",v);});
    if (includeProxy) httpProbe("代理策略 Proxy",PROXY_URL,"Proxy",function(v){collect("proxy",v);});
  }
  function resultLine(r) {
    var prefix = r.ok===null?"—":r.ok?"✓":"✗";
    return prefix+" "+r.label+"："+r.detail+(typeof r.ms==="number"?"（"+r.ms+" ms）":"");
  }
  function manual() {
    batch(true,function(r){
      nativeDns(function(n){
        var all=[r.direct,r.proxy,r.doh,n];
        var fail=all.some(function(x){return x.ok===false;});
        var unknown=all.some(function(x){return x.ok===null;});
        var title=fail?"结果：存在异常项目":unknown?"结果：部分项目不可用":"结果：所测项目正常";
        finish([title].concat(all.map(resultLine)).concat([
          "提示：DoH 接口测试不代表 Loon 所有 DNS 查询都使用 DoH，不能据此判断 DNS 泄漏。",
          "排查建议：失败时先查看 Loon 请求日志和 DNS 日志，再检查相应节点或探测服务。"
        ]).join("\n"));
      });
    });
  }
  function notify(result) {
    if (finished) return; // Never alert after a watchdog timeout has completed the script.
    // A single endpoint failure is an indication, not proof of DNS misconfiguration.
    var problem=!result.doh.ok?"DoH 检测服务不可达":!result.direct.ok?"直连探测未通过":"";
    if (!problem) {
      try { $persistentStore.write(JSON.stringify({key:"ok",at:Date.now()}),ALERT_KEY); }catch(e){}
      return;
    }
    var key=!result.doh.ok?"doh":"direct";
    var last=null;
    try { last=JSON.parse($persistentStore.read(ALERT_KEY)||"null"); }catch(e){}
    if (last && last.key===key && Date.now()-Number(last.at||0)<COOLDOWN) return;
    try { $persistentStore.write(JSON.stringify({key:key,at:Date.now()}),ALERT_KEY); }catch(e){}
    try { $notification.post("Loon 网络异常提醒",problem,"连续两次探测未通过；可能是网络切换或探测服务暂时不可达，并不代表 DNS 泄漏。"); }catch(e){}
  }
  if (!automatic) return manual();
  // iOS may invoke network-changed before the new route becomes usable.
  setTimeout(function(){
    batch(false,function(first){
      if(first.direct.ok && first.doh.ok){ notify(first); return finish("网络变化后探测正常"); }
      setTimeout(function(){
        batch(false,function(second){ notify(second); finish("网络变化检查完成"); });
      },2200);
    });
  },1600);
})();
