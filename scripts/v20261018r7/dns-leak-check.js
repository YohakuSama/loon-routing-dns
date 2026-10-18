/* Loon Routing DNS · DNS Resolver Exposure Check v2.3
 * Manual only. Observes recursive resolvers at bash.ws authoritative DNS.
 * Neither a DoH connectivity test nor a universal DNS-leak safety certificate.
 * Requires Loon Build 988+ for $dns.query; does not alter configuration.
 * HTTP uses the current Loon routing, never forces DIRECT.
 */
(function () {
  "use strict";
  var API = "https://bash.ws";
  // 10 unique domains match the public bash.ws web-test sample size.
  // Probe results are polled independently from Loon DNS callback completion.
  var COUNT = 10;
  var finished = false;
  var TIMER_MS = 39000;
  var phase = "准备";
  var stats = {sent:0, replied:0, failed:0, polls:0, lastError:""};
  var currentID = "";
  function progress() {
    return "诊断进度：DNS 查询 "+stats.replied+"/"+stats.sent+
      " 已回调（错误 "+stats.failed+"），服务端结果检查 "+stats.polls+" 次。"+
      (currentID ? " 测试 ID："+currentID : "");
  }
  function clean(s, n) {
    var x = typeof s === "number" && isFinite(s) ? String(s) :
      typeof s === "string" ? s : "";
    return x.replace(/[\u0000-\u001f\u007f]/g, " ").trim().slice(0, n || 100);
  }
  function finish(title, lines) {
    if (finished) return;
    finished = true;
    try {
      $done({title:"DNS 解析器泄漏检测",content:[title].concat(lines || []).join("\n")});
    } catch (e) { try { $done(); } catch (_) {} }
  }
  function unknown(reason) {
    finish("检测结果：无法判定",[
      "失败阶段："+phase,
      clean(reason, 170),
      progress(),
      "没有足够证据判断是否发生 DNS 泄漏；请勿把检测失败当作安全通过。",
      "可在 Loon DNS 日志中核对查询路径，并使用独立浏览器测试交叉验证。"
    ]);
  }
  function get(url, cb) {
    var called = false;
    function done(err,data) {
      if (called || finished) return;
      called = true;
      cb(err,data);
    }
    try {
      $httpClient.get({
        url:url,timeout:8000,headers:{"Accept":"application/json, text/plain"},
        "auto-cookie":false,"auto-redirect":false
      },function(err,response,body){
        if(err) return done("请求失败："+clean(err && (err.message || err),85),null);
        if(Number(response && response.status)!==200)
          return done("检测服务 HTTP "+String(response && response.status || "未知"),null);
        if(typeof body!=="string"||body.length>100000)
          return done("检测服务响应格式错误",null);
        done(null,body);
      });
    } catch(e) { done("检测请求无法执行",null); }
  }
  function sanitizeID(x) {
    var id = clean(x,80);
    // bash.ws /id supplies a decimal session id. Never interpolate unknown URLs.
    return /^\d{1,18}$/.test(id) ? id : "";
  }
  function validIPv4(ip) {
    if(!/^\d{1,3}(?:\.\d{1,3}){3}$/.test(ip))return false;
    return ip.split(".").every(function(n){return Number(n)<=255;});
  }
  function validAddress(ip) {
    if(validIPv4(ip))return true;
    if(ip.indexOf(":")<0||ip.length>45||!/^[:a-fA-F0-9.]+$/.test(ip)||
       ip.indexOf(":::")>=0)return false;
    var sides=ip.split("::");
    if(sides.length>2)return false;
    var parts=[],hasV4=false;
    for(var j=0;j<sides.length;j++){
      if(!sides[j])continue;
      var groups=sides[j].split(":");
      for(var k=0;k<groups.length;k++) {
        var g=groups[k];
        if(g.indexOf(".")>=0){
          if(k!==groups.length-1||j!==sides.length-1||!validIPv4(g)||hasV4)
            return false;
          hasV4=true;
          parts.push("v4","v4");
        }else{
          if(!/^[a-fA-F0-9]{1,4}$/.test(g))return false;
          parts.push(g);
        }
      }
    }
    return sides.length===2?parts.length<8:parts.length===8;
  }
  function parseResult(body) {
    try {
      var raw=JSON.parse(body);
      if(!Array.isArray(raw) || raw.length>120) return null;
      var dns=[],http=[],summary=[];
      var seen={};
      for(var i=0;i<raw.length;i++) {
        var r=raw[i];
        if(!r||typeof r!=="object") continue;
        var type=clean(r.type,30).toLowerCase();
        if(type==="conclusion") {
          summary.push(clean(r.ip,120)); // service verdict is intentionally not authoritative
          continue;
        }
        if(type!=="dns"&&type!=="ip") continue;
        var address=clean(r.ip,70);
        if(!validAddress(address))continue;
        var key=type+"|"+address;
        if(seen[key])continue;
        seen[key]=true;
        var entry={ip:address,country:clean(r.country_name||r.country,75),
          asn:clean(r.asn,100)};
        if(type==="dns")dns.push(entry);
        else http.push(entry);
      }
      return {dns:dns,http:http,summary:summary};
    } catch(e) { return null; }
  }
  function formatResolver(x) {
    var detail=[x.country,x.asn].filter(function(a){return !!a;}).join(" / ");
    return "• "+x.ip+(detail?"（"+detail+"）":"（运营商未知）");
  }
  function reviewText(list) {
    // Configured provider: AliDNS. Resolver source/ASN may be anycast or differ
    // from the endpoint; therefore mismatches are a warning, not proof of leakage.
    var matches=0,unverified=0,others=[];
    for(var i=0;i<list.length;i++) {
      var owner=list[i].asn.toLowerCase();
      if(/alibaba|aliyun|alidns|alicloud/.test(owner))matches++;
      else if(!owner||/^as\d+$/i.test(owner))unverified++;
      else others.push(list[i].ip);
    }
    if(others.length)
      return "有 "+others.length+" 个解析器归属名称未匹配 AliDNS，应核对是否为预期上游："+others.join(", ")+"；不能据此直接认定泄漏。";
    if(unverified)
      return "有 "+unverified+" 个解析器仅有 ASN 编号或缺失组织信息，无法仅凭名称判断；请人工对照预期 DNS。";
    return "本次采样 "+matches+" 个解析器的运营商名称匹配 AliDNS 相关关键词；不代表所有 DNS 请求均安全。";
  }
  function render(values, id, queries) {
    if(values.dns.length===0) {
      return unknown("检测服务尚未观察到任何递归 DNS 解析器，可能是查询失败、返回延迟、网络拦截或 DNS 服务缓存。");
    }
    var lines=[
      "检测方式：独立权威 DNS 观察（bash.ws），一次性域名 "+COUNT+" 个。",
      "测试 ID："+id,
      "观测 DNS 解析器（"+values.dns.length+"）："
    ];
    values.dns.slice(0,18).forEach(function(x){lines.push(formatResolver(x));});
    if(values.dns.length>18)lines.push("其余 "+(values.dns.length-18)+" 个已省略。");
    lines.push("",
      "与项目默认 DNS 的比对：",
      reviewText(values.dns)
    );
    if(values.http.length) {
      lines.push("","测试服务观察到的 HTTP 出口（经 Loon 当前分流）：");
      values.http.slice(0,3).forEach(function(x){lines.push(formatResolver(x));});
    }
    var fail=stats.failed;
    lines.push("","【执行情况】",progress());
    if(fail)lines.push("注：有 "+fail+" 次 DNS 查询报告错误；服务端仍可能收到查询，不代表这 "+fail+" 次没有被解析。");
    if(stats.replied<COUNT)lines.push("部分 Loon DNS 回调未返回，但权威 DNS 已提供了观测数据。");
    lines.push("",
      "判断范围：只记录本次 Loon DNS 栈发出的采样查询；不能检测其他 App、Safari 的所有请求、系统旁路 DNS 或持续泄漏。",
      "注意：DNS 解析器的 ASN 与代理出口 ASN 不一致，本身不构成泄漏证据。若当前配置修改过 DNS，请按实际设置人工对照。",
      "隐私：手动运行会向 bash.ws 发送随机测试域名，检测服务可看到解析器 IP 及当前路由的 HTTP 出口；没有强制 DIRECT 请求。",
      "测试无法保证零泄漏。请结合实际 DNS 日志与外部网站再验证。");
    finish("检测结果：已获取解析器观测信息（需人工核对）",lines);
  }
  function poll(id, queries, attempt) {
    if (finished) return;
    phase = "读取 bash.ws 权威 DNS 观测";
    stats.polls++;
    get(API+"/dnsleak/test/"+id+"?json",function(err,body){
      var data=err ? null : parseResult(body);
      if (err) stats.lastError = err;
      else if (!data) stats.lastError = "检测结果 JSON 格式与预期不符";
      else if (!data.dns.length) stats.lastError = "服务暂未观察到 DNS 解析器";
      if (data && data.dns.length>0) return render(data,id,queries);
      if (attempt<6 && !finished) {
        setTimeout(function(){ if(!finished)poll(id,queries,attempt+1); },2300);
        return;
      }
      unknown("已重试 6 次，仍无法读取到有效的解析器记录。"+
        (stats.lastError?" 最近原因："+stats.lastError:"")+
        " 网页可用只代表浏览器路径可用；Loon DNS 栈的查询路径可能不同。");
    });
  }
  function queryDns(domain,cb) {
    var replied=false;
    function done(result) {
      if(replied||finished)return;
      replied=true;
      cb(result);
    }
    try {
      $dns.query({domain:domain,protocol:"auto",timeout:6500},
        function(error,result){
          var code=clean(error && error.code,30);
          // NO_ANSWER is not proof that the upstream never saw the DNS packet.
          // Do not fabricate a successful answer; rely on authoritative observations.
          done({ok:!error && !!result,code:code||"OK"});
        });
    }catch(e){done({ok:false,code:"API_ERROR"});}
  }
  function run(id) {
    currentID = id;
    phase = "发起 Loon DNS 查询";
    var queries=[];
    // Start the observation polling even when a Loon DNS callback never fires.
    // The HTTP probe/visibility result is independent of individual query errors.
    for(var i=1;i<=COUNT;i++){
      (function(n){
        stats.sent++;
        queryDns(n+"."+id+".bash.ws",function(item){
          queries[n-1]=item;
          stats.replied++;
          if(item.ok===false)stats.failed++;
        });
      })(i);
    }
    setTimeout(function() {
      if(!finished)poll(id,queries,1);
    },4000);
  }
  if(typeof $dns==="undefined"||!$dns||typeof $dns.query!=="function"){
    unknown("当前 Loon 不支持 $dns.query（需要 Build 988+）。无法通过插件触发 DNS 栈的独立查询。");
    return;
  }
  setTimeout(function() {
    if(!finished) unknown("检测超出 39 秒：可能是 HTTP 访问受限、结果延迟或 Loon DNS 无回调。");
  },TIMER_MS);
  phase = "创建 bash.ws 会话";
  get(API+"/id",function(err,body){
    if(err)return unknown("无法创建检测会话："+err);
    var id=sanitizeID(body);
    if(!id)return unknown("检测服务返回的测试 ID 不符合格式要求（不显示原始内容）。");
    run(id);
  });
})();
