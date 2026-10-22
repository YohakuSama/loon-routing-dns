"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const script=fs.readFileSync(path.join(root,"scripts/v20261022r5/media-unlock.js"),"utf8");
const services=["DAZN","Discovery+","Paramount+","Disney+","Netflix","ChatGPT","YouTube Premium"];
function run(reply,options={}){
  const sent=[],pending=[],output=[],timers=[];
  let active=0,maxActive=0;
  function request(req,cb){active++;maxActive=Math.max(active,maxActive);sent.push(req);pending.push({req,cb});}
  vm.runInNewContext(script,{
    $environment:{params:options.params||{node:"Selected-JP"}},
    $argument:{target_policy:"Proxy"},
    $httpClient:{get:request,post:request},
    $done:r=>output.push(r),
    setTimeout:(fn,ms)=>timers.push({fn,ms})
  },{timeout:2000});
  function next(){
    const item=pending.shift();if(!item)return;
    active--;
    const answer=(reply&&reply(item.req))||{};
    item.cb(answer.error||null,{status:answer.status===undefined?200:answer.status,headers:answer.headers||{}},answer.body||"");
  }
  if(!options.stall){let n=0;while(pending.length){assert(++n<45,"probe count bounded");next();}}
  if(options.fireTimeout)timers.forEach(t=>t.fn());
  return {sent,pending,output,timers,next,maxActive};
}
function rows(test){
  assert.equal(test.output.length,1);
  const content=test.output[0].content;
  assert.match(content,/LoonKit v6\.4\.7/);
  assert(!/Spotify：|TikTok：|Gemini：|Claude：|待确认|仅检测公开地区|节点解锁查询|完整解锁|未解锁|支持自制剧集|⟦|🎉|⚠️|🚫|➟/.test(content));
  assert.equal(test.output[0].title,"解锁检测");
  const data={};
  for(const name of services){
    const matches=content.split("\n").filter(x=>x.startsWith(name+"："));
    assert.equal(matches.length,1,name);
    data[name]=matches[0].slice(name.length+1);
  }
  return data;
}
const normal=run(req=>{
  const u=req.url;
  if(u.includes("indazn"))return {body:'{"GeolocatedCountry":"JP"}'};
  if(u.includes("discoveryplus.com/token"))return {body:'{"data":{"attributes":{"token":"secret"}}}'};
  if(u.includes("discoveryplus.com/users/me"))return {body:'{"data":{"attributes":{"currentLocationTerritory":"us"}}}'};
  if(u.includes("bamgrid"))return {body:'{"extensions":{"sdk":{"session":{"inSupportedLocation":true,"location":{"countryCode":"JP"}}}}}'};
  if(u.includes("netflix.com/title"))return {headers:{"X-Originating-URL":"https://www.netflix.com/jp/title/81280792"},body:"Netflix title"};
  if(u.includes("youtube.com/premium"))return {body:'{"GL":"JP"}'};
  if(u.includes("cdn-cgi/trace"))return {body:"loc=JP\n"};
  if(u.includes("chatgpt.com/"))return {body:"ChatGPT web"};
  return {body:""};
});
const yes=rows(normal);
assert.equal(yes["DAZN"],"已解锁（JP）");
assert.equal(yes["Discovery+"],"已解锁");
assert.equal(yes["Paramount+"],"已解锁");
assert.equal(yes["Disney+"],"已解锁（JP）");
assert.equal(yes["Netflix"],"完整解锁（JP）");
assert.equal(yes["ChatGPT"],"已解锁（JP）");
assert.equal(yes["YouTube Premium"],"已解锁（JP）");
assert(normal.maxActive<=7);
assert(normal.sent.every(x=>x.node==="Selected-JP"&&x.insecure===false));
assert(!normal.sent.some(x=>/gemini|spotify|tiktok|claude|fast\.com/.test(x.url)));
assert.equal(normal.timers[0].ms,22000);
assert(normal.sent.every(x=>!Object.prototype.hasOwnProperty.call(x,"auto-cookie")));
assert(normal.sent.filter(x=>x.url.includes("netflix.com/title")||x.url.includes("youtube.com/premium")||x.url.includes("paramountplus.com")).every(x=>!Object.prototype.hasOwnProperty.call(x,"auto-redirect")));
assert(normal.sent.some(x=>x.url==="https://chatgpt.com/"&&x["auto-redirect"]===false));
assert.equal(normal.sent.find(x=>x.url.includes("youtube.com/premium")).timeout,10000);
assert.equal(normal.sent.find(x=>x.url.includes("netflix.com/title")).timeout,6000);
assert.equal(normal.sent.find(x=>x.url.endsWith("/users/me")).headers.Cookie,"st=secret");
const nfLogin=run(req=>req.url.includes("netflix.com/title")?{body:"Sign in to Netflix"}:{status:503});
assert.equal(rows(nfLogin)["Netflix"],"检测失败");
const nfGeneric=run(req=>req.url.includes("netflix.com/title")?{body:"generic page"}:{status:503});
assert.equal(rows(nfGeneric)["Netflix"],"检测失败");
const nf200=run(req=>req.url.includes("netflix.com/title")?{body:"Netflix title 81280792"}:{status:503});
assert.match(rows(nf200)["Netflix"],/^完整解锁/);
const nf403=run(req=>req.url.includes("netflix.com/title")?{status:403}:{status:503});
assert.equal(rows(nf403)["Netflix"],"未解锁");
const nf404=run(req=>req.url.includes("netflix.com/title")?{status:404}:{status:503});
assert.equal(rows(nf404)["Netflix"],"仅自制剧");
const disneyNoSession=run(req=>req.url.includes("bamgrid")?{body:'{"extensions":{"sdk":{}}}'}:{status:503});
assert.equal(rows(disneyNoSession)["Disney+"],"检测失败");
const disneyFalse=run(req=>req.url.includes("bamgrid")?{body:'{"extensions":{"sdk":{"session":{"inSupportedLocation":false,"location":{"countryCode":"JP"}}}}}'}:{status:503});
assert.equal(rows(disneyFalse)["Disney+"],"未解锁");
const disneyMissingBool=run(req=>req.url.includes("bamgrid")?{body:'{"extensions":{"sdk":{"session":{"location":{"countryCode":"JP"}}}}}'}:{status:503});
assert.equal(rows(disneyMissingBool)["Disney+"],"检测失败");
const paramount302=run(req=>req.url.includes("paramountplus.com")?{status:302,headers:{Location:"https://www.paramountplus.com/global/"}}:{status:503});
assert.equal(rows(paramount302)["Paramount+"],"检测失败");
const paramountUnsupported=run(req=>req.url.includes("paramountplus.com")?{status:302,headers:{Location:"/not-available"}}:{status:503});
assert.equal(rows(paramountUnsupported)["Paramount+"],"未解锁");
const youtubeNoGeo=run(req=>req.url.includes("youtube.com/premium")?{body:"YouTube Premium"}:{status:503});
assert.equal(rows(youtubeNoGeo)["YouTube Premium"],"已解锁");
const youtubeBlocked=run(req=>req.url.includes("youtube.com/premium")?{body:"Premium is not available in your country"}:{status:503});
assert.equal(rows(youtubeBlocked)["YouTube Premium"],"未解锁");
const youtubeChallenge=run(req=>req.url.includes("youtube.com/premium")?{body:"verify you are human"}:{status:503});
assert.equal(rows(youtubeChallenge)["YouTube Premium"],"检测失败");
const chatBlocked=run(req=>req.url.includes("chatgpt.com/")?{status:403,body:"unsupported_country"}:{status:503});
assert.equal(rows(chatBlocked)["ChatGPT"],"未解锁");
const chatGeneric=run(req=>req.url.includes("chatgpt.com/")?{status:403,body:"Cloudflare challenge"}:
  req.url.includes("ios.chat.openai.com/")?{status:403,body:"access denied"}:{status:503});
assert.equal(rows(chatGeneric)["ChatGPT"],"检测失败");
const chatIOS=run(req=>req.url.includes("chatgpt.com/")?{status:403,body:"Cloudflare challenge"}:
  req.url.includes("ios.chat.openai.com/")?{status:403,body:"request is not allowed. please try again later."}:
  req.url.includes("cdn-cgi/trace")?{body:"loc=JP\n"}:{status:503});
assert.equal(rows(chatIOS)["ChatGPT"],"已解锁（JP）");
const failed=run(()=>({status:503}));
assert(services.every(s=>rows(failed)[s]==="检测失败"));
const stalled=run(()=>({status:503}),{stall:true,fireTimeout:true});
assert(services.every(s=>rows(stalled)[s]==="检测失败"));
while(stalled.pending.length)stalled.next();
assert.equal(stalled.output.length,1);
const invalid=run(()=>({status:200}),{params:{node:"bad\nnode"}});
assert.equal(invalid.sent.length,0);
assert.match(invalid.output[0].content,/节点名称无效/);
const plugin=fs.readFileSync(path.join(root,"release/Network_Diagnostics.plugin"),"utf8");
assert(plugin.includes("scripts/v20261022r5/media-unlock.js"));
console.log("Unlock transport, regional verdict and WAF/reachability regression: PASS");
