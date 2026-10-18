/* DNS resolver observation v2.5: mocked Loon runtime, no live network calls. */
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const src=fs.readFileSync(path.join(root,"scripts/v20261018r9/dns-leak-check.js"),"utf8");
let count=0;
function check(label,fn) {
  try {fn();count++;console.log("PASS",label);}
  catch(e){console.error("FAIL",label,e);process.exitCode=1;}
}
const SAMPLE=[
  {type:"ip",ip:"198.51.100.24",country_name:"Japan",asn:"AS64500 Example Transit"},
  {type:"dns",ip:"223.5.5.5",country_name:"China",asn:"AS37963 Alibaba Cloud"},
  {type:"dns",ip:"223.6.6.6",country_name:"China",asn:"AS37963 Alibaba Cloud"},
  {type:"conclusion",ip:"No leak"}
];
function run(o={}) {
  const requests=[],dnsCalls=[],answers=[],jobs=[];
  let now=0,timerId=0,attempts=0;
  const script={
    $dns:o.missingAPI?undefined:{
      query(opts,cb) {
        dnsCalls.push(opts);
        if(o.neverQueryReturns)return;
        cb(o.dnsError?{code:"NO_ANSWER"}:null,o.dnsError?null:{answers:[{type:"A",value:"127.0.0.1"}]});
      }
    },
    $httpClient:{
      get(req,cb) {
        requests.push(req);
        const isResult=req.url.includes("/dnsleak/test/");
        const isSession=req.url.endsWith("/id");
        const simulatedTLS="HTTPClient request failed with error:Error Domain=LNGCDAsyncSocketTLSError Code=16777";
        if((isResult&&req.alpn==="h1"&&o.resultTLSH1)||
           (isResult&&req.alpn==="h2"&&o.resultTLSH2)||
           (isSession&&req.alpn==="h1"&&o.sessionTLSH1)||
           (isSession&&req.alpn==="h2"&&o.sessionTLSH2))
          return cb(simulatedTLS,null,null);
        if(o.httpError)return cb("offline",null,null);
        if(o.httpStatus)return cb(null,{status:o.httpStatus},"HTTP error");
        if(req.url.includes("/dnsleak/test/"))attempts++;
        const data=req.url.endsWith("/id") ? (o.invalidID||"12345678") :
          (o.malformedJSON?"{}":JSON.stringify(
            attempts<=Number(o.emptyPolls||0)?[]:(o.rows===undefined?SAMPLE:o.rows)));
        cb(null,{status:200},data);
      }
    },
    setTimeout:(fn,delay)=>{
      const id=++timerId;
      jobs.push({id,when:now+delay,fn});return id;
    },
    $done:(v)=>answers.push(v),
    console:{log(){}}
  };
  vm.runInNewContext(src,script,{timeout:3000});
  while(jobs.length && now<40000){
    jobs.sort((a,b)=>a.when-b.when);
    const job=jobs.shift();now=job.when;job.fn();
    if(answers.length)break;
  }
  assert.equal(answers.length,1,"script should complete exactly once");
  return {text:answers[0].content,requests,dnsCalls,answers};
}
check("normal sample reports observed resolvers without claiming absolute security",()=>{
  const a=run();
  assert.match(a.text,/已获取解析器观测信息（需人工核对）/);
  assert.match(a.text,/223\.5\.5\.5/);
  assert.match(a.text,/223\.6\.6\.6/);
  assert.match(a.text,/测试服务观察到的 HTTP 出口/);
  assert.match(a.text,/本次采样/);
  assert.doesNotMatch(a.text,/检测结果：没有 DNS 泄漏|检测结果：安全|100% 安全/);
  assert.equal(a.dnsCalls.length,10);
  assert(a.dnsCalls.every(x=>x.protocol==="auto"&&x.timeout===6500&&/^\d+\.12345678\.bash\.ws$/.test(x.domain)));
  assert(a.requests.every(x=>!Object.prototype.hasOwnProperty.call(x,"node")));
});
check("live bash.ws 16-char alphanumeric session ID is accepted",()=>{
  const id="aB12Cd34Ef56Gh78";
  const r=run({invalidID:id});
  assert.match(r.text,/已获取解析器观测信息/);
  assert.equal(r.dnsCalls.length,10);
  assert(r.dnsCalls.every(x=>x.domain.endsWith("."+id+".bash.ws")));
  assert(r.requests.some(x=>x.url.includes("/dnsleak/test/"+id+"?json")));
});
check("valid internal hyphen remains a safe DNS label",()=>{
  const id="ab12-CD34-ef56";
  const r=run({invalidID:id});
  assert.match(r.text,/已获取解析器观测信息/);
  assert.equal(r.dnsCalls.length,10);
});
check("unsafe session ID forms reject before DNS queries or result URL",()=>{
  for(const id of ["<html>Error</html>",'{"id":"abcXYZ1234"}',
                   "abc.def.1234","../../etc/passwd","ABC_1234",
                   "-abCDef1234","abcDEF1234-","short","X".repeat(64)]) {
    const r=run({invalidID:id});
    assert.match(r.text,/无法判定/);
    assert.match(r.text,/安全的 DNS 标签/);
    assert.equal(r.dnsCalls.length,0,"unexpected DNS query for invalid ID");
    assert.equal(r.requests.length,1,"unexpected result request for invalid ID");
    assert(!r.text.includes(id),"raw invalid session value echoed");
  }
});
check("legacy numeric session IDs remain accepted",()=>{
  const r=run({invalidID:"1234567890123456"});
  assert.match(r.text,/已获取解析器观测信息/);
  assert.equal(r.dnsCalls.length,10);
});
check("older Loon: unavailable DNS API yields inconclusive with no HTTP requests",()=>{
  const r=run({missingAPI:true});
  assert.match(r.text,/无法判定/);
  assert.match(r.text,/988/);
  assert.equal(r.requests.length,0);
});
check("bad session ID fails closed without sending DNS queries",()=>{
  const r=run({invalidID:"ABC-hello.example.org"});
  assert.match(r.text,/无法判定/);
  assert.match(r.text,/测试 ID/);
  assert.equal(r.dnsCalls.length,0);
  assert.equal(r.requests.length,1);
});
check("malformed response fails closed, never returns safe",()=>{
  const r=run({malformedJSON:true});
  assert.match(r.text,/无法判定/);
  assert.match(r.text,/检测结果 JSON 格式与预期不符/);
});
check("missing resolver observations retry six times then explain failure",()=>{
  const r=run({rows:[SAMPLE[0]]});
  assert.match(r.text,/无法判定/);
  assert.match(r.text,/仍无法读取到有效的解析器记录/);
  assert.match(r.text,/失败阶段：读取 bash.ws 权威 DNS 观测/);
  assert.match(r.text,/诊断进度：DNS 查询 10\/10/);
  assert.equal(r.requests.filter(x=>x.url.includes("/dnsleak/test/")).length,6);
});
check("native NO_ANSWER is not treated as evidence of no DNS requests",()=>{
  const r=run({dnsError:true});
  assert.match(r.text,/已获取解析器观测信息/);
  assert.match(r.text,/10 次 DNS 查询报告错误/);
});
check("third-party ASN differs: advisory only, not conclusive leak",()=>{
  const rows=[{type:"dns",ip:"1.1.1.1",country_name:"United States",asn:"AS13335 Cloudflare"}];
  const r=run({rows});
  assert.match(r.text,/需要核对|应核对/);
  assert.match(r.text,/不能据此直接认定泄漏/);
});
check("ASN numeric alone cannot prove provider mismatch",()=>{
  const rows=[{type:"dns",ip:"223.5.5.5",country_name:"China",asn:"AS37963"}];
  const r=run({rows});
  assert.match(r.text,/仅有 ASN 编号/);
  assert.doesNotMatch(r.text,/发现需要核对的解析器/);
});
check("invalid IP resolver records cannot be misreported",()=>{
  const r=run({rows:[{type:"dns",ip:"totally-invalid"},{type:"dns",ip:"2001:::db8"}]});
  assert.match(r.text,/无法判定/);
});
check("HTTP failure does not become a false-negative safety verdict",()=>{
  const r=run({httpError:true});
  assert.match(r.text,/无法判定/);
  assert.match(r.text,/无法创建检测会话/);
});
check("DNS callbacks absent do not block authoritative observations",()=>{
  const r=run({neverQueryReturns:true});
  assert.match(r.text,/已获取解析器观测信息/);
  assert.match(r.text,/部分 Loon DNS 回调未返回/);
  assert.match(r.text,/DNS 查询 0\/10/);
});
check("late backend results can be observed on a subsequent poll",()=>{
  const r=run({emptyPolls:2});
  assert.match(r.text,/已获取解析器观测信息/);
  assert.match(r.text,/服务端结果检查 3 次/);
});
check("no DNS callbacks and no DNS records are inconclusive with diagnostics",()=>{
  const r=run({neverQueryReturns:true,rows:[]});
  assert.match(r.text,/无法判定/);
  assert.match(r.text,/DNS 查询 0\/10/);
});
check("session identification failures include failure phase",()=>{
  const r=run({invalidID:"not.an.id"});
  assert.match(r.text,/失败阶段：创建 bash.ws 会话/);
});
check("TLS 16777 on result retries once over h2 and accepts resolver evidence",()=>{
  const r=run({resultTLSH1:true});
  assert.match(r.text,/已获取解析器观测信息/);
  assert.match(r.text,/HTTP\/2 备用 1 次（成功 1）/);
  const resultRequests=r.requests.filter(x=>x.url.includes("/dnsleak/test/"));
  assert.equal(resultRequests.length,2);
  assert.equal(resultRequests[0].alpn,"h1");
  assert.equal(resultRequests[1].alpn,"h2");
  assert(resultRequests.every(x=>!Object.prototype.hasOwnProperty.call(x,"node")));
  assert(resultRequests.every(x=>!Object.prototype.hasOwnProperty.call(x,"insecure")));
});
check("TLS 16777 on session creates a valid ID using h2 fallback",()=>{
  const r=run({sessionTLSH1:true});
  assert.match(r.text,/已获取解析器观测信息/);
  assert.equal(r.requests[0].alpn,"h1");
  assert.equal(r.requests[1].alpn,"h2");
  assert.equal(r.dnsCalls.length,10);
});
check("both h1 and h2 TLS failures return precise inconclusive reason",()=>{
  const r=run({resultTLSH1:true,resultTLSH2:true});
  assert.match(r.text,/检测结果：无法判定/);
  assert.match(r.text,/HTTP\/1\.1 和 HTTP\/2 均发生 TLS 握手错误/);
  assert.match(r.text,/16777/);
  assert.match(r.text,/失败阶段：读取 bash\.ws 权威 DNS 观测/);
  assert.match(r.text,/HTTP\/2 备用 1 次（成功 0）/);
  const requests=r.requests.filter(x=>x.url.includes("/dnsleak/test/"));
  assert.equal(requests.length,2);
  assert.doesNotMatch(r.text,/检测结果：安全|无 DNS 泄漏/);
});
check("plain network errors are not blindly retried with HTTP2",()=>{
  const r=run({httpError:true});
  assert.match(r.text,/无法判定/);
  assert.equal(r.requests.filter(x=>x.alpn==="h2").length,0);
});
check("HTTP status errors never use h2 TLS fallback",()=>{
  const r=run({httpStatus:503});
  assert.match(r.text,/无法判定/);
  assert.equal(r.requests.filter(x=>x.alpn==="h2").length,0);
});
check("explicit h1 remains default with secure certificate checks",()=>{
  const r=run();
  assert(r.requests.every(x=>x.alpn==="h1"));
  assert(r.requests.every(x=>!Object.prototype.hasOwnProperty.call(x,"insecure")));
  assert(r.requests.every(x=>!Object.prototype.hasOwnProperty.call(x,"node")));
});
check("script API only uses GET + $dns.query; no settings mutations",()=>{
  assert(!/setConfig|setSelectPolicy|setRunningModel|setSelectedPolicy/.test(src));
  assert(!/node\s*:\s*["']DIRECT["']/.test(src));
});
check("plugin has three manual actions, monitoring still opt-in",()=>{
  const p=fs.readFileSync(path.join(root,"plugins/v20261018r9/Network_Diagnostics.plugin"),"utf8");
  const lines=p.split("\n").filter(x=>x.startsWith("generic then script("));
  assert.equal(lines.length,3);
  assert.equal(p.split("\n").filter(x=>x.startsWith("network-changed then script(")).length,1);
  assert(lines.some(x=>x.includes("dns-leak-check.js")&&x.includes("DNS 解析器泄漏检测")));
  assert(p.includes("auto_check = switch,false"));
  assert(p.includes("compare_direct = switch,false"));
  assert(!p.includes('dns-leak-check.js", {}'));
});
console.log("DNS resolver check v2.5 tests:",count);
