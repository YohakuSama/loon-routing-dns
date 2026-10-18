/* Regression guard: retired DNS leak checker must not reappear in public plugin.
 * Keeps the useful node-report and basic network/DNS diagnostics intact. */
"use strict";
const fs=require("node:fs");
const path=require("node:path");
const assert=require("node:assert/strict");
const ROOT=path.resolve(__dirname,"..");
const read=p=>fs.readFileSync(path.join(ROOT,p),"utf8");
let total=0;
function test(label,fn){
  try {fn();total++;console.log("PASS",label);}
  catch(e){console.error("FAIL",label,e);process.exitCode=1;}
}
const plugin=read("plugins/Network_Diagnostics.plugin");
const pinned=read("plugins/v20261018r10/Network_Diagnostics.plugin");
const profile=read("Loon_Routing_DNS.lcf");
test("versioned plugin and standalone plugin are identical",()=>assert.equal(plugin,pinned));
test("only two manual actions remain",()=>{
  const entries=plugin.split("\n").filter(x=>x.startsWith("generic then script("));
  assert.equal(entries.length,2);
  assert(entries.some(x=>x.includes('tag="节点出口信息"')));
  assert(entries.some(x=>x.includes('tag="网络与 DNS 诊断"')));
  assert(!entries.some(x=>/泄漏|dns-leak|bash\.ws/i.test(x)));
});
test("network event remains opt in and does not add a manual action",()=>{
  assert.equal(plugin.split("\n").filter(x=>x.startsWith("network-changed then script(")).length,1);
  assert(plugin.includes("auto_check = switch,false"));
  assert(plugin.includes("compare_direct = switch,false"));
  assert(plugin.includes("with enable=\${auto_check}"));
});
test("exactly three settings remain",()=>{
  const args=plugin.split("[Argument]")[1].split("[Script]")[0].split("\n")
    .filter(x=>/^[a-z_]+\s*=/.test(x)).map(x=>x.split("=")[0].trim());
  assert.deepEqual(args,["auto_check","target_policy","compare_direct"]);
});
test("formal config links to new clean plugin and preserves DNS final logic",()=>{
  assert(profile.includes("/main/plugins/v20261018r10/Network_Diagnostics.plugin, enabled=true"));
  assert(profile.includes("GEOIP,CN,DIRECT,no-resolve"));
  assert(profile.includes("FINAL,Final"));
  assert(profile.includes("dns-server = 223.5.5.5,223.6.6.6"));
  assert(profile.includes("doh-server = https://dns.alidns.com/dns-query"));
});
test("remaining script URLs only use node intel and base network diagnostics",()=>{
  const urls=plugin.split("\n").filter(x=>x.startsWith("generic then script(")||x.startsWith("network-changed then script("));
  assert.equal(urls.filter(x=>x.includes("/v20261018r10/node-intelligence.js")).length,1);
  assert.equal(urls.filter(x=>x.includes("/v20261018r4/network-diagnostics.js")).length,2);
});
test("old DNS leak detector scripts, plugins, previews, tests are deleted",()=>{
  const removed=[
    "plugins/preview/DNS_Leak_Check_v2_3.plugin",
    "plugins/v20261018r6/Network_Diagnostics.plugin",
    "plugins/v20261018r7/Network_Diagnostics.plugin",
    "plugins/v20261018r8/Network_Diagnostics.plugin",
    "scripts/v20261018r6/dns-leak-check.js",
    "scripts/v20261018r7/dns-leak-check.js",
    "scripts/v20261018r8/dns-leak-check.js",
    "tests/test_dns_leak_check.js",
    "tests/test_dns_probe_reliability.js"
  ];
  for(const p of removed)assert(!fs.existsSync(path.join(ROOT,p)),p+" must stay removed");
});
test("current plugin description is focused on functionality",()=>{
  assert(!/已移除|旧版|情报源|bash\.ws|DNS 泄漏/.test(plugin));
  assert(plugin.includes("查看节点出口、网络状态和 DNS 连接情况"));
});
test("public plugin and docs do not reference deleted detector endpoints",()=>{
  assert(!/bash\.ws|dns-leak-check\.js|DNS 解析器泄漏检测/.test(plugin));
  assert(!/bash\.ws|dns-leak-check\.js|v20261018r[678]/.test(read("README.md")));
  const guide=read("docs/NETWORK_DIAGNOSTICS.md");
  assert(!/bash\.ws|dns-leak-check\.js|v20261018r[678]/.test(guide));
});
console.log("Clean plugin regression checks:",total);
