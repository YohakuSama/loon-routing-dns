/* Detailed node report v2.1 regression tests. Fully offline. */
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const script=fs.readFileSync(path.join(root,"scripts/v20261018r5/node-intelligence.js"),"utf8");
let count=0;
function check(name,fn){
  try{fn();count++;console.log("PASS",name)}
  catch(e){console.error("FAIL",name,e);process.exitCode=1}
}
const rich={
  ip:"203.0.113.22",
  location:{
    country:"Japan",country_code:"JP",state:"Tokyo",city:"Chiyoda",
    timezone:"Asia/Tokyo",zipcode:"100-0001",latitude:35.69,longitude:139.75
  },
  isp:{asn:"AS64500",isp:"Example ISP",org:"Example Network Ltd."},
  risk:{
    is_datacenter:true,is_mobile:false,is_vpn:true,is_proxy:false,is_tor:false,risk_score:42
  }
};
function run(opt={}){
  const outputs=[],calls=[];
  const args={target_policy:opt.policy||"Proxy",compare_direct:!!opt.compare_direct};
  const ctx={
    $argument:args,$environment:{params:opt.params||{}},
    $utils:opt.withLocal===false?undefined:{
      geoip:()=>opt.localGeo||"JP",ipasn:()=>"AS64500",ipaso:()=>"Local Provider"
    },
    $httpClient:{
      get(o,cb){
        calls.push(o);
        if(opt.allFail)return cb("timeout");
        if(opt.primaryFail&&o.url.includes("ipquery"))return cb(null,{status:503},"");
        let raw=o.url.includes("ipwho.is")?{
          ip:"2001:db8::2",country:"Japan",country_code:"JP",region:"Tokyo",
          city:"Chiyoda",timezone:{id:"Asia/Tokyo"},postal:"100-0001",
          latitude:35.6,longitude:139.7,
          connection:{asn:64500,isp:"Backup ISP",org:"Backup Organization"}
        }:(opt.payload||rich);
        if(o.node==="DIRECT")raw={...raw,ip:"198.51.100.1"};
        cb(null,{status:200},JSON.stringify(raw));
      }
    },
    $done:x=>outputs.push(x),
    console:{log(){}}
  };
  vm.runInNewContext(script,ctx,{timeout:2500});
  assert.equal(outputs.length,1);
  return {text:outputs[0].content,calls};
}
check("restores structured location and network identity",()=>{
  const r=run();
  assert.match(r.text,/【查询对象】/);
  assert.match(r.text,/【地理位置】/);
  assert.match(r.text,/国家\/地区：Japan \(JP\)/);
  assert.match(r.text,/州\/省：Tokyo/);
  assert.match(r.text,/城市：Chiyoda/);
  assert.match(r.text,/时区：Asia\/Tokyo/);
  assert.match(r.text,/邮编：100-0001/);
  assert.match(r.text,/近似坐标：35\.690, 139\.750/);
  assert.match(r.text,/【网络归属】/);
  assert.match(r.text,/ASN：AS64500/);
  assert.match(r.text,/ISP：Example ISP/);
  assert.match(r.text,/运营组织：Example Network Ltd\./);
});
check("reports specific security flags and sourced score",()=>{
  const r=run();
  assert.match(r.text,/【安全与网络特征】/);
  assert.match(r.text,/机房：情报源标记有/);
  assert.match(r.text,/移动网络：情报源未标记/);
  assert.match(r.text,/VPN：情报源标记有/);
  assert.match(r.text,/代理：情报源未标记/);
  assert.match(r.text,/Tor：情报源未标记/);
  assert.match(r.text,/风险评分：42\/100（服务商自有指标/);
  assert.match(r.text,/不是节点质量或安全认证/);
});
check("compares local GeoIP ASN and ASO with remote source",()=>{
  const r=run();
  assert.match(r.text,/【Loon 本地数据库对照】/);
  assert.match(r.text,/GeoIP：JP/);
  assert.match(r.text,/ASO：Local Provider/);
  assert.doesNotMatch(r.text,/本地 GeoIP 与远程情报国家代码不一致/);
});
check("mismatched local GeoIP warns without claiming a network fault",()=>{
  const r=run({localGeo:"US"});
  assert.match(r.text,/本地 GeoIP 与远程情报国家代码不一致/);
});
check("missing local utils leaves remote report working",()=>{
  const r=run({withLocal:false});
  assert.match(r.text,/出口 IP：203\.0\.113\.22/);
  assert.doesNotMatch(r.text,/【Loon 本地数据库对照】/);
});
check("fallback response shows location and unknown security flags",()=>{
  const r=run({primaryFail:true});
  assert.equal(r.calls.length,2);
  assert.match(r.text,/出口 IP：2001:db8::2/);
  assert.match(r.text,/IP 类型：IPv6/);
  assert.match(r.text,/数据源：ipwho\.is/);
  assert.match(r.text,/运营组织：Backup Organization/);
  assert.match(r.text,/VPN：无数据/);
  assert.match(r.text,/风险评分：无数据/);
  assert.match(r.text,/时区：Asia\/Tokyo/);
});
check("missing and inconsistent optional fields are not invented",()=>{
  const r=run({payload:{
    ip:"203.0.113.23",location:{country:"Japan",latitude:999,longitude:139.7},
    isp:{asn:"AS64500"},risk:{is_datacenter:"true",risk_score:150}
  }});
  assert.match(r.text,/机房：无数据/);
  assert.match(r.text,/风险评分：无数据/);
  assert.doesNotMatch(r.text,/近似坐标：/);
  assert.match(r.text,/ISP：未知/);
});
check("DIRECT privacy is opt-in and comparison labeled",()=>{
  const def=run();
  assert.equal(def.calls.length,1);
  assert(def.calls.every(x=>x.node==="Proxy"));
  assert.match(def.text,/DIRECT 对照：默认关闭/);
  const enabled=run({compare_direct:true});
  assert.equal(enabled.calls.length,2);
  assert.equal(enabled.calls[1].node,"DIRECT");
  assert.match(enabled.text,/DIRECT 出口 IP：198\.51\.100\.1/);
});
check("node entry context is used as request route",()=>{
  const r=run({params:{node:"Tokyo Node"}});
  assert.equal(r.calls[0].node,"Tokyo Node");
});
check("provider outage never impersonates DIRECT egress",()=>{
  const r=run({allFail:true});
  assert.equal(r.calls.length,2);
  assert(r.calls.every(x=>x.node==="Proxy"));
  assert.match(r.text,/没有把 DIRECT 地址冒充节点出口/);
});
check("v2.1 changes node path but preserves two actions and three options",()=>{
  const p=fs.readFileSync(path.join(root,"plugins/v20261018r5/Network_Diagnostics.plugin"),"utf8");
  const lines=p.split("\n").filter(x=>x.startsWith("generic then script("));
  assert.equal(lines.length,2);
  assert(p.includes("scripts/v20261018r5/node-intelligence.js"));
  assert(p.includes("scripts/v20261018r4/network-diagnostics.js"));
  assert(p.includes("auto_check = switch,false"));
  assert(p.includes("compare_direct = switch,false"));
  const names=p.split("[Argument]")[1].split("[Script]")[0].split("\n")
    .filter(x=>/^[a-z_]+\s*=/.test(x)).map(x=>x.split("=")[0].trim());
  assert.deepEqual(names,["auto_check","target_policy","compare_direct"]);
});
console.log("Detailed node report v2.1 tests:",count);
