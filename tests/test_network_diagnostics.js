/* Loon network and DNS diagnostic mock-runtime regressions. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ROOT = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(ROOT, "scripts/v20261018r11/network-diagnostics.js"), "utf8");
const query = [0,0,1,0,0,1,0,0,0,0,0,0,7,101,120,97,109,112,108,101,3,99,111,109,0,0,1,0,1];
const validAnswer = new Uint8Array([0,0,129,128,0,1,0,1,0,0,0,0,...query.slice(12),192,12,0,1,0,1,0,0,1,0,0,4,93,184,215,14]);
let passed = 0;
function check(name, fn) {
  try { fn(); passed++; console.log("PASS", name); }
  catch (e) { console.error("FAIL", name, e); process.exitCode=1; }
}
function run(options={}) {
  const requests=[],results=[],alerts=[],jobs=[],cancelled=new Set(),store=options.store||{};
  let nextTimer=0;
  const ctx={
    Uint8Array,
    console:{log(){}},
    $argument:{},
    $script:{name:options.auto?"网络切换异常监测":"网络与 DNS 诊断"},
    setTimeout(fn,ms){const id=++nextTimer;jobs.push({id,fn,ms});return id;},
    clearTimeout(id){cancelled.add(id);},
    $httpClient:{
      get(req,cb){
        requests.push(req);
        const bad=req.node==="DIRECT"?options.directFail:options.proxyFail;
        cb(bad?"timeout":null,bad?null:{status:204},"");
      },
      post(req,cb){
        requests.push(req);
        cb(options.dohFail?"timeout":null,options.dohFail?null:{status:200},
           options.badDoH?new Uint8Array([1,2]):validAnswer);
      }
    },
    $persistentStore:{read:k=>store[k]||null,write:(v,k)=>(store[k]=v,true)},
    $notification:{post:(...a)=>alerts.push(a)},
    $done:response=>results.push(response)
  };
  if(options.native!=="absent")ctx.$dns={query(req,cb){
    requests.push({native:true,request:req});
    cb(options.native==="fail"?"timeout":null,options.native==="fail"?null:
       {answers:[{type:"A",value:"93.184.215.14"}]});
  }};
  vm.runInNewContext(source,ctx,{timeout:2500});
  while(jobs.length){
    jobs.sort((a,b)=>a.ms-b.ms);
    const task=jobs.shift();
    if(!cancelled.has(task.id))task.fn();
  }
  return {requests,results,alerts,store};
}
check("healthy manual test includes DIRECT Proxy DoH and native DNS",()=>{
  const r=run();
  assert.equal(r.results.length,1);
  assert.match(r.results[0].content,/结果：所测项目正常/);
  assert.match(r.results[0].content,/直连网络/);
  assert.match(r.results[0].content,/代理策略 Proxy/);
  assert.match(r.results[0].content,/DoH 服务/);
  assert.match(r.results[0].content,/Loon 原生 DNS/);
  assert.equal(r.requests.filter(x=>x.native).length,1);
});
check("native DNS failure marks full result abnormal",()=>{
  const r=run({native:"fail"});
  assert.match(r.results[0].content,/结果：存在异常项目/);
  assert.match(r.results[0].content,/✗ Loon 原生 DNS：查询失败/);
});
check("unsupported native DNS is not misreported healthy",()=>{
  const r=run({native:"absent"});
  assert.match(r.results[0].content,/结果：部分项目不可用/);
  assert.match(r.results[0].content,/— Loon 原生 DNS/);
});
check("malformed DoH response fails visibly",()=>{
  const r=run({badDoH:true});
  assert.match(r.results[0].content,/结果：存在异常项目/);
  assert.match(r.results[0].content,/DNS 响应无效/);
});
check("DIRECT HTTP failure marks result abnormal",()=>{
  const r=run({directFail:true});
  assert.match(r.results[0].content,/结果：存在异常项目/);
  assert.match(r.results[0].content,/直连网络：超时/);
});
check("proxy HTTP failure does not get hidden by other successes",()=>{
  const r=run({proxyFail:true});
  assert.match(r.results[0].content,/结果：存在异常项目/);
  assert.match(r.results[0].content,/代理策略 Proxy：超时/);
});
check("automatic healthy check is silent and never probes Proxy",()=>{
  const r=run({auto:true});
  assert.equal(r.results.length,1);
  assert.equal(r.alerts.length,0);
  assert(r.requests.every(x=>x.node==="DIRECT"));
});
check("automatic DoH failures alert only once within cooldown",()=>{
  const store={};
  const first=run({auto:true,dohFail:true,store});
  const second=run({auto:true,dohFail:true,store});
  assert.equal(first.alerts.length,1);
  assert.equal(second.alerts.length,0);
  assert.equal(first.results.length,1);
  assert.equal(second.results.length,1);
});
check("monitoring and IP comparison remain opt-in plugin settings",()=>{
  const plugin=fs.readFileSync(path.join(ROOT,"plugins/Network_Diagnostics.plugin"),"utf8");
  assert.match(plugin,/auto_check = switch,false/);
  assert.match(plugin,/compare_direct = switch,false/);
  assert.equal(plugin.split("\n").filter(x=>x.startsWith("generic then script(")).length,2);
  assert.equal(plugin.split("\n").filter(x=>x.startsWith("network-changed then script(")).length,1);
});
console.log("Current network diagnostic tests:",passed);
