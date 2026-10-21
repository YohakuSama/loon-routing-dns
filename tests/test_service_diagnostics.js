"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const code=fs.readFileSync(path.join(__dirname,"../scripts/v20261021r3/service-diagnostics.js"),"utf8");
function run(service="Spotify",options={}) {
  const requests=[],answers=[],scheduled=[];
  const ctx={
    $argument:{service},
    $httpClient:{get(request,callback){
      requests.push(request);
      callback(options.error||null, options.error?null:{status:options.status===undefined?200:options.status});
    }},
    $done:function(x){answers.push(x);},
    setTimeout(fn,delay){scheduled.push({fn,delay});}
  };
  vm.runInNewContext(code,ctx,{timeout:1500});
  if(options.timeout){for(const timer of scheduled)timer.fn();}
  return {requests,answers,scheduled};
}
const EXPECTED={
  Spotify:"open.spotify.com",Twitch:"www.twitch.tv",Abema:"abema.tv",
  BBC:"www.bbc.com",Line:"line.me",Reddit:"www.reddit.com",
  Linkedin:"www.linkedin.com"
};
for(const [name,hostname] of Object.entries(EXPECTED)){
  const r=run(name);
  assert.equal(r.requests.length,1,name);
  assert.equal(r.requests[0].node,name);
  assert.equal(new URL(r.requests[0].url).hostname,hostname);
  assert.equal(r.requests[0]["auto-cookie"],false);
  assert.equal(r.requests[0]["auto-redirect"],false);
  assert.equal(r.answers.length,1,name);
  assert.match(r.answers[0].content,/不代表登录、播放或地区权限正常/);
}
for(const name of ["../../evil","DIRECT","",null,["Spotify"]]){
  const r=run(name);
  assert.equal(r.requests.length,0,"invalid service sent request");
  assert.equal(r.answers.length,1);
}
for(const status of [200,204,301,401,403,404,503]){
  const r=run("Spotify",{status});
  assert.equal(r.answers.length,1);
  assert.match(r.answers[0].content,new RegExp("HTTP "+status));
  if(status>=500)assert.match(r.answers[0].content,/不能据此认定节点故障/);
}
for(const err of ["timeout","TLS handshake failed","DNS failed","network error"]){
  const r=run("Spotify",{error:err});
  assert.equal(r.answers.length,1);
  assert.doesNotMatch(r.answers[0].content,/正常/);
}
const r=run("Line",{timeout:true});
assert.equal(r.answers.length,1,"timeout after a result must not report twice");
const plugin=fs.readFileSync(path.join(__dirname,"../release/Service_Diagnostics.plugin"),"utf8");
assert.match(plugin,/#!name = LoonKit · 服务连通性诊断/);
assert.match(plugin,/service = select,"Spotify","Twitch","Abema","BBC","Line","Reddit","Linkedin"/);
assert.match(plugin,/scripts\/v20261021r3\/service-diagnostics\.js/);
assert.doesNotMatch(plugin,/network-changed|cron |push |http-request/);
console.log("Optional service diagnostic tests passed");
