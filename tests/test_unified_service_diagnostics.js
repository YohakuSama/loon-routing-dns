"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const source=fs.readFileSync(path.join(root,"scripts/v20261021r13/media-unlock.js"),"utf8");

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
assert(generic.maxActive<=6,"HTTP semaphore must hold including Netflix and ChatGPT");
assert(generic.maxActive>=4,"parallel scan expected");
assert(generic.sent.every(x=>x.node==="JP-node"),"all requests use selected node");
assert(generic.sent.every(x=>x.timeout<=4300 && x["auto-cookie"]===false && x.insecure===false));
assert.equal(generic.timers[0].ms,13000);
assert.match(resultOf(generic.out[0],"Netflix"),/未取得有效响应/);
assert.match(resultOf(generic.out[0],"YouTube Premium"),/网站可访问/);
assert.match(resultOf(generic.out[0],"Spotify"),/网站可访问/);
assert.match(resultOf(generic.out[0],"ChatGPT"),/未取得有效响应/);
assert.match(resultOf(generic.out[0],"Claude"),/网站可访问/);
assert.doesNotMatch(generic.out[0].content,/解锁成功|全部解锁/);
assert(!generic.out[0].content.includes("Bilibili"));
assert(generic.out[0].content.includes("检测器 v6.3.6"));
assert(!/可能可用|开放信号|非片库证明|非 Claude 解锁/.test(generic.out[0].content));

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
assert.match(resultOf(b,"Netflix"),/片库可访问/);
assert.match(resultOf(b,"Disney+"),/地区支持 · JP/);
assert.match(resultOf(b,"YouTube Premium"),/出口地区 JP · 服务未验证/);
assert.match(resultOf(b,"Spotify"),/地区接口支持 · JP/);
assert.match(resultOf(b,"TikTok"),/网站可访问 · 出口 JP/);
assert.match(resultOf(b,"ChatGPT"),/Web \/ iOS 接口可访问/);
assert.match(resultOf(b,"Gemini"),/网站可访问/);
assert.match(resultOf(b,"Claude"),/网站可访问 · 出口 JP/);

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
assert.match(resultOf(retry.out[0],"Spotify"),/地区接口支持 · US/);
assert(!retry.out[0].content.includes("PRIVATE_TOKEN"));

const partial=mock({reply:url=>{
  if(url.includes("/title/81280792")||url.includes("/title/70143836"))return {status:404,body:""};
  if(url.includes("/title/80018499"))return {status:200,body:"Netflix title 80018499"};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(partial.out[0],"Netflix"),/未取得有效响应/);


// Region-only Netflix fast.com signal must not be misreported as full playback.
const cdn=mock({reply:url=>{
  if(url.includes("api.fast.com"))return {status:200,body:'{"targets":[{"location":{"country":"JP"}}]}'};
  if(url.includes("/title/"))return {status:404,body:""};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(cdn.out[0],"Netflix"),/出口地区 JP · 服务未验证/);
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
assert.match(resultOf(spotifyRedirect.out[0],"Spotify"),/地区接口支持 · JP/);


const premium=mock({reply:url=>url.includes("youtube.com/premium")?
  {status:200,body:'{"isPremiumAvailable":true,"GL":"JP"}'}:
  {status:200,body:"generic"}});
assert.match(resultOf(premium.out[0],"YouTube Premium"),/Premium 入口支持 · JP/);
const premiumBlocked=mock({reply:url=>url.includes("youtube.com/premium")?
  {status:200,body:"Premium is not available in your country"}:
  {status:200,body:"generic"}});
assert.match(resultOf(premiumBlocked.out[0],"YouTube Premium"),/地区受限/);
const falsePositive=mock({reply:url=>url.includes("youtube.com/premium")?
  {status:200,body:'{"browseId":"SPunlimited","GL":"JP"}'}:
  {status:200,body:"generic"}});
assert.doesNotMatch(resultOf(falsePositive.out[0],"YouTube Premium"),/地区支持/);
const orderProof=mock({order:"reverse",reply:url=>{
  if(url.includes("/title/81280792"))return {status:200,body:"Netflix title 81280792"};
  if(url.includes("/title/70143836"))return {status:404};
  if(url.includes("api.fast.com"))return {status:200,body:"not JSON"};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(orderProof.out[0],"Netflix"),/片库可访问/);
assert(!/可能可用|开放信号/.test(orderProof.out[0].content));


// Platform-region marker, a country in a CDN trace and a generic webpage
// should never be collapsed to proof of subscription/media playback.
const geminiSupport=mock({reply:url=>url.includes("gemini.google.com")?
  {status:200,body:',2,1,200,"JPN"'}:{status:200,body:"generic"}});
assert.match(resultOf(geminiSupport.out[0],"Gemini"),/地区支持 · JPN/);
const geminiBlocked=mock({reply:url=>url.includes("gemini.google.com")?
  {status:200,body:',2,1,200,"CHN"'}:{status:200,body:"generic"}});
assert.match(resultOf(geminiBlocked.out[0],"Gemini"),/地区受限 · CHN/);
const premiumOffer=mock({reply:url=>url.includes("youtube.com/premium")?
  {status:200,body:"<html>YouTube Premium Individual plan Start trial</html>"}:
  {status:200,body:"generic"}});
assert.match(resultOf(premiumOffer.out[0],"YouTube Premium"),/Premium 入口支持/);
const marketingOnly=mock({reply:url=>url.includes("youtube.com/premium")?
  {status:200,body:"YouTube Premium is a streaming platform"}:
  {status:200,body:"generic"}});
assert.doesNotMatch(resultOf(marketingOnly.out[0],"YouTube Premium"),/Premium 入口支持/);
const tikDenied=mock({order:"reverse",reply:url=>url.includes("tiktok.com/")&&!url.includes("cdn-cgi")?
  {status:451,body:""}:url.includes("tiktok.com/cdn-cgi")?
  {status:200,body:"loc=JP\\n"}:{status:200,body:"generic"}});
assert.match(resultOf(tikDenied.out[0],"TikTok"),/地区受限/);
const mixedChat=mock({reply:url=>url.includes("api.openai.com")?
  {status:200,body:'{"required":false}'}:url.includes("ios.chat.openai.com")?
  {error:"timeout"}:{status:200,body:"generic"}});
assert.match(resultOf(mixedChat.out[0],"ChatGPT"),/部分接口可访问/);

const full=mock({full:true,policy:"Manual-node"});
assert.equal(full.out.length,1);
assert.equal(full.timers[0].ms,20000);
assert(full.sent.every(x=>x.node==="Manual-node"));
assert(full.sent.length>generic.sent.length);
assert(resultOf(full.out[0],"Apple 地区"));
assert(resultOf(full.out[0],"Bilibili 港澳台"));
assert(resultOf(full.out[0],"Prime Video"));

const stall=mock({stall:true,fireTimeout:true});
assert.equal(stall.out.length,1);
assert.match(stall.out[0].content,/检测超时/);
stall.drain();
assert.equal(stall.out.length,1,"no second report from late callbacks");
const invalid=mock({environment:{node:"illegal\nnode"}});
assert.equal(invalid.sent.length,0);
assert.match(invalid.out[0].content,/节点名称无效/);

const plugin=fs.readFileSync(path.join(root,"release/Network_Diagnostics.plugin"),"utf8");
const profile=fs.readFileSync(path.join(root,"LoonKit.lcf"),"utf8");
assert(plugin.includes('tag="解锁检测"'));
assert(plugin.includes("scripts/v20261021r12/media-unlock.js"));
assert(plugin.includes('img_url="play.rectangle.system"'));
assert(!plugin.includes("service = select"));
assert(profile.split("\n").filter(x=>x.includes(".plugin, enabled=true")).length===1);
console.log("Accuracy, media-specific evidence, concurrent HTTP, retry, timeout, node routing: PASS");
