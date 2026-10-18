/* Offline Loon runtime checks for the bash.ws HTTPS readback route diagnostic. */
"use strict";
const assert=require("node:assert/strict");
const vm=require("node:vm");
const fs=require("node:fs");
const path=require("node:path");
const src=fs.readFileSync(path.resolve(__dirname,"../scripts/preview/dns-readback-route-probe.js"),"utf8");
let cases=0;
function test(name,run){try{run();cases++;console.log("PASS",name)}catch(e){process.exitCode=1;console.error("FAIL",name,e)}}
const TLS="HTTPClient request failed with error:Error Domain=LNGCDAsyncSocketTLSError Code=16777";
function check(o={}){
 const calls=[],dns=[],results=[],timers=[];
 let clock=0,serial=0;
 const ctx={
   $dns:o.missingDns?undefined:{query(q,cb){dns.push(q);if(!o.noDnsCallback)cb(null,{answers:[]});}},
   $httpClient:{get(q,cb){
     calls.push(q);
     if(q.url.endsWith("/id"))return cb(o.sessionTLS?TLS:null,{status:200},o.invalidID?"bad.id":"abCD12efGH34ij56");
     const isProxy=q.node==="Proxy";
     if((isProxy&&o.proxyTLS)||(!isProxy&&o.autoTLS))return cb(TLS,null,null);
     if((isProxy&&o.proxyHttp503)||(!isProxy&&o.autoHttp503))return cb(null,{status:503},"bad");
     cb(null,{status:200},JSON.stringify([
       {type:"dns",ip:"203.0.113.1"},{type:"ip",ip:"198.51.100.1"},{type:"conclusion",ip:"0"}
     ]));
   }},
   $done:x=>results.push(x),
   setTimeout:(fn,delay)=>{const id=++serial;timers.push({fn,when:clock+delay,id});return id;}
 };
 vm.runInNewContext(src,ctx,{timeout:1500});
 let iterations=0;
 while(!results.length&&timers.length&&iterations++<20){
   timers.sort((a,b)=>a.when-b.when);let item=timers.shift();clock=item.when;item.fn();
 }
 assert.equal(results.length,1);
 return {calls,dns,content:results[0].content};
}
test("normal and Proxy paths both observe resolver responses",()=>{
 const r=check();
 assert.equal(r.dns.length,10);
 assert.match(r.content,/当前分流：HTTP\/TLS 成功，服务端返回 1 个 DNS 解析器记录/);
 assert.match(r.content,/Proxy：HTTP\/TLS 成功，服务端返回 1 个 DNS 解析器记录/);
 assert.equal(r.calls.length,3);
 assert.equal(r.calls.filter(x=>x.node==="Proxy").length,1);
});
test("default route TLS error and Proxy success are kept distinct",()=>{
 const r=check({autoTLS:true});
 assert.match(r.content,/当前分流：失败.*16777/);
 assert.match(r.content,/Proxy：HTTP\/TLS 成功/);
 assert.equal(r.dns.length,10);
});
test("both routes TLS fail with no DNS safety claim",()=>{
 const r=check({autoTLS:true,proxyTLS:true});
 assert.match(r.content,/当前分流：失败.*16777/);
 assert.match(r.content,/Proxy：失败.*16777/);
 assert.doesNotMatch(r.content,/无 DNS 泄漏|DNS 泄漏已排除/);
});
test("session API error blocks DNS probes and Proxy fallback",()=>{
 const r=check({sessionTLS:true});
 assert.equal(r.dns.length,0);
 assert.equal(r.calls.length,1);
 assert.match(r.content,/无法创建 bash.ws 测试会话/);
});
test("invalid ID is rejected before any test-domain queries",()=>{
 const r=check({invalidID:true});
 assert.equal(r.dns.length,0);
 assert.equal(r.calls.length,1);
 assert.match(r.content,/ID 格式与预期不同/);
});
test("missing native DNS API yields explicit unsupported without requests",()=>{
 const r=check({missingDns:true});
 assert.equal(r.calls.length,0);
 assert.match(r.content,/不支持 \$dns.query/);
});
test("HTTP failures are not misclassified as TLS success",()=>{
 const r=check({autoHttp503:true,proxyHttp503:true});
 assert.match(r.content,/当前分流：失败 — HTTP 503/);
 assert.match(r.content,/Proxy：失败 — HTTP 503/);
});
test("no forced DIRECT and no certificate bypass anywhere",()=>{
 const r=check({autoTLS:true});
 assert(r.calls.every(x=>!Object.prototype.hasOwnProperty.call(x,"insecure")));
 assert(r.calls.every(x=>x.node===undefined||x.node==="Proxy"));
 assert(r.calls.every(x=>x.alpn==="h1"));
});
test("missing DNS callbacks still allows readback network diagnosis",()=>{
 const r=check({noDnsCallback:true});
 assert.match(r.content,/Loon 回调 0\/10/);
 assert.match(r.content,/HTTP\/TLS 成功/);
});
console.log("DNS readback route mock tests passed:",cases);
