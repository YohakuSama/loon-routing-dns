/* LoonKit · single-node network/DNS diagnostics v6.5.0.
 * Inspect the resolver used by the native Loon DNS stack. This cannot prove
 * that browsers or other apps do not use independent encrypted DNS.
 * No routing, DNS, policy, or VPN settings are modified. */
(function () {
  "use strict";
  var name = (typeof $script === "object" && $script && $script.name) || "";
  var automatic = name === "网络切换异常监测";
  var DIRECT_URL = "http://wifi.vivo.com.cn/generate_204";
  var MANUAL_URL = "http://bing.com/generate_204";
  var ALERT_KEY = "loonkit:v4:network-alert";
  var COOLDOWN = 30 * 60 * 1000;
  var finished = false;

  setTimeout(function () {
    finish("检测超时，请稍后重试或查看 Loon 连接记录。");
  }, 34000);

  function finish(message) {
    if (finished) return;
    finished = true;
    // Loon does not guarantee a clearTimeout API. Guard against late callbacks.
    if (automatic) $done();
    else $done(message && typeof message==="object"?message:{title:"网络检测",content:message});
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
        if (status===204) return done(true,"正常");
        // This is a generate_204 endpoint. HTTP 200 might be a captive portal.
        if (status===200) return done(null,"响应异常（HTTP 200），可能需要网络认证");
        // A redirect proves a response, not a broken proxy; do not follow it.
        if (status>=300 && status<400)
          return done(null,"HTTP "+status+"（页面跳转，连接状态待确认）");
        if (status>=400 && status<=599)
          return done(null,"HTTP "+status+"（目标站点已响应，连接状态待确认）");
        done(null,"HTTP "+(status || "未知")+"（无法确认）");
      });
    } catch (error) {done(false,errorText(error));}
  }
  function nativeDns(cb) {
    var label="DNS 解析";
    if (typeof $dns === "undefined" || !$dns || typeof $dns.query !== "function") {
      cb({label:label,ok:null,detail:"当前 Loon 版本不支持 DNS 检测"});
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
          cb({label:label,ok:false,detail:"没有获得有效的解析地址"});
          return;
        }

        var protocol=String(reply.protocol || "unknown").toLowerCase().trim();
        var server=String(reply.server || "").trim().slice(0,180);
        // A successful answer proves resolution, not capture of all DNS traffic.
        if (reply.fromCache===true) {
          cb({label:label,ok:true,detail:"解析成功（缓存）"});
          return;
        }

        // DNS is user-configurable. Identify the protocol without requiring a
        // specific public resolver. A bare "https://" is not a full URL.
        var httpsUrl=/^https:\/\/[^\s\/?#]+(?:[\/?#]|$)/i.test(server);
        var tlsUrl=/^(?:tls|dot):\/\/[^\s\/?#]+/i.test(server);
        if (protocol==="udp" || protocol==="system") {
          cb({label:label,ok:true,detail:"解析成功 · 普通 DNS"});
        } else if (protocol==="doh" || (protocol==="auto" && httpsUrl)) {
          cb({label:label,ok:true,detail:"解析成功 · DoH"});
        } else if (protocol==="dot" || (protocol==="auto" && tlsUrl)) {
          cb({label:label,ok:true,detail:"解析成功 · DoT"});
        } else if (protocol==="doh3" || protocol==="quic") {
          cb({label:label,ok:true,detail:"解析成功 · Loon 报告加密 DNS"});
        } else {
          cb({label:label,ok:true,detail:"解析成功",
            notice:"已解析，但无法确认所用 DNS 传输方式。"});
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
  function choose(value) {
    return typeof value==="string" && value.trim()?value.trim():"";
  }
  function safe(value) {
    return String(value||"").replace(/[\u0000-\u001f\u007f]/g," ").trim().slice(0,100);
  }
  function resolveNode() {
    var env=(typeof $environment==="object" && $environment && $environment.params)||{};
    var args=(typeof $argument==="object" && $argument)||{};
    var info=env.nodeInfo && typeof env.nodeInfo==="object"?env.nodeInfo:{};
    // Node actions carry the concrete node. Do not substitute a policy group for it.
    var selected=choose(env.node)||choose(info.name)||choose(info.tag);
    if(!selected)selected=choose(env.policyGroup)||choose(args.target_policy);
    if(!selected) return "";
    var config=typeof $config==="object"&&$config;
    var visited={},depth=0;
    while(depth++<8){
      if(visited[selected])return "";
      visited[selected]=true;
      var child="";
      try {
        if(config&&typeof config.getSelectedPolicy==="function")
          child=choose(config.getSelectedPolicy(selected));
      }catch(e){}
      if(child && child!==selected){selected=child;continue;}
      // Proxy/Auto/Fallback are groups in the LoonKit profile; without a
      // concrete selection, don't report aggregate group requests as node latency.
      if(/^(Proxy|Auto|Fallback|ALL_Filter)$/i.test(selected))return "";
      // Also fail closed for any other known group, if the config exposes it.
      try {
        var cfg=config&&typeof config.getConfig==="function"?
          JSON.parse(config.getConfig()||"{}"):{};
        var groups=cfg.all_policy_groups;
        if(Array.isArray(groups) && groups.some(function(group){
          return group===selected || group&&typeof group==="object"&&
            (group.name===selected||group.tag===selected);
        }))return "";
      } catch(e){}
      return selected;
    }
    return "";
  }
  function htmlSafe(value) {
    return String(value||"").replace(/&/g,"&amp;").replace(/</g,"&lt;")
      .replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");
  }
  function stateText(item) {
    return item.ok===true?"正常":item.ok===false?"失败":"需检查";
  }
  function stateColor(item) {
    return item.ok===true?"#198754":item.ok===false?"#d9534f":"#996d19";
  }
  function row(label,item) {
    var duration=typeof item.ms==="number"?" · "+item.ms+" ms":"";
    var value=item.detail+duration;
    return '<div style="padding:13px 0;border-bottom:1px solid #e8ebf0;">'
      +'<div style="display:flex;justify-content:space-between;align-items:center;gap:14px;">'
      +'<span style="font-size:13px;font-weight:600;color:#556170;">'+htmlSafe(label)+'</span>'
      +'<span style="color:'+stateColor(item)+';font-size:13px;font-weight:700;">'+stateText(item)+'</span>'
      +'</div><div style="margin-top:7px;font-size:15px;font-weight:600;line-height:1.5;color:#202935;">'
      +htmlSafe(value)+'</div></div>';
  }
  function display(node,direct,proxy,dns) {
    var list=[{label:"节点请求",value:proxy},{label:"直连请求",value:direct},{label:"DNS 解析",value:dns}];
    var failure=list.some(function(item){return item.value.ok===false;});
    var uncertain=list.some(function(item){return item.value.ok===null;});
    var headline=failure?"部分检测失败":uncertain?"部分结果需检查":"检测正常";
    var caption=proxy.ok===true?"HTTP 响应 "+proxy.ms+" ms":proxy.detail;
    var plain=["节点："+safe(node),"状态："+headline,"",
      "节点请求："+proxy.detail+(typeof proxy.ms==="number"?" · "+proxy.ms+" ms":""),
      "直连请求："+direct.detail+(typeof direct.ms==="number"?" · "+direct.ms+" ms":""),
      "DNS 解析："+dns.detail,"","目标：bing.com/generate_204"];
    var html='<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">'
      +'</head><body style="margin:0;padding:12px 8px;background:#f6f8fb;color:#202935;font-family:-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif;">'
      +'<div style="max-width:450px;margin:0 auto;">'
      +'<div style="padding:18px 16px;border-radius:16px;background:#fff;border:1px solid #e8ebf0;">'
      +'<div style="font-size:12px;font-weight:600;letter-spacing:.4px;color:#687586;">LOONKIT · NETWORK</div>'
      +'<div style="margin-top:8px;font-size:21px;font-weight:700;">'+htmlSafe(headline)+'</div>'
      +'<div style="margin-top:7px;font-size:13px;color:#596676;overflow-wrap:anywhere;">'+htmlSafe(node)+'</div>'
      +'<div style="margin-top:14px;padding:11px 12px;background:#f5f7fa;border-radius:10px;">'
      +'<div style="font-size:11px;color:#738092;">节点 HTTP 响应耗时</div>'
      +'<div style="font-size:17px;font-weight:700;margin-top:3px;">'+htmlSafe(caption)+'</div></div>'
      +'<div style="margin-top:8px;">'
      +row("节点连接",proxy)+row("直连网络",direct)+row("DNS",dns)
      +'</div><div style="padding-top:12px;color:#85909d;font-size:11px;">'
      +'测试目标 · bing.com/generate_204　|　v6.5.0</div></div></div></body></html>';
    return {title:"网络检测",content:plain.join("\n"),htmlMessage:html};
  }
  function manual() {
    var target=resolveNode();
    if(!target || /[\u0000-\u001f\u007f]/.test(target)) {
      finish({title:"网络检测",
        content:"请在单个节点的菜单中运行网络检测，或在插件的「检测策略」中填写具体节点名称。",
        htmlMessage:'<div style="font-family:-apple-system;padding:18px;line-height:1.8;">'
          +'<b>请选择单个节点</b><p>从节点菜单运行「网络检测」，或在插件设置中填写具体节点名称。</p></div>'});
      return;
    }
    var pending=2, results={};
    function collect(key,item){
      if(results[key])return;
      results[key]=item;
      if(--pending!==0)return;
      nativeDns(function(dns){finish(display(target,results.direct,results.node,dns));});
    }
    httpProbe("直连网络",MANUAL_URL,"DIRECT",function(x){collect("direct",x);});
    httpProbe("节点连接",MANUAL_URL,target,function(x){collect("node",x);});
  }
  function notify(result) {
    if (finished || result.ok !== false) return;
    var last=null;
    try {last=JSON.parse($persistentStore.read(ALERT_KEY)||"null");}catch(e){}
    if (last && Date.now()-Number(last.at||0)<COOLDOWN) return;
    try {$persistentStore.write(JSON.stringify({at:Date.now()}),ALERT_KEY);}catch(e){}
    try {$notification.post("Loon 网络切换提醒","直连连接连续失败",
      "网络切换后连续两次连接失败，请检查当前网络。");}catch(e){}
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