/* Mock runtime regression tests of the CURRENT Loon DNS diagnostics. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ROOT = path.resolve(__dirname,"..");
const source = fs.readFileSync(path.join(ROOT,"scripts/v20261021r3/network-diagnostics.js"),"utf8");
let passed=0;
function check(name,fn) {
  try {fn();passed++;console.log("PASS",name);}
  catch(error){process.exitCode=1;console.error("FAIL",name,error);}
}
function run(options={}) {
  const requests=[],results=[],alerts=[],jobs=[],store=options.store||{};
  const ctx={
    console:{log(){}},
    $script:{name:options.auto?"网络切换异常监测":"网络检测"},
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
      server:options.server===undefined?"https://dns.alidns.com/dns-query":options.server,
      fromCache:options.cached===true,
      answers:options.answers===undefined?[{type:"A",value:"93.184.215.14"}]:options.answers
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
check("healthy manual test reports DoH address without claiming capture",()=>{
  const r=run();
  assert.equal(r.results.length,1);
  assert.equal(r.results[0].title,"网络检测");
  assert.match(r.results[0].content,/网络与 DNS 检测正常/);
  assert.match(r.results[0].content,/解析成功 · DoH/);
  assert(r.requests.some(x=>x.native));
  assert(!r.requests.some(x=>x.url&&x.url.includes("/dns-query")));
});
check("proxy 301 is an inconclusive redirect, not a false outage",()=>{
  const r=run({proxyStatus:301});
  assert.match(r.results[0].content,/部分项目待确认/);
  assert.match(r.results[0].content,/HTTP 301/);
  assert.doesNotMatch(r.results[0].content,/连接或解析失败/);
  const p=r.requests.find(x=>x.node==="Proxy");
  assert.equal(p.url,"https://www.gstatic.com/generate_204");
  assert.equal(p["auto-redirect"],false);
});
check("target 503 proves server responded but does not prove proxy failure",()=>{
  const r=run({proxyStatus:503});
  assert.match(r.results[0].content,/部分项目待确认/);
  assert.match(r.results[0].content,/HTTP 503/);
});
check("Loon auto / https prefix is inconclusive, not a DNS leak",()=>{
  const r=run({protocol:"auto",server:"https://"});
  assert.match(r.results[0].content,/网络与 DNS 检测正常/);
  assert.match(r.results[0].content,/已解析，但无法确认所用 DNS 传输方式/);
  assert.doesNotMatch(r.results[0].content,/连接或解析失败|明文 DNS 查询/);
});
check("cached UDP metadata does not claim a new plaintext lookup",()=>{
  const r=run({protocol:"udp",server:"223.5.5.5:53",cached:true});
  assert.match(r.results[0].content,/解析成功（缓存）/);
  assert.match(r.results[0].content,/网络与 DNS 检测正常/);
  assert.doesNotMatch(r.results[0].content,/结果：检测发现异常|本次使用普通 DNS 查询/);
});
check("both HTTP 204 probes and ambiguous auto DNS are not an outage",()=>{
  const r=run({protocol:"auto",server:"https://"});
  assert.match(r.results[0].content,/网络与 DNS 检测正常/);
  assert.match(r.results[0].content,/直连网络：正常/);
  assert.match(r.results[0].content,/代理策略 Proxy：正常/);
  assert.doesNotMatch(r.results[0].content,/部分项目不可用|存在异常项目/);
});
check("auto DNS with a full HTTPS resolver address is unverified",()=>{
  const r=run({protocol:"auto",server:"https://dns.alidns.com/dns-query"});
  assert.match(r.results[0].content,/DoH/);
  assert.match(r.results[0].content,/网络与 DNS 检测正常/);
});
check("user-selected UDP resolves normally without false alert",()=>{
  const r=run({protocol:"udp",server:"223.5.5.5:53"});
  assert.match(r.results[0].content,/网络与 DNS 检测正常/);
  assert.match(r.results[0].content,/解析成功 · 普通 DNS/);
  assert.match(r.results[0].content,/解析成功 · 普通 DNS/);
});
check("custom DoH resolver is accepted without any provider warning",()=>{
  const r=run({server:"https://cloudflare-dns.com/dns-query"});
  assert.match(r.results[0].content,/网络与 DNS 检测正常/);
  assert.match(r.results[0].content,/DoH/);
  assert.doesNotMatch(r.results[0].content,/AliDNS|不是配置|请确认/);
});
check("cached DoH cannot prove this test used an encrypted request",()=>{
  const r=run({cached:true});
  assert.match(r.results[0].content,/网络与 DNS 检测正常/);
  assert.match(r.results[0].content,/缓存/);
});
check("no DNS API cannot be misreported healthy",()=>{
  const r=run({native:"absent"});
  assert.match(r.results[0].content,/部分项目待确认/);
  assert.match(r.results[0].content,/当前 Loon 版本不支持 DNS 检测/);
});
check("native DNS error and proxy failure are detected",()=>{
  const r=run({native:"fail",proxyFail:true});
  assert.match(r.results[0].content,/连接或解析失败/);
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
  assert.equal(first.alerts[0][0],"Loon 网络切换提醒");
  assert.equal(first.alerts[0][1],"直连连接连续失败");
  assert.match(first.alerts[0][2],/网络切换后连续两次连接失败/);
});

check("diagnostics switches default to privacy-preserving values",()=>{
  const plugin=fs.readFileSync(path.join(ROOT,"release/Network_Diagnostics.plugin"),"utf8");
  assert.match(plugin,/auto_check = switch,false/);
  assert.match(plugin,/compare_direct = switch,false/);
  assert.equal(plugin.split("\n").filter(x=>x.startsWith("generic then script(")).length,3);
  assert.doesNotMatch(plugin,/service = select|请选择服务/);
  assert.match(plugin,/scripts\/v20261022r7\/media-unlock\.js/);
});

check("HTTP 200 on generate_204 endpoint is not reported as healthy",()=>{
  const r=run({directStatus:200});
  assert.match(r.results[0].content,/部分项目待确认/);
  assert.match(r.results[0].content,/HTTP 200/);
  assert.match(r.results[0].content,/可能需要网络认证/);
});
check("auto with any valid HTTPS resolver is identified as DoH",()=>{
  const r=run({protocol:"auto",server:"https://dns.alidns.com/dns-query"});
  assert.match(r.results[0].content,/网络与 DNS 检测正常/);
  assert.match(r.results[0].content,/解析成功 · DoH/);
  assert.doesNotMatch(r.results[0].content,/已解析，但无法确认所用 DNS 传输方式/);
});
check("unknown or truncated auto HTTPS DNS does not certify DoH",()=>{
  const r=run({protocol:"auto",server:"https://"});
  assert.match(r.results[0].content,/已解析，但无法确认所用 DNS 传输方式/);
  assert.doesNotMatch(r.results[0].content,/解析成功 · DoH/);
});
check("user-selected ordinary DNS is not treated as a config violation",()=>{
  const r=run({protocol:"udp",server:"223.5.5.5:53"});
  assert.match(r.results[0].content,/解析成功 · 普通 DNS/);
  assert.match(r.results[0].content,/解析成功 · 普通 DNS/);
  assert.match(r.results[0].content,/网络与 DNS 检测正常/);
  assert.doesNotMatch(r.results[0].content,/连接或解析失败/);
});
check("an empty DNS address does not infer DoH or normal UDP",()=>{
  const r=run({protocol:"auto",server:""});
  assert.match(r.results[0].content,/已解析，但无法确认所用 DNS 传输方式/);
  assert.doesNotMatch(r.results[0].content,/解析成功 · DoH/);
});
check("no A or AAAA value is a DNS failure even with record type",()=>{
  const r=run({answers:[{type:"A",value:""}]});
  assert.match(r.results[0].content,/连接或解析失败/);
  assert.match(r.results[0].content,/没有获得有效的解析地址/);
});

check("custom DoH servers never trigger AliDNS mismatch tips",()=>{
  for(const server of ["https://cloudflare-dns.com/dns-query","https://dns.google/dns-query","https://example.org/custom-query"]){
    const r=run({protocol:"auto",server});
    assert.match(r.results[0].content,/解析成功 · DoH/);
    assert.doesNotMatch(r.results[0].content,/提示：|AliDNS|不符合配置|不是配置/);
  }
});
check("user-selected DoT and UDP do not trigger provider mismatch tips",()=>{
  const dot=run({protocol:"auto",server:"tls://one.one.one.one"});
  assert.match(dot.results[0].content,/解析成功 · DoT/);
  assert.doesNotMatch(dot.results[0].content,/提示：|AliDNS/);
  const udp=run({protocol:"udp",server:"1.1.1.1:53"});
  assert.match(udp.results[0].content,/解析成功 · 普通 DNS/);
  assert.doesNotMatch(udp.results[0].content,/提示：|AliDNS/);
});

console.log("Current network diagnostic tests:",passed);
