"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const code = fs.readFileSync(
  path.join(__dirname, "../scripts/v20261021r5/service-diagnostics.js"), "utf8");

function run(service = "Spotify", options = {}) {
  const requests = [], answers = [], scheduled = [];
  const ctx = {
    $argument: {service},
    $httpClient: {get(request, callback) {
      requests.push(request);
      if (options.noCallback) return;
      const idx = requests.length - 1;
      const err = Array.isArray(options.errors) ? options.errors[idx] : options.error;
      const status = Array.isArray(options.statuses) ? options.statuses[idx]
        : options.status === undefined ? 200 : options.status;
      callback(err || null, err ? null : {status});
    }},
    $done(x) {answers.push(x);},
    setTimeout(fn, delay) {scheduled.push({fn, delay});}
  };
  vm.runInNewContext(code, ctx, {timeout: 1500});
  if (options.timeout) for (const task of scheduled) task.fn();
  return {requests, answers, scheduled};
}
const EXPECTED = {
  Spotify: ["open.spotify.com", "accounts.spotify.com"],
  Twitch: ["www.twitch.tv", "id.twitch.tv"],
  Abema: ["abema.tv", "api.abema.io"],
  BBC: ["www.bbc.com", "www.bbc.co.uk"],
  Line: ["line.me", "access.line.me"],
  Reddit: ["www.reddit.com", "oauth.reddit.com"],
  Linkedin: ["www.linkedin.com", "static.licdn.com"]
};
for (const [name, hosts] of Object.entries(EXPECTED)) {
  const r = run(name);
  assert.equal(r.requests.length, 2, name);
  for (let i = 0; i < 2; i++) {
    assert.equal(r.requests[i].node, name);
    assert.equal(new URL(r.requests[i].url).hostname, hosts[i]);
    assert.equal(r.requests[i]["auto-cookie"], false);
    assert.equal(r.requests[i]["auto-redirect"], false);
    assert.equal(r.requests[i].insecure, false);
    assert.equal(r.requests[i].timeout, 7000);
  }
  assert.equal(r.answers.length, 1, name);
  assert.match(r.answers[0].content, /两个端点都有 HTTP 响应/);
  assert.match(r.answers[0].content, /不代表登录、播放与地区权限正常/);
}
for (const invalid of ["../../evil", "DIRECT", "", null, ["Spotify"]]) {
  const r = run(invalid);
  assert.equal(r.requests.length, 0, "invalid service sent request");
  assert.equal(r.answers.length, 1);
}
for (const status of [200, 204, 301, 401, 403, 404, 503]) {
  const r = run("Spotify", {statuses: [200, status]});
  assert.equal(r.requests.length, 2);
  assert.equal(r.answers.length, 1);
  assert.match(r.answers[0].content, new RegExp("HTTP " + status));
  if (status >= 500) assert.match(r.answers[0].content, /5xx/);
}
const serverOnly = run("Spotify", {statuses: [503, 503]});
assert.match(serverOnly.answers[0].content, /不能据此认定节点故障/);
const partial = run("Line", {errors: [null, "timeout SECRET_NODE_1"]});
assert.match(partial.answers[0].content, /部分端点有响应/);
assert.match(partial.answers[0].content, /超时/);
assert.doesNotMatch(partial.answers[0].content, /SECRET_NODE_1/);
for (const error of ["TLS handshake failed", "DNS failed", "network error"]) {
  const r = run("Spotify", {errors: [error, error]});
  assert.equal(r.answers.length, 1);
  assert.doesNotMatch(r.answers[0].content, /两个端点都有 HTTP 响应/);
}
const pending = run("Line", {noCallback: true, timeout: true});
assert.equal(pending.requests.length, 1);
assert.equal(pending.answers.length, 1);
assert.match(pending.answers[0].content, /检测未完成或超时/);
const completed = run("Line", {timeout: true});
assert.equal(completed.answers.length, 1, "timer must not report twice");
const plugin = fs.readFileSync(
  path.join(__dirname, "../release/Service_Diagnostics.plugin"), "utf8");
assert.match(plugin, /#!name = LoonKit · 服务连通性诊断/);
assert.match(plugin, /service = select,"Spotify","Twitch","Abema","BBC","Line","Reddit","Linkedin"/);
assert.match(plugin, /scripts\/v20261021r5\/service-diagnostics\.js/);
assert.match(plugin, /4b46a8c4d2733b30d807db8ec51c98b6285faa37/,
             "optional plugin must pin reviewed immutable code");
assert.doesNotMatch(plugin, /network-changed|cron |push |http-request/);
console.log("Optional two-endpoint service diagnostic tests passed");
