/* Console diagnostic bundle: independent, bounded checks. No MITM or rule mutation. */
(function(){
"use strict";
var jobs=[
 {name:"广告域名阻断",url:"http://doubleclick.net/",expect:"reject"},
 {name:"隐私追踪域名阻断",url:"http://google-analytics.com/",expect:"reject"},
 {name:"国内服务连通",url:"https://www.amap.com/",expect:"connect"},
 {name:"海外服务连通",url:"https://www.google.com/generate_204",expect:"connect"}
],out=[],pending=jobs.length,ended=false;
function finish(){if(ended)return;ended=true;var lines=["Loon Routing DNS · 综合辅助诊断","检测时间："+new Date().toISOString(),"━━━━━━━━━━━━━━━━━━"];jobs.forEach(function(j,i){lines.push(j.name+"："+(out[i]||"未完成"));});lines.push("注意：广告/隐私域名失败不一定是 REJECT，可能是 DNS、网络或目标站点故障。");lines.push("连通性不证明实际命中预期规则；请结合 Loon 请求记录确认。");lines.push("不读取或上传节点订阅、日志及真实直连公网 IP。");$done({title:"综合辅助诊断",content:lines.join("\n")});}
jobs.forEach(function(j,i){try{$httpClient.get({url:j.url,timeout:6500,"auto-redirect":false,"auto-cookie":false},function(err,res){var status=res&&res.status;out[i]=err?"请求失败（可能被拦截，需查看请求日志）":"HTTP "+String(status||"未知")+(j.expect==="reject"?"（已响应；请检查 AdBlock 策略）":"");if(!--pending)finish();});}catch(e){out[i]="调用失败";if(!--pending)finish();}});
})();