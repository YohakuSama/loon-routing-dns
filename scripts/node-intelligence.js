/*
 * Loon Network Diagnostics - Node Intelligence v1.3
 * Manual only. No MITM, no DNS/policy mutation.
 * IP data: ipquery.io; fallback: ipwho.is.
 * Classification is heuristic. Outgoing IP != physical node entry address.
 */
(function () {
  "use strict";

  var DEFAULT_POLICY = "Proxy";
  var TIMEOUT = 8500;
  var doneOnce = false;
  var arg = (typeof $argument === "object" && $argument) || {};
  var context = (typeof $environment === "object" && $environment && $environment.params) || {};
  var configured = typeof arg.target_policy === "string" && arg.target_policy.trim() || DEFAULT_POLICY;
  var compare = arg.compare_direct === true;
  function url(value, fallback) {
    var x = typeof value === "string" ? value.trim() : "";
    return /^https:\/\/[^\s#]+$/i.test(x) && x.length <= 2048 ? x : fallback;
  }
  var PRIMARY = url(arg.primary_ip_url, "https://api.ipquery.io/?format=json");
  var FALLBACK = url(arg.backup_ip_url, "https://ipwho.is/");
  var FALLBACK_ENABLED = arg.enable_ip_backup !== false;
  function cacheTTL(value) {
    var n = Number(value);
    return isFinite(n) && n >= 0 && n <= 600 ? Math.floor(n)*1000 : 120000;
  }
  var CACHE_DURATION = cacheTTL(arg.cache_seconds);
  var route = selectRoute();
  function simpleHash(x) {
    var h=2166136261;
    for(var i=0;i<x.length;i++){h ^= x.charCodeAt(i); h = Math.imul(h,16777619);}
    return (h>>>0).toString(16);
  }
  var cacheKey = "loon:node-intel:v2:" + encodeURIComponent(route) + ":" +
    simpleHash(PRIMARY + "|" + FALLBACK + "|" + String(FALLBACK_ENABLED));
  
  function cacheIsSafe() {
    // Do not reuse potentially stale cached egress for dynamic selector groups.
    // Only explicit node entry points have a stable identity; even then use short TTL.
    var explicit = choose(context.node) ||
      (context.nodeInfo && typeof context.nodeInfo === "object" && (choose(context.nodeInfo.name) || choose(context.nodeInfo.tag)));
    return !!explicit && explicit === route && route !== "DIRECT";
  }
  function readCache() {
    if (!CACHE_DURATION || !cacheIsSafe() || typeof $persistentStore === "undefined") return null;
    try {
      var record = JSON.parse($persistentStore.read(cacheKey) || "null");
      if (!record || !record.at || Date.now() - record.at > CACHE_DURATION ||
          !record.info || !validIp(record.info.ip)) return null;
      record.info.cached = true;
      return record.info;
    } catch (e) { return null; }
  }
  function writeCache(info) {
    if (!CACHE_DURATION || !cacheIsSafe() || typeof $persistentStore === "undefined" || !info) return;
    try { $persistentStore.write(JSON.stringify({at: Date.now(), info: info}), cacheKey); } catch (e) {}
  }


  function choose(v) {
    return typeof v === "string" && v.trim() ? v.trim() : "";
  }
  function selectRoute() {
    var info = context.nodeInfo;
    // Only use a node's visible name, never its server config, token or password.
    var name = choose(context.node);
    if (!name && info && typeof info === "object") {
      name = choose(info.name) || choose(info.tag);
    }
    if (!name) name = choose(context.policyGroup);
    return name || configured;
  }
  function safe(v, fallback) {
    if (typeof v === "number" && isFinite(v)) v = String(v);
    if (typeof v !== "string") return fallback || "未知";
    v = v.replace(/[\r\n\t\u0000-\u001f\u007f]/g, " ").trim();
    return v ? v.slice(0, 140) : (fallback || "未知");
  }
  function validIp(s) {
    if (typeof s !== "string" || s.length > 45 || s.length < 3) return false;
    if (s.indexOf(":") >= 0) return /^[0-9a-f:]+$/i.test(s) && s.indexOf(":") !== -1;
    var a = s.split(".");
    if (a.length !== 4) return false;
    for (var i = 0; i < 4; i++) {
      if (!/^\d{1,3}$/.test(a[i]) || +a[i] > 255) return false;
    }
    return true;
  }
  function errorText(err) {
    var s = String(err || "");
    if (/timeout|timed out/i.test(s)) return "超时";
    if (/dns|resolve|unknown host/i.test(s)) return "域名解析失败";
    if (/tls|ssl|certificat/i.test(s)) return "TLS/证书错误";
    return "连接失败";
  }
  function request(url, policy, cb) {
    var start = Date.now();
    try {
      $httpClient.get({
        url: url,
        node: policy,
        timeout: TIMEOUT,
        headers: { "Accept": "application/json", "Cache-Control": "no-store" },
        "auto-cookie": false,
        "auto-redirect": false
      }, function (err, response, data) {
        if (err) return cb({ ok: false, reason: errorText(err) });
        var status = response && response.status;
        if (status !== 200) return cb({ ok: false, reason: "HTTP " + String(status || "未知") });
        if (typeof data !== "string" || data.length > 100000) return cb({ ok: false, reason: "响应格式异常" });
        try {
          cb({ ok: true, value: JSON.parse(data), ms: Date.now() - start });
        } catch (e) {
          cb({ ok: false, reason: "JSON 格式错误" });
        }
      });
    } catch (e) {
      cb({ ok: false, reason: errorText(e) });
    }
  }
  function parsePrimary(raw) {
    if (!raw || typeof raw !== "object" || !validIp(raw.ip)) return null;
    var loc = raw.location || {};
    var isp = raw.isp || {};
    var risk = raw.risk || {};
    return {
      ip: raw.ip,
      country: safe(loc.country),
      countryCode: safe(loc.country_code),
      region: safe(loc.state),
      city: safe(loc.city),
      timezone: safe(loc.timezone),
      zip: safe(loc.zipcode),
      lat: typeof loc.latitude === "number" ? loc.latitude : null,
      lon: typeof loc.longitude === "number" ? loc.longitude : null,
      asn: safe(isp.asn),
      org: safe(isp.org),
      isp: safe(isp.isp),
      mobile: typeof risk.is_mobile === "boolean" ? risk.is_mobile : null,
      datacenter: typeof risk.is_datacenter === "boolean" ? risk.is_datacenter : null,
      vpn: typeof risk.is_vpn === "boolean" ? risk.is_vpn : null,
      proxy: typeof risk.is_proxy === "boolean" ? risk.is_proxy : null,
      tor: typeof risk.is_tor === "boolean" ? risk.is_tor : null,
      riskScore: typeof risk.risk_score === "number" && isFinite(risk.risk_score) && risk.risk_score >= 0 && risk.risk_score <= 100 ? risk.risk_score : null,
      provider: "ipquery.io"
    };
  }
  function parseFallback(raw) {
    if (!raw || raw.success === false || !validIp(raw.ip)) return null;
    var loc = raw || {};
    var isp = raw.connection || {};
    return {
      ip: raw.ip,
      country: safe(loc.country),
      countryCode: safe(loc.country_code),
      region: safe(loc.region),
      city: safe(loc.city),
      timezone: safe((loc.timezone || {}).id || loc.timezone),
      zip: safe(loc.postal),
      lat: typeof loc.latitude === "number" ? loc.latitude : null,
      lon: typeof loc.longitude === "number" ? loc.longitude : null,
      asn: isp.asn ? "AS" + String(isp.asn).replace(/^AS/i, "") : "未知",
      org: safe(isp.org), isp: safe(isp.isp),
      mobile: null, datacenter: null, vpn: null, proxy: null, tor: null,
      riskScore: null,
      provider: "ipwho.is（仅位置与 ASN）"
    };
  }
  function decodeAPI(raw) {
    if (!raw || typeof raw !== "object") return null;
    // Accept supported IPQuery or ipwho JSON schemas from user-configured HTTPS mirrors.
    if (raw.success === false) return null;
    if (raw.location && raw.isp && typeof raw.isp === "object")
      return parsePrimary(raw);
    if (raw.connection || (raw.country && raw.ip))
      return parseFallback(raw);
    return null;
  }
  function fetchInfo(policy, cb) {
    request(PRIMARY, policy, function (r) {
      var item = r.ok ? decodeAPI(r.value) : null;
      if (item) { item.ms = r.ms; return cb(null, item); }
      var primaryError = r.ok ? "主要 API JSON 字段不兼容" : r.reason;
      if (!FALLBACK_ENABLED || FALLBACK === PRIMARY) return cb("主要 API：" + primaryError + "；备用源已关闭/重复", null);
      request(FALLBACK, policy, function (f) {
        item = f.ok ? decodeAPI(f.value) : null;
        if (item) { item.ms = f.ms; return cb(null, item); }
        cb("主要 API：" + primaryError + "；备用 API：" + (f.ok ? "JSON 字段不兼容" : f.reason), null);
      });
    });
  }
  function classification(x) {
    if (x.mobile === true) return "移动网络 / 蜂窝 IP（情报判断）";
    if (x.datacenter === true) return "机房 / 云服务 / 托管 IP（情报判断）";
    if (x.datacenter === false && x.mobile === false) {
      return "未标记为机房或移动网络；可能是家宽 / 企业 ISP（无法证实家宽）";
    }
    return "未知（当前情报源无机房识别字段）";
  }
  function signal(v) {
    return v === true ? "检测到" : v === false ? "未检测到" : "无数据";
  }
  function localIntel(ip) {
    if (typeof $utils === "undefined" || !$utils) return null;
    function check(method) {
      try { return typeof $utils[method] === "function" ? safe($utils[method](ip), "无数据") : "无数据"; }
      catch (e) { return "无数据"; }
    }
    return {geo: check("geoip"), asn: check("ipasn"), org: check("ipaso")};
  }

  function egressChange(info) {
    if (!cacheIsSafe() || info.cached || typeof $persistentStore === "undefined")
      return "出口变化：动态策略组或缓存结果不进行对比";
    var key = "loon:node-egress:v1:" + encodeURIComponent(route);
    var old = null;
    try { old = JSON.parse($persistentStore.read(key) || "null"); } catch(e) {}
    var message = "出口变化：首次记录基线";
    if (old && old.ip && old.at && Date.now() >= old.at &&
        Date.now() - old.at < 30 * 86400000) {
      var changes = [];
      if (old.ip !== info.ip) changes.push("IP " + safe(old.ip) + " → " + info.ip);
      if (old.asn !== "未知" && info.asn !== "未知" && old.asn !== info.asn)
        changes.push("ASN " + safe(old.asn) + " → " + info.asn);
      if (old.isp !== "未知" && info.isp !== "未知" && old.isp !== info.isp)
        changes.push("ISP " + safe(old.isp) + " → " + info.isp);
      message = changes.length ? "出口变化：" + changes.join("；") +
        "（IP 动态变化或情报更新不一定是故障）" : "出口变化：与上次查询一致";
    }
    try { $persistentStore.write(JSON.stringify({
      at: Date.now(), ip: info.ip, asn: info.asn, isp: info.isp
    }), key); } catch(e) {}
    return message;
  }
  function shortName(value) {
    var name = safe(value);
    return name.length > 34 ? name.slice(0, 16) + "…" + name.slice(-14) : name;
  }
  function render(info, local) {
    var arr = [
      "【基本信息】",
      "节点：" + shortName(route),
      "出口 IP：" + info.ip,
      "国家/地区：" + info.country + (info.countryCode !== "未知" ? " (" + info.countryCode + ")" : "")
    ];
    if (info.region !== "未知") arr.push("省/州：" + info.region);
    if (info.city !== "未知") arr.push("城市：" + info.city);
    arr.push("", "【网络归属】", "ASN：" + info.asn, "ISP：" + info.isp);
    if (info.org !== "未知" && info.org !== info.isp) arr.push("运营组织：" + info.org);
    arr.push("网络类型：" + classification(info));
    arr.push("", "【安全情报】");
    if (info.riskScore !== null) arr.push("风险评分：" + info.riskScore + "/100（情报指标）");
    arr.push("VPN：" + signal(info.vpn));
    arr.push("Proxy：" + signal(info.proxy));
    arr.push("Tor：" + signal(info.tor));
    arr.push("", "【本地核验】");
    var localData = localIntel(info.ip);
    if (localData) {
      if (localData.geo !== "无数据") arr.push("Loon GeoIP：" + localData.geo);
      if (localData.asn !== "无数据") arr.push("Loon ASN：" + localData.asn);
      if (localData.geo !== "无数据" && info.countryCode !== "未知" &&
          localData.geo.toUpperCase() !== info.countryCode.toUpperCase())
        arr.push("注意：本地 GeoIP 与第三方数据不一致");
    }
    var change = egressChange(info);
    if (change.indexOf("出口变化：动态") !== 0)
      arr.push(change.indexOf("出口变化：首次") === 0 ? "出口变化：已记录首次基线" : change);
    if (local && local.ip) {
      arr.push("直连出口：" + local.ip);
      if (route !== "DIRECT" && info.ip === local.ip)
        arr.push("注意：代理与直连出口相同，请核对所选策略");
    } else if (compare) arr.push("直连对照：查询失败");
    arr.push("", "情报来源：" + info.provider + (info.cached ? "（缓存）" : ""));
    return arr.join("\n");
  }
  function finish(text) {
    if (doneOnce) return;
    doneOnce = true;
    console.log("[Node Intelligence] " + text);
    $done({ title: "节点出口详情", content: text });
  }
  if (!route || route.length > 200) {
    finish("节点或策略组名称无效，请检查插件参数。");
    return;
  }
  // Both calls are routed explicitly. Do not silently replace a failed Proxy result with DIRECT.
  function onTargetInfo(err, info) {
    if (err) {
      finish("目标：「" + safe(route) + "」\n节点出口查询失败：" + err + "\n请检查节点可用性、策略是否为 DIRECT，以及情报 API 是否被拦截。未回退到本地 IP 冒充节点出口。");
      return;
    }
    if (!compare || route === "DIRECT") {
      finish(render(info, null));
      return;
    }
    fetchInfo("DIRECT", function (directErr, direct) {
      finish(render(info, directErr ? null : direct));
    });
  }

  var cached = readCache();
  if (cached) {
    onTargetInfo(null, cached);
  } else {
    fetchInfo(route, function (err, info) {
      if (!err) writeCache(info);
      onTargetInfo(err, info);
    });
  }
})();