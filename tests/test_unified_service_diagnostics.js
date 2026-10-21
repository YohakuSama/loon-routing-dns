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
function check(t,expected){
  assert.equal(t.output.length,1);
  const contents=t.output[0].content;
  assert.match(contents,/检测器 v6\.4\.4/);
  assert(!/Spotify：|TikTok：|Gemini：|Claude：|待确认|可连接/.test(contents));
  for(const n of names){
    assert.equal(contents.split("\n").filter(row=>row.startsWith(n+"：")).length,1,n);
    if(expected)assert.match(value(t,n),new RegExp(expected),n);
  }
}
const yes=mock(req=>{
  const u=req.url;
  if(u.includes("bamgrid.com"))return {status:200,body:'{"extensions":{"sdk":{"session":{"inSupportedLocation":true,"location":{"countryCode":"JP"}}}}}'};
  if(u.includes("indazn.com"))return {status:200,body:'{"GeolocatedCountry":"JP"}'};
  if(u.includes("discoveryplus.com/token"))return {status:200,body:'{"data":{"attributes":{"token":"123"}}}'};
  if(u.includes("discoveryplus.com/users/me"))return {status:200,body:'{"data":{"attributes":{"currentLocationTerritory":"us"}}}'};
  if(u.includes("cdn-cgi/trace"))return {status:200,body:"loc=JP\n"};
  return {status:200,body:""};
});
check(yes,"已解锁");
assert(yes.maxActive<=6);
assert(yes.requests.every(r=>r.node==="JP-node"&&r.timeout<=6000&&r["auto-cookie"]===false&&!r.insecure));
assert.equal(yes.timers[0].ms,17500);
assert.equal(yes.requests.filter(r=>r.url.includes("bamgrid.com")).length,1);
assert(!yes.requests.some(r=>/gemini|spotify|tiktok|claude|fast\.com/.test(r.url)));
assert.equal(value(yes,"Disney+"),"已解锁（JP）");
const denied=mock(()=>({status:451,body:"forbidden.location"}));
check(denied,"未解锁");
const httpFailure=mock(()=>({status:503,body:""}));
check(httpFailure,"检测失败");
const partial=mock(req=>req.url.includes("netflix.com/title")?{status:404}:{status:503});
assert.equal(value(partial,"Netflix"),"仅自制剧");
const netflixPage=mock(req=>req.url.includes("netflix.com/title")?{status:200,body:"generic"}:{status:503});
assert.equal(value(netflixPage,"Netflix"),"已解锁");
const youtube=mock(req=>req.url.includes("youtube.com/premium")?{status:200,body:"generic"}:{status:503});
assert.equal(value(youtube,"YouTube Premium"),"已解锁");
const ytBlocked=mock(req=>req.url.includes("youtube.com/premium")?{status:200,body:"Premium is not available in your country"}:{status:503});
assert.equal(value(ytBlocked,"YouTube Premium"),"未解锁");
const geoChat=mock(req=>req.url.includes("cdn-cgi/trace")?{status:200,body:"loc=JP\n"}:
  req.url.includes("chatgpt.com/")?{status:308,headers:{Location:"https://chatgpt.com/auth/login"}}:{status:503});
assert.equal(value(geoChat,"ChatGPT"),"已解锁（JP）");
assert(geoChat.requests.filter(r=>r.url.includes("chatgpt.com")).every(r=>r["auto-redirect"]===false));
const invalidDisney=mock(req=>req.url.includes("bamgrid.com")?{status:200,body:'{"error":"x"}'}:{status:503});
assert.equal(value(invalidDisney,"Disney+"),"检测失败");
const stall=mock(()=>({status:503}),{stall:true,forceTimeout:true});
check(stall,"检测失败");while(stall.pending.length)stall.next();assert.equal(stall.output.length,1);
const invalid=mock(()=>({status:200}),{params:{node:"bad\nnode"}});
assert.equal(invalid.requests.length,0);assert.match(invalid.output[0].content,/节点名称无效/);
const plugin=fs.readFileSync(path.join(root,"release/Network_Diagnostics.plugin"),"utf8");
const profile=fs.readFileSync(path.join(root,"LoonKit.lcf"),"utf8");
assert(plugin.includes("scripts/v20261022r2/media-unlock.js"));
assert(!plugin.includes("full_scan"));
assert.equal(profile.split("\n").filter(x=>x.includes(".plugin, enabled=true")).length,1);
console.log("Seven-service reference checks: PASS");
