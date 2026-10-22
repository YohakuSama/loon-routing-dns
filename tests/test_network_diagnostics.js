/* Regression tests: single-node network check, HTML presentation, native DNS and automatic monitoring. */
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const ROOT=path.resolve(__dirname,"..");
const source=fs.readFileSync(path.join(ROOT,"scripts/v20261022r9/network-diagnostics.js"),"utf8");
let passed=0;
function check(name,fn){
  try{fn();passed++;console.log("PASS",name);}
  catch(e){process.exitCode=1;console.error("FAIL",name,e);}
}
function run(options={}){
  const requests=[],results=[],alerts=[],timers=[],store=options.store||{};
  let selected=options.selections||{Proxy:"Auto",Auto:"JP Individual"};
  const cfg={
    getConfig:()=>JSON.stringify({all_policy_groups:options.groups||["Proxy","Auto","Fallback","ALL_Filter"],
      policy_select:options.snapshotSelect===undefined?selected:options.snapshotSelect}),
    getSelectedPolicy:name=>options.noSelectionApi?"":selected[name]||""
  };
  const ctx={
    $script:{name:options.auto?"网络切换异常监测":"网络检测"},
    $environment:{params:options.params===undefined?{node:"JP Individual"}:options.params},
    $argument:{target_policy:options.targetPolicy||"Proxy"},
    $config:options.noConfig?undefined:cfg,
    $persistentStore:{read:key=>store[key]||null,write:(v,key)=>(store[key]=v,true)},
    $notification:{post:(...args)=>alerts.push(args)},
    $done:v=>results.push(v),
    setTimeout:(fn,ms)=>timers.push({fn,ms}),
    $httpClient:{
      get(req,cb){
        requests.push(req);
        const failure=req.node==="DIRECT"?options.directFail:options.nodeFail;
        const status=req.node==="DIRECT"?(options.directStatus===undefined?204:options.directStatus):
          (options.nodeStatus===undefined?204:options.nodeStatus);
        const error=failure?"timeout":null;
        cb(error,error?null:{status},"");
      },
      post(){throw Error("unexpected diagnostic POST");}
    },
    console:{log(){}}
  };
  if(options.dns!=="missing"){
    ctx.$dns={query(req,cb){
      requests.push({native:true,request:req});
      if(options.dns==="fail")return cb({code:"TIMEOUT",message:"timeout"},null);
      cb(null,{protocol:options.protocol||"doh",
        server:options.server===undefined?"https://dns.alidns.com/dns-query":options.server,
        fromCache:options.cached===true,
        answers:options.answers===undefined?[{type:"A",value:"93.184.215.14"}]:options.answers});
    }};
  }
  vm.runInNewContext(source,ctx,{timeout:2500});
  // Auto monitoring includes delayed checks; manual network checks finish synchronously.
  if(options.auto){
    let count=0;
    while(timers.length&&++count<15){timers.sort((a,b)=>a.ms-b.ms);timers.shift().fn();}
    assert(count<15,"timer loop");
  }
  return {requests,results,alerts,store,timers};
}
function manual(r){
  assert.equal(r.results.length,1);
  const result=r.results[0];
  assert.equal(result.title,"网络检测");
  assert(typeof result.content==="string");
  assert.equal(result.htmlMessage,undefined);
  assert(result.content.includes("v6.5.1"));
  return result;
}
check("single node from context, same measurement target for direct and selected node",()=>{
  const r=run(),p=manual(r);
  const req=r.requests.filter(x=>!x.native);
  assert.equal(req.length,2);
  assert.equal(req[0].node,"DIRECT");
  assert.equal(req[1].node,"JP Individual");
  assert(req.every(x=>x.url==="https://www.gstatic.com/generate_204"));
  assert(req.every(x=>x.timeout===6500&&x["auto-redirect"]===false));
  assert(!req.some(x=>x.node==="Proxy"));
  assert.match(p.content,/节点：JP Individual/);
  assert.match(p.content,/网络正常/);
  assert.match(p.content,/www\.gstatic\.com\/generate_204/);
  assert.match(p.content,/解析成功/);
});
check("node-menu context overrides fallback policy group",()=>{
  const r=run({params:{node:"HK 01",nodeInfo:{name:"JP stale"}}});
  manual(r);
  assert.equal(r.requests.filter(x=>!x.native)[1].node,"HK 01");
});
check("nodeInfo supports Loon's current node-menu metadata",()=>{
  const r=run({params:{nodeInfo:{name:"UK-Node"}}});
  manual(r);
  assert.equal(r.requests.filter(x=>!x.native)[1].node,"UK-Node");
});
check("plugin entry resolves nested Proxy / Auto group to concrete selected node",()=>{
  const r=run({params:{},targetPolicy:"Proxy",selections:{Proxy:"Auto",Auto:"SG Node"}});
  const p=manual(r);assert.match(p.content,/节点：SG Node/);
  assert.equal(r.requests.filter(x=>!x.native)[1].node,"SG Node");
});
check("selection snapshot fallback works when selected-policy API returns empty",()=>{
  const r=run({params:{},targetPolicy:"Proxy",noSelectionApi:true,
    snapshotSelect:{Proxy:"Auto",Auto:"KR Node"}});
  manual(r);assert.equal(r.requests.filter(x=>!x.native)[1].node,"KR Node");
});
check("missing policy selection never masquerades group Proxy as a node",()=>{
  const r=run({params:{},targetPolicy:"Proxy",selections:{}});
  assert.equal(r.results.length,1);
  assert.equal(r.requests.length,0);
  assert.match(r.results[0].content,/单个节点/);
});
check("custom unknown policy group without selection fails closed",()=>{
  const r=run({params:{},targetPolicy:"MyGroup",groups:["MyGroup"],selections:{}});
  assert.equal(r.requests.length,0);
  assert.match(r.results[0].content,/具体节点/);
});
check("DIRECT or REJECT is not reported as a proxy node",()=>{
  for(const leaf of ["DIRECT","REJECT"]){
    const r=run({params:{},targetPolicy:"Proxy",selections:{Proxy:leaf}});
    assert.equal(r.requests.length,0);
    assert.match(r.results[0].content,/单个节点/);
  }
});
check("cycle in policy selections fails closed",()=>{
  const r=run({params:{},selections:{Proxy:"Auto",Auto:"Proxy"}});
  assert.equal(r.requests.length,0);
});
check("native popup returns plain text and never injects HTML",()=>{
  const r=run({params:{node:'<script>alert("x")</script> Node'}});
  const p=manual(r);
  assert.equal(p.htmlMessage,undefined);
  assert.match(p.content,/Node/);
});
check("captive portal HTTP 200 is flagged as uncertain, not healthy",()=>{
  const r=run({nodeStatus:200}),p=manual(r);
  assert.match(p.content,/部分结果需确认/);
  assert.match(p.content,/响应异常（HTTP 200）/);
  assert(!p.content.includes("检测正常"));
});
check("HTTP 301 is inconclusive rather than a disconnected node",()=>{
  const r=run({nodeStatus:301}),p=manual(r);
  assert.match(p.content,/HTTP 301/);
  assert.match(p.content,/部分结果需确认/);
});
check("HTTP 503 is uncertain, not a proxy outage verdict",()=>{
  const r=run({nodeStatus:503}),p=manual(r);
  assert.match(p.content,/HTTP 503/);
  assert.match(p.content,/部分结果需确认/);
});
check("timeout on node reports failure without changing selected policy",()=>{
  const r=run({nodeFail:true}),p=manual(r);
  assert.match(p.content,/部分检测失败/);
  assert.match(p.content,/节点请求：失败.*超时/);
});
check("native DoH metadata and success are retained",()=>{
  const r=run(),p=manual(r);
  assert.match(p.content,/解析成功 · DoH/);
  assert(r.requests.some(x=>x.native));
  assert(!r.requests.some(x=>x.url&&x.url.includes("/dns-query")));
});
check("cached DNS does not assert that a new query was sent",()=>{
  const p=manual(run({cached:true}));
  assert.match(p.content,/解析成功（缓存）/);
});
check("user-selected UDP is accepted without provider-specific warnings",()=>{
  const p=manual(run({protocol:"udp",server:"223.5.5.5:53"}));
  assert.match(p.content,/解析成功 · 普通 DNS/);
  assert(!/不是配置|AliDNS/.test(p.content));
});
check("custom DoT and DoH metadata remain supported",()=>{
  const dot=manual(run({protocol:"auto",server:"tls://one.one.one.one"}));
  assert.match(dot.content,/解析成功 · DoT/);
  const doh=manual(run({protocol:"auto",server:"https://example.org/custom-query"}));
  assert.match(doh.content,/解析成功 · DoH/);
});
check("missing native DNS API is not falsely healthy",()=>{
  const p=manual(run({dns:"missing"}));
  assert.match(p.content,/部分结果需确认/);
  assert.match(p.content,/当前 Loon 版本不支持 DNS 检测/);
});
check("DNS timeout remains an explicit failure",()=>{
  const p=manual(run({dns:"fail"}));
  assert.match(p.content,/部分检测失败/);
  assert.match(p.content,/查询失败/);
});
check("empty DNS answers are not silently accepted",()=>{
  const p=manual(run({answers:[{type:"A",value:""}]}));
  assert.match(p.content,/没有获得有效的解析地址/);
});
check("automatic network-change checks stay DIRECT-only and quiet when healthy",()=>{
  const r=run({auto:true});
  assert.equal(r.results.length,1);
  assert.equal(r.alerts.length,0);
  assert(r.requests.every(x=>x.node==="DIRECT"));
  assert(r.requests.every(x=>x.url==="http://wifi.vivo.com.cn/generate_204"));
});
check("auto monitor warns on consecutive direct failures only once per cooldown",()=>{
  const store={};
  const first=run({auto:true,directFail:true,store}),second=run({auto:true,directFail:true,store});
  assert.equal(first.alerts.length,1);assert.equal(second.alerts.length,0);
  assert.equal(first.requests.length,2);
});
check("auto monitor treats redirects as inconclusive and does not notify",()=>{
  const r=run({auto:true,directStatus:301});
  assert.equal(r.alerts.length,0);assert.equal(r.requests.length,1);
});
check("plugin points to the current node-specific diagnostic script",()=>{
  const plugin=fs.readFileSync(path.join(ROOT,"release/Network_Diagnostics.plugin"),"utf8");
  assert(plugin.includes("scripts/v20261022r9/network-diagnostics.js"));
  assert.equal(plugin.split("\n").filter(x=>x.startsWith("generic then script(")).length,3);
  assert.match(plugin,/auto_check = switch,false/);
});
console.log("Single-node network checks:",passed);
