"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const code=fs.readFileSync("scripts/v20261022r9/network-diagnostics.js","utf8");
function test(label,config={}) {
  const requests=[],results=[],timers=[];
  const context={
    $script:{name:"网络检测"},
    $environment:{params:{node:config.node||"JP-01"}},
    $argument:{target_policy:"Proxy"},
    $httpClient:{get(req,cb){
      requests.push(req);
      const isDirect=req.node==="DIRECT";
      const status=isDirect?(config.directStatus??204):(config.nodeStatus??204);
      const err=isDirect?config.directError:config.nodeError;
      cb(err||null,err?null:{status},"");
    }},
    $dns:{query(req,cb){cb(null,{protocol:"doh",server:"https://example.org/query",answers:[{type:"A",value:"93.184.215.14"}]});}},
    $done:result=>results.push(result),
    setTimeout:(fn,ms)=>timers.push({fn,ms})
  };
  vm.runInNewContext(code,context,{timeout:2500});
  assert.equal(results.length,1,label+": must finish once");
  assert.equal(results[0].title,"网络检测");
  assert.equal(results[0].htmlMessage,undefined,"native plain-text popup only");
  assert.match(results[0].content,/HTTP 请求耗时，不代表节点测速延迟/);
  assert.equal(requests.length,2);
  assert.equal(requests[0].node,"DIRECT");
  assert.equal(requests[1].node,config.node||"JP-01");
  assert(requests.every(x=>x.url==="http://cp.cloudflare.com/"));
  console.log("PASS",label);
  return results[0].content;
}
const ok=test("normal 204");
assert.match(ok,/网络连接正常/);
assert.match(ok,/HTTP 204/);
const redirect=test("redirect 301",{nodeStatus:301,directStatus:301});
assert.match(redirect,/部分结果需确认/);
assert.match(redirect,/HTTP 301 · 目标重定向/);
assert(!redirect.includes("检测失败"));
const failed=test("node timeout",{nodeError:"timeout"});
assert.match(failed,/部分检测失败/);
assert.match(failed,/节点请求：失败/);
const slow=test("HTTP timing is not Loon node ping");
assert.match(slow,/HTTP 请求耗时/);
const long=test("long node names",{node:"JMS-"+("very-long-node-name-".repeat(6))});
assert(!long.includes("very-long-node-name-very-long-node-name-very-long-node-name"));
console.log("Candidate network tests passed");
