/* Loon Routing DNS · Node Egress v2.0 — manual only.
 * Observed exit IP is not necessarily the proxy server's entry IP.
 * All provider classifications are unverified hints, not quality scores. */
(function () {
  "use strict";
  var args=(typeof $argument==="object" && $argument)||{};
  var ctx=(typeof $environment==="object" && $environment && $environment.params)||{};
  var PRIMARY="https://api.ipquery.io/?format=json";
  var BACKUP="https://ipwho.is/";
  var finished=false;
  function choose(v){return typeof v==="string" && v.trim()?v.trim():"";}
  var info=ctx.nodeInfo && typeof ctx.nodeInfo==="object"?ctx.nodeInfo:{};
  var route=choose(ctx.node)||choose(info.name)||choose(info.tag)||
    choose(ctx.policyGroup)||choose(args.target_policy)||"Proxy";
  function safe(x){
    if(typeof x==="number"&&isFinite(x)) x=String(x);
    return typeof x==="string"&&x.trim()?
      x.replace(/[\u0000-\u001f\u007f]/g," ").trim().slice(0,80):"未知";
  }
  function ipv4(s) {
    if(!/^\d{1,3}(?:\.\d{1,3}){3}$/.test(s)) return false;
    return s.split(".").every(function(x){return Number(x)<=255;});
  }
  function validIP(s){
    if(typeof s!=="string"||s.length<2||s.length>45) return false;
    if(s.indexOf(":")<0) return ipv4(s);
    if(!/^[0-9a-f:.]+$/i.test(s)||s.indexOf(":::")>=0) return false;
    var split=s.split("::");
    if(split.length>2) return false;
    var pieces=[];
    split.forEach(function(v){if(v) pieces=pieces.concat(v.split(":"));});
    if(pieces.some(function(v){return !/^[0-9a-f]{1,4}$/i.test(v);})) return false;
    return split.length===2?pieces.length<8:pieces.length===8;
  }
  function toNode(x) {
    if(!x || typeof x!=="object"||x.success===false||!validIP(x.ip)) return null;
    if(x.location && x.isp && typeof x.isp==="object") {
      var l=x.location,r=x.risk||{};
      return {ip:x.ip,country:safe(l.country),region:safe(l.state),
        city:safe(l.city),asn:safe(x.isp.asn),isp:safe(x.isp.isp||x.isp.org),
        datacenter:typeof r.is_datacenter==="boolean"?r.is_datacenter:null,
        mobile:typeof r.is_mobile==="boolean"?r.is_mobile:null,provider:"ipquery.io"};
    }
    if(x.connection || (x.country && x.ip)) {
      var c=x.connection||{};
      return {ip:x.ip,country:safe(x.country),region:safe(x.region),city:safe(x.city),
        asn:c.asn?"AS"+safe(String(c.asn).replace(/^AS/i,"")):"未知",
        isp:safe(c.isp||c.org),datacenter:null,mobile:null,provider:"ipwho.is"};
    }
    return null;
  }
  function explain(err){
    var str=String(err||"").toLowerCase();
    if(/timeout|timed out/.test(str))return "连接超时";
    if(/dns|resolv|host/.test(str))return "域名解析失败";
    if(/tls|ssl|certificat/.test(str))return "TLS/证书失败";
    return "请求失败";
  }
  function request(url,node,cb){
    var done=false;
    function finish(err,val){
      if(done)return;
      done=true;
      cb(err,val);
    }
    try {
      $httpClient.get({url:url,node:node,timeout:8500,
        headers:{"Accept":"application/json"},"auto-cookie":false,"auto-redirect":false},
      function(err,response,body){
        if(err) return finish(explain(err),null);
        if(Number(response && response.status)!==200)
          return finish("HTTP "+String(response&&response.status||"未知"),null);
        if(typeof body!=="string"||body.length>100000)
          return finish("响应体格式不正确",null);
        try {
          var normalized=toNode(JSON.parse(body));
          if(!normalized)return finish("IP 情报字段不兼容",null);
          finish(null,normalized);
        } catch(e) {finish("JSON 解析失败",null);}
      });
    }catch(e){finish(explain(e),null);}
  }
  function lookup(node,done){
    request(PRIMARY,node,function(err,item){
      if(item)return done(null,item);
      request(BACKUP,node,function(err2,backup){
        done(backup?null:"主服务："+err+"；备用："+err2,backup);
      });
    });
  }
  function category(item){
    if(item.mobile===true)return "移动网络（第三方估计）";
    if(item.datacenter===true)return "机房或云服务（第三方估计）";
    if(item.datacenter===false && item.mobile===false)
      return "未标记机房，不能据此确认家宽";
    return "未知（情报来源未提供相关字段）";
  }
  function show(item,direct){
    var where=[item.country,item.region,item.city].filter(function(x){return x!=="未知";}).join(" · ")||"未知";
    var lines=[
      "节点/策略："+safe(route),
      "出口 IP："+item.ip,
      "地区："+where,
      "ASN："+item.asn,
      "ISP："+item.isp,
      "网络类型："+category(item),
      "数据来源："+item.provider
    ];
    if(direct) {
      lines.push("直连出口 IP："+direct.ip);
      lines.push(item.ip===direct.ip?
        "提示：两种查询路线得到相同出口；请检查当前策略是否真正通过代理。":
        "提示：两种查询路线出口不同，但不能据此证明 DNS/网络完全无泄漏。");
    } else if(args.compare_direct===true && route!=="DIRECT") {
      lines.push("直连对照未完成；以上节点出口信息不受影响。");
    }
    lines.push("说明：这是第三方 API 观察到的出口，不是节点入口地址；地区及网络类型可能不准确。");
    return lines.join("\n");
  }
  function done(msg){
    if(finished)return;
    finished=true;
    $done({title:"节点出口信息",content:msg});
  }
  if(route.length>200 || /[\r\n\u0000-\u001f]/.test(route)) {
    done("节点或策略名称无效。");return;
  }
  lookup(route,function(err,item){
    if(err) {
      done("节点/策略："+safe(route)+"\n查询失败："+safe(err)+
        "\n请检查选定节点或策略是否可用；没有把 DIRECT 地址冒充节点出口。");
      return;
    }
    if(args.compare_direct!==true||route==="DIRECT")return done(show(item,null));
    lookup("DIRECT",function(directErr,direct){
      done(show(item,directErr?null:direct));
    });
  });
})();
