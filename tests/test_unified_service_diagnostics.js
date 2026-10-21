"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const script=fs.readFileSync(path.join(root,"scripts/v20261022r3/media-unlock.js"),"utf8");
const services=["DAZN","Discovery+","Paramount+","Disney+","Netflix","ChatGPT","YouTube Premium"];

function run(reply,options={}){
  const sent=[],pending=[],output=[],timers=[];
  let active=0,maxActive=0;
  function request(req,cb){active++;maxActive=Math.max(active,maxActive);sent.push(req);pending.push({req,cb});}
  vm.runInNewContext(script,{
    $environment:{params:options.params||{node:"JP-selected"}},
    $argument:{target_policy:"Proxy"},
    $httpClient:{get:request,post:request},
    $done:r=>output.push(r),
    setTimeout:(fn,ms)=>timers.push({fn,ms})
  },{timeout:2000});
  function next(){
    const item=pending.shift();
    if(!item)return;
    active--;
    const answer=reply?reply(item.req):{status:200,body:""};
    const a=answer||{};
    item.cb(a.error||null,{status:a.status===undefined?200:a.status,headers:a.headers||{}},a.body||"");
  }
  if(!options.stall){
    let n=0;while(pending.length){assert(++n<35,"bounded requests");next();}
  }
  if(options.fireTimeout)timers.forEach(t=>t.fn());
  return {sent,pending,output,timers,next,maxActive};
}
function rows(test){
  assert.equal(test.output.length,1);
  const content=test.output[0].content;
  assert.match(content,/检测器 v6\.4\.5/);
  assert(!content.includes("待确认"));
  assert(!content.includes("仅检测公开地区"));
  assert(!/Spotify：|TikTok：|Gemini：|Claude：/.test(content));
  const data={};
  for(const name of services){
    const matches=content.split("\n").filter(x=>x.startsWith(name+"："));
    assert.equal(matches.length,1,name);
    data[name]=matches[0].slice(name.length+1);
  }
  return data;
}
const positive=run(req=>{
  const u=req.url;
  if(u.includes("indazn"))return {body:'{"GeolocatedCountry":"JP"}'};
  if(u.includes("discoveryplus.com/token"))return {body:'{"data":{"attributes":{"token":"token123"}}}'};
  if(u.includes("discoveryplus.com/users/me"))return {body:'{"data":{"attributes":{"currentLocationTerritory":"us"}}}'};
  if(u.includes("bamgrid"))return {body:'{"extensions":{"sdk":{"session":{"inSupportedLocation":true,"location":{"countryCode":"JP"}}}}}'};
  if(u.includes("netflix.com/title"))return {headers:{"X-Originating-URL":"https://www.netflix.com/jp/title/81280792"}};
  if(u.includes("youtube.com/premium"))return {body:'{"GL":"JP"}'};
  if(u.includes("cdn-cgi/trace"))return {body:"loc=JP\n"};
  return {status:200};
});
const pass=rows(positive);
assert.equal(pass["DAZN"],"支持 ⟦🇯🇵⟧");
assert.equal(pass["Discovery+"],"支持");
assert.equal(pass["Paramount+"],"支持");
assert.equal(pass["Disney+"],"支持 ⟦🇯🇵⟧");
assert.equal(pass["Netflix"],"完整支持 ⟦🇯🇵⟧");
assert.equal(pass["ChatGPT"],"支持 ⟦🇯🇵⟧");
assert.equal(pass["YouTube Premium"],"支持 ⟦🇯🇵⟧");
assert(positive.maxActive<=7);
assert(positive.sent.every(req=>req.node==="JP-selected"&&req["auto-cookie"]===false&&!req.insecure));
assert.equal(positive.sent.filter(r=>r.url.includes("bamgrid")).length,1);
assert(!positive.sent.some(r=>/gemini|spotify|tiktok|claude|fast\.com/.test(r.url)));
assert.equal(positive.timers[0].ms,22000);
assert.equal(positive.sent.find(r=>r.url==="https://www.youtube.com/premium").timeout,10000);
assert.equal(positive.sent.find(r=>r.url.includes("netflix.com/title")).timeout,6000);
assert(positive.sent.filter(r=>r.url.startsWith("https://chat.openai.com/")).some(r=>r["auto-redirect"]===false));
const discoveryCookie=positive.sent.find(r=>r.url.endsWith("/users/me")).headers.Cookie;
assert(discoveryCookie.includes("st=token123"));

const daznNoGeo=run(req=>req.url.includes("indazn")?{body:"{}"}:{status:503});
assert.equal(rows(daznNoGeo)["DAZN"],"未支持");
const discoveryNotUS=run(req=>req.url.includes("/token?")?{body:'{"data":{"attributes":{"token":"x"}}}'}:
  req.url.includes("/users/me")?{body:'{"data":{"attributes":{"currentLocationTerritory":"jp"}}}'}:{status:503});
assert.equal(rows(discoveryNotUS)["Discovery+"],"未支持");
const paramount302=run(req=>req.url.includes("paramountplus")?{status:302}:{status:503});
assert.equal(rows(paramount302)["Paramount+"],"未支持");
const disneyComing=run(req=>req.url.includes("bamgrid")?
  {body:'{"extensions":{"sdk":{"session":{"inSupportedLocation":false,"location":{"countryCode":"JP"}}}}}'}:{status:503});
assert.equal(rows(disneyComing)["Disney+"],"即将登陆 ⟦🇯🇵⟧");
const disneyNoSession=run(req=>req.url.includes("bamgrid")?{body:'{"extensions":{"sdk":{}}}'}:{status:503});
assert.equal(rows(disneyNoSession)["Disney+"],"未支持");
const disneyUnknownBool=run(req=>req.url.includes("bamgrid")?
  {body:'{"extensions":{"sdk":{"session":{"location":{"countryCode":"JP"}}}}}'}:{status:503});
assert.equal(rows(disneyUnknownBool)["Disney+"],"支持 ⟦🇯🇵⟧");

for(const [status,expected] of [[403,"未支持"],[404,"支持自制剧集"],[200,"完整支持 ⟦未知地区⟧"],[503,"检测失败"]]){
  const t=run(req=>req.url.includes("netflix.com/title")?{status}:{status:503});
  assert.equal(rows(t)["Netflix"],expected);
}
for(const [body,expected] of [
  ["Premium is not available in your country","未支持"],
  ['{"GL":"JP"}',"支持 ⟦🇯🇵⟧"],
  ["www.google.cn","支持 ⟦🇨🇳⟧"],
  ["normal page","支持 ⟦🇺🇸⟧"]]){
  const t=run(req=>req.url.includes("youtube.com/premium")?{body}:{status:503});
  assert.equal(rows(t)["YouTube Premium"],expected);
}
const chatUnsupported=run(req=>req.url==="https://chat.openai.com/"?
  {status:200,headers:{"Content-Type":"text/plain"}}:{status:503});
assert.equal(rows(chatUnsupported)["ChatGPT"],"未支持");
assert(!chatUnsupported.sent.some(r=>r.url.includes("cdn-cgi/trace")));
const chatDenied=run(req=>req.url.includes("cdn-cgi/trace")?{body:"loc=CN\n"}:{status:308});
assert.equal(rows(chatDenied)["ChatGPT"],"未支持");
const chatFailure=run(req=>req.url.includes("cdn-cgi/trace")?{error:"timeout",status:0}:{status:308});
assert.equal(rows(chatFailure)["ChatGPT"],"检测失败");
const error=run(()=>({status:503}));
for(const verdict of Object.values(rows(error)))assert.equal(verdict,"检测失败");
const stall=run(()=>({status:503}),{stall:true,fireTimeout:true});
for(const verdict of Object.values(rows(stall)))assert.equal(verdict,"检测失败");
while(stall.pending.length)stall.next();
assert.equal(stall.output.length,1);
const malformed=run(()=>({status:200}),{params:{node:"bad\nnode"}});
assert.equal(malformed.sent.length,0);
assert.match(malformed.output[0].content,/节点名称无效/);

const plugin=fs.readFileSync(path.join(root,"release/Network_Diagnostics.plugin"),"utf8");
const profile=fs.readFileSync(path.join(root,"LoonKit.lcf"),"utf8");
assert(plugin.includes("scripts/v20261022r3/media-unlock.js"));
assert.equal(profile.split("\n").filter(x=>x.includes(".plugin, enabled=true")).length,1);
console.log("Reference-compatible seven-platform checks: PASS");
