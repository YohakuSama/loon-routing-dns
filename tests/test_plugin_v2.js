/* Lean Loon plugin v2.0 tests, no network or third-party modules. */
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const ROOT=path.resolve(__dirname,"..");
const code={
  diag:fs.readFileSync(path.join(ROOT,"scripts/v20261018r4/network-diagnostics.js"),"utf8"),
  node:fs.readFileSync(path.join(ROOT,"scripts/v20261018r4/node-intelligence.js"),"utf8")
};
let tests=0;
function check(name,fn) {
  try {fn();tests++;console.log("PASS",name);}
  catch(e){console.error("FAIL",name,e.stack||e);process.exitCode=1;}
}
const query=[0,0,1,0,0,1,0,0,0,0,0,0,7,101,120,97,109,112,108,101,3,99,111,109,0,0,1,0,1];
const answer=new Uint8Array([0,0,129,128,0,1,0,1,0,0,0,0,...query.slice(12),192,12,0,1,0,1,0,0,1,0,0,4,93,184,215,14]);
function harnessDiag(options={}) {
  const requests=[],done=[],notice=[],store=options.store||{};
  const jobs=[],cancelled=new Set();let timerId=0;
  function setT(fn,ms){var id=++timerId;jobs.push({fn,ms,id});return id;}
  const ctx={
    Uint8Array,console:{log(){}},$argument:{},$script:{name:options.auto?"网络切换异常监测":"网络与 DNS 诊断"},
    setTimeout:setT,clearTimeout:id=>cancelled.add(id),
    $httpClient:{
      get(o,cb){requests.push(o);let bad=(o.node==="DIRECT"?options.directFail:options.proxyFail);
        cb(bad?"timeout":null,bad?null:{status:204},"");},
      post(o,cb){requests.push(o);cb(options.dohFail?"timeout":null,
        {status:200},options.dohMalformed?new Uint8Array([1,2]):answer);}
    },
    $persistentStore:{read:k=>store[k]||null,write:(v,k)=>(store[k]=v,true)},
    $notification:{post:(...args)=>notice.push(args)},
    $done:x=>done.push(x)
  };
  if(options.native!=="absent")ctx.$dns={query(o,cb){requests.push({native:true});
    cb(options.native==="fail"?"timeout":null,options.native==="fail"?null:{
      answers:[{type:"A",value:"93.184.215.14"}]});}};
  vm.runInNewContext(code.diag,ctx,{timeout:3000});
  // Process only scheduled callbacks still pending. First automatic delay then retry.
  while(jobs.length){jobs.sort((a,b)=>a.ms-b.ms);const t=jobs.shift();if(!cancelled.has(t.id))t.fn();}
  return {done,notice,requests,store};
}
function harnessNode(options={}) {
  const done=[],requests=[],store={};
  const sample=options.sample||{ip:"203.0.113.8",
    location:{country:"Japan",state:"Tokyo",city:"Tokyo"},
    isp:{asn:"AS64500",isp:"Sample ISP"},risk:{is_datacenter:true,is_mobile:false}};
  const directSample={...sample,ip:"198.51.100.10"};
  const ctx={
    $argument:{target_policy:"Proxy",compare_direct:!!options.direct},
    $environment:{params:options.context||{}},console:{log(){}},
    $persistentStore:{read:k=>store[k]||null,write:(v,k)=>(store[k]=v,true)},
    $httpClient:{get(o,cb){requests.push(o);
      if(options.failPrimary && o.url.includes("ipquery"))return cb(null,{status:429},"");
      if(options.failAll)return cb("timeout");
      if(o.url.includes("ipwho.is"))return cb(null,{status:200},JSON.stringify({
        ip:o.node==="DIRECT"?"198.51.100.10":"203.0.113.8",country:"Japan",city:"Tokyo",
        connection:{asn:64500,isp:"Backup ISP"}}));
      cb(null,{status:200},JSON.stringify(o.node==="DIRECT"?directSample:sample));}},
    $done:r=>done.push(r)
  };
  vm.runInNewContext(code.node,ctx,{timeout:3000});
  return {done,requests,store};
}
check("manual: native DNS failure marks overall result abnormal",()=>{
  const r=harnessDiag({native:"fail"});
  assert.equal(r.done.length,1);
  assert.match(r.done[0].content,/结果：存在异常项目/);
  assert.match(r.done[0].content,/✗ Loon 原生 DNS：查询失败/);
});
check("manual: missing native DNS marked unsupported rather than healthy",()=>{
  const r=harnessDiag({native:"absent"});
  assert.match(r.done[0].content,/结果：部分项目不可用/);
  assert.match(r.done[0].content,/— Loon 原生 DNS/);
});
check("manual: success has four checks and DNS-leak disclaimer",()=>{
  const r=harnessDiag({});
  assert.equal(r.done.length,1);
  assert.equal(r.requests.filter(x=>x.native).length,1);
  assert(r.requests.some(x=>x.node==="Proxy"));
  assert.match(r.done[0].content,/结果：所测项目正常/);
  assert.match(r.done[0].content,/不能据此判断 DNS 泄漏/);
});
check("manual: malformed DoH payload is an abnormal result",()=>{
  const r=harnessDiag({dohMalformed:true});
  assert.match(r.done[0].content,/✗ DoH 服务/);
  assert.match(r.done[0].content,/结果：存在异常项目/);
});
check("network change: healthy means no notification and no proxy probing",()=>{
  const r=harnessDiag({auto:true});
  assert.equal(r.done.length,1);
  assert.equal(r.notice.length,0);
  assert(r.requests.every(x=>x.node==="DIRECT"));
});
check("network change: repeat verified failures are throttled",()=>{
  const store={};
  const a=harnessDiag({auto:true,dohFail:true,store});
  const b=harnessDiag({auto:true,dohFail:true,store});
  assert.equal(a.notice.length,1);
  assert.equal(b.notice.length,0);
  assert.equal(a.done.length,1);
  assert.equal(b.done.length,1);
});
check("node details: concise output, no direct lookup by default",()=>{
  const r=harnessNode({});
  assert.equal(r.requests.length,1);
  assert.equal(r.requests[0].node,"Proxy");
  assert.match(r.done[0].content,/地区：Japan · Tokyo/);
  assert.match(r.done[0].content,/网络类型：机房或云服务/);
  assert.doesNotMatch(r.done[0].content,/时区：|邮编|风险评分|近似坐标/);
});
check("node details: native node context overrides configured selector",()=>{
  const r=harnessNode({context:{node:"Tokyo-01"}});
  assert.equal(r.requests[0].node,"Tokyo-01");
});
check("node details: DIRECT lookup occurs only when explicitly enabled",()=>{
  const r=harnessNode({direct:true});
  assert.equal(r.requests.length,2);
  assert.equal(r.requests[1].node,"DIRECT");
  assert.match(r.done[0].content,/直连出口 IP/);
});
check("node details: 429 primary falls back to location-only provider",()=>{
  const r=harnessNode({failPrimary:true});
  assert.equal(r.requests.length,2);
  assert.match(r.done[0].content,/ipwho.is/);
  assert.match(r.done[0].content,/未知（情报来源未提供相关字段）/);
});
check("node details: invalid IP response is refused",()=>{
  const r=harnessNode({sample:{ip:"2001:::db8",location:{country:"Japan"},isp:{asn:"AS1"}}});
  assert.equal(r.requests.length,2);
  assert.match(r.done[0].content,/ipwho.is/);
});
check("node details: all API failures do not silently use DIRECT",()=>{
  const r=harnessNode({failAll:true});
  assert(r.requests.every(x=>x.node==="Proxy"));
  assert.match(r.done[0].content,/没有把 DIRECT 地址冒充节点出口/);
});
check("plugin exposes exactly two manual actions and three settings",()=>{
  const plugin=fs.readFileSync(path.join(ROOT,"plugins/v20261018r4/Network_Diagnostics.plugin"),"utf8");
  assert.equal(plugin.split("\n").filter(x=>x.startsWith("generic then script")).length,2);
  assert.equal(plugin.split("\n").filter(x=>x.startsWith("network-changed then script")).length,1);
  assert.match(plugin,/auto_check = switch,false/);
  assert(!/模拟网络切换|状态与设置摘要|primary_ip_url|cache_seconds/.test(plugin));
  const expected=new Set(["auto_check","target_policy","compare_direct"]);
  const actual=new Set(plugin.split("[Argument]")[1].split("[Script]")[0].split("\n")
    .filter(x=>/^[a-z_]+\s*=/.test(x)).map(x=>x.split("=")[0].trim()));
  assert.deepEqual(actual,expected);
});
console.log("Lean plugin v2 regression tests:",tests);
