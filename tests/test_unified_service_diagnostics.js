"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname,"..");
const source = fs.readFileSync(path.join(root,"scripts/v20261021r7/service-diagnostics.js"),"utf8");
const cases = {
  "Spotify（音乐）":{policy:"Spotify", hosts:["open.spotify.com","i.scdn.co"]},
  "Twitch（直播）":{policy:"Twitch", hosts:["www.twitch.tv","static.twitchcdn.net"]},
  "Abema（视频）":{policy:"Abema", hosts:["abema.tv","api.abema.io"]},
  "BBC（资讯）":{policy:"BBC", hosts:["www.bbc.com","static.bbci.co.uk"]},
  "LINE（通讯）":{policy:"Line", hosts:["line.me","access.line.me"]},
  "Reddit（社区）":{policy:"Reddit", hosts:["www.reddit.com","www.redditstatic.com"]},
  "LinkedIn（职场）":{policy:"Linkedin", hosts:["www.linkedin.com","static.licdn.com"]}
};
function run(service,options={}) {
  const requests=[],dns=[],complete=[],timers=[];
  let pending=null;
  const ctx={
    $argument: typeof service==="undefined" ? {} : {service},
    $done:x=>complete.push(x),
    setTimeout:(fn,ms)=>timers.push({fn,ms}),
    $httpClient:{get(req,cb){
      requests.push(req);
      if(options.httpPending){pending=cb;return;}
      const index=requests.length-1;
      const error=options.errors && options.errors[index];
      const status=options.statuses ? options.statuses[index] : 200;
      cb(error||null,error?null:{status});
    }}
  };
  if(!options.noDns)ctx.$dns={query(req,cb){
    dns.push(req);
    if(options.dnsPending)return;
    if(options.dnsError)return cb({message:"SECRET_DNS_TOKEN"},null);
    cb(null,{answers: options.records === undefined ? [{type:"A",value:"192.0.2.1"}]:options.records});
  }};
  vm.runInNewContext(source,ctx,{timeout:1800});
  if(options.fireTimer)timers.forEach(x=>x.fn());
  if(options.fireLate && pending)pending(null,{status:200});
  return {requests,dns,complete,timers};
}
for(const [name,item] of Object.entries(cases)){
  const r=run(name,{statuses:[200,404]});
  assert.equal(r.requests.length,2,name);
  assert.equal(r.dns.length,1,name);
  assert.equal(r.complete.length,1,name);
  assert.equal(r.dns[0].domain,item.hosts[0]);
  assert.equal(r.dns[0].protocol,"auto");
  r.requests.forEach((req,i)=>{
    assert.equal(new URL(req.url).hostname,item.hosts[i]);
    assert.equal(req.node,item.policy);
    assert.equal(req["auto-cookie"],false);
    assert.equal(req["auto-redirect"],false);
    assert.equal(req.insecure,false);
  });
  const result=r.complete[0];
  assert.match(result.title,/服务检测/);
  assert.match(result.title,/已收到响应/);
  assert.match(result.content,/网站：可连接/);
  assert.match(result.content,/相关资源：有响应/);
  assert.match(result.content,/DNS 解析：正常/);
  assert.doesNotMatch(result.content,/HTTP 404|A 1|AAAA 0|节点故障|播放与账号|网络相关故障/);
  assert(result.content.length<=135,"unnecessary copy: "+name);
}
for(const value of [undefined,"请选择服务","",null,{},["Spotify（音乐）"],"Spotify","DIRECT"]){
  const r=run(value);
  assert.equal(r.requests.length,0);
  assert.equal(r.dns.length,0);
  assert.equal(r.complete.length,1);
  assert.match(r.complete[0].content,/先.*选择/);
}
const okay=run("Spotify（音乐）");
assert.match(okay.complete[0].title,/连接正常/);
const dnsFail=run("Twitch（直播）",{dnsError:true});
assert.match(dnsFail.complete[0].title,/DNS 检查异常/);
assert.match(dnsFail.complete[0].content,/DNS 解析：解析失败/);
assert.doesNotMatch(dnsFail.complete[0].content,/SECRET_DNS_TOKEN/);
const noDns=run("BBC（资讯）",{noDns:true});
assert.match(noDns.complete[0].content,/当前版本不支持检测/);
assert.doesNotMatch(noDns.complete[0].title,/连接正常/);
const justA=run("LINE（通讯）",{records:[{type:"A",value:"192.0.2.100"}]});
assert.match(justA.complete[0].content,/DNS 解析：正常/);
assert.doesNotMatch(justA.complete[0].content,/IPv6|AAAA/);
const emptyDns=run("Reddit（社区）",{records:[]});
assert.match(emptyDns.complete[0].content,/DNS 解析：暂未确认/);
assert.doesNotMatch(emptyDns.complete[0].title,/DNS 检查异常/);
const server=run("Abema（视频）",{statuses:[200,503]});
assert.match(server.complete[0].title,/服务响应异常/);
assert.match(server.complete[0].content,/响应异常（HTTP 503）/);
assert.match(server.complete[0].content,/稍后重试/);
const fail=run("LinkedIn（职场）",{errors:[{message:"TLS SECRET_NODE_ADDRESS"},null]});
assert.match(fail.complete[0].title,/部分连接失败/);
assert.match(fail.complete[0].content,/安全连接失败/);
assert.doesNotMatch(fail.complete[0].content,/SECRET_NODE_ADDRESS/);
const time=run("Spotify（音乐）",{httpPending:true,dnsPending:true,fireTimer:true,fireLate:true});
assert.equal(time.complete.length,1,"late callbacks must not duplicate popup");
assert.match(time.complete[0].title,/检查未完成/);
assert.equal(time.timers[0].ms,19500);
const plugin=fs.readFileSync(path.join(root,"release/Network_Diagnostics.plugin"),"utf8");
const profile=fs.readFileSync(path.join(root,"LoonKit.lcf"),"utf8");
assert.match(plugin,/service = select,"请选择服务","Spotify（音乐）"/);
assert.match(plugin,/tag="服务检测"/);
assert.match(plugin,/scripts\/v20261021r7\/service-diagnostics\.js/);
assert.doesNotMatch(plugin,/service = select,"Spotify"/);
assert.equal(profile.split("\n").filter(x=>x.includes(".plugin, enabled=true")).length,1);
assert.doesNotMatch(profile,/\/release\/Service_Diagnostics\.plugin, enabled=true/);
console.log("Professional service copy and manual probe regressions passed");
