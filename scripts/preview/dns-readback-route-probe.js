/* Loon DNS readback route probe: manual, no configuration mutation.
 * Specifically diagnoses bash.ws HTTPS result fetch after Loon DNS activity.
 * Never disables TLS validation, never forces DIRECT, never certifies leak safety.
 */
(function(){
"use strict";
var BASE="https://bash.ws",finished=false,callbackCount=0,dnsErrors=0;
function errorText(e){
  var t=typeof e==="string"?e:e&&e.message?e.message:String(e||"未知错误");
  return t.replace(/[\u0000-\u001f\u007f]/g," ").slice(0,165);
}
function done(lines){
  if(finished)return;
  finished=true;
  $done({title:"bash.ws HTTPS 读取链路诊断",content:lines.join("\n")});
}
var watchdog=setTimeout(function(){
  done(["结果：未完成（39 秒超时）",
       "DNS 回调："+callbackCount+"/10，DNS 错误："+dnsErrors,
       "请检查 Loon 脚本与请求日志，不能据此判断 DNS 泄漏。"]);
},39000);
function request(url,policy,cb){
  var options={url:url,timeout:8000,alpn:"h1",
    headers:{"Accept":"application/json, text/plain"},
    "auto-cookie":false,"auto-redirect":false};
  if(policy==="Proxy")options.node="Proxy";
  var returned=false;
  try{
    $httpClient.get(options,function(err,response,body){
      if(returned||finished)return;
      returned=true;
      if(err)return cb({ok:false,error:errorText(err),policy:policy||"当前分流"});
      if(Number(response&&response.status)!==200)
        return cb({ok:false,error:"HTTP "+String(response&&response.status||"未知"),policy:policy||"当前分流"});
      if(typeof body!=="string"||body.length>100000)
        return cb({ok:false,error:"响应格式或长度无效",policy:policy||"当前分流"});
      cb({ok:true,body:body,policy:policy||"当前分流"});
    });
  }catch(e){if(!returned)cb({ok:false,error:errorText(e),policy:policy||"当前分流"});}
}
function label(r){
  if(!r.ok)return r.policy+"：失败 — "+r.error;
  try {
    var body=JSON.parse(r.body);
    if(!Array.isArray(body))return r.policy+"：HTTP 已成功，检测结果 JSON 结构未知";
    var count=body.filter(function(x){return x&&x.type==="dns";}).length;
    return r.policy+"：HTTP/TLS 成功，服务端返回 "+count+" 个 DNS 解析器记录";
  }catch(e){return r.policy+"：HTTP/TLS 成功，结果 JSON 无法解析";}
}
function run(id){
  for(var i=1;i<=10;i++)(function(n){
    try {
      $dns.query({domain:n+"."+id+".bash.ws",protocol:"auto",timeout:6500},
        function(err,res){callbackCount++;if(err||!res)dnsErrors++;});
    }catch(e){callbackCount++;dnsErrors++;}
  })(i);
  setTimeout(function(){
    if(finished)return;
    var url=BASE+"/dnsleak/test/"+id+"?json";
    request(url,null,function(auto){
      if(finished)return;
      request(url,"Proxy",function(proxy){
        if(finished)return;
        var lines=[
          "【相同测试会话下的 HTTPS 读取结果】",
          label(auto),
          label(proxy),
          "【DNS 查询】",
          "10 个一次性域名已发起；Loon 回调 "+callbackCount+"/10，错误 "+dnsErrors+"。",
          "【解释】",
          "本测试仅比较 bash.ws 检测结果的 HTTPS 读取链路，并不根据 Proxy 读取成功就判断 DNS 没有泄漏。",
          "当前分流路径与 Proxy 策略可能选择同一节点，也可能不同。未修改 DNS、分流规则或节点选择。",
          "HTTPS 仍正常验证证书；不会强制 DIRECT。",
          "如两种路径均报 TLS 错误，请提供这两行错误信息及 Loon 请求日志，不要公开个人节点信息。"
        ];
        done(lines);
      });
    });
  },4000);
}
if(typeof $dns==="undefined"||!$dns||typeof $dns.query!=="function")
  return done(["当前 Loon 不支持 $dns.query；无法重现本次 DNS 后的结果请求。"]);
request(BASE+"/id",null,function(r){
  if(!r.ok)return done(["无法创建 bash.ws 测试会话："+r.error,"尚未发起 DNS 查询。"]);
  var id=r.body.trim();
  if(!/^[A-Za-z0-9](?:[A-Za-z0-9-]{6,61}[A-Za-z0-9])$/.test(id))
    return done(["bash.ws 会话 ID 格式与预期不同；未发起 DNS 查询。"]);
  run(id);
});
})();
