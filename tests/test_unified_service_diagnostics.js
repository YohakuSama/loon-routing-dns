"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root,"scripts/v20261021r8/service-diagnostics.js"),"utf8");
const services = ["netflix.com","disneyplus.com","youtube.com","primevideo.com",
  "spotify.com","tiktok.com","chatgpt.com","gemini.google.com","claude.ai",
  "abema.tv","bbc.co.uk","twitch.tv","line.me","reddit.com","linkedin.com"];
function run(options={}) {
  const requests=[],pending=[],done=[],timers=[];
  let active=0,maxActive=0;
  const ctx={
    $argument:{target_policy:options.policy || "Proxy"},
    $environment:{params:options.environment || {}},
    $done(x){done.push(x);},
    setTimeout(fn,ms){timers.push({fn,ms});},
    $httpClient:{get(req,cb){
      requests.push(req);active++;maxActive=Math.max(maxActive,active);
      const ix=requests.length-1;
      if(options.async) {pending.push({ix,cb});return;}
      cb(options.errors&&options.errors[ix] || null,
         {status: options.statuses && options.statuses[ix] || 200},
         options.bodies&&options.bodies[ix] || "");
      active--;
    }}
  };
  vm.runInNewContext(source,ctx,{timeout:2000});
  if(options.async && !options.skipDrain) {
    while(pending.length) {
      const {ix,cb}=pending.shift();
      active--;
      cb(null,{status:options.statuses&&options.statuses[ix]||200},
         options.bodies&&options.bodies[ix]||"");
    }
  }
  if(options.fireTimer)timers.forEach(t=>t.fn());
  return {requests,pending,done,timers,maxActive};
}
const plain=run({environment:{node:"Tokyo-01"},async:true});
assert.equal(plain.requests.length,services.length);
assert.equal(plain.done.length,1);
assert(plain.maxActive<=4);
assert(plain.maxActive>=2);
for(let i=0;i<services.length;i++){
  const r=plain.requests[i];
  assert(new URL(r.url).hostname.endsWith(services[i]),r.url);
  assert.equal(r.node,"Tokyo-01");
  assert.equal(r["auto-cookie"],false);
  assert.equal(r["auto-redirect"],false);
  assert.equal(r.insecure,false);
}
assert.match(plain.done[0].content,/节点\/策略：Tokyo-01/);
assert.match(plain.done[0].content,/网页可访问：/);
assert.doesNotMatch(plain.done[0].content,/地区可能可用：/);
assert.doesNotMatch(plain.done[0].content,/全部解锁|已经解锁/);
const fallback=run({policy:"Proxy-Manual",environment:{}});
assert.equal(fallback.requests.length,services.length);
assert(fallback.requests.every(r=>r.node==="Proxy-Manual"));
const flags=run({statuses:[200,451,429],bodies:[
  "Netflix netflix.com/title/81280792","region restricted",""
],errors:[null,null,null,{message:"secret PRIVATE_NODE_ADDRESS"}]});
const output=flags.done[0].content;
assert.match(output,/地区可能可用：Netflix/);
assert.match(output,/地区受限：Disney\+/);
assert.match(output,/暂无法判断：/);
assert.match(output,/连接失败：Prime Video/);
assert.doesNotMatch(output,/PRIVATE_NODE_ADDRESS/);
const pending=run({async:true,skipDrain:true,fireTimer:true});
assert.equal(pending.requests.length,4);
assert.equal(pending.done.length,1);
assert.match(pending.done[0].content,/暂无法判断：/);
assert.equal(pending.timers[0].ms,33000);
for(const task of pending.pending)task.cb(null,{status:200},"");
assert.equal(pending.done.length,1);
const plugin=fs.readFileSync(path.join(root,"release/Network_Diagnostics.plugin"),"utf8");
const profile=fs.readFileSync(path.join(root,"LoonKit.lcf"),"utf8");
assert.match(plugin,/tag="服务检测"/);
assert.match(plugin,/scripts\/v20261021r8\/service-diagnostics\.js/);
assert.match(plugin,/(\$\{target_policy\})\}\) with tag="服务检测"/);
assert.doesNotMatch(plugin,/service = select|请选择服务|Spotify（音乐）/);
assert.equal(profile.split("\n").filter(s=>s.includes(".plugin, enabled=true")).length,1);
console.log("Selected-node, all-service, timeout and result-classification tests passed");
