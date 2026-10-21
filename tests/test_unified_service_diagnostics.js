"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const source=fs.readFileSync(path.join(root,"scripts/v20261021r9/media-unlock.js"),"utf8");

function simulate(options={}) {
  const requests=[],queue=[],finished=[],timers=[];
  let active=0,maxActive=0;
  function transport(method,req,cb){
    requests.push({method,...req});
    active++;
    maxActive=Math.max(maxActive,active);
    const entry={method,req,cb};
    if(options.async){queue.push(entry);return;}
    respond(entry);
  }
  function respond(entry){
    active--;
    const response=options.reply ? options.reply(entry.req.url,entry.method) : null;
    const obj=response || {status:200,body:"<html>OK</html>"};
    entry.cb(obj.error||null,obj.error?null:{status:obj.status,url:obj.url||entry.req.url},obj.body||"");
  }
  const ctx={
    $argument:{target_policy:options.policy||"Proxy",full_scan:options.full||false},
    $environment:{params:options.environment||{}},
    $done(x){finished.push(x);},
    setTimeout(fn,ms){timers.push({fn,ms});return timers.length;},
    $httpClient:{get(req,cb){transport("GET",req,cb);},post(req,cb){transport("POST",req,cb);}}
  };
  vm.runInNewContext(source,ctx,{timeout:1800});
  if(options.async&&!options.stall){
    let n=0;
    while(queue.length){
      assert(++n<50,"request loop");
      respond(queue.shift());
    }
  }
  if(options.fireTimeout)timers.forEach(t=>t.fn());
  return {requests,queue,finished,timers,maxActive,respond};
}
const base=simulate({async:true,environment:{node:"JMS-chosen"}});
assert.equal(base.finished.length,1);
assert(base.requests.length>=9&&base.requests.length<=15,base.requests.length);
assert(base.maxActive<=6);
assert(base.maxActive>=4);
assert(base.requests.every(r=>r.node==="JMS-chosen"));
assert(base.requests.every(r=>r["auto-cookie"]===false&&r["auto-redirect"]===false&&r.insecure===false));
assert(base.requests.every(r=>r.timeout<=3200));
assert.match(base.finished[0].title,/解锁检测/);
assert.match(base.finished[0].content,/Netflix：/);
assert.match(base.finished[0].content,/Disney\+：/);
assert.match(base.finished[0].content,/ChatGPT：/);
assert.doesNotMatch(base.finished[0].content,/Prime Video|Bilibili|BBC iPlayer|Abema/);
assert.doesNotMatch(base.finished[0].content,/地区可用.*Netflix|Netflix：地区可用/);
assert.equal(base.timers[0].ms,11500);

const confirmedTitle=simulate({reply:url=>{
  if(url.includes("/title/81280792"))return {status:200,body:"<title>Netflix</title> netflix.com/title/81280792"};
  if(url.includes("/title/70143836"))return {status:404,body:""};
  return {status:200,body:"generic response"};
}});
assert.match(confirmedTitle.finished[0].content,/Netflix：地区可用 · 片库/);
const noTitle=simulate({reply:url=>url.includes("/title/")?
  {status:200,body:"generic HTTP 200 page"}:{status:200,body:""}});
assert.match(noTitle.finished[0].content,/Netflix：未确认/);
assert.doesNotMatch(noTitle.finished[0].content,/Netflix：地区可用/);

const extended=simulate({full:true,policy:"Dedicated",async:true});
assert.equal(extended.finished.length,1);
assert(extended.requests.length>base.requests.length);
assert(extended.requests.every(r=>r.node==="Dedicated"));
assert.match(extended.finished[0].content,/Prime Video：/);
assert.match(extended.finished[0].content,/Bilibili 港澳台：/);
assert.match(extended.finished[0].content,/Bilibili 大陆：/);
assert.match(extended.finished[0].content,/Apple 地区：/);
assert.match(extended.finished[0].content,/BBC iPlayer：/);
assert.equal(extended.timers[0].ms,19000);
const replies=url=>{
  if(url.includes("/title/81280792"))return {status:404,body:""};
  if(url.includes("/title/70143836"))return {status:404,body:""};
  if(url.includes("youtube.com/premium"))return {status:200,body:'{"browseId":"SPunlimited","GL":"JP"}'};
  if(url.includes("spotify.com/api/"))return {status:200,body:'{"countryCode":"US"}'};
  if(url.includes("tiktok.com/cdn-cgi/trace"))return {status:200,body:"loc=JP\n"};
  if(url.includes("disneyplus.com"))return {status:200,body:'{"inSupportedLocation":true,"countryCode":"JP"}'};
  if(url.includes("gemini.google.com"))return {status:200,body:',2,1,200,"CHN"'};
  if(url.includes("claude.ai/cdn-cgi/trace"))return {status:200,body:"loc=US\n"};
  if(url.includes("compliance/cookie_requirements"))return {status:200,body:'{"required":false}'};
  if(url.includes("ios.chat.openai.com"))return {status:403,body:"request is not allowed. please try again later."};
  return {status:200,body:""};
};
const judged=simulate({reply:replies});
const lines=judged.finished[0].content;
assert.match(lines,/Netflix：仅部分可用 · 仅自制剧/);
assert.match(lines,/Disney\+：地区可用 · JP/);
assert.match(lines,/YouTube Premium：地区可用 · JP/);
assert.match(lines,/Spotify：地区可用 · US/);
assert.match(lines,/TikTok：地区识别 · JP/);
assert.match(lines,/ChatGPT：地区可用 · Web \+ iOS/);
assert.match(lines,/Gemini：地区受限 · CHN/);
assert.match(lines,/Claude：地区识别 · US/);
const denied=simulate({reply:url=>{
 if(url.includes("disneyplus.com"))return {status:200,body:'{"inSupportedLocation":false,"countryCode":"JP"}'};
 if(url.includes("youtube.com"))return {status:200,body:"YouTube Premium is not available in your country"};
 if(url.includes("api.openai.com"))return {status:403,body:"unsupported_country"};
 if(url.includes("ios.chat.openai.com"))return {status:200,body:"sorry, you have been blocked"};
 return {status:200,body:"Generic homepage and navbar mentioning Netflix Spotify."};
}});
assert.match(denied.finished[0].content,/Disney\+：地区受限 · JP/);
assert.match(denied.finished[0].content,/YouTube Premium：地区受限/);
assert.match(denied.finished[0].content,/ChatGPT：地区受限/);
assert.doesNotMatch(denied.finished[0].content,/Spotify：地区可用/);
const error=simulate({reply:url=>url.includes("spotify.com")?{error:"PRIVATE_PASSWORD"}:{status:200,body:""}});
assert.match(error.finished[0].content,/Spotify：连接失败/);
assert.doesNotMatch(error.finished[0].content,/PRIVATE_PASSWORD/);
const pending=simulate({async:true,stall:true,fireTimeout:true});
assert(pending.requests.length<=6);
assert.equal(pending.finished.length,1);
assert.match(pending.finished[0].content,/未确认/);
while(pending.queue.length)pending.respond(pending.queue.shift());
assert.equal(pending.finished.length,1,"late callbacks must not produce duplicate result");
const invalid=simulate({environment:{node:"bad\nnode"}});
assert.equal(invalid.requests.length,0);
assert.match(invalid.finished[0].content,/节点名称无效/);
const plugin=fs.readFileSync(path.join(root,"release/Network_Diagnostics.plugin"),"utf8");
const profile=fs.readFileSync(path.join(root,"LoonKit.lcf"),"utf8");
assert.match(plugin,/tag="解锁检测"/);
assert.match(plugin,/img_url="play\.rectangle\.system"/);
assert(!plugin.includes('tag="服务检测"'));
assert.match(plugin,/scripts\/v20261021r9\/media-unlock\.js/);
assert.match(plugin,/full_scan = switch,false/);
assert.equal(profile.split("\n").filter(s=>s.includes(".plugin, enabled=true")).length,1);
console.log("Media unlock probing, node binding, status, concurrency and deadline: PASS");