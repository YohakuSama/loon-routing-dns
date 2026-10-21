"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const code=fs.readFileSync(path.join(root,"scripts/v20261022r2/media-unlock.js"),"utf8");

function mock(reply=()=>({status:200,body:"generic page"}), options={}){
  const requests=[],pending=[],output=[],timers=[];
  let active=0,maxActive=0;
  const client={};
  function schedule(req,cb){
    active++;maxActive=Math.max(active,maxActive);
    requests.push(req);pending.push({req,cb});
  }
  client.get=schedule;
  client.post=schedule;
  const ctx={
    $environment:{params:options.params||{node:"JP-node"}},
    $argument:{target_policy:"Proxy",full_scan:!!options.full},
    $httpClient:client,
    $done:x=>output.push(x),
    setTimeout:(fn,ms)=>timers.push({fn,ms}),
  };
  vm.runInNewContext(code,ctx,{timeout:2000});
  function next(){
    const item=pending.shift();if(!item)return;
    active--;
    const r=reply(item.req)||{};
    item.cb(r.error||null,{status:r.status||200,headers:r.headers||{}},r.body||"");
  }
  if(!options.stall){
    let count=0;
    while(pending.length){assert(++count<90,"unexpected probe loop");next();}
  }
  if(options.forceTimeout)timers.forEach(t=>t.fn());
  return {requests,pending,output,timers,next,maxActive};
}
function value(test,service){
  const row=test.output[0].content.split("\n").find(x=>x.startsWith(service+"："));
  assert(row,"missing service "+service);
  return row.split("：")[1];
}
const names=["DAZN","Discovery+","Paramount+","Disney+","Netflix","ChatGPT","YouTube Premium"];
function checkRows(t){
  assert.equal(t.output.length,1);
  const content=t.output[0].content;
  for(const n of names)assert.equal(content.split("\n").filter(x=>x.startsWith(n+"：")).length,1,n);
  assert(!/Spotify：|TikTok：|Gemini：|Claude：|待确认|可连接/.test(content));
  assert(content.includes("检测器 v6.4.4"));
}
const yes=mock(req=>{
  const u=req.url;
  if(u.includes("netflix.com/title"))return {status:200};
  if(u.includes("bamgrid.com"))return {body:'{"extensions":{"sdk":{"session":{"inSupportedLocation":true,"location":{"countryCode":"JP"}}}}}'};
  if(u.includes("youtube.com/premium"))return {body:'{"GL":"JP"}'};
  if(u.includes("indazn.com"))return {body:'{"GeolocatedCountry":"JP"}'};
  if(u.includes("discoveryplus.com/token"))return {body:'{"data":{"attributes":{"token":"123"}}}'};
  if(u.includes("discoveryplus.com/users/me"))return {body:'{"data":{"attributes":{"currentLocationTerritory":"us"}}}'};
  if(u.includes("/cdn-cgi/trace"))return {body:"loc=JP\n"};
  return {status:200};
});checkRows(yes);
for(const n of names)assert.match(resultOf(yes.output[0],n),/已解锁/);
assert(yes.maxActive<=6);
assert(yes.sent.every(r=>r.node==="JP-node"&&r.timeout<=6000&&r["auto-cookie"]===false&&!r.insecure));
assert.equal(yes.timers[0].ms,17500);
assert.equal(yes.sent.filter(r=>r.url.includes("bamgrid.com")).length,1);
assert(!yes.sent.some(r=>/gemini|spotify|tiktok|claude|fast\.com/.test(r.url)));
const blocked=mock({reply:()=>({status:451,body:"forbidden.location"})});checkRows(blocked);
for(const n of names)assert.match(resultOf(blocked.out[0],n),/未解锁/);
const missing=mock({reply:u=>u.includes("netflix.com/title")?{status:404}:{status:503}});
assert.match(resultOf(missing.out[0],"Netflix"),/仅自制剧/);
const nf=mock({reply:u=>u.includes("netflix.com/title")?{status:200,body:""}:{status:503}});
assert.match(resultOf(nf.out[0],"Netflix"),/已解锁/);
const youtube=mock({reply:u=>u.includes("youtube.com/premium")?{status:200,body:"generic"}:{status:503}});
assert.match(resultOf(youtube.out[0],"YouTube Premium"),/已解锁/);
const youtubeBlocked=mock({reply:u=>u.includes("youtube.com/premium")?{status:200,body:"Premium is not available in your country"}:{status:503}});
assert.match(resultOf(youtubeBlocked.out[0],"YouTube Premium"),/未解锁/);
const disneyUnknown=mock({reply:u=>u.includes("bamgrid.com")?{status:200,body:'{"error":"test"}'}:{status:503}});
assert.match(resultOf(disneyUnknown.out[0],"Disney+"),/检测失败/);
const chat=mock({reply:u=>u.includes("/cdn-cgi/trace")?{status:200,body:"loc=JP\n"}:
  u.includes("chatgpt.com/")?{status:308,headers:{Location:"https://chatgpt.com/auth/login"}}:{status:503}});
assert.match(resultOf(chat.out[0],"ChatGPT"),/已解锁（JP）/);
assert(chat.sent.filter(r=>r.url.includes("chatgpt.com")).every(r=>r["auto-redirect"]===false));
const failed=mock({reply:()=>({status:503,body:""})});checkRows(failed);
for(const n of names)assert.match(resultOf(failed.out[0],n),/检测失败/);
const stall=mock({stall:true,fireTimeout:true});checkRows(stall);
assert.match(resultOf(stall.out[0],"Netflix"),/检测失败/);
stall.drain();assert.equal(stall.out.length,1);
const invalid=mock({environment:{node:"bad\nnode"}});
assert.equal(invalid.sent.length,0);
assert.match(invalid.out[0].content,/节点名称无效/);
const plugin=fs.readFileSync(path.join(root,"release/Network_Diagnostics.plugin"),"utf8");
assert(plugin.includes("scripts/v20261022r2/media-unlock.js"));
assert(!plugin.includes("full_scan"));
console.log("Seven service unlock diagnoses, direct verdicts, errors and node routing: PASS");
