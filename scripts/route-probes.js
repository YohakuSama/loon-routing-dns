/* Route probes: compares explicit DIRECT and Proxy connectivity; no claim of rule hit. */
(function(){
"use strict";
var targets=[
 ["国内地图","https://www.amap.com/"],
 ["国内视频","https://www.bilibili.com/"],
 ["海外搜索","https://www.google.com/generate_204"],
 ["海外视频","https://www.youtube.com/"]
], results=[],pending=targets.length*2,finished=false;
function finish(){if(finished)return;finished=true;var lines=["国内/海外连通性对照","说明：显式指定 DIRECT/Proxy 的探测，不代表 Loon 实际规则命中。"];targets.forEach(function(t,i){var a=results[i*2],b=results[i*2+1];lines.push(t[0]+"："+(a||"DIRECT 未完成")+" / "+(b||"Proxy 未完成"));});lines.push("若需确认真实分流，请在 Loon 请求日志中查看目标域名命中策略。");$done({title:"国内外分流辅助诊断",content:lines.join("\n")});}
targets.forEach(function(t,i){["DIRECT","Proxy"].forEach(function(node,j){try{$httpClient.get({url:t[1],node:node,timeout:6500,"auto-redirect":false,"auto-cookie":false},function(err,res){results[i*2+j]=node+" "+(err?"失败":("HTTP "+(res&&res.status||"?")));if(!--pending)finish();});}catch(e){results[i*2+j]=node+" 调用失败";if(!--pending)finish();}});});
})();