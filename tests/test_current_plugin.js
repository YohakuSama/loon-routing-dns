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
  assert(plugin.includes("/af78ebb6b75bdbb341996db446d87cb2be719af4/scripts/v20261021r2/network-diagnostics.js"));
  assert(plugin.includes("/d9333b47b1a0361d911fc57e3dc5808683d416d5/icons/v20261021r2/Console.png"));
});
check("exactly two manual tools with expected names",()=>{
  const entries=plugin.split("\n").filter(x=>x.startsWith("generic then script("));
  assert.equal(entries.length,2);
  assert(entries.some(x=>x.includes('tag="节点出口信息"')));
  assert(entries.some(x=>x.includes('tag="网络与 DNS 诊断"')));
});
check("only the current network-change event is opt-in",()=>{
  const entries=plugin.split("\n").filter(x=>x.startsWith("network-changed then script("));
  assert.equal(entries.length,1);
  assert(entries[0].includes("with enable=\${auto_check}"));
  assert(plugin.includes("auto_check = switch,false"));
});
check("exactly three settings and private comparison off",()=>{
  const args=plugin.split("[Argument]")[1].split("[Script]")[0].split("\n")
    .filter(x=>/^[a-z_]+\s*=/.test(x)).map(x=>x.split("=")[0].trim());
  assert.deepEqual(args,["auto_check","target_policy","compare_direct"]);
  assert(plugin.includes("compare_direct = switch,false"));
});
check("all current scripts remain local versioned assets",()=>{
  const s=plugin.split("\n").filter(x=>/then script\("/.test(x));
  assert.equal(s.length,3);
  assert.equal(s.filter(x=>x.includes("scripts/v20261021r1/node-intelligence.js")).length,1);
  assert.equal(s.filter(x=>x.includes("scripts/v20261021r2/network-diagnostics.js")).length,2);
  assert(fs.existsSync(path.join(root,"scripts/v20261021r1/node-intelligence.js")));
  assert(fs.existsSync(path.join(root,"scripts/v20261021r2/network-diagnostics.js")));
});
check("formal profile loads current plugin with fallback routing intact",()=>{
  const rc2 = read("release/Network_Diagnostics.plugin");
  assert(profile.includes("/a338f2ef8b4a56c7bf46785040a8118d0be1485a/release/Network_Diagnostics.plugin, enabled=true"));
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
    "scripts/v20261018r5/node-intelligence.js"
  ];
  names.forEach(name=>assert(!fs.existsSync(path.join(root,name)),name));
});
console.log("Current plugin tests:",passed);
