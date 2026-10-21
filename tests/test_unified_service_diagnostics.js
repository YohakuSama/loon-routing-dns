"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const source = fs.readFileSync(path.join(__dirname, "../scripts/v20261021r6/service-diagnostics.js"), "utf8");
const hosts = {
  Spotify:["open.spotify.com","i.scdn.co"],
  Twitch:["www.twitch.tv","static.twitchcdn.net"],
  Abema:["abema.tv","api.abema.io"],
  BBC:["www.bbc.com","static.bbci.co.uk"],
  Line:["line.me","access.line.me"],
  Reddit:["www.reddit.com","www.redditstatic.com"],
  Linkedin:["www.linkedin.com","static.licdn.com"]
};
function run(service="Spotify", opts={}) {
  const requests=[], dns=[], done=[], timers=[];
  let delayedHttp=null;
  const ctx={
    $argument:{service},
    $done: value=>done.push(value),
    setTimeout:(fn,ms)=>timers.push({fn,ms}),
    $httpClient:{get(req,cb){
      requests.push(req);
      const i=requests.length-1;
      if(opts.httpPending) {delayedHttp=cb;return;}
      const error=opts.errors && opts.errors[i];
      const status=opts.statuses ? opts.statuses[i] : 200;
      cb(error || null,error ? null : {status});
    }}
  };
  if(!opts.dnsAbsent) ctx.$dns={query(req,cb){
    dns.push(req);
    if(opts.dnsPending)return;
    if(opts.dnsError){cb({message:"PRIVATE_DNS_QUERY_EXAMPLE"},null);return;}
    cb(null,{answers:opts.answers===undefined?[{type:"A",value:"192.0.2.1"}]:opts.answers});
  }};
  vm.runInNewContext(source,ctx,{timeout:2000});
  if(opts.fireTimer) for(const timer of timers)timer.fn();
  if(opts.fireLate&&delayedHttp)delayedHttp(null,{status:200});
  return {requests,dns,done,timers};
}
for(const [service,expected] of Object.entries(hosts)){
  const r=run(service,{statuses:[200,404]});
  assert.equal(r.requests.length,2,service);
  assert.equal(r.dns.length,1,service);
  assert.equal(r.done.length,1,service);
  assert.equal(r.dns[0].domain,expected[0],service);
  assert.equal(r.dns[0].protocol,"auto");
  for(let i=0;i<2;i++){
    assert.equal(new URL(r.requests[i].url).hostname,expected[i]);
    assert.equal(r.requests[i].node,service);
    assert.equal(r.requests[i]["auto-cookie"],false);
    assert.equal(r.requests[i]["auto-redirect"],false);
    assert.equal(r.requests[i].insecure,false);
  }
  assert.match(r.done[0].content,/两个 HTTPS 端点均有响应/,service);
  assert.match(r.done[0].content,/HTTP 404/,service);
  assert.match(r.done[0].content,/A 1 \/ AAAA 0/,service);
  assert.doesNotMatch(r.done[0].content,/连接失败|IPv6 故障|地区已解锁|播放成功/,service);
  assert(r.done[0].content.length<220,"dialog too long: "+service);
}
for(const invalid of ["", "DIRECT", "ssh://steal", {}, null, ["Spotify"]]){
 const r=run(invalid);
 assert.equal(r.requests.length,0);
 assert.equal(r.done.length,1);
}
const tls=run("Twitch",{errors:[{message:"TLS certificate failure SECRET_SERVER"},null],statuses:[200,200]});
assert.match(tls.done[0].content,/TLS\/证书错误/);
assert.doesNotMatch(tls.done[0].content,/SECRET_SERVER/);
const server=run("Abema",{statuses:[503,503]});
assert.match(server.done[0].content,/不能判定节点故障/);
assert.doesNotMatch(server.done[0].content,/两个 HTTPS 端点均有响应/);
const dns=run("BBC",{dnsError:true});
assert.match(dns.done[0].content,/DNS：查询失败/);
assert.doesNotMatch(dns.done[0].content,/PRIVATE_DNS_QUERY_EXAMPLE/);
const noDns=run("Line",{dnsAbsent:true});
assert.match(noDns.done[0].content,/Build 988/);
const noIpv6=run("Spotify",{answers:[{type:"A",value:"203.0.113.1"}]});
assert.match(noIpv6.done[0].content,/A 1 \/ AAAA 0/);
const pending=run("Spotify",{httpPending:true,dnsPending:true,fireTimer:true,fireLate:true});
assert.equal(pending.done.length,1,"timeout must complete once");
assert.match(pending.done[0].content,/超时/);
assert.equal(pending.timers[0].ms,19500);
const plugin=fs.readFileSync(path.join(__dirname,"../release/Network_Diagnostics.plugin"),"utf8");
const profile=fs.readFileSync(path.join(__dirname,"../LoonKit.lcf"),"utf8");
assert.match(plugin,/scripts\/v20261021r6\/service-diagnostics\.js/);
assert.match(plugin,/tag="服务连通性诊断"/);
assert.match(plugin,/service = select,"Spotify"/);
assert.match(plugin,/auto_check = switch,false/);
assert.equal(profile.split("\n").filter(x=>x.includes(".plugin, enabled=true")).length,1);
assert.doesNotMatch(profile,/Service_Diagnostics\.plugin, enabled=true/);
assert.match(profile,/8122c6993e3f13a3152449d3d4ec62717a96cded\/release\/Network_Diagnostics\.plugin/);
console.log("Unified manual seven-service diagnostic tests passed");
