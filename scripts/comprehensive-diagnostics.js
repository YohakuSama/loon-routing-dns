/* Loon Routing DNS — focused ad/privacy request diagnostics.
 * Requests follow configured Loon rules; failures alone do not prove REJECT.
 */
(function(){
"use strict";
var tests=[
 ["广告：DoubleClick","http://doubleclick.net/"],
 ["广告：Google Ads","http://googleadservices.com/"],
 ["隐私：Google Analytics","http://google-analytics.com/"],
 ["隐私：Google Tag Manager","http://googletagmanager.com/"]
],result=[],pending=tests.length,completed=false;
function finish(){
 if(completed)return;completed=true;
 var lines=["广告与隐私规则诊断","━━━━━━━━━━━━━━━━━━",
 "以下请求使用 Loon 默认分流，不强制 DIRECT/Proxy。",
 "请确认 AdBlock 策略组当前为 REJECT。"];
 tests.forEach(function(t,i){lines.push(t[0]+"："+(result[i]||"未完成"));});
 lines.push("━━━━━━━━━━━━━━━━━━","判定方法：在 Loon 请求记录搜索以上域名，确认命中 AdBlock 且策略为 REJECT。",
 "请求失败 ≠ 证明拦截成功；HTTP 响应 ≠ 证明规则失效。",
 "本检测不统计拦截率、不上传请求日志、不修改配置。");
 $done({title:"广告与隐私规则诊断",content:lines.join("\n")});
}
tests.forEach(function(t,i){
 try{$httpClient.get({url:t[1],timeout:6500,"auto-redirect":false,"auto-cookie":false},
 function(err,response){result[i]=err?"请求未成功（核对 Loon 请求记录）":"HTTP "+String(response&&response.status||"未知")+"（核对 Loon 请求记录）";if(!--pending)finish();});}
 catch(e){result[i]="请求无法执行";if(!--pending)finish();}
});
})();