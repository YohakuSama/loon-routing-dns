/* Loon Routing DNS · Node Egress v2.1 — detailed structured report — manual only.
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
  function boundedNumber(x,min,max) {
    return typeof x==="number" && isFinite(x) && x>=min && x<=max ? x : null;
  }
  function optionalText(x) {
    var v=safe(x);
    return v==="未知"?"":v;
  }
  function truth(x) {
    return typeof x==="boolean"?x:null;
  }
  function asn(x) {
    if (x===null || x===undefined || x==="") return "未知";
    var t=safe(String(x)).replace(/^AS/i,"");
    return /^\d+$/.test(t)?"AS"+t:safe(x);
  }
  function toNode(x) {
    if(!x || typeof x!=="object"||x.success===false||!validIP(x.ip)) return null;
    if(x.location && typeof x.location==="object" && x.isp && typeof x.isp==="object") {
      var l=x.location,r=x.risk&&typeof x.risk==="object"?x.risk:{};
      return {
        ip:x.ip,country:safe(l.country),countryCode:safe(l.country_code),
        region:safe(l.state),city:safe(l.city),timezone:optionalText(l.timezone),
        zip:optionalText(l.zipcode),lat:boundedNumber(l.latitude,-90,90),
        lon:boundedNumber(l.longitude,-180,180),
        asn:asn(x.isp.asn),isp:safe(x.isp.isp),org:safe(x.isp.org),
        datacenter:truth(r.is_datacenter),mobile:truth(r.is_mobile),
        vpn:truth(r.is_vpn),proxy:truth(r.is_proxy),tor:truth(r.is_tor),
        riskScore:boundedNumber(r.risk_score,0,100),provider:"ipquery.io"
      };
    }
    if(x.connection || (x.country && x.ip)) {
      var c=x.connection&&typeof x.connection==="object"?x.connection:{};
      var timezone=typeof x.timezone==="object"&&x.timezone?x.timezone.id:x.timezone;
      return {
        ip:x.ip,country:safe(x.country),countryCode:safe(x.country_code),
        region:safe(x.region),city:safe(x.city),timezone:optionalText(timezone),
        zip:optionalText(x.postal),lat:boundedNumber(x.latitude,-90,90),
        lon:boundedNumber(x.longitude,-180,180),
        asn:asn(c.asn),isp:safe(c.isp),org:safe(c.org),
        datacenter:null,mobile:null,vpn:null,proxy:null,tor:null,
        riskScore:null,provider:"ipwho.is"
      };
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
    if(item.mobile===true)return "移动网络（数据源判断）";
    if(item.datacenter===true)return "机房 / 云服务（数据源判断）";
    if(item.datacenter===false && item.mobile===false)
      return "未标记机房或移动网络；不能确认为家宽";
    return "未知（数据源未提供完整类型标签）";
  }
  function feature(label,value) {
    return label+"："+(value===true?"情报源标记有":value===false?"情报源未标记":"无数据");
  }
  function localInfo(ip) {
    if(typeof $utils==="undefined" || !$utils)return null;
    function call(method) {
      try {
        return typeof $utils[method]==="function" ? safe($utils[method](ip)) : "无数据";
      } catch(e){return "无数据";}
    }
    return {geo:call("geoip"),asn:call("ipasn"),org:call("ipaso")};
  }
  function show(item,direct) {
    var location=[item.country,item.region,item.city].filter(function(v){
      return v!=="未知";
    }).join(" · ") || "未知";
    var lines=[
      "【查询对象】",
      "节点/策略："+safe(route),
      "出口 IP："+item.ip,
      "IP 类型："+(item.ip.indexOf(":")>=0?"IPv6":"IPv4"),
      "",
      "【地理位置】",
      "国家/地区："+item.country+(item.countryCode!=="未知"?" ("+item.countryCode+")":""),
      "州/省："+item.region,
      "城市："+item.city
    ];
    if(item.timezone)lines.push("时区："+item.timezone);
    if(item.zip)lines.push("邮编："+item.zip);
    if(item.lat!==null&&item.lon!==null)
      lines.push("近似坐标："+item.lat.toFixed(3)+", "+item.lon.toFixed(3));
    lines.push("",
      "【网络归属】",
      "ASN："+item.asn,
      "ISP："+item.isp,
      "运营组织："+item.org,
      "网络类型："+category(item),
      "",
      "【安全与网络特征】",
      feature("机房",item.datacenter),
      feature("移动网络",item.mobile),
      feature("VPN",item.vpn),
      feature("代理",item.proxy),
      feature("Tor",item.tor)
    );
    lines.push("风险评分："+(item.riskScore===null?"无数据":
      item.riskScore+"/100（服务商自有指标，不是节点质量或安全认证）"));
    var local=localInfo(item.ip);
    if(local) {
      lines.push("","【Loon 本地数据库对照】",
        "GeoIP："+local.geo,
        "ASN："+local.asn,
        "ASO："+local.org);
      if(local.geo!=="无数据"&&local.geo!=="未知"&&
         item.countryCode!=="未知"&&
         local.geo.toUpperCase()!==item.countryCode.toUpperCase()) {
        lines.push("提示：本地 GeoIP 与远程情报国家代码不一致，以实际请求日志为准。");
      }
    }
    lines.push("","【查询说明】","数据源："+item.provider);
    if(direct) {
      lines.push("DIRECT 出口 IP："+direct.ip);
      lines.push(item.ip===direct.ip?
        "提示：代理和直连观察到相同出口；请检查当前策略是否选中 DIRECT。":
        "提示：代理与直连出口不同；仍不能据此证明不存在 DNS 泄漏。");
    } else if(args.compare_direct===true&&route!=="DIRECT") {
      lines.push("DIRECT 对照：查询失败或无效，不影响代理出口信息。");
    } else {
      lines.push("DIRECT 对照：默认关闭，未查询真实直连 IP。");
    }
    lines.push("说明：情报来源的地址与机房/VPN/代理标签均可能不准确；出口 IP 不是节点服务器入口 IP。",
      "标签“未标记”不等于检测确认安全；无数据不等于没有风险。");
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
