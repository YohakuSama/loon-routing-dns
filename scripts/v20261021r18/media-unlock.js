/* LoonKit · 手动节点解锁检测。
 * 固定节点出口；服务专项信号与普通网页响应分开。
 * 请求排队限流，暂时故障最多重试一次，超时按事实报告。
 */
(function () {
  "use strict";
  var args=(typeof $argument==="object" && $argument)||{};
  var ctx=(typeof $environment==="object" && $environment && $environment.params)||{};
  var info=(ctx.nodeInfo && typeof ctx.nodeInfo==="object")?ctx.nodeInfo:{};
  function nonempty(s){return typeof s==="string"&&s.trim()?s.trim():"";}
  var node=nonempty(ctx.node)||nonempty(info.name)||nonempty(info.tag)||
    nonempty(ctx.policyGroup)||nonempty(args.target_policy)||"Proxy";
  var full=args.full_scan===true||args.full_scan==="true";
  var budget=full?26000:19000,started=Date.now(),ended=false;
  var serviceList=[
    ["netflix","Netflix","流媒体"],["disney","Disney+","流媒体"],
    ["youtube","YouTube Premium","流媒体"],["spotify","Spotify","流媒体"],
    ["tiktok","TikTok","流媒体"],["chatgpt","ChatGPT","AI"],
    ["gemini","Gemini","AI"],["claude","Claude","AI"]
  ];
  if(full)serviceList=serviceList.concat([
    ["prime","Prime Video","流媒体"],["apple","Apple 地区","其他"],
    ["bili_hk","Bilibili 港澳台","其他"],["bili_cn","Bilibili 大陆","其他"],
    ["bbc","BBC iPlayer","其他"],["abema","Abema","其他"]
  ]);
  var result=new Array(serviceList.length),queue=[],inFlight=0,finished=0,idx=0,running=0,flushing=false;
  var MAX_HTTP=6,MAX_SERVICES=8;
  // Start time-sensitive Gemini checks early rather than behind all media probes.
  var serviceOrder=[6,0,2,1,3,5,4,7];
  for(var si=8;si<serviceList.length;si++)serviceOrder.push(si);
  function state(code,extra){return {code:code,extra:extra||""};}
  function done(payload){if(ended)return;ended=true;$done(payload);}
  if(node.length>220||/[\u0000-\u001f\u007f]/.test(node)){done({title:"解锁检测",content:"节点名称无效"});return;}
  function elapsed(){return Date.now()-started;}
  function timeLeft(){return budget-elapsed();}
  function cleanBody(body){return typeof body==="string"?body.slice(0,200000):"";}
  function httpStatus(r){return Number(r&&r.status)||0;}
  function header(r,key){
    var headers=r&&r.headers||{},keys=Object.keys(headers);
    for(var i=0;i<keys.length;i++)if(keys[i].toLowerCase()===key.toLowerCase())return String(headers[keys[i]]||"");
    return "";
  }
  function country(s){var x=String(s||"").toUpperCase();return /^[A-Z]{2,3}$/.test(x)?x:"";}
  function knownResponse(r){var c=httpStatus(r);return c>=200&&c<400;}
  function actionable(err,r){return err&&!httpStatus(r);}
  function extract(body,re){var m=body.match(re);return m?country(m[1]):"";}
  function traceRegion(body){return extract(body,/^loc=([A-Za-z]{2})\s*$/m);}
  function restricted(body){return /unsupported_country|forbidden.location|not available in your (?:country|region)|not supported in your (?:country|region)|this service is not available in your (?:country|region)/i.test(body);}
  function statusError(err){
    if(!err)return "";
    var s=String(err&&err.message||err).toLowerCase();
    return /timeout|timed out|time out/.test(s)?"timeout":"failed";
  }
  // Shared HTTP semaphore: multi-request Netflix/ChatGPT cannot exceed MAX_HTTP.
  function send(){
    if(flushing||ended)return;
    flushing=true;
    while(inFlight<MAX_HTTP && queue.length && !ended){
      (function(task){
        inFlight++;
        var finishedTask=false,opts={
          url:task.url,node:node,timeout:5100,
          "auto-cookie":false,"auto-redirect":task.follow!==false,insecure:false,
          headers:{"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36","Accept-Language":"en-US,en;q=0.8"}
        };
        if(task.headers)Object.keys(task.headers).forEach(function(k){opts.headers[k]=task.headers[k];});
        if(task.method==="POST")opts.body=task.body;
        function complete(err,res,body){
          if(finishedTask)return;
          finishedTask=true;
          inFlight--;
          if(!ended)task.cb(err&&httpStatus(res)>=400?null:err,res||{},cleanBody(body));
          if(!ended)send();
        }
        try{var requester=task.method==="POST"?$httpClient.post:$httpClient.get;
          if(typeof requester!=="function")throw new Error("HTTP method unavailable");
          requester.call($httpClient,opts,complete);
        }catch(e){complete(e,null,"");}
      })(queue.shift());
    }
    flushing=false;
  }
  function get(url,cb,follow){if(ended)return;queue.push({url:url,cb:cb,follow:follow,method:"GET"});send();}
  function post(url,body,headers,cb){
    if(ended)return;
    queue.push({url:url,body:body,headers:headers,cb:cb,follow:false,method:"POST"});send();
  }
  function decodeJSON(body){try{return JSON.parse(body);}catch(e){return null;}}
  function reliable(url,cb,follow){
    var tried=false;
    function once(err,r,body){
      if(err && !tried && timeLeft()>6600){
        tried=true;get(url,once,follow);return;
      }
      cb(err,r,body);
    }
    get(url,once,follow);
  }
  function resultFromError(err){return state(statusError(err)==="timeout"?"timeout":"failed");}
  function run(item,cb){
    var id=item[0],called=false;
    function finish(code,extra){if(called)return;called=true;cb(state(code,extra));}
    if(id==="netflix"){
      var statuses=[0,0],proof=[false,false],errs=["",""],count=0,cdnDone=false,cdnRegion="";
      var originalsRequested=false,originalsDone=false,originalsProof=false;
      function realTitle(err,r,b,film){
        if(err)return false;
        var status=httpStatus(r),loc=header(r,"location"),canonical=header(r,"x-originating-url");
        var titlePage=/netflix/i.test(b)&&
          (b.indexOf(film)>=0||canonical.indexOf("/title/"+film)>=0);
        return (status===200&&titlePage)||
          ((status===301||status===302)&&/netflix\.com/i.test(loc)&&
           (loc.indexOf("/title/"+film)>=0));
      }
      function netflixResult(){
        if(called)return;
        if(proof[0]||proof[1])return finish("available",cdnRegion);
        if(count!==2)return;
        if(statuses.indexOf(451)>=0)return finish("blocked");
        if(statuses[0]===404&&statuses[1]===404&&!originalsRequested){
          originalsRequested=true;
          // An original-title response provides evidence when regional titles
          // are unavailable; two 404s alone never prove "originals only".
          get("https://www.netflix.com/title/80018499",function(err,r,b){
            originalsProof=realTitle(err,r,b,"80018499");
            originalsDone=true;netflixResult();
          },false);
        }
        if(originalsRequested&&!originalsDone)return;
        if(originalsProof)return finish("partial",cdnRegion);
        if(!cdnDone)return;
        if(cdnRegion)return finish("cdn",cdnRegion);
        if(errs[0]&&errs[1])return finish(errs.indexOf("timeout")>=0?"timeout":"failed");
        finish("unknown","影片页面无有效信息");
      }
      ["81280792","70143836"].forEach(function(film,n){
        reliable("https://www.netflix.com/title/"+film,function(err,r,b){
          statuses[n]=httpStatus(r);errs[n]=statusError(err);
          proof[n]=realTitle(err,r,b,film);
          count++;netflixResult();
        },false);
      });
      get("https://api.fast.com/netflix/speedtest/v2?https=true&token=YXNkZmFzZGxmbnNkYWZoYXNkZmhrYWxm&urlCount=5",function(err,r,b){
        if(!err&&httpStatus(r)===200){
          var json=decodeJSON(b);
          cdnRegion=country(json&&json.targets&&json.targets[0]&&json.targets[0].location&&json.targets[0].location.country);
        }
        cdnDone=true;netflixResult();
      },false);
    } else if(id==="disney"){
      // Anonymous BAMTech region session is the strongest available signal.
      // A home page/landing region is a useful fallback but NOT unlock proof.
      var root="https://disney.api.edge.bamgrid.com";
      var auth="Bearer ZGlzbmV5JmJyb3dzZXImMS4wLjA.Cu56AgSfBTDag5NiRA81oLHkDZfu5L3CKadnefEAY84";
      var hdr={"authorization":auth,"Content-Type":"application/json"};
      var homepage={ready:false,region:"",reachable:false,blocked:false},fallbackFn=null;
      get("https://www.disneyplus.com/",function(err,r,b){
        homepage.ready=true;
        homepage.region=!err&&httpStatus(r)===200?
          extract(b,/"region"\s*:\s*"([A-Za-z]{2})"/i):"";
        homepage.blocked=httpStatus(r)===451||(!err&&restricted(b));
        homepage.reachable=!err&&knownResponse(r);
        if(fallbackFn){var next=fallbackFn;fallbackFn=null;next();}
      },true);
      function fallback(reason){
        function settle(){
          if(homepage.blocked)return finish("blocked");
          if(homepage.region)return finish("site_region",homepage.region);
          if(homepage.reachable)return finish("reachable",reason||"地区接口无有效结果");
          finish("unknown",reason||"地区接口无有效结果");
        }
        if(homepage.ready)return settle();
        fallbackFn=settle;
      }
      function interpret(body){
        var data=decodeJSON(body);
        var session=data&&data.extensions&&data.extensions.sdk&&data.extensions.sdk.session;
        var code=session&&session.location&&country(session.location.countryCode);
        var supported=session&&session.inSupportedLocation;
        if(code&&typeof supported==="boolean")
          return finish(supported?"available":"blocked",code);
        fallback("地区会话无有效状态");
      }
      function failure(err,r,body){
        if(/forbidden[-_.]location|unsupported_country|unsupported.country/i.test(body)||
            httpStatus(r)===451)return finish("blocked");
        if(httpStatus(r)===429)return fallback("地区接口请求过多");
        if(httpStatus(r)===403)return fallback("地区接口拒绝访问");
        fallback(err&&statusError(err)==="timeout"?"地区接口请求超时":"地区接口无有效结果");
      }
      function graphRefresh(token){
        var payload=JSON.stringify({query:"mutation refreshToken($input: RefreshTokenInput!) { refreshToken(refreshToken: $input) { activeSession { sessionId } } }",
          variables:{input:{refreshToken:token}}});
        post(root+"/graph/v1/device/graphql",payload,hdr,function(err,r,b){
          if(err||httpStatus(r)!==200)return failure(err,r,b);
          interpret(b);
        });
      }
      function exchange(assertion){
        var form=["grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Atoken-exchange",
          "latitude=0","longitude=0","platform=browser",
          "subject_token="+encodeURIComponent(assertion),
          "subject_token_type=urn%3Abamtech%3Aparams%3Aoauth%3Atoken-type%3Adevice"].join("&");
        post(root+"/token",form,{"authorization":auth,"Content-Type":"application/x-www-form-urlencoded"},
        function(err,r,b){
          if(err||httpStatus(r)!==200)return failure(err,r,b);
          var data=decodeJSON(b),token=data&&data.refresh_token;
          if(typeof token!=="string"||!token||token.length>5000)
            return fallback("地区接口令牌无效");
          graphRefresh(token);
        });
      }
      function verifyLegacy(){
        post(root+"/devices",JSON.stringify({deviceFamily:"browser",applicationRuntime:"chrome",
        deviceProfile:"windows",attributes:{}}),hdr,function(err,r,b){
        if(err||httpStatus(r)!==200)return failure(err,r,b);
        var data=decodeJSON(b),assertion=data&&data.assertion;
        if(!assertion&&data&&data.data)assertion=data.data.assertion;
        if(typeof assertion!=="string"||!assertion||assertion.length>5000)
          return fallback("地区接口设备注册失败");
        exchange(assertion);
      });
      }
      // First probe the one-step regional session used by established Loon tools.
      // Use the longer token workflow only when it has no actionable result.
      var quick=JSON.stringify({
        query:"mutation registerDevice($input: RegisterDeviceInput!) { registerDevice(registerDevice: $input) { grant { grantType assertion } } }",
        variables:{input:{applicationRuntime:"chrome",deviceFamily:"browser",
          deviceLanguage:"en",deviceProfile:"windows",
          attributes:{browserName:"chrome",browserVersion:"94.0.4606",
            manufacturer:"microsoft",operatingSystem:"windows",
            operatingSystemVersion:"10.0",osDeviceIds:[]}}}
      });
      post(root+"/graph/v1/device/graphql",quick,{
        "Authorization":auth.replace(/^Bearer /,""),
        "Content-Type":"application/json","User-Agent":"UA"
      },function(err,r,b){
        var parsed=decodeJSON(b),session=parsed&&parsed.extensions&&parsed.extensions.sdk&&parsed.extensions.sdk.session;
        var code=session&&session.location&&country(session.location.countryCode);
        if(!err&&httpStatus(r)===200&&code&&typeof session.inSupportedLocation==="boolean")
          return finish(session.inSupportedLocation?"available":"blocked",code);
        verifyLegacy();
      });
    } else if(id==="youtube"){
      reliable("https://www.youtube.com/premium?hl=en",function(err,r,b){
        if(err)return finish(statusError(err));
        if(httpStatus(r)===451||restricted(b))return finish("blocked");
        var countryCode=extract(b,/"GL"\s*:\s*"([A-Za-z]{2})"/)||
          extract(b,/"countryCode"\s*:\s*"([A-Za-z]{2})"/i)||
          extract(b,/id=["']country-code["'][^>]*>\s*([A-Za-z]{2})/i);
        var confirmed=/"isPremiumAvailable"\s*:\s*true/i.test(b)||
          /premium is available in your country/i.test(b)||
          /"browseId"\s*:\s*"SPunlimited"/i.test(b);
        if(httpStatus(r)===200&&confirmed)return finish("available",countryCode);
        // Public Premium page: recognizable purchase/plan area is a usable
        // regional product signal, but a generic brand mention is not.
        var offer=/youtube premium/i.test(b)&&
          /(?:try premium|individual plan|family plan|student plan|join premium|start trial|get premium)/i.test(b);
        if(httpStatus(r)===200&&offer)return finish("available",countryCode);
        if(httpStatus(r)===200&&countryCode&&/youtube premium/i.test(b))
          return finish("reachable",countryCode);
        if(countryCode)return finish("region",countryCode);
        finish(knownResponse(r)?"reachable":"unknown","");
      },true);
    } else if(id==="spotify"){
      reliable("https://www.spotify.com/api/content/v1/country-selector?platform=web&format=json",function(err,r,b){
        if(err)return finish(statusError(err));
        if(httpStatus(r)===451||restricted(b))return finish("blocked");
        var code=extract(b,/"countryCode"\s*:\s*"([A-Za-z]{2})"/i);
        var redirect=header(r,"location"),url=String(r&&r.url||"");
        var m=(redirect||url).match(/spotify\.com\/([a-z]{2})(?:[-/]|$)/i);
        if(!code&&m)code=country(m[1]);
        if(code&&knownResponse(r))return finish("available",code);
        // Country-selector frequently responds with a generic landing page.
        // Such a response only proves that the site answered.
        if(knownResponse(r))return finish("reachable","");
        finish("unknown",httpStatus(r)===429?"访问次数受限":"");
      },false);
    } else if(id==="tiktok"){
      var edge="",pageResult="",pageError="",pending=2;
      function assessTikTok(){
        if(--pending)return;
        if(pageResult==="blocked")return finish("blocked","");
        if(pageResult==="reachable")return finish("reachable",edge);
        if(edge)return finish("region",edge);
        if(pageError)return finish(pageError,"");
        finish("unknown","无有效检测响应");
      }
      reliable("https://www.tiktok.com/cdn-cgi/trace",function(err,r,b){
        if(!err&&httpStatus(r)===200)edge=traceRegion(b);
        assessTikTok();
      },false);
      reliable("https://www.tiktok.com/",function(err,r,b){
        if(err)pageError=statusError(err);
        else if(httpStatus(r)===451||restricted(b)||/tiktok is not available in (?:your|this) (?:region|country)/i.test(b))
          pageResult="blocked";
        else if(httpStatus(r)===200&&/(?:tiktok|SIGI_STATE|webapp)/i.test(b))pageResult="reachable";
        else if(httpStatus(r)===200)pageResult="reachable";
        assessTikTok();
      },true);
    } else if(id==="chatgpt"){
      var parts=["未响应","未响应"],kind=["unknown","unknown"],remaining=2;
      function finishBoth(){
        if(--remaining)return;
        var detail="Web "+parts[0]+"，iOS "+parts[1];
        if(kind.indexOf("blocked")>=0)return finish("blocked",detail);
        if(kind[0]==="reachable"&&kind[1]==="reachable")return finish("reachable","Web / iOS");
        if(kind.indexOf("reachable")>=0)return finish("partial",detail);
        if(kind.indexOf("timeout")>=0)return finish("timeout",detail);
        if(kind.indexOf("failed")>=0)return finish("failed",detail);
        finish("unknown",detail);
      }
      reliable("https://api.openai.com/compliance/cookie_requirements",function(err,r,b){
        if(err){parts[0]="连接失败";kind[0]=statusError(err);return finishBoth();}
        if(httpStatus(r)===451||restricted(b)){parts[0]="地区受限";kind[0]="blocked";return finishBoth();}
        // HTTP 200 JSON from the compliance API confirms endpoint access,
        // not account login or model access.
        if(httpStatus(r)===200&&/^\s*\{/.test(b)){parts[0]="可访问";kind[0]="reachable";}
        else if(httpStatus(r)===403){parts[0]="访问被拒";kind[0]="unknown";}
        finishBoth();
      },true);
      reliable("https://ios.chat.openai.com/",function(err,r,b){
        if(err){parts[1]="连接失败";kind[1]=statusError(err);return finishBoth();}
        if(/disallowed isp|unsupported_country|not supported in your (?:country|region)/i.test(b)||httpStatus(r)===451){
          parts[1]="地区受限";kind[1]="blocked";return finishBoth();
        }
        if(b.toLowerCase().indexOf("request is not allowed. please try again later.")>=0){
          parts[1]="接口可响应";kind[1]="reachable";
        }else if(httpStatus(r)===403||/have been blocked/i.test(b)){
          parts[1]="安全验证拦截";kind[1]="unknown";
        }
        finishBoth();
      },true);
    } else if(id==="gemini"){
      // Application homepage first; a valid Google API auth response can
      // establish API reachability even when the app frontend times out.
      function fallbackGemini(err) {
        get("https://generativelanguage.googleapis.com/v1beta/models",function(apiErr,r,b){
          if(!apiErr&&httpStatus(r)===451)return finish("blocked","");
          if(!apiErr&&httpStatus(r)===200&&/models|google/i.test(b))
            return finish("api_reachable","");
          if(!apiErr&&httpStatus(r)>=400&&httpStatus(r)<500&&
            /api.key|API_KEY|UNAUTHENTICATED|INVALID_ARGUMENT/i.test(b))
            return finish("api_reachable","");
          finish(statusError(err)==="timeout"?"timeout":statusError(apiErr)||"unknown","");
        },false);
      }
      get("https://gemini.google.com/",function(err,r,b){
        if(err)return fallbackGemini(err);
        if(httpStatus(r)===451||restricted(b))return finish("blocked","");
        var code=extract(b,/,2,1,200,"([A-Z]{3})"/);
        if(code&&httpStatus(r)===200)return finish("region",code);
        if(httpStatus(r)===200)return finish("reachable","");
        fallbackGemini(null);
      },true);
    } else if(id==="claude"){
      var edge="",pageResult="",pageError="",pending=2;
      function assessClaude(){
        if(--pending)return;
        if(pageResult==="blocked")return finish("blocked",edge);
        if(pageResult==="reachable")return finish("reachable",edge);
        if(edge)return finish("region",edge);
        if(pageError)return finish(pageError,"");
        finish("unknown","");
      }
      reliable("https://claude.ai/cdn-cgi/trace",function(err,r,b){
        if(!err&&httpStatus(r)===200)edge=traceRegion(b);
        assessClaude();
      },false);
      reliable("https://claude.ai/",function(err,r,b){
        if(err)pageError=statusError(err);
        else if(httpStatus(r)===451||restricted(b))pageResult="blocked";
        else if(httpStatus(r)===200)pageResult="reachable";
        assessClaude();
      },true);
    } else if(id==="prime"){
      reliable("https://www.primevideo.com/",function(err,r,b){
        if(err)return finish(statusError(err));
        var code=extract(b,/"currentTerritory"\s*:\s*"([A-Za-z]{2})"/i);
        if(/"isServiceRestricted"\s*:\s*true/i.test(b)||httpStatus(r)===451)return finish("blocked",code);
        if(code&&/"isServiceRestricted"\s*:\s*false/i.test(b))return finish("available",code);
        finish(code?"region":"unknown",code);
      },true);
    } else if(id==="apple"){
      reliable("https://gspe1-ssl.ls.apple.com/pep/gcc",function(err,r,b){
        if(err)return finish(statusError(err));
        var code=country(b.trim());
        finish(code.length===2&&httpStatus(r)===200?"region":"unknown",code);
      },true);
    } else if(id==="bili_hk"||id==="bili_cn"){
      var q=id==="bili_hk"?
        "avid=18281381&cid=29892777&qn=0&type=&otype=json&ep_id=183799&fourk=1&fnver=0&fnval=16&module=bangumi":
        "avid=82846771&qn=0&type=&otype=json&ep_id=307247&fourk=1&fnver=0&fnval=16&module=bangumi";
      reliable("https://api.bilibili.com/pgc/player/web/playurl?"+q,function(err,r,b){
        if(err)return finish(statusError(err));
        try{
          var obj=JSON.parse(b),v=obj.code,stream=obj.result||obj.data||{};
          var playable=!!((Array.isArray(stream.durl)&&stream.durl.length)||
            (stream.dash&&Array.isArray(stream.dash.video)&&stream.dash.video.length));
          return finish(v===0&&playable?"available":v===-10403?"blocked":"unknown");
        }
        catch(e){finish("unknown");}
      },true);
    } else if(id==="bbc"||id==="abema"){
      reliable(id==="bbc"?"https://www.bbc.co.uk/iplayer":"https://abema.tv/",function(err,r,b){
        if(err)return finish(statusError(err));
        if(httpStatus(r)===451||/bbc iplayer only works in the uk|only available in the uk|お住まいの地域では視聴できません|outside of japan/i.test(b))
          return finish("blocked");
        finish("unknown","无可用播放判定");
      },true);
    } else finish("unknown");
  }
  // Keep the node menu readable. Verdicts describe reachability and the
  // platform's public regional response, NOT logged-in/paid account benefits.
  function value(r,id){
    var code=r&&r.code||"unknown";
    var region=r&&/^[A-Z]{2,3}$/.test(r.extra||"")?r.extra:"";
    var suffix=region?"（"+region+"）":"";
    if(code==="blocked")return "不可用"+suffix;
    if(code==="available")return "可用"+suffix;
    if(code==="partial")return "部分可用"+suffix;
    if(code==="site_region"||code==="cdn"||code==="region")
      return "可连接"+suffix;
    if(code==="api_reachable")return "可连接";
    if(code==="reachable")return "可连接"+suffix;
    return "检测失败";
  }
  function output(){
    var ms=elapsed(),display=node.length>32?node.slice(0,24)+"…"+node.slice(-5):node;
    var lines=["节点："+display,"耗时："+(ms/1000).toFixed(1)+" 秒"];
    serviceList.forEach(function(s,i){
      lines.push(s[1]+"："+value(result[i]||state("timeout"),s[0]));
    });
    lines.push("","仅检测节点连接与地区，会员及实际播放需登录确认。","检测器 v6.4.2");
    return {title:"解锁检测",content:lines.join("\n")};
  }
  function pumpService(){
    if(ended)return;
    if(finished===serviceList.length){done(output());return;}
    while(running<MAX_SERVICES&&idx<serviceList.length&&!ended){
      (function(i){
        var released=false;
        running++;
        function release(r){
          if(released||ended)return;released=true;
          result[i]=r;running--;finished++;
          pumpService();
        }
        try{run(serviceList[i],release);}catch(e){release(state("unknown","脚本异常"));}
      })(serviceOrder[idx++]);
    }
  }
  setTimeout(function(){done(output());},budget);
  pumpService();
})();