/* Console v1.3 regression tests: no third-party dependencies. */
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const load=p=>fs.readFileSync(path.join(root,p),"utf8");
const diagnostic=load("scripts/network-diagnostics.js");
const intel=load("scripts/node-intelligence.js");
const consoleScript=load("scripts/console.js");
const dnsAnswer=new Uint8Array([0,0,129,128,0,1,0,1,0,0,0,0,7,101,120,97,109,112,108,101,3,99,111,109,0,0,1,0,1,192,12,0,1,0,1,0,0,1,0,0,4,93,184,215,14]);
let passed=0;
function check(title,run) {try{run();passed++;console.log("PASS",title)}catch(e){console.error("FAIL",title,e);process.exitCode=1}}
function diagnose({name="手动网络与 DNS 诊断",args={},dohFailure=false,store={}}={}){
 const done=[],notifications=[],requests=[];
 const context={Uint8Array,setTimeout:fn=>fn(),console:{log(){}},
   $script:{name},$argument:args,$done:v=>done.push(v),
   $persistentStore:{read:k=>store[k]||null,write:(v,k)=>(store[k]=v,true)},
   $notification:{post:(...p)=>notifications.push(p)},
   $httpClient:{
     get(o,cb){requests.push(o);cb(null,{status:204},"")},
     post(o,cb){requests.push(o);return dohFailure?cb("timeout"):cb(null,{status:200},dnsAnswer)}
   }
 };
 vm.runInNewContext(diagnostic,context,{timeout:3000});
 assert.equal(done.length,1);
 return {requests,notifications,store,report:done[0]&&done[0].content};
}
function ipquery(url="https://api.ipquery.io/?format=json"){
 let calls=[],done=[];
 const scriptArgs={target_policy:"Proxy",compare_direct:false,primary_ip_url:url,
   backup_ip_url:"https://ipwho.is/",enable_ip_backup:true,cache_seconds:"120"};
 const sample={ip:"18.144.88.66",location:{country:"United States",country_code:"US",state:"CA",city:"San Francisco",timezone:"America/Los_Angeles"},isp:{asn:"AS16509",isp:"Amazon.com",org:"Amazon.com"},risk:{is_datacenter:true,is_mobile:false}};
 return {calls,done,scriptArgs,sample,
  run(override={}){
    const opts={...scriptArgs,...override};
    const context={$argument:opts,$environment:{params:{}},
     $utils:{geoip:()=>"US",ipasn:()=>"AS16509",ipaso:()=>"Amazon"},
     $persistentStore:{read(){return null},write(){return true}},
     $httpClient:{get(o,cb){calls.push(o);if(o.url.includes("invalid"))return cb(null,{status:404},"no");
        cb(null,{status:200},JSON.stringify(sample))}},
     $done:r=>done.push(r),console:{log(){}}
    };
    vm.runInNewContext(intel,context,{timeout:3000});assert.equal(done.length,1);
    return done[0].content;
  }
 };
}
check("custom connectivity endpoints stay in own script",()=>{
 const x=diagnose({args:{direct_probe_url:"https://example.org/health",proxy_probe_url:"https://example.net/204",doh_url:"https://dns.example.net/dns-query",probe_timeout:"3000"}});
 assert.equal(x.requests.length,3);
 assert(x.requests.some(x=>x.url==="https://example.org/health"&&x.node==="DIRECT"&&x.timeout===3000));
 assert(x.requests.some(x=>x.url==="https://example.net/204"&&x.node==="Proxy"));
 assert(x.requests.some(x=>x.url==="https://dns.example.net/dns-query"&&x.node==="DIRECT"));
});
check("invalid URLs use safe built-in defaults",()=>{
 const x=diagnose({args:{direct_probe_url:"javascript:bad",proxy_probe_url:"file:///etc/passwd",doh_url:"http://insecure.example",probe_timeout:"1"}});
 assert(x.requests.some(x=>x.url==="http://wifi.vivo.com.cn/generate_204"&&x.timeout===6500));
 assert(x.requests.some(x=>x.url==="https://dns.alidns.com/dns-query"));
});
check("automatic successful event stores record but no notification by default",()=>{
 const x=diagnose({name:"网络切换诊断",args:{notify_every_change:false}});
 assert.equal(x.notifications.length,0);
 assert(x.store["loon-routing-dns:diag:last-auto:v1"]);
});
check("automatic event supports opt-in success notification",()=>{
 const x=diagnose({name:"网络切换诊断",args:{notify_every_change:true}});
 assert.equal(x.notifications.length,1);
});
check("manually simulated network change records event without notification",()=>{
 const x=diagnose({name:"模拟网络切换诊断",args:{notify_every_change:true}});
 assert.equal(x.notifications.length,0);
 assert.match(x.report,/直连网络/);
 assert.match(x.store["loon-routing-dns:diag:last-auto:v1"],/手动模拟/);
});
check("automatic failure waits and alerts once",()=>{
 const store={};const a=diagnose({name:"网络切换诊断",dohFailure:true,store});
 const b=diagnose({name:"网络切换诊断",dohFailure:true,store});
 assert.equal(a.notifications.length,1);assert.equal(b.notifications.length,0);
});
check("custom ipquery-compatible API, no direct exposure",()=>{
 const q=ipquery("https://mirror.example/api");const report=q.run();
 assert.equal(q.calls.length,1);
 assert.equal(q.calls[0].url,"https://mirror.example/api");
 assert.equal(q.calls[0].node,"Proxy");
 assert.match(report,/机房/);
});
check("user chooses IP backup, error falls back without direct",()=>{
 const q=ipquery("https://invalid.example/api");
 const report=q.run();
 assert.equal(q.calls.length,2);assert.equal(q.calls[1].node,"Proxy");
 assert.match(report,/机房/);
});
check("user turns off IP backup",()=>{
 const q=ipquery("https://invalid.example/api");
 const report=q.run({enable_ip_backup:false});
 assert.equal(q.calls.length,1);assert.match(report,/备用源已关闭/);
});
check("DIRECT IP lookup never happens until explicitly enabled",()=>{
 const q=ipquery();q.run();assert(q.calls.every(c=>c.node==="Proxy"));
});
check("console reads last network change record, masks DoH path tokens",()=>{
 const done=[],store={"loon-routing-dns:diag:last-auto:v1":JSON.stringify({time:Date.now(),status:"全部检测正常",kind:"自动网络变化"})};
 vm.runInNewContext(consoleScript,{$argument:{auto_check:true,compare_direct:false,doh_url:"https://private.dns.net/dns-query/SECRET-TOKEN",notify_every_change:false},$persistentStore:{read:k=>store[k]},$done:r=>done.push(r),console:{log(){}}},{timeout:3000});
 assert.equal(done.length,1);assert.match(done[0].content,/全部检测正常/);
 assert.doesNotMatch(done[0].content,/SECRET-TOKEN/);assert.match(done[0].content,/private.dns.net/);
});
console.log("Console regression tests passed:",passed);
