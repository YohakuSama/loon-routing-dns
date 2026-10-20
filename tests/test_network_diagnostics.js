/* Mock runtime regression tests of the CURRENT Loon DNS diagnostics. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ROOT = path.resolve(__dirname,"..");
const source = fs.readFileSync(path.join(ROOT,"scripts/v20261020r1/network-diagnostics.js"),"utf8");
let passed=0;
function check(name,fn) {
  try {fn();passed++;console.log("PASS",name);}
  catch(error){process.exitCode=1;console.error("FAIL",name,error);}
}
function run(options={}) {
  const requests=[],results=[],alerts=[],jobs=[],store=options.store||{};
  const ctx={
    console:{log(){}},
    $script:{name:options.auto?"网络切换异常监测":"网络与 DNS 诊断"},
    $persistentStore:{read:key=>store[key]||null,write:(value,key)=>(store[key]=value,true)},
    $notification:{post:(...args)=>alerts.push(args)},
    $done:x=>results.push(x),
    setTimeout(fn,ms){jobs.push({fn,ms});return jobs.length;},
    $httpClient:{
      get(req,cb){
        requests.push(req);
        const fail=req.node==="DIRECT"?options.directFail:options.proxyFail;
        const status=req.node==="DIRECT"?(options.directStatus||204):(options.proxyStatus||204);
        cb(fail?"timeout":null,fail?null:{status},"");
      },
      post(){throw Error("An unsolicited third-party DNS probe must never run");}
    }
    // Intentionally do NOT define clearTimeout: Loon does not guarantee it.
  };
  if(options.native!=="absent")ctx.$dns={query(req,cb){
    requests.push({native:true,request:req});
    if(options.native==="fail")return cb({code:"TIMEOUT",message:"timeout"},null);
    cb(null,{
      protocol:options.protocol||"doh",
      server:options.server||"https://dns.alidns.com/dns-query",
      fromCache:options.cached===true,
      answers:[{type:"A",value:"93.184.215.14"}]
    });
  }};
  vm.runInNewContext(source,ctx,{timeout:2500});
  let loops=0;
  while(jobs.length && ++loops<20) {
    jobs.sort((a,b)=>a.ms-b.ms);
    jobs.shift().fn();
  }
  assert(loops<20,"unbounded timers");
  return {requests,results,alerts,store};
}
check("healthy manual test reports actual configured DoH without clearTimeout",()=>{
  const r=run();
  assert.equal(r.results.length,1);
  assert.match(r.results[0].content,/所测项目正常/);
  assert.match(r.results[0].content,/dns.alidns.com/);
  assert(r.requests.some(x=>x.native));
  assert(!r.requests.some(x=>x.url&&x.url.includes("/dns-query")));
});
check("proxy 301 is an inconclusive redirect, not a false outage",()=>{
  const r=run({proxyStatus:301});
  assert.match(r.results[0].content,/部分项目不可用/);
  assert.match(r.results[0].content,/HTTP 301/);
  assert.doesNotMatch(r.results[0].content,/结果：存在异常项目/);
  const p=r.requests.find(x=>x.node==="Proxy");
  assert.equal(p.url,"https://www.gstatic.com/generate_204");
  assert.equal(p["auto-redirect"],false);
});
check("target 503 proves server responded but does not prove proxy failure",()=>{
  const r=run({proxyStatus:503});
  assert.match(r.results[0].content,/部分项目不可用/);
  assert.match(r.results[0].content,/HTTP 503/);
});
check("Loon auto / https prefix is inconclusive, not a DNS leak",()=>{
  const r=run({protocol:"auto",server:"https://"});
  assert.match(r.results[0].content,/部分项目不可用/);
  assert.match(r.results[0].content,/返回 auto/);
  assert.doesNotMatch(r.results[0].content,/结果：存在异常项目|明文 DNS 查询/);
});
check("cached UDP metadata does not claim a new plaintext lookup",()=>{
  const r=run({protocol:"udp",server:"223.5.5.5:53",cached:true});
  assert.match(r.results[0].content,/缓存解析成功/);
  assert.doesNotMatch(r.results[0].content,/结果：存在异常项目|本次使用普通 DNS 查询/);
});
check("native UDP is flagged as plaintext instead of DoH success",()=>{
  const r=run({protocol:"udp",server:"223.5.5.5:53"});
  assert.match(r.results[0].content,/存在异常项目/);
  assert.match(r.results[0].content,/普通 DNS 查询/);
});
check("unconfigured alternate DoH is not misreported as expected resolver",()=>{
  const r=run({server:"https://cloudflare-dns.com/dns-query"});
  assert.match(r.results[0].content,/部分项目不可用/);
  assert.match(r.results[0].content,/使用加密 DNS，非当前配置预期地址/);
});
check("cached DoH cannot prove this test used an encrypted request",()=>{
  const r=run({cached:true});
  assert.match(r.results[0].content,/部分项目不可用/);
  assert.match(r.results[0].content,/缓存命中/);
});
check("no DNS API cannot be misreported healthy",()=>{
  const r=run({native:"absent"});
  assert.match(r.results[0].content,/部分项目不可用/);
  assert.match(r.results[0].content,/988/);
});
check("native DNS error and proxy failure are detected",()=>{
  const r=run({native:"fail",proxyFail:true});
  assert.match(r.results[0].content,/存在异常项目/);
  assert.match(r.results[0].content,/超时/);
});
check("automatic check has no DNS probe and is silent when healthy",()=>{
  const r=run({auto:true});
  assert.equal(r.results.length,1);
  assert.equal(r.alerts.length,0);
  assert(!r.requests.some(x=>x.native));
  assert(r.requests.every(x=>x.node==="DIRECT"));
});
check("auto notification ignores HTTP 301 on direct network",()=>{
  const r=run({auto:true,directStatus:301});
  assert.equal(r.alerts.length,0);
  assert.equal(r.requests.length,1);
  assert.equal(r.results.length,1);
});
check("automatic double-failure alerts only once per cooldown",()=>{
  const store={};
  const first=run({auto:true,directFail:true,store});
  const second=run({auto:true,directFail:true,store});
  assert.equal(first.alerts.length,1);
  assert.equal(second.alerts.length,0);
  assert.equal(first.requests.length,2);
});
check("diagnostics switches default to privacy-preserving values",()=>{
  const plugin=fs.readFileSync(path.join(ROOT,"release/phase-07/assets/Network_Diagnostics.plugin"),"utf8");
  assert.match(plugin,/auto_check = switch,false/);
  assert.match(plugin,/compare_direct = switch,false/);
  assert.equal(plugin.split("\n").filter(x=>x.startsWith("generic then script(")).length,2);
});
console.log("Current network diagnostic tests:",passed);
