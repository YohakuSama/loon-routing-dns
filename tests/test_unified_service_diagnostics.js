"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const source=fs.readFileSync(path.join(root,"scripts/v20261021r11/media-unlock.js"),"utf8");

function mock(options={}){
  const sent=[],pending=[],out=[],timers=[],attempts={};
  let active=0,maxActive=0;
  const runtime={
    $argument:{target_policy:options.policy||"Proxy",full_scan:!!options.full},
    $environment:{params:options.environment||{}},
    $done(x){out.push(x);},
    setTimeout(fn,ms){timers.push({fn,ms});},
    $httpClient:{get(req,callback){
      attempts[req.url]=(attempts[req.url]||0)+1;
      sent.push(req);active++;maxActive=Math.max(active,maxActive);
      pending.push({req,callback,attempt:attempts[req.url]});
    }}
  };
  vm.runInNewContext(source,runtime,{timeout:2000});
  function respond(entry){
    active--;
    const reply=options.reply?options.reply(entry.req.url,entry.attempt):null;
    const r=reply||{status:200,body:"<html>Generic homepage</html>"};
    entry.callback(r.error||null,{status:r.status||200,headers:r.headers||{}},r.body||"");
  }
  function drain(order){
    let n=0;
    while(pending.length){
      assert(++n<80,"unbounded requests");
      const e=order==="reverse"?pending.pop():pending.shift();
      respond(e);
    }
  }
  if(!options.stall)drain(options.order);
  if(options.fireTimeout)timers.forEach(x=>x.fn());
  return {sent,pending,out,timers,drain,respond,maxActive,attempts};
}
function resultOf(output,name){
  const lines=output.content.split("\n");
  const row=lines.find(line=>line.startsWith(name+"："));
  assert(row,"missing service "+name);
  return row;
}
const generic=mock({environment:{node:"JP-node"},order:"reverse"});
assert.equal(generic.out.length,1);
assert.match(generic.out[0].content,/节点：JP-node/);
assert(generic.maxActive<=5,"HTTP semaphore must hold including Netflix and ChatGPT");
assert(generic.maxActive>=4,"parallel scan expected");
assert(generic.sent.every(x=>x.node==="JP-node"),"all requests use selected node");
assert(generic.sent.every(x=>x.timeout<=5600 && x["auto-cookie"]===false && x.insecure===false));
assert.equal(generic.timers[0].ms,16500);
assert.match(resultOf(generic.out[0],"Netflix"),/未确认/);
assert.match(resultOf(generic.out[0],"YouTube Premium"),/仅可访问/);
assert.match(resultOf(generic.out[0],"Spotify"),/仅可访问/);
assert.match(resultOf(generic.out[0],"ChatGPT"),/未确认/);
assert.match(resultOf(generic.out[0],"Claude"),/未确认|仅可访问/);
assert.doesNotMatch(generic.out[0].content,/解锁成功|全部解锁/);
assert(!generic.out[0].content.includes("Bilibili"));
assert(generic.out[0].content.includes("检测器 v6.3.4"));

const signals=mock({order:"reverse",reply:url=>{
  if(url.includes("/title/81280792"))return {status:200,body:"Netflix title 81280792"};
  if(url.includes("/title/70143836"))return {status:404};
  if(url.includes("disneyplus.com"))return {status:200,body:'{"inSupportedLocation":true,"countryCode":"JP"}'};
  if(url.includes("youtube.com/premium"))return {status:200,body:'{"GL":"JP"}'};
  if(url.includes("spotify.com/api"))return {status:200,body:'{"countryCode":"JP"}'};
  if(url.includes("tiktok.com/cdn-cgi/trace"))return {status:200,body:"loc=JP\n"};
  if(url.includes("api.openai.com"))return {status:200,body:'{"required":false}'};
  if(url.includes("ios.chat.openai.com"))return {status:403,body:"request is not allowed. please try again later."};
  if(url.includes("gemini.google.com"))return {status:200,body:"generic gemini HTML"};
  if(url.includes("claude.ai/cdn-cgi/trace"))return {status:200,body:"loc=JP\n"};
  if(url.includes("claude.ai/"))return {status:200,body:"generic page"};
  return {status:200,body:"generic"};
}});
const b=signals.out[0];
assert.match(resultOf(b,"Netflix"),/可能可用/);
assert.match(resultOf(b,"Disney+"),/可能可用 · JP/);
assert.match(resultOf(b,"YouTube Premium"),/识别地区 · JP（不能证明 Premium）/);
assert.match(resultOf(b,"Spotify"),/可能可用 · JP/);
assert.match(resultOf(b,"TikTok"),/识别地区 · JP/);
assert.match(resultOf(b,"ChatGPT"),/仅可访问/);
assert.match(resultOf(b,"Gemini"),/仅可访问/);
assert.match(resultOf(b,"Claude"),/识别地区 · JP/);

const geo=mock({reply:url=>{
  if(url.includes("disneyplus.com"))return {status:200,body:'{"inSupportedLocation":false,"countryCode":"JP"}'};
  if(url.includes("youtube.com/premium"))return {status:200,body:"Premium is not available in your country"};
  if(url.includes("api.openai.com"))return {status:403,body:"unsupported_country"};
  if(url.includes("ios.chat.openai.com"))return {status:403,body:"sorry, you have been blocked"};
  if(url.includes("claude.ai/")&&!url.includes("cdn-cgi"))return {status:451,body:""};
  return {status:403,body:"Access forbidden"};
}});
const g=geo.out[0];
assert.match(resultOf(g,"Disney+"),/地区受限 · JP/);
assert.match(resultOf(g,"YouTube Premium"),/地区受限/);
assert.match(resultOf(g,"ChatGPT"),/地区受限/);
assert.match(resultOf(g,"Claude"),/地区受限/);
assert.doesNotMatch(resultOf(g,"Netflix"),/地区受限/);
assert.doesNotMatch(resultOf(g,"Spotify"),/地区受限/);

const retry=mock({reply:(url,attempt)=>{
  if(url.includes("spotify.com")&&attempt===1)return {error:"timeout PRIVATE_TOKEN"};
  if(url.includes("spotify.com"))return {status:200,body:'{"countryCode":"US"}'};
  return {status:200,body:"generic"};
}});
assert.equal(retry.attempts[Object.keys(retry.attempts).find(x=>x.includes("spotify.com"))],2);
assert.match(resultOf(retry.out[0],"Spotify"),/可能可用 · US/);
assert(!retry.out[0].content.includes("PRIVATE_TOKEN"));

const partial=mock({reply:url=>{
  if(url.includes("/title/81280792")||url.includes("/title/70143836"))return {status:404,body:""};
  if(url.includes("/title/80018499"))return {status:200,body:"Netflix title 80018499"};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(partial.out[0],"Netflix"),/未确认/);


// Region-only Netflix fast.com signal must not be misreported as full playback.
const cdn=mock({reply:url=>{
  if(url.includes("api.fast.com"))return {status:200,body:'{"targets":[{"location":{"country":"JP"}}]}'};
  if(url.includes("/title/"))return {status:404,body:""};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(cdn.out[0],"Netflix"),/识别地区 · JP（Netflix CDN，非片库证明）/);
// Loon returns HTTP status in response even with network error: preserve evidence.
const httpEvidence=mock({reply:url=>{
  if(url.includes("youtube.com/premium"))return {error:"HTTP failure",status:451,body:""};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(httpEvidence.out[0],"YouTube Premium"),/地区受限/);
// A Spotify redirect with regional path counts as a region-specific result.
const spotifyRedirect=mock({reply:url=>url.includes("spotify.com/api")?
  {status:302,headers:{Location:"https://www.spotify.com/jp/"}}:
  {status:200,body:"generic"}});
assert.match(resultOf(spotifyRedirect.out[0],"Spotify"),/可能可用 · JP/);

const full=mock({full:true,policy:"Manual-node"});
assert.equal(full.out.length,1);
assert.equal(full.timers[0].ms,23000);
assert(full.sent.every(x=>x.node==="Manual-node"));
assert(full.sent.length>generic.sent.length);
assert(resultOf(full.out[0],"Apple 地区"));
assert(resultOf(full.out[0],"Bilibili 港澳台"));
assert(resultOf(full.out[0],"Prime Video"));

const stall=mock({stall:true,fireTimeout:true});
assert.equal(stall.out.length,1);
assert.match(stall.out[0].content,/请求超时 · 超过总等待时间/);
stall.drain();
assert.equal(stall.out.length,1,"no second report from late callbacks");
const invalid=mock({environment:{node:"illegal\nnode"}});
assert.equal(invalid.sent.length,0);
assert.match(invalid.out[0].content,/节点名称无效/);

const plugin=fs.readFileSync(path.join(root,"release/Network_Diagnostics.plugin"),"utf8");
const profile=fs.readFileSync(path.join(root,"LoonKit.lcf"),"utf8");
assert(plugin.includes('tag="解锁检测"'));
assert(plugin.includes("scripts/v20261021r11/media-unlock.js"));
assert(plugin.includes('img_url="play.rectangle.system"'));
assert(!plugin.includes("service = select"));
assert(profile.split("\n").filter(x=>x.includes(".plugin, enabled=true")).length===1);
console.log("Accuracy, media-specific evidence, concurrent HTTP, retry, timeout, node routing: PASS");
