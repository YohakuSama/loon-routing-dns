/* Loon Routing DNS · DNS Resolver Exposure Check v2.2
 * Manual only. Observes recursive resolvers at bash.ws authoritative DNS.
 * Neither a DoH connectivity test nor a universal DNS-leak safety certificate.
 * Requires Loon Build 988+ for $dns.query; does not alter configuration.
 * HTTP uses the current Loon routing, never forces DIRECT.
 */
(function () {
  "use strict";
  var API = "https://bash.ws";
  var COUNT = 4;
  var finished = false;
  var TIMER_MS = 33000;
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
      clean(reason, 170),
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
        if(err) return done("网络请求失败",null);
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
    return /^\d{5,15}$/.test(id) ? id : "";
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
        if(!/^[0-9a-f:.]+$/i.test(address)||address.length>45||address.length<3)
          continue;
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
    var suspicious=[],unclear=[];
    for(var i=0;i<list.length;i++) {
      var owner=list[i].asn.toLowerCase();
      if(!owner) unclear.push(list[i].ip);
      else if(!/alibaba|aliyun|alidns|alicloud/i.test(owner))
        suspicious.push(list[i].ip);
    }
    if(suspicious.length)
      return "发现需要核对的解析器："+suspicious.join(", ")+"。与项目默认 AliDNS 名称不一致，仅代表疑点，不是泄漏定论。";
    if(unclear.length)
      return "部分解析器没有运营商资料，无法确认与当前 DNS 设置是否一致。";
    return "解析器运营商名称与项目默认 AliDNS 看起来一致；仅代表本次采样，没有证明完全无泄漏。";
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
    var fail=queries.filter(function(q){return q.ok===false;}).length;
    if(fail)lines.push("注：有 "+fail+" 次 DNS 查询返回错误或空结果；服务端仍可能收到请求，数据可能不完整。");
    lines.push("",
      "判断范围：只记录本次 Loon DNS 栈发出的采样查询；不能检测其他 App、Safari 的所有请求、系统旁路 DNS 或持续泄漏。",
      "注意：DNS 解析器的 ASN 与代理出口 ASN 不一致，本身不构成泄漏证据。若当前配置修改过 DNS，请按实际设置人工对照。",
      "隐私：手动运行会向 bash.ws 发送随机测试域名，检测服务可看到解析器 IP 及当前路由的 HTTP 出口；没有强制 DIRECT 请求。",
      "测试无法保证零泄漏。请结合实际 DNS 日志与外部网站再验证。");
    finish("检测结果：已获取解析器观测信息（需人工核对）",lines);
  }
  function poll(id, queries, retry) {
    get(API+"/dnsleak/test/"+id+"?json",function(err,body){
      if(err)return unknown("无法读取权威 DNS 观测结果："+err);
      var data=parseResult(body);
      if(!data)return unknown("权威 DNS 检测服务返回了不支持的结果格式。");
      if(data.dns.length===0 && retry) {
        setTimeout(function(){
          if(!finished)poll(id,queries,false);
        },1800);
        return;
      }
      render(data,id,queries);
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
    var done=0,queries=[];
    for(var i=1;i<=COUNT;i++){
      (function(n){
        queryDns(n+"."+id+".bash.ws",function(item){
          queries[n-1]=item;
          done++;
          if(done===COUNT) {
            setTimeout(function(){
              if(!finished)poll(id,queries,true);
            },2200);
          }
        });
      })(i);
    }
  }
  if(typeof $dns==="undefined"||!$dns||typeof $dns.query!=="function"){
    unknown("当前 Loon 不支持 $dns.query（需要 Build 988+）。无法通过插件触发 DNS 栈的独立查询。");
    return;
  }
  setTimeout(function() {
    if(!finished) unknown("DNS 泄漏检测已超时；检测服务或 Loon DNS 查询没有及时返回。");
  },TIMER_MS);
  get(API+"/id",function(err,body){
    if(err)return unknown("无法创建检测会话："+err);
    var id=sanitizeID(body);
    if(!id)return unknown("检测服务未返回有效的随机测试 ID。");
    run(id);
  });
})();
