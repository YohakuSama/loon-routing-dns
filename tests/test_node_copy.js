/* Current node report copy, detail and privacy regression tests (no network). */
"use strict";
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const assert=require("node:assert/strict");
const root=path.resolve(__dirname,"..");
const src=fs.readFileSync(path.join(root,"scripts/v20261018r11/node-intelligence.js"),"utf8");
let count=0;
function check(label,fn){try{fn();console.log("PASS",label);count++;}catch(e){process.exitCode=1;console.error("FAIL",label,e);}}
const rich={
  ip:"203.0.113.21",location:{country:"Japan",country_code:"JP",state:"Osaka",city:"Osaka",
    zipcode:"540-0002",timezone:"Asia/Tokyo",latitude:34.708,longitude:135.493},
  isp:{asn:"AS25820",isp:"IT7 Networks Inc",org:"IT7 Networks Inc"},
  risk:{is_datacenter:true,is_mobile:false,is_vpn:false,is_proxy:false,is_tor:false,risk_score:20}
};
function run(o={}){
  const calls=[],done=[];
  const ctx={
    $argument:{target_policy:"Proxy",compare_direct:!!o.compare},
    $environment:{params:o.context||{}},
    $utils:o.noLocal?undefined:{geoip:()=>"JP",ipasn:()=>"25820",ipaso:()=>"IT7NET"},
    $httpClient:{get(req,cb){
      calls.push(req);
      if(o.allFail)return cb("timeout",null,null);
      if(o.primaryFail&&req.url.includes("ipquery"))return cb(null,{status:503},"");
      const result=req.url.includes("ipwho.is")?{
        ip:"2001:db8::1",country:"Japan",country_code:"JP",region:"Osaka",city:"Osaka",
        connection:{asn:25820,isp:"Backup",org:"Backup Org"}
      }:(o.payload||rich);
      cb(null,{status:200},JSON.stringify(req.node==="DIRECT"?{...result,ip:"198.51.100.9"}:result));
    }},
    $done:msg=>done.push(msg)
  };
  vm.runInNewContext(src,ctx,{timeout:2000});
  assert.equal(done.length,1);
  return {content:done[0].content,calls};
}
check("full report preserves detailed location and ASN/ISP",()=>{
  const r=run();
  assert.match(r.content,/【出口信息】/);
  assert.match(r.content,/公网 IP：203\.0\.113\.21/);
  assert.match(r.content,/Japan \(JP\) · Osaka · Osaka/);
  assert.match(r.content,/时区：Asia\/Tokyo/);
  assert.match(r.content,/邮编：540-0002/);
  assert.match(r.content,/坐标：34\.708, 135\.493/);
  assert.match(r.content,/ASN：AS25820/);
  assert.match(r.content,/ISP：IT7 Networks Inc/);
});
check("repeated ISP/organization is shown once",()=>{
  const r=run();
  assert.doesNotMatch(r.content,/组织：IT7 Networks Inc/);
  assert.equal((r.content.match(/IT7 Networks Inc/g)||[]).length,1);
});
check("short network feature values replace awkward classification copy",()=>{
  const r=run();
  assert.match(r.content,/机房：是/);
  assert.match(r.content,/移动：否/);
  assert.match(r.content,/VPN：否/);
  assert.match(r.content,/代理：否/);
  assert.match(r.content,/Tor：否/);
  assert.match(r.content,/风险分：20\/100/);
  assert.doesNotMatch(r.content,/情报源|标记有|未标记|不是节点质量|安全认证|服务商自有指标/);
});
check("local database stays available, with no unnecessary provider notes",()=>{
  const r=run();
  assert.match(r.content,/【本地数据库】/);
  assert.match(r.content,/GeoIP：JP/);
  assert.match(r.content,/ASO：IT7NET/);
  assert.doesNotMatch(r.content,/【查询说明】|数据源：|情报来源：/);
});
check("default does not request DIRECT or show default-off disclaimer",()=>{
  const r=run();
  assert.equal(r.calls.length,1);
  assert.equal(r.calls[0].node,"Proxy");
  assert.doesNotMatch(r.content,/DIRECT 对照：默认关闭/);
});
check("explicit opt-in shows real DIRECT egress comparison",()=>{
  const r=run({compare:true});
  assert.equal(r.calls.length,2);
  assert.equal(r.calls[1].node,"DIRECT");
  assert.match(r.content,/【出口对照】/);
  assert.match(r.content,/直连 IP：198\.51\.100\.9/);
});
check("optional data is omitted instead of five unknown filler lines",()=>{
  const r=run({noLocal:true,payload:{
    ip:"203.0.113.22",location:{country:"Japan"},isp:{asn:"AS1",isp:"Provider"}
  }});
  assert.doesNotMatch(r.content,/【网络特征】/);
  assert.doesNotMatch(r.content,/风险分：/);
  assert.doesNotMatch(r.content,/【本地数据库】/);
  assert.match(r.content,/类型：未知/);
});
check("different ISP organization is displayed",()=>{
  const r=run({payload:{...rich,isp:{asn:"AS1",isp:"ISP A",org:"Company B"}}});
  assert.match(r.content,/组织：Company B/);
});
check("backup API still returns valid egress without inventing flags",()=>{
  const r=run({primaryFail:true});
  assert.equal(r.calls.length,2);
  assert.match(r.content,/IPv6/);
  assert.match(r.content,/ISP：Backup/);
  assert.match(r.content,/组织：Backup Org/);
  assert.doesNotMatch(r.content,/【网络特征】/);
});
check("node menu context takes precedence and outage stays explicit",()=>{
  const c=run({context:{node:"Selected Node"}});
  assert.equal(c.calls[0].node,"Selected Node");
  const fail=run({allFail:true});
  assert(fail.calls.every(x=>x.node==="Proxy"));
  assert.match(fail.content,/查询失败/);
  assert.doesNotMatch(fail.content,/情报源|没有把 DIRECT 地址冒充/);
});
check("current plugin uses versioned script and only two manual actions",()=>{
  const p=fs.readFileSync(path.join(root,"release/phase-07/assets/Network_Diagnostics.plugin"),"utf8");
  assert.equal(p.split("\n").filter(x=>x.startsWith("generic then script(")).length,2);
  assert(p.includes("95b6e0eb02d3cc6e82fc8e6998dd130a2c5b7a98/scripts/v20261018r11/node-intelligence.js"));
  assert(p.includes("auto_check = switch,false"));
  assert(p.includes("compare_direct = switch,false"));
  assert(!/已移除|情报源|DNS 解析器泄漏检测/.test(p));
});
console.log("Current node copy regressions:",count);
