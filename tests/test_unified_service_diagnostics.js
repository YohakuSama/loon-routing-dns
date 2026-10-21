"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const code=fs.readFileSync(path.join(root,"scripts/v20261022r1/media-unlock.js"),"utf8");

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
  const row=test.output[0].content.split("\\n").find(x=>x.startsWith(service+"："));
  assert(row,"missing service "+service);
  return row.split("：")[1];
}
const defaultCase=mock();
assert.equal(defaultCase.output.length,1);
assert.equal(defaultCase.timers[0].ms,18000);
assert(defaultCase.maxActive<=5,"HTTP requests must be bounded");
assert(defaultCase.requests.every(x=>x.node==="JP-node"));
assert(defaultCase.requests.every(x=>x.timeout===5500&&x["auto-cookie"]===false&&!x.insecure));
for(const name of ["Netflix","Disney+","YouTube Premium","Spotify","TikTok","ChatGPT","Gemini","Claude"]){
  assert.equal(value(defaultCase,name),"待确认");
}
assert(!defaultCase.requests.some(x=>x.url.includes("api.fast.com")));
assert(!defaultCase.requests.some(x=>/bamgrid.com\\/(?:devices|token)$/.test(x.url)));
assert.match(defaultCase.output[0].content,/检测器 v6\\.4\\.3/);
assert(!/可连接|解锁成功/.test(defaultCase.output[0].content));

const positive=mock(req=>{
  const u=req.url;
  if(u.includes("/title/81280792"))return {status:200,headers:{"X-Originating-URL":"https://www.netflix.com/jp/title/81280792"},body:"Netflix /title/81280792"};
  if(u.includes("/title/70143836"))return {status:404};
  if(u.includes("bamgrid.com"))return {status:200,body:'{"extensions":{"sdk":{"session":{"inSupportedLocation":true,"location":{"countryCode":"JP"}}}}}'};
  if(u.includes("youtube.com/premium"))return {status:200,body:'{"GL":"JP"} YouTube Premium individual plan'};
  if(u.includes("spotify.com/api"))return {status:200,body:'{"countryCode":"JP"}'};
  if(u.includes("/cdn-cgi/trace"))return {status:200,body:"loc=JP\\n"};
  if(u.includes("tiktok.com/"))return {status:200,body:"TikTok webapp"};
  if(u.includes("chatgpt.com/"))return {status:308,headers:{Location:"https://chatgpt.com/auth/login"}};
  if(u.includes("gemini.google.com"))return {status:200,body:"Google Gemini"};
  if(u.includes("claude.ai/"))return {status:200,body:"Claude AI"};
  return {status:200,body:"generic"};
});
for(const name of ["Netflix","Disney+","YouTube Premium","Spotify","TikTok","ChatGPT","Gemini","Claude"]){
  assert.match(value(positive,name),/^支持/,"expected support: "+name);
}
assert.match(value(positive,"Disney+"),/JP/);
assert.equal(positive.output.length,1);
assert(positive.maxActive<=5);

const blocked=mock(req=>{
  const u=req.url;
  if(u.includes("netflix.com/title/"))return {status:451};
  if(u.includes("bamgrid.com"))return {status:200,body:'{"extensions":{"sdk":{"session":{"inSupportedLocation":false,"location":{"countryCode":"US"}}}}}'};
  if(u.includes("youtube.com/premium"))return {status:200,body:"Premium is not available in your country"};
  if(u.includes("spotify.com"))return {status:451};
  if(u.includes("tiktok.com/")&&!u.includes("cdn-cgi"))return {status:451};
  if(u.includes("chatgpt.com/"))return {status:403,body:"unsupported_country"};
  if(u.includes("gemini.google.com/"))return {status:451};
  if(u.includes("claude.ai/")&&!u.includes("cdn-cgi"))return {status:451};
  return {status:200,body:"generic"};
});
for(const name of ["Netflix","Disney+","YouTube Premium","Spotify","TikTok","ChatGPT","Gemini","Claude"]){
  assert.match(value(blocked,name),/^不支持/,"expected block: "+name);
}
const netflixPartial=mock(req=>{
  if(/netflix\\.com\\/title\\/(81280792|70143836)/.test(req.url))return {status:404};
  if(req.url.includes("netflix.com/title/80018499"))return {status:200,body:"Netflix /title/80018499"};
  return {status:200,body:"generic"};
});
assert.equal(value(netflixPartial,"Netflix"),"部分支持");

const west=mock(req=>{
  if(req.url.includes("chatgpt.com"))return {status:403,body:"Cloudflare security challenge"};
  if(req.url.includes("ios.chat.openai.com"))return {status:403,body:"you have been blocked"};
  return {status:200,body:"generic"};
});
assert.notEqual(value(west,"ChatGPT"),"不支持","WAF 403 is not a region ban");

const full=mock(()=>({status:200,body:"generic"}),{full:true});
assert.equal(full.timers[0].ms,26000);
for(const name of ["Prime Video","Apple 地区","Bilibili 港澳台","Bilibili 大陆","BBC iPlayer","Abema"]){
  assert(value(full,name));
}
const stalled=mock(()=>({status:200,body:"generic"}),{stall:true,forceTimeout:true});
assert.equal(stalled.output.length,1);
assert.match(value(stalled,"Netflix"),/检测失败/);
while(stalled.pending.length)stalled.next();
assert.equal(stalled.output.length,1);
const bad=mock(()=>({status:200}),{params:{node:"node\\ninvalid"}});
assert.equal(bad.requests.length,0);
assert.match(bad.output[0].content,/节点名称无效/);

const plugin=fs.readFileSync(path.join(root,"release/Network_Diagnostics.plugin"),"utf8");
const profile=fs.readFileSync(path.join(root,"LoonKit.lcf"),"utf8");
assert(plugin.includes("scripts/v20261022r1/media-unlock.js"));
assert.equal(profile.split("\\n").filter(x=>x.includes(".plugin, enabled=true")).length,1);
console.log("Simple media checks: routing, positive/negative results, no false positives, concurrency, timeouts, full scan: PASS");
