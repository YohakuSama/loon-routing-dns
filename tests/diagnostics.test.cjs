// Offline Loon API doubles: no actual requests, no change to production probe logic.
'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ROOT = path.resolve(__dirname, '..');
const SCRIPTS = {
  node: 'node-intelligence.js',
  network: 'network-diagnostics.js',
  media: 'media-unlock.js'
};

function run(kind, handler, options = {}) {
  const requests = [], completed = [], timers = [], alerts = [], writes = [];
  const http = (method, request, callback) => {
    requests.push({method, request, callback});
    const reply = handler({method, request, index: requests.length - 1});
    if (reply && reply.hold) return;
    callback(reply && reply.error || null,
      reply && reply.response || {status: reply && reply.status !== undefined ? reply.status : 200,
                                  headers: reply && reply.headers || {}},
      reply && reply.body !== undefined ? reply.body : '');
  };
  const dns = options.dns === null ? undefined : {
    query(request, callback) {
      const result = options.dns || {
        reply: {answers: [{type:'A', value:'203.0.113.1'}],
                protocol: 'doh', server: 'https://dns.example/dns-query'}
      };
      if (result.throwError) throw new Error('bad native dns API');
      callback(result.error || null, result.reply);
    }
  };
  const sandbox = {
    $argument: options.argument || {target_policy:'Node-A'},
    $environment: {params: options.params || {node: 'Node-A'}},
    $script: {name: options.automatic ? '网络切换异常监测' : '手动检测'},
    $httpClient: {
      get(request, callback) {return http('GET', request, callback);},
      post(request, callback) {return http('POST', request, callback);}
    },
    $dns: dns,
    $done(value) {completed.push(value);},
    $persistentStore: {
      read() {return null;},
      write(value, key) {writes.push({value,key});}
    },
    $notification: {post(...args) {alerts.push(args);}},
    setTimeout(fn, delay) {timers.push({fn, delay}); return timers.length;}
  };
  const src = fs.readFileSync(path.join(ROOT, 'scripts/v20261022r11', SCRIPTS[kind]), 'utf8');
  vm.runInNewContext(src, sandbox, {timeout:3000, filename:SCRIPTS[kind]});
  return {requests, completed, timers, alerts, writes};
}
const output = session => String(session.completed[0] && session.completed[0].content || '');

function nodeGoodResponse() {
  return JSON.stringify({
    ip:'8.8.8.8', location:{country:'United States',country_code:'US',city:'Mountain View',state:'CA'},
    isp:{asn:15169,isp:'Google',org:'Google LLC'},
    risk:{is_datacenter:true,is_mobile:false,is_vpn:false,is_proxy:false,is_tor:false,risk_score:7}
  });
}
test('node: successful primary JSON stays on named node, disables redirects and completes once', () => {
  const session = run('node', () => ({status:200, body:nodeGoodResponse()}));
  assert.equal(session.requests.length, 1);
  assert.equal(session.requests[0].request.node, 'Node-A');
  assert.equal(session.requests[0].request['auto-redirect'], false);
  assert.equal(session.requests[0].request['auto-cookie'], false);
  assert.match(output(session), /8\.8\.8\.8/);
  assert.match(output(session), /风险评分：7/);
  assert.equal(session.completed.length, 1);
});

test('node: redirect, timeout, malformed JSON and thrown error use the existing backup', () => {
  const primaryCases = [
    {status:302, headers:{location:'https://other.example'}},
    {error:new Error('timeout')},
    {status:200, body:'{invalid'},
    {throwError:true}
  ];
  for (const primary of primaryCases) {
    const session = run('node', ({index}) => {
      if (index === 0) {
        if (primary.throwError) throw new Error('TLS certificate error');
        return primary;
      }
      return {status:200, body:JSON.stringify({
        ip:'1.1.1.1', country:'Australia', country_code:'AU',
        connection:{asn:13335,isp:'Cloudflare',org:'Cloudflare'}
      })};
    });
    assert.equal(session.requests.length, 2);
    assert.match(session.requests[1].request.url, /ipwho\.is/);
    assert.match(output(session), /1\.1\.1\.1/);
    assert.equal(session.completed.length, 1);
  }
});

test('node: malformed primary and backup never become successful measurements', () => {
  const session = run('node', () => ({status:200, body:'{"ip":"nonsense"}'}));
  assert.equal(session.requests.length, 2);
  assert.match(output(session), /查询失败/);
  assert.equal(session.completed.length, 1);
});

function networkReply(request, status) {
  assert.equal(request['auto-redirect'], false);
  assert.equal(request['auto-cookie'], false);
  assert.equal(request.url, 'https://www.gstatic.com/generate_204');
  return {status};
}
test('network: HTTP 204 plus native DoH produces a successful manual summary', () => {
  const session = run('network', ({request}) => networkReply(request, 204));
  assert.equal(session.requests.length, 2);
  assert.equal(session.requests[0].request.node, 'DIRECT');
  assert.equal(session.requests[1].request.node, 'Node-A');
  assert.match(output(session), /连接正常/);
  assert.match(output(session), /解析成功 · DoH/);
  assert.equal(session.completed.length, 1);
});

test('network: redirects and captive-portal HTTP 200 stay uncertain, not success', () => {
  const session = run('network', ({request,index}) =>
    networkReply(request, index === 0 ? 302 : 200));
  assert.match(output(session), /待确认/);
  assert.match(output(session), /目标重定向/);
  assert.match(output(session), /网络认证/);
  assert.doesNotMatch(output(session), /结论：连接正常/);
});

test('network: timeout and malformed DNS evidence fail without false DoH claims', () => {
  const session = run('network', ({index}) =>
    index === 0 ? {error:new Error('timeout')} : {status:204},
    {dns:{reply:{protocol:'doh', answers:[{type:'CNAME', value:'invalid'}]}}});
  assert.match(output(session), /部分失败/);
  assert.match(output(session), /超时/);
  assert.match(output(session), /没有获得有效的解析地址/);
  assert.doesNotMatch(output(session), /解析成功 · DoH/);
});

test('network: DNS exception and unsupported native API cannot be misreported as success', () => {
  const thrown = run('network', () => ({status:204}), {dns:{throwError:true}});
  assert.match(output(thrown), /DNS API 调用异常/);
  const missing = run('network', () => ({status:204}), {dns:null});
  assert.match(output(missing), /不支持 DNS 检测/);
  assert.match(output(missing), /部分待确认/);
});

test('network: automatic probe only sends a notification after two actual failures', () => {
  const session = run('network', () => ({error:new Error('timeout')}), {automatic:true});
  assert.equal(session.requests.length, 0);
  const first = session.timers.find(t => t.delay === 1600);
  assert.ok(first);
  first.fn();
  assert.equal(session.requests.length, 1);
  assert.equal(session.alerts.length, 0);
  const second = session.timers.find(t => t.delay === 2200);
  assert.ok(second);
  second.fn();
  assert.equal(session.requests.length, 2);
  assert.equal(session.alerts.length, 1);
  assert.equal(session.completed.length, 1);
});

function mediaResponse({method, request}) {
  const url = new URL(request.url);
  if (url.hostname === 'startup.core.indazn.com') return {status:200, body:JSON.stringify({GeolocatedCountry:'US'})};
  if (url.hostname === 'us1-prod-direct.discoveryplus.com' && url.pathname === '/token') return {status:200, body:JSON.stringify({data:{attributes:{token:'fake-test-token'}}})};
  if (url.hostname === 'us1-prod-direct.discoveryplus.com' && url.pathname === '/users/me') return {status:200, body:JSON.stringify({data:{attributes:{currentLocationTerritory:'us'}}})};
  if (url.hostname === 'www.paramountplus.com') return {status:200, body:'Paramount+'};
  if (url.hostname === 'disney.api.edge.bamgrid.com') return {status:200, body:JSON.stringify({extensions:{sdk:{session:{inSupportedLocation:true,location:{countryCode:'US'}}}}})};
  if (url.hostname === 'www.netflix.com' && url.pathname.startsWith('/title/')) return {status:200, body:'Netflix /title/81280792'};
  if (url.hostname === 'www.youtube.com' && url.pathname === '/premium') return {status:200, body:'{"GL":"US"}'};
  if (url.hostname === 'chatgpt.com' && url.pathname === '/cdn-cgi/trace') return {status:200, body:'loc=US\n'};
  if (url.href === 'https://chatgpt.com/') return {status:200, body:'ChatGPT OpenAI'};
  return {status:503};
}
test('media: seven mocked supported responses produce seven distinct verdicts', () => {
  const session = run('media', mediaResponse);
  assert.equal(session.completed.length, 1);
  const out = output(session);
  for (const name of ['DAZN','Discovery+','Paramount+','Disney+','Netflix','ChatGPT','YouTube Premium']) {
    assert.ok(out.includes(name + '：'), 'missing service result: ' + name);
  }
  assert.match(out, /Netflix：完整解锁/);
  assert.match(out, /YouTube Premium：已解锁/);
  assert.equal((out.match(/已解锁/g)||[]).length, 6);
  assert.ok(session.requests.every(r => r.request.node === 'Node-A'));
  assert.ok(session.requests.length >= 9);
  assert.ok(session.requests.filter(r => r.method === 'POST').length >= 2);
});

test('media: redirect-based block and Netflix 404 remain conservative', () => {
  const session = run('media', call => {
    if (new URL(call.request.url).hostname === 'www.paramountplus.com')
      return {status:302, headers:{location:'https://www.paramountplus.com/unavailable'}};
    if (new URL(call.request.url).hostname === 'www.netflix.com') return {status:404};
    if (call.request.url === 'https://chatgpt.com/')
      return {status:302, headers:{Location:'https://auth.openai.com/login'}};
    return mediaResponse(call);
  });
  assert.match(output(session), /Paramount\+：未解锁/);
  assert.match(output(session), /Netflix：仅自制剧/);
  assert.match(output(session), /ChatGPT：已解锁/);
});

test('media: malformed platform JSON and thrown requests cannot create supported verdicts', () => {
  const session = run('media', call => {
    if (new URL(call.request.url).hostname === 'disney.api.edge.bamgrid.com') return {status:200, body:'{broken'};
    if (new URL(call.request.url).hostname === 'startup.core.indazn.com') throw new Error('request exception');
    return mediaResponse(call);
  });
  assert.match(output(session), /DAZN：检测失败/);
  assert.match(output(session), /Disney\+：检测失败/);
});

test('media: a delayed request reaches the existing 22-second watchdog exactly once', () => {
  const session = run('media', call => {
    if (new URL(call.request.url).hostname === 'www.netflix.com') return {hold:true};
    return mediaResponse(call);
  });
  assert.equal(session.completed.length, 0);
  const watchdog = session.timers.find(t => t.delay === 22000);
  assert.ok(watchdog);
  watchdog.fn();
  assert.equal(session.completed.length, 1);
  assert.match(output(session), /Netflix：检测失败/);
  session.requests.find(r => new URL(r.request.url).hostname === 'www.netflix.com')
    .callback(null, {status:200}, 'Netflix /title/81280792');
  watchdog.fn();
  assert.equal(session.completed.length, 1);
});
