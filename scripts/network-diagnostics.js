/*
 * Loon Routing DNS Console — Network Diagnostics v1.3
 * One script for Generic (manual) and Network Changed (automatic).
 * No MITM, rewrites, policy changes, or modifications to DNS settings.
 * Requirements: Loon >= 3.5.1 (983).
 */
(function () {
  "use strict";

  var TAG_AUTO = "网络切换诊断";
  var tag = typeof $script !== "undefined" && $script && $script.name || "";
  var auto = tag === TAG_AUTO;
  var simulated = tag === "模拟网络切换诊断";
  var args = typeof $argument !== "undefined" && $argument && typeof $argument === "object" ? $argument : {};
  function endpoint(value, fallback, secureOnly) {
    var url = typeof value === "string" ? value.trim() : "";
    if (url.length > 2048 || url.indexOf("#") !== -1 ||
       !(secureOnly ? /^https:\/\/[^\s]+$/i : /^https?:\/\/[^\s]+$/i).test(url)) return fallback;
    return url;
  }
  function milliseconds(value) {
    var n = Number(value);
    return isFinite(n) && n >= 2000 && n <= 12000 ? Math.floor(n) : 6500;
  }
  var dohURL = endpoint(args.doh_url,"https://dns.alidns.com/dns-query",true);
  var DIRECT_URL = endpoint(args.direct_probe_url,"http://wifi.vivo.com.cn/generate_204",false);
  var PROXY_URL = endpoint(args.proxy_probe_url,"http://cp.cloudflare.com/generate_204",false);
  var STORE_KEY = "loon-routing-dns:diagnostics:auto-alert:v1";
  var LAST_AUTO = "loon-routing-dns:diag:last-auto:v1";
  var LAST_MANUAL = "loon-routing-dns:diag:last-manual:v1";
  var COOLDOWN_MS = 30 * 60 * 1000;
  var HTTP_TIMEOUT = milliseconds(args.probe_timeout);
  var finished = false;

  function finish(report) {
    if (finished) return;
    finished = true;
    console.log("[Network Diagnostics] " + report);
    if (auto) $done();
    else $done({ title: simulated ? "模拟网络变化诊断" : "Loon 网络与 DNS 诊断", content: report });
  }
  function keepLast(group,results,kind) {
    var status = (!results.direct.ok || !results.doh.ok || (results.proxy && !results.proxy.ok)) ?
      "有检测项目异常" : "全部检测正常";
    var compact = { time: Date.now(), status: status, kind: kind };
    try { $persistentStore.write(JSON.stringify(compact), group === "auto" ? LAST_AUTO : LAST_MANUAL); }
    catch (e) {}
  }

  function classifyError(error) {
    var msg = String(error || "").toLowerCase();
    if (/timed? ?out|timeout/.test(msg)) return "连接超时";
    if (/certificat|ssl|tls|handshake/.test(msg)) return "TLS/证书错误";
    if (/resolve|dns|host not found|unknown host/.test(msg)) return "域名解析失败";
    if (/cancel/.test(msg)) return "请求被取消";
    return "连接失败";
  }

  function result(ok, label, ms, detail) {
    return { ok: ok, label: label, ms: ms, detail: detail };
  }

  function makeDnsQuery() {
    // RFC 1035: example.com A IN, RD=1; DNS transaction ID=0 per RFC 8484.
    var bytes = [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0];
    var labels = ["example", "com"];
    for (var i = 0; i < labels.length; i++) {
      bytes.push(labels[i].length);
      for (var j = 0; j < labels[i].length; j++) bytes.push(labels[i].charCodeAt(j));
    }
    bytes.push(0, 0, 1, 0, 1);
    return new Uint8Array(bytes);
  }

  function validateDnsReply(data) {
    if (!(data instanceof Uint8Array) || data.length < 33) return "DNS 响应不完整";
    if (data[0] !== 0 || data[1] !== 0) return "DNS 请求 ID 不匹配";
    if ((data[2] & 128) === 0) return "缺少 DNS 响应标志";
    if ((data[2] & 2) !== 0) return "DNS 响应被截断";
    if ((data[2] & 120) !== 0) return "DNS 操作码异常";
    var rcode = data[3] & 15;
    if (rcode !== 0) return "DNS 返回 RCODE " + rcode;
    var questions = (data[4] << 8) | data[5];
    var answers = (data[6] << 8) | data[7];
    if (questions !== 1) return "DNS Question 数量异常";
    if (answers < 1) return "DNS 未返回答案";

    // Match the exact example.com A/IN question sent by this script.
    var request = makeDnsQuery();
    if (data.length < request.length) return "DNS Question 不完整";
    for (var k = 12; k < request.length; k++) {
      if (data[k] !== request[k]) return "DNS Question 与请求不一致";
    }
    var offset = request.length;
    for (var i = 0; i < answers; i++) {
      // The answer name may use RFC 1035 compression pointers.
      var steps = 0;
      while (true) {
        if (offset >= data.length || ++steps > 128) return "DNS Answer 域名不完整";
        var length = data[offset];
        if ((length & 192) === 192) {
          if (offset + 1 >= data.length) return "DNS 压缩指针不完整";
          offset += 2;
          break;
        }
        if ((length & 192) !== 0) return "DNS Answer 域名格式错误";
        offset += 1;
        if (length === 0) break;
        if (offset + length > data.length) return "DNS Answer 域名不完整";
        offset += length;
      }
      if (offset + 10 > data.length) return "DNS Answer 记录头不完整";
      var type = (data[offset] << 8) | data[offset + 1];
      var klass = (data[offset + 2] << 8) | data[offset + 3];
      var rdlength = (data[offset + 8] << 8) | data[offset + 9];
      offset += 10;
      if (offset + rdlength > data.length) return "DNS Answer 记录数据不完整";
      if (type === 1 && klass === 1 && rdlength === 4) return null;
      offset += rdlength;
    }
    return "DNS 未返回有效 A 记录";
  }

  function probeDirect(done) {
    var start = Date.now();
    try {
      $httpClient.get({
        url: DIRECT_URL, node: "DIRECT", timeout: HTTP_TIMEOUT,
        "auto-redirect": false, "auto-cookie": false
      }, function (error, response) {
        var ms = Date.now() - start;
        if (error) return done(result(false, "直连网络", ms, classifyError(error)));
        var status = response && response.status;
        done(result((status === 204 || status === 200), "直连网络", ms, (status === 204 || status === 200) ? "HTTP " + status : "探测站点返回 HTTP " + String(status || "未知")));
      });
    } catch (error) {
      done(result(false, "直连网络", Date.now() - start, classifyError(error)));
    }
  }

  function probeDoh(done) {
    var start = Date.now();
    if (!/^https:\/\/[^\s#]+$/i.test(dohURL)) {
      done(result(false, "加密 DNS", 0, "DoH 地址必须是完整 HTTPS URL"));
      return;
    }
    try {
      $httpClient.post({
        url: dohURL, node: "DIRECT", timeout: HTTP_TIMEOUT,
        headers: { "Accept": "application/dns-message", "Content-Type": "application/dns-message" },
        body: makeDnsQuery(), "binary-mode": true,
        "auto-redirect": false, "auto-cookie": false, insecure: false
      }, function (error, response, data) {
        var ms = Date.now() - start;
        if (error) return done(result(false, "加密 DNS", ms, classifyError(error)));
        var status = response && response.status;
        if (status !== 200) {
          return done(result(false, "加密 DNS", ms, "DoH HTTP " + String(status || "未知")));
        }
        var err = validateDnsReply(data);
        done(result(!err, "加密 DNS", ms, err || "DNS A 查询成功 (example.com)"));
      });
    } catch (error) {
      done(result(false, "加密 DNS", Date.now() - start, classifyError(error)));
    }
  }

  function probeProxy(done) {
    var start = Date.now();
    try {
      $httpClient.get({
        url: PROXY_URL, node: "Proxy", timeout: HTTP_TIMEOUT,
        "auto-redirect": false, "auto-cookie": false
      }, function (error, response) {
        var ms = Date.now() - start;
        if (error) return done(result(false, "代理策略 Proxy", ms, classifyError(error) + "（检查节点订阅与 Proxy 选择）"));
        var status = response && response.status;
        done(result((status === 204 || status === 200), "代理策略 Proxy", ms,
          (status === 204 || status === 200) ? "HTTP " + status : "探测站点返回 HTTP " + String(status || "未知")));
      });
    } catch (error) {
      done(result(false, "代理策略 Proxy", Date.now() - start, classifyError(error)));
    }
  }

  function probeNativeDNS(done) {
    // $dns.query is available only in Loon Build 988 or later.
    if (typeof $dns === "undefined" || !$dns || typeof $dns.query !== "function") {
      done({ available: false, text: "原生 DNS：当前 Loon 不支持 $dns.query（需 Build 988+）；HTTP DoH 检测仍可用。" });
      return;
    }
    var start = Date.now();
    var returned = false;
    function finishNative(v) {
      if (returned) return;
      returned = true;
      done(v);
    }
    try {
      $dns.query({ domain: "example.com", protocol: "auto", timeout: HTTP_TIMEOUT },
        function (error, reply) {
          var elapsed = Date.now() - start;
          if (error || !reply) {
            var code = error && error.code ? safeDNSLabel(error.code) : "QUERY_FAILED";
            finishNative({ available: true, text: "原生 DNS：失败（" + code + "，" + elapsed + " ms）" });
            return;
          }
          var protocol = safeDNSLabel(reply.protocol || "未知");
          var answers = Array.isArray(reply.answers) ? reply.answers : [];
          var a = 0, aaaa = 0;
          for (var i = 0; i < answers.length; i++) {
            if (answers[i].type === "A") a++;
            if (answers[i].type === "AAAA") aaaa++;
          }
          var passed = a + aaaa > 0;
          // Never print the resolver's full URL because personal DoH URLs may contain tokens.
          finishNative({
            available: true,
            text: (passed ? "✓ " : "✗ ") + "Loon 原生 DNS：" +
              (passed ? "有解析记录" : "无 A/AAAA") + "，协议 " + protocol +
              "，A " + a + " / AAAA " + aaaa +
              "，缓存 " + (reply.fromCache === true ? "命中" : "未命中/未知") +
              "，" + elapsed + " ms（服务器完整地址已隐藏）"
          });
        });
    } catch (e) {
      finishNative({ available: true, text: "原生 DNS：API 调用失败，请检查 Loon Build 988+。" });
    }
  }
  function safeDNSLabel(text) {
    return String(text || "").replace(/[^A-Za-z0-9_-]/g, "").slice(0, 40) || "未知";
  }

  function runBatch(which, callback) {
    var pending = which.length;
    var results = {};
    function collect(name, value) {
      results[name] = value;
      pending -= 1;
      if (!pending) callback(results);
    }
    for (var i = 0; i < which.length; i++) {
      (function (name) {
        var fn = name === "direct" ? probeDirect : name === "doh" ? probeDoh : probeProxy;
        fn(function (value) { collect(name, value); });
      })(which[i]);
    }
  }

  function line(item) {
    return (item.ok ? "✓ " : "✗ ") + item.label + "：" + item.detail + "，" + item.ms + " ms";
  }

  function fullReport(results, isRetry) {
    var list = [results.direct, results.doh];
    if (results.proxy) list.push(results.proxy);
    var parts = [];
    for (var i = 0; i < list.length; i++) parts.push(line(list[i]));
    if (isRetry) parts.push("已在网络切换后进行二次确认。");
    parts.push("提示：这是探测请求，不等于证明 Loon 所有 DNS 查询均通过 DoH；请结合 Loon DNS 日志核对。");
    return parts.join("\n");
  }

  function notifyIfNeeded(results) {
    if (simulated) return; // Manual simulation never posts a background failure alert.
    var directFailed = !results.direct.ok;
    var dohFailed = !results.doh.ok;
    if (!dohFailed && !directFailed) {
      try { $persistentStore.write(JSON.stringify({ key: "ok", time: Date.now() }), STORE_KEY); } catch (error) {}
      return;
    }
    // An isolated failure of the chosen HTTP 204 endpoint does not prove loss of internet.
    if (!dohFailed && directFailed) return;
    var key = directFailed ? "direct+doh" : "doh";
    var old = {};
    try { old = JSON.parse($persistentStore.read(STORE_KEY) || "{}"); } catch (error) {}
    if (old.key === key && Date.now() - Number(old.time || 0) < COOLDOWN_MS) return;
    try { $persistentStore.write(JSON.stringify({ key: key, time: Date.now() }), STORE_KEY); } catch (error) {}
    try {
      $notification.post("Loon 网络诊断", directFailed ? "网络切换后直连与 DoH 均异常" : "网络切换后 DoH 连接异常",
        directFailed ? "已二次检测失败；可能网络尚未恢复。请打开 Loon 查看日志。" : "直连探测正常，但 DoH 测试失败。请检查 DNS 服务器与网络连接。");
    } catch (error) {}
  }

  if (!auto && !simulated) {
    runBatch(["direct", "doh", "proxy"], function (results) {
      keepLast("manual",results,"手动");
      probeNativeDNS(function (native) {
        finish(fullReport(results, false) + "\n" + native.text);
      });
    });
    return;
  }

  // iOS network switching can trigger before the new route is ready.
  setTimeout(function () {
    runBatch(["direct", "doh"], function (first) {
      if (first.direct.ok && first.doh.ok) {
        keepLast("auto",first,simulated?"手动模拟":"自动网络变化");
        notifyIfNeeded(first);
        if (auto && args.notify_every_change === true) {
          try { $notification.post("Loon 网络诊断","网络变化检测已触发","直连和 DoH 探测均正常"); } catch(e) {}
        }
        finish(fullReport(first, false));
        return;
      }
      setTimeout(function () {
        runBatch(["direct", "doh"], function (second) {
          keepLast("auto",second,simulated?"手动模拟":"自动网络变化");
          notifyIfNeeded(second);
          if (auto && args.notify_every_change === true && second.direct.ok && second.doh.ok) {
            try { $notification.post("Loon 网络诊断","网络变化已触发","第二次检测恢复正常"); } catch(e) {}
          }
          finish(fullReport(second, true));
        });
      }, 2500);
    });
  }, 1800);
})();
