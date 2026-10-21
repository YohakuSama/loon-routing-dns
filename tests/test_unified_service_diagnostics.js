"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const source=fs.readFileSync(path.join(root,"scripts/v20261021r17/media-unlock.js"),"utf8");

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
      pending.push({req,callback,attempt:attempts[req.url],method:"GET"});
    },post(req,callback){
      attempts[req.url]=(attempts[req.url]||0)+1;
      sent.push({...req,method:"POST"});active++;maxActive=Math.max(active,maxActive);
      pending.push({req,callback,attempt:attempts[req.url],method:"POST"});
    }}
  };
  vm.runInNewContext(source,runtime,{timeout:2000});
  function respond(entry){
    active--;
    const reply=options.reply?options.reply(entry.req.url,entry.attempt,entry.req,entry.method):null;
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
assert(generic.sent.every(x=>x.timeout<=5100 && x["auto-cookie"]===false && x.insecure===false));
assert.equal(generic.timers[0].ms,19000);
assert.match(resultOf(generic.out[0],"Netflix"),/未取得有效响应/);
assert.match(resultOf(generic.out[0],"YouTube Premium"),/网站可访问/);
assert.match(resultOf(generic.out[0],"Spotify"),/网站可访问/);
assert.match(resultOf(generic.out[0],"ChatGPT"),/未取得有效响应/);
assert.match(resultOf(generic.out[0],"Claude"),/网站可访问/);
assert.doesNotMatch(generic.out[0].content,/解锁成功|全部解锁/);
assert(!generic.out[0].content.includes("Bilibili"));
assert(generic.out[0].content.includes("检测器 v6.4.1"));
assert(!/可能可用|开放信号|非片库证明|非 Claude 解锁/.test(generic.out[0].content));

const signals=mock({order:"reverse",reply:url=>{
  if(url.includes("/title/81280792"))return {status:200,body:"Netflix title 81280792"};
  if(url.includes("/title/70143836"))return {status:404};
  if(url.endsWith("/devices"))return {status:200,body:'{"assertion":"anon-device-token"}'};
  if(url.endsWith("/token"))return {status:200,body:'{"refresh_token":"anon-session-token"}'};
  if(url.includes("bamgrid.com/graph/"))return {status:200,body:'{"extensions":{"sdk":{"session":{"inSupportedLocation":true,"location":{"countryCode":"JP"}}}}}'};
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
assert.match(resultOf(b,"YouTube Premium"),/YouTube 地区 JP · Premium 未确认/);
assert.match(resultOf(b,"Spotify"),/地区接口支持 · JP/);
assert.match(resultOf(b,"TikTok"),/网站可访问 · 出口 JP/);
assert.match(resultOf(b,"ChatGPT"),/Web \/ iOS 接口已响应/);
assert.match(resultOf(b,"Gemini"),/Gemini 页面可访问/);
assert.match(resultOf(b,"Claude"),/网站可访问 · 出口 JP/);

const geo=mock({reply:url=>{
  if(url.endsWith("/devices"))return {status:451,body:"forbidden-location"};
  if(url.includes("disneyplus.com"))return {status:200,body:'{"inSupportedLocation":false,"countryCode":"JP"}'};
  if(url.includes("youtube.com/premium"))return {status:200,body:"Premium is not available in your country"};
  if(url.includes("api.openai.com"))return {status:403,body:"unsupported_country"};
  if(url.includes("ios.chat.openai.com"))return {status:403,body:"sorry, you have been blocked"};
  if(url.includes("claude.ai/")&&!url.includes("cdn-cgi"))return {status:451,body:""};
  return {status:403,body:"Access forbidden"};
}});
const g=geo.out[0];
assert.match(resultOf(g,"Disney+"),/地区受限/);
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
assert.match(resultOf(partial.out[0],"Netflix"),/部分测试影片可访问/);


// Region-only Netflix fast.com signal must not be misreported as full playback.
const cdn=mock({reply:url=>{
  if(url.includes("api.fast.com"))return {status:200,body:'{"targets":[{"location":{"country":"JP"}}]}'};
  if(url.includes("/title/"))return {status:404,body:""};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(cdn.out[0],"Netflix"),/Netflix CDN 地区 · JP/);
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
assert.match(resultOf(geminiSupport.out[0],"Gemini"),/页面地区 JPN · 功能未验证/);
const geminiBlocked=mock({reply:url=>url.includes("gemini.google.com")?
  {status:200,body:',2,1,200,"CHN"'}:{status:200,body:"generic"}});
assert.match(resultOf(geminiBlocked.out[0],"Gemini"),/页面地区 CHN · 功能未验证/);
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


const disneyAllowed=mock({environment:{node:"Selected"},reply:(url,attempt,req,method)=>{
  if(url.endsWith("/devices")) {
    assert.equal(method,"POST");
    assert.equal(req.node,"Selected");
    assert.equal(req.headers["Content-Type"],"application/json");
    return {status:200,body:'{"assertion":"device-assertion"}'};
  }
  if(url.endsWith("/token")) {
    assert.equal(method,"POST");
    assert.match(req.body,/subject_token=device-assertion/);
    assert.match(req.headers["Content-Type"],/form-urlencoded/);
    return {status:200,body:'{"refresh_token":"short-lived-session"}'};
  }
  if(url.includes("/graph/v1/device/graphql")) {
    assert.equal(method,"POST");
    assert.match(req.body,/short-lived-session/);
    return {status:200,body:'{"extensions":{"sdk":{"session":{"location":{"countryCode":"JP"},"inSupportedLocation":true}}}}'};
  }
  return {status:200,body:"generic"};
}});
assert.match(resultOf(disneyAllowed.out[0],"Disney+"),/地区支持 · JP/);
assert.equal(disneyAllowed.sent.filter(x=>x.method==="POST").length,3);
assert(disneyAllowed.sent.every(x=>x.node==="Selected"));
assert(!disneyAllowed.out[0].content.includes("short-lived-session"));
assert(!disneyAllowed.out[0].content.includes("device-assertion"));
assert(disneyAllowed.maxActive<=6);
const disneyUnavailable=mock({reply:url=>{
  if(url.endsWith("/devices"))return {status:200,body:'{"assertion":"device"}'};
  if(url.endsWith("/token"))return {status:200,body:'{"refresh_token":"refresh"}'};
  if(url.includes("/graph/v1/device/graphql"))return {status:200,body:'{"extensions":{"sdk":{"session":{"location":{"countryCode":"KR"},"inSupportedLocation":false}}}}'};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(disneyUnavailable.out[0],"Disney+"),/地区受限 · KR/);
const disneyTokenBlocked=mock({reply:url=>{
  if(url.endsWith("/devices"))return {status:200,body:'{"assertion":"device"}'};
  if(url.endsWith("/token"))return {status:403,body:"forbidden-location"};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(disneyTokenBlocked.out[0],"Disney+"),/地区受限/);
assert.equal(disneyTokenBlocked.sent.filter(x=>x.url.includes("bamgrid.com/graph/")).length,0);
const disneyGeneric403=mock({reply:url=>url.endsWith("/devices")?
  {status:403,body:"403 ERROR - API access denied"}:{status:200,body:"generic"}});
assert.doesNotMatch(resultOf(disneyGeneric403.out[0],"Disney+"),/地区受限/);
assert.match(resultOf(disneyGeneric403.out[0],"Disney+"),/网站可访问 · 地区接口拒绝访问/);
const disneyMalformed=mock({reply:url=>url.endsWith("/devices")?
  {status:200,body:'{"not_assertion":"placeholder"}'}:{status:200,body:"generic"}});
assert.match(resultOf(disneyMalformed.out[0],"Disney+"),/网站可访问 · 地区接口设备注册失败/);
assert.equal(disneyMalformed.sent.filter(x=>x.url.endsWith("/token")).length,0);
const disneyNoToken=mock({reply:url=>{
  if(url.endsWith("/devices"))return {status:200,body:'{"assertion":"device"}'};
  if(url.endsWith("/token"))return {status:200,body:'{"access_token":"not-refresh"}'};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(disneyNoToken.out[0],"Disney+"),/网站可访问 · 地区接口令牌无效/);
assert.equal(disneyNoToken.sent.filter(x=>x.url.includes("bamgrid.com/graph/")).length,0);
const disneyTransportFailure=mock({reply:url=>url.endsWith("/devices")?
  {error:"timed out TOKEN_SECRET"}:{status:200,body:"generic"}});
assert.match(resultOf(disneyTransportFailure.out[0],"Disney+"),/网站可访问 · 地区接口请求超时/);
assert(!disneyTransportFailure.out[0].content.includes("TOKEN_SECRET"));
const disneyWrongJson=mock({reply:url=>{
  if(url.endsWith("/devices"))return {status:200,body:'{"assertion":"device"}'};
  if(url.endsWith("/token"))return {status:200,body:'{"refresh_token":"refresh"}'};
  if(url.includes("/graph/v1/device/graphql"))return {status:200,body:'{"errors":[{"message":"not a region status"}]}'};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(disneyWrongJson.out[0],"Disney+"),/网站可访问 · 地区会话无有效状态/);
const netflixOriginating=mock({reply:url=>{
  if(url.includes("/title/81280792"))return {status:200,headers:{"X-Originating-URL":"https://www.netflix.com/jp/title/81280792"},body:"Netflix title page"};
  if(url.includes("/title/70143836"))return {status:404,body:""};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(netflixOriginating.out[0],"Netflix"),/片库可访问/);


// Regional decisions must come from the platform session, not unrelated fields.
const disneyDecoy=mock({reply:url=>{
  if(url.endsWith("/devices"))return {status:200,body:'{"assertion":"device"}'};
  if(url.endsWith("/token"))return {status:200,body:'{"refresh_token":"refresh"}'};
  if(url.includes("/graph/v1/device/graphql"))return {status:200,
    body:'{"data":{"countryCode":"JP","inSupportedLocation":true},"extensions":{"sdk":{"session":null}}}'};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(disneyDecoy.out[0],"Disney+"),/网站可访问 · 地区会话无有效状态/);
assert.doesNotMatch(resultOf(disneyDecoy.out[0],"Disney+"),/地区支持/);
const disneyBrokenSession=mock({reply:url=>{
  if(url.endsWith("/devices"))return {status:200,body:'{"assertion":"device"}'};
  if(url.endsWith("/token"))return {status:200,body:'{"refresh_token":"refresh"}'};
  if(url.includes("/graph/v1/device/graphql"))return {status:200,
    body:'{"extensions":{"sdk":{"session":{"location":{"countryCode":"JP"}}}},"data":{"inSupportedLocation":true}}'};
  return {status:200,body:"generic"};
}});
assert.doesNotMatch(resultOf(disneyBrokenSession.out[0],"Disney+"),/地区支持/);
// Cloudflare/WAF access denied is NOT equivalent to an OpenAI region ban.
const chatWaf=mock({reply:url=>{
  if(url.includes("api.openai.com"))return {status:403,body:"Request forbidden"};
  if(url.includes("ios.chat.openai.com"))return {status:403,body:"Sorry, you have been blocked by security checks"};
  return {status:200,body:"generic"};
}});
assert.doesNotMatch(resultOf(chatWaf.out[0],"ChatGPT"),/地区受限/);
assert.match(resultOf(chatWaf.out[0],"ChatGPT"),/未取得有效响应/);
const chatUnsupported=mock({reply:url=>{
  if(url.includes("api.openai.com"))return {status:403,body:"unsupported_country"};
  if(url.includes("ios.chat.openai.com"))return {status:403,body:"Sorry, you have been blocked"};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(chatUnsupported.out[0],"ChatGPT"),/地区受限/);
// An application region marker is not a supported/blocked policy response.
for(const locale of ["USA","JPN","CHN","HKG"]){
  const sample=mock({reply:url=>url.includes("gemini.google.com")?
    {status:200,body:',2,1,200,"'+locale+'"'}:{status:200,body:"generic"}});
  assert.match(resultOf(sample.out[0],"Gemini"),new RegExp("页面地区 "+locale+" · 功能未验证"));
  assert.doesNotMatch(resultOf(sample.out[0],"Gemini"),/地区受限|地区支持/);
}


// More useful evidence is shown when available, without pretending it is a paid-playback test.
const netflixOriginal=mock({reply:url=>{
  if(url.includes("/title/81280792")||url.includes("/title/70143836"))
    return {status:404,body:""};
  if(url.includes("/title/80018499"))
    return {status:200,body:"Netflix title 80018499"};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(netflixOriginal.out[0],"Netflix"),/部分测试影片可访问/);
assert.equal(netflixOriginal.sent.filter(x=>x.url.includes("/title/80018499")).length,1);
const netflixThreeMissing=mock({reply:url=>url.includes("/title/")?
  {status:404,body:""}:{status:200,body:"generic"}});
assert.match(resultOf(netflixThreeMissing.out[0],"Netflix"),/未取得有效响应/);
assert.doesNotMatch(resultOf(netflixThreeMissing.out[0],"Netflix"),/部分测试影片可访问/);
const disneyPageRegion=mock({reply:url=>{
  if(url.endsWith("/devices"))return {status:403,body:"Not authorized"};
  if(url.includes("disneyplus.com"))return {status:200,body:'{"region":"JP"}'};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(disneyPageRegion.out[0],"Disney+"),/Disney\+ 页面地区 · JP/);
assert.doesNotMatch(resultOf(disneyPageRegion.out[0],"Disney+"),/地区支持/);
const disneyLandingBlocked=mock({reply:url=>{
  if(url.endsWith("/devices"))return {status:200,body:"unexpected"};
  if(url.includes("disneyplus.com"))return {status:451,body:"Service unavailable"};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(disneyLandingBlocked.out[0],"Disney+"),/地区受限/);
const youtubeRegionalPage=mock({reply:url=>url.includes("youtube.com/premium")?
  {status:200,body:'<html>YouTube Premium is a video platform. {"GL":"JP"}</html>'}:
  {status:200,body:"generic"}});
assert.match(resultOf(youtubeRegionalPage.out[0],"YouTube Premium"),/Premium 页面可访问 · JP/);
assert.doesNotMatch(resultOf(youtubeRegionalPage.out[0],"YouTube Premium"),/Premium 入口支持/);
const geminiRoot=mock({reply:url=>url.includes("gemini.google.com")?
  {status:200,body:',2,1,200,"JPN"'}:{status:200,body:"generic"}});
assert(geminiRoot.sent.some(x=>x.url==="https://gemini.google.com/"));
assert(!geminiRoot.sent.some(x=>x.url.includes("generativelanguage.googleapis.com")));
assert.match(resultOf(geminiRoot.out[0],"Gemini"),/页面地区 JPN/);
const geminiFallback=mock({reply:url=>{
  if(url==="https://gemini.google.com/")return {error:"timeout"};
  if(url.includes("generativelanguage.googleapis.com"))return {status:403,body:'{"error":{"status":"INVALID_ARGUMENT","message":"API key is invalid"}}'};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(geminiFallback.out[0],"Gemini"),/Google AI 接口可达/);
assert(geminiFallback.sent.some(x=>x.url==="https://gemini.google.com/"));
assert(geminiFallback.sent.some(x=>x.url.includes("generativelanguage.googleapis.com")));
assert(!geminiFallback.sent.some(x=>x.url==="https://gemini.google.com/app"));
// Netflix generic login / title HTML and redirects must not imply catalog playback.
const netflixLogin=mock({reply:url=>{
  if(url.includes("/title/81280792"))return {status:200,body:"<html><title>Netflix Login</title></html>"};
  if(url.includes("/title/70143836"))return {status:302,headers:{Location:"https://www.netflix.com/login"}};
  return {status:200,body:"generic"};
}});
assert.doesNotMatch(resultOf(netflixLogin.out[0],"Netflix"),/片库可访问|部分测试影片可访问/);
const netflixCdnOnly=mock({reply:url=>{
  if(url.includes("api.fast.com"))return {status:200,body:'{"targets":[{"location":{"country":"JP"}}]}'};
  if(url.includes("/title/"))return {status:200,body:"<html><title>Netflix Login</title></html>"};
  return {status:200,body:"generic"};
}});
assert.match(resultOf(netflixCdnOnly.out[0],"Netflix"),/Netflix CDN 地区 · JP/);
assert.doesNotMatch(resultOf(netflixCdnOnly.out[0],"Netflix"),/片库可访问/);

const full=mock({full:true,policy:"Manual-node"});
assert.equal(full.out.length,1);
assert.equal(full.timers[0].ms,26000);
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
assert(plugin.includes("scripts/v20261021r17/media-unlock.js"));
assert(plugin.includes('img_url="play.rectangle.system"'));
assert(!plugin.includes("service = select"));
assert(profile.split("\n").filter(x=>x.includes(".plugin, enabled=true")).length===1);
console.log("Accuracy, media-specific evidence, concurrent HTTP, retry, timeout, node routing: PASS");
