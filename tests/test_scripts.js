/* Loon script regression checks, using Node built-in vm only. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const diagnostics = fs.readFileSync(path.join(root, "scripts/network-diagnostics.js"), "utf8");
const intel = fs.readFileSync(path.join(root, "scripts/node-intelligence.js"), "utf8");
const sample = {
  ip: "20.169.77.88",
  isp: { asn: "AS8075", org: "Microsoft Corporation", isp: "Microsoft Corporation" },
  location: { country: "United States", country_code: "US", state: "Arizona",
    city: "Phoenix", latitude: 33.463, longitude: -112.083, zipcode: "85001",
    timezone: "America/Phoenix" },
  risk: { is_mobile: false, is_datacenter: true, is_vpn: false,
    is_proxy: false, is_tor: false, risk_score: 20 }
};
const query = [
  0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0,
  7, 101, 120, 97, 109, 112, 108, 101, 3, 99, 111, 109, 0, 0, 1, 0, 1
];
const answer = new Uint8Array(
  [0, 0, 129, 128, 0, 1, 0, 1, 0, 0, 0, 0,
    ...query.slice(12),
    192, 12, 0, 1, 0, 1, 0, 0, 1, 0, 0, 4, 93, 184, 215, 14]
);
let count = 0;
function check(name, f) {
  try { f(); count++; console.log("PASS", name); }
  catch (error) { console.error("FAIL", name, error); process.exitCode = 1; }
}
function runDiagnostics({ auto = false, native = "ok", doh = "ok", proxy = "ok", store = {} } = {}) {
  let results = [], log = [], calls = [], notices = [];
  const client = {
    get(opt, cb) {
      calls.push({ method: "GET", node: opt.node, url: opt.url });
      if (opt.node === "Proxy" && proxy === "fail") return cb("timeout");
      cb(null, { status: 204 });
    },
    post(opt, cb) {
      calls.push({ method: "POST", node: opt.node });
      if (doh === "fail") return cb("timeout");
      cb(null, { status: 200 }, doh === "malformed" ? new Uint8Array([0, 1]) : answer);
    }
  };
  const context = {
    Uint8Array, setTimeout: fn => fn(),
    $httpClient: client,
    $script: { name: auto ? "网络切换诊断" : "手动网络诊断" },
    $argument: { doh_url: "https://dns.alidns.com/dns-query" },
    $persistentStore: { read: k => store[k] || null, write: (v, k) => (store[k] = v, true) },
    $notification: { post: (...a) => notices.push(a) },
    $done: result => results.push(result),
    console: { log: x => log.push(x) }
  };
  if (native !== "missing") context.$dns = {
    query(opts, cb) {
      calls.push({ method: "NATIVE", domain: opts.domain, protocol: opts.protocol });
      if (native === "fail") return cb({ code: "TIMEOUT", message: "test" }, null);
      return cb(null, { domain: "example.com", protocol: "doh", server: "https://secret.test/token",
        fromCache: false, answers: [
          { name: "example.com", type: "A", value: "93.184.215.14", ttl: 300 },
          { name: "example.com", type: "AAAA", value: "2606:2800::1", ttl: 300 }
        ] });
    }
  };
  vm.runInNewContext(diagnostics, context, { timeout: 1500 });
  assert.equal(results.length, 1);
  return { text: results[0] && results[0].content || log[0], calls, notices };
}
function runIntel({ env = {}, args = { target_policy: "Proxy", compare_direct: false },
                    primaryFail = false, proxyFail = false, store = {},
                    risk = sample.risk } = {}) {
  let results = [], requests = [];
  const context = {
    $argument: args,
    $environment: { params: env },
    $utils: { geoip: () => "US", ipasn: () => "AS8075",
      ipaso: () => "Microsoft Corporation" },
    $httpClient: {
      get(opt, cb) {
        requests.push({ url: opt.url, node: opt.node });
        if (proxyFail && opt.node !== "DIRECT") return cb("timeout");
        if (primaryFail && opt.url.includes("ipquery")) return cb(null, { status: 429 });
        const ip = opt.node === "DIRECT" ? "118.89.89.89" : sample.ip;
        if (opt.url.includes("ipquery")) return cb(null, { status: 200 },
          JSON.stringify({ ...sample, ip, risk }));
        cb(null, { status: 200 }, JSON.stringify({
          ip, country: "United States", region: "California", city: "LA",
          connection: { asn: 15169, isp: "Google", org: "Google" }
        }));
      }
    },
    $persistentStore: { read: k => store[k] || null,
      write: (v, k) => (store[k] = v, true) },
    $done: value => results.push(value),
    console: { log() {} }
  };
  vm.runInNewContext(intel, context, { timeout: 1500 });
  assert.equal(results.length, 1);
  return { text: results[0].content, requests };
}

check("DoH succeeds and native DNS resolves A/AAAA", () => {
  const r = runDiagnostics();
  assert.match(r.text, /Loon 原生 DNS.*协议 doh/);
  assert.match(r.text, /A 1 \/ AAAA 1/);
  assert.doesNotMatch(r.text, /secret\.test/);
});
check("Older Loon skips native query without blocking probes", () => {
  const r = runDiagnostics({ native: "missing" });
  assert.match(r.text, /需 Build 988/);
  assert.match(r.text, /DNS A 查询成功/);
});
check("Native DNS timeout is visible", () => {
  const r = runDiagnostics({ native: "fail" });
  assert.match(r.text, /原生 DNS：失败（TIMEOUT/);
});
check("DoH malformed response is rejected", () => {
  const r = runDiagnostics({ doh: "malformed" });
  assert.match(r.text, /✗ 加密 DNS/);
});
check("Automatic check does not run native DNS nor proxy tests", () => {
  const r = runDiagnostics({ auto: true });
  assert.equal(r.calls.filter(c => c.method === "NATIVE").length, 0);
  assert.equal(r.calls.filter(c => c.node === "Proxy").length, 0);
  assert.equal(r.notices.length, 0);
});
check("Automatic confirmed DoH failure alerts once", () => {
  const store = {};
  const a = runDiagnostics({ auto: true, doh: "fail", store });
  const b = runDiagnostics({ auto: true, doh: "fail", store });
  assert.equal(a.notices.length, 1);
  assert.equal(b.notices.length, 0);
});
check("Node details do not expose DIRECT by default", () => {
  const r = runIntel();
  assert.equal(r.requests.length, 1);
  assert.equal(r.requests[0].node, "Proxy");
  assert.match(r.text, /机房 \/ 云服务/);
  assert.match(r.text, /Loon 本地 GeoIP：US/);
});
check("DIRECT comparison only after user enables it", () => {
  const r = runIntel({ args: { target_policy: "Proxy", compare_direct: true } });
  assert.equal(r.requests.length, 2);
  assert.equal(r.requests[1].node, "DIRECT");
  assert.match(r.text, /直连出口 IP/);
});
check("Explicit node may reuse its own two-minute cache", () => {
  const store = {};
  const a = runIntel({ env: { nodeInfo: { name: "Tokyo ISP" } }, store });
  const b = runIntel({ env: { nodeInfo: { name: "Tokyo ISP" } }, store });
  assert.equal(a.requests.length, 1);
  assert.equal(b.requests.length, 0);
  assert.match(b.text, /本机缓存/);
});
check("Switching explicitly selected nodes does not reuse cache", () => {
  const store = {};
  runIntel({ env: { nodeInfo: { name: "Tokyo ISP" } }, store });
  const b = runIntel({ env: { nodeInfo: { name: "HK ISP" } }, store });
  assert.equal(b.requests.length, 1);
});
check("Generic Proxy target deliberately bypasses cache", () => {
  const store = {};
  const a = runIntel({ store });
  const b = runIntel({ store });
  assert.equal(a.requests.length, 1);
  assert.equal(b.requests.length, 1);
});
check("Node lookup failure never impersonates local IP", () => {
  const r = runIntel({ proxyFail: true });
  assert.match(r.text, /未回退到本地 IP/);
  assert.doesNotMatch(r.text, /118\.89\.89\.89/);
});
check("Fallback provider does not claim residential type", () => {
  const r = runIntel({ primaryFail: true });
  assert.match(r.text, /类型：未知/);
});
check("Mobile classifier uses documented API data", () => {
  const r = runIntel({ risk: { ...sample.risk, is_mobile: true, is_datacenter: false } });
  assert.match(r.text, /类型：移动网络（情报）/);
});
console.log("Completed", count, "regression tests.");
