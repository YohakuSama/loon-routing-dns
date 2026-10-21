/* Current public plugin contract, routing safety and privacy defaults. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname,"..");
const read = file => fs.readFileSync(path.join(root,file),"utf8");
const plugin = read("release/Network_Diagnostics.plugin");
const profile = read("LoonKit.lcf");
let passed=0;
function check(name,fn){
  try {fn();passed++;console.log("PASS",name);}
  catch(err){process.exitCode=1;console.error("FAIL",name,err);}
}
check("only the shipped immutable plugin is present",()=>{
  assert(!fs.existsSync(path.join(root,"plugins/")));
  for(const dir of ["release/phase-07","release/phase-08","icons/v20261018r2","icons/v20261018r3","scripts/v20261018r11","scripts/v20261020r1","scripts/v20261020r2"])
    assert(!fs.existsSync(path.join(root,dir)),dir);
  assert(plugin.includes("/01e8a70ba5f7c6fe8c14ad79a1f3eba643ec801d/scripts/v20261021r3/network-diagnostics.js"));
  assert(plugin.includes("/67249c58f40a99d3d034acc7934aa1de03d3d72d/scripts/v20261022r2/media-unlock.js"));
  assert(plugin.includes("/97c48a5d14087597dbba35119d5ee8d43b1ce537/icons/v20261021r1/Console.png"));
  
});
check("three integrated manual tools with expected names",()=>{
  const entries=plugin.split("\n").filter(x=>x.startsWith("generic then script("));
  assert.equal(entries.length,3);
  assert(entries.some(x=>x.includes('tag="节点信息"')));
  assert(entries.some(x=>x.includes('tag="网络检测"')));
  assert(entries.some(x=>x.includes('tag="解锁检测"')));
});
check("only the current network-change event is opt-in",()=>{
  const entries=plugin.split("\n").filter(x=>x.startsWith("network-changed then script("));
  assert.equal(entries.length,1);
  assert(entries[0].includes("with enable=\${auto_check}"));
  assert(plugin.includes("auto_check = switch,false"));
});
check("four settings, private comparison and automation off",()=>{
  const args=plugin.split("[Argument]")[1].split("[Script]")[0].split("\n")
    .filter(x=>/^[a-z_]+\s*=/.test(x)).map(x=>x.split("=")[0].trim());
  assert.deepEqual(args,["auto_check","target_policy","compare_direct"]);
  assert(plugin.includes("compare_direct = switch,false"));
  assert(!plugin.includes("service = select"));
  assert(plugin.includes("tag=检测策略"));
  assert(!plugin.includes("full_scan"));
  assert(plugin.includes('img_url="play.rectangle.system"'));
  assert(!plugin.includes('service = select,"Spotify"'));
});
check("all current scripts remain local versioned assets",()=>{
  const s=plugin.split("\n").filter(x=>/then script\("/.test(x));
  assert.equal(s.length,4);
  assert.equal(s.filter(x=>x.includes("scripts/v20261021r3/node-intelligence.js")).length,1);
  assert.equal(s.filter(x=>x.includes("scripts/v20261021r3/network-diagnostics.js")).length,2);
  assert.equal(s.filter(x=>x.includes("scripts/v20261022r2/media-unlock.js")).length,1);
  assert(fs.existsSync(path.join(root,"scripts/v20261021r3/node-intelligence.js")));
  assert(fs.existsSync(path.join(root,"scripts/v20261021r3/network-diagnostics.js")));
  assert(fs.existsSync(path.join(root,"scripts/v20261022r2/media-unlock.js")));
});
check("formal profile loads current plugin with fallback routing intact",()=>{
  const rc2 = read("release/Network_Diagnostics.plugin");
  assert(profile.includes("/9c43b437789c2bee0685f8ecb22e2bdb3f73ac63/release/Network_Diagnostics.plugin, enabled=true"));
  assert.equal(profile.split("\n").filter(x=>x.includes(".plugin, enabled=true")).length,1);
  assert(!profile.includes("/release/Service_Diagnostics.plugin, enabled=true"));
  assert(!rc2.includes("/main/scripts/"));
  assert(!rc2.includes("/main/icons/"));
  assert(profile.includes("dns-server = 223.5.5.5,223.6.6.6"));
  assert(profile.includes("doh-server = https://dns.alidns.com/dns-query"));
  assert(!profile.includes("dns.alidns.com = 223.5.5.5"));
  assert(!profile.includes("cloudflare-dns.com"));
  assert(profile.includes("GEOIP,CN,DIRECT,no-resolve"));
  assert(profile.includes("FINAL,Final"));
});
check("no abandoned features in active plugin",()=>{
  assert(!/dns-leak-check\.js|bash\.ws|DNS 解析器泄漏检测|模拟网络切换|状态与设置摘要/.test(plugin));
  assert(!/已移除|情报源标记有|安全认证/.test(plugin));
});
check("no retired standalone plugin or script assets remain",()=>{
  const names=[
    "plugins/v20261018r2/Network_Diagnostics.plugin",
    "plugins/v20261018r4/Network_Diagnostics.plugin",
    "plugins/v20261018r5/Network_Diagnostics.plugin",
    "plugins/v20261018r9/Network_Diagnostics.plugin",
    "scripts/network-diagnostics.js",
    "scripts/node-intelligence.js",
    "scripts/console.js",
    "scripts/v20261018r4/node-intelligence.js",
    "scripts/v20261018r5/node-intelligence.js",
    "release/Service_Diagnostics.plugin",
    "scripts/v20261021r3/service-diagnostics.js",
    "scripts/v20261021r4/service-diagnostics.js",
    "scripts/v20261021r5/service-diagnostics.js",
    "scripts/v20261021r6/service-diagnostics.js",
    "scripts/v20261021r8/service-diagnostics.js",
    "scripts/v20261021r9/media-unlock.js",
    "scripts/v20261021r10/media-unlock.js",
    "scripts/v20261021r11/media-unlock.js",
    "scripts/v20261021r12/media-unlock.js",
    "scripts/v20261021r13/media-unlock.js",
    "scripts/v20261021r14/media-unlock.js",
    "scripts/v20261021r15/media-unlock.js",
    "scripts/v20261021r16/media-unlock.js",
    "scripts/v20261021r17/media-unlock.js",
    "scripts/v20261021r18/media-unlock.js",
    "scripts/v20261022r1/media-unlock.js",
    "scripts/v20261021r7/node-intelligence.js",
    "scripts/v20261021r7/network-diagnostics.js"
  ];
  names.forEach(name=>assert(!fs.existsSync(path.join(root,name)),name));
});
console.log("Current plugin tests:",passed);
