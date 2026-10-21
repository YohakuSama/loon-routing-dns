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
  var budget=full?19500:12000,started=Date.now(),ended=false;
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
  var MAX_HTTP=6,MAX_SERVICES=6;
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
          url:task.url,node:node,timeout:3900,
          "auto-cookie":false,"auto-redirect":task.follow!==false,insecure:false,
          headers:{"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36","Accept-Language":"en-US,en;q=0.8"}
        };
        function complete(err,res,body){
          if(finishedTask)return;
          finishedTask=true;
          inFlight--;
          if(!ended)task.cb(err&&httpStatus(res)>=400?null:err,res||{},cleanBody(body));
          if(!ended)send();
        }
        try{$httpClient.get(opts,complete);}catch(e){complete(e,null,"");}
      })(queue.shift());
    }
    flushing=false;
  }
  function get(url,cb,follow){if(ended)return;queue.push({url:url,cb:cb,follow:follow});send();}
  function reliable(url,cb,follow){
    var tried=false;
    function once(err,r,body){
      if(err && !tried && timeLeft()>5600){
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
      var codes=[0,0],valid=[false,false],fail=["",""],titlesDone=0,cdnDone=false,cdnCode="";
      function netflixResult(){
        if(called)return;
        if(valid[0]||valid[1])return finish("available","影片页面正常");
        if(titlesDone!==2||!cdnDone)return;
        if(codes.indexOf(451)>=0)return finish("blocked");
        if(cdnCode)return finish("region",cdnCode);
        if(fail[0]&&fail[1])return finish(fail.indexOf("timeout")>=0?"timeout":"failed");
        finish("unknown","未能验证影片");
      }
      ["81280792","70143836"].forEach(function(film,n){
        reliable("https://www.netflix.com/title/"+film,function(err,r,b){
          codes[n]=httpStatus(r);fail[n]=statusError(err);
          var loc=header(r,"location");
          valid[n]=!err&&((codes[n]===200&&/netflix/i.test(b)&&b.indexOf(film)>=0)||
            ((codes[n]===301||codes[n]===302)&&/netflix\.com/i.test(loc)&&loc.indexOf(film)>=0));
          titlesDone++;netflixResult();
        },false);
      });
      // CDN can identify the country, but never confirms video playback.
      get("https://api.fast.com/netflix/speedtest/v2?https=true&token=YXNkZmFzZGxmbnNkYWZoYXNkZmhrYWxm&urlCount=5",function(err,r,b){
        if(!err&&httpStatus(r)===200){
          try{
            var json=JSON.parse(b);
            cdnCode=country(json.targets&&json.targets[0]&&json.targets[0].location&&json.targets[0].location.country);
          }catch(ignore){}
        }
        cdnDone=true;netflixResult();
      },false);
    } else if(id==="disney"){
      reliable("https://www.disneyplus.com/",function(err,r,b){
        if(err)return finish(statusError(err));
        var region=extract(b,/"countryCode"\s*:\s*"([A-Za-z]{2})"/i)||
          extract(b,/"region"\s*:\s*"([A-Za-z]{2})"/i);
        if(httpStatus(r)===451||restricted(b)||/\/(?:preview|unavailable)(?:\/|$)/i.test(header(r,"location")))
          return finish("blocked",region);
        var support=/"inSupportedLocation"\s*:\s*(true|false)/i.exec(b);
        if(support&&httpStatus(r)===200)return finish(support[1].toLowerCase()==="true"?"available":"blocked",region);
        finish(region?"region":knownResponse(r)?"reachable":"unknown",region||"");
      },true);
    } else if(id==="youtube"){
      reliable("https://www.youtube.com/premium?hl=en",function(err,r,b){
        if(err)return finish(statusError(err));
        if(httpStatus(r)===451||restricted(b))return finish("blocked");
        var countryCode=extract(b,/"GL"\s*:\s*"([A-Za-z]{2})"/)||
          extract(b,/"countryCode"\s*:\s*"([A-Za-z]{2})"/i)||
          extract(b,/id=["']country-code["'][^>]*>\s*([A-Za-z]{2})/i);
        var confirmed=/"isPremiumAvailable"\s*:\s*true/i.test(b)||
          /premium is available in your country/i.test(b)||
          (/"browseId"\s*:\s*"SPunlimited"/i.test(b)&&/youtube premium/i.test(b));
        if(httpStatus(r)===200&&confirmed)return finish("available",countryCode);
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
      reliable("https://www.tiktok.com/cdn-cgi/trace",function(err,r,b){
        if(!err && httpStatus(r)===451)return finish("blocked");
        var code=!err?traceRegion(b):"";
        if(code)return finish("region",code);
        reliable("https://www.tiktok.com/",function(e,resp,page){
          if(!e&&(httpStatus(resp)===451||restricted(page)))return finish("blocked");
          if(!e&&httpStatus(resp)===200)return finish("reachable","");
          finish(err&&e?(statusError(err)==="timeout"?"timeout":"failed"):"unknown");
        },true);
      },false);
    } else if(id==="chatgpt"){
      var parts=["未确认","未确认"],kind=["unknown","unknown"],remaining=2;
      function each(n,s,type){
        parts[n]=s;kind[n]=type;
        if(--remaining)return;
        var detail="网页："+parts[0]+"，iOS："+parts[1];
        if(kind.indexOf("blocked")>=0)return finish("blocked",detail);
        if(kind[0]==="reachable"&&kind[1]==="reachable")return finish("reachable",detail);
        if(kind[0]==="timeout"&&kind[1]==="timeout")return finish("timeout",detail);
        finish("unknown",detail);
      }
      reliable("https://api.openai.com/compliance/cookie_requirements",function(err,r,b){
        if(err)return each(0,statusError(err)==="timeout"?"超时":"连接异常",statusError(err));
        if(httpStatus(r)===451||restricted(b))return each(0,"地区受限","blocked");
        // HTTP 200 with cookie requirements is a reachable API, not a login/unlock guarantee.
        each(0,httpStatus(r)===200&&/^\s*\{/.test(b)?"接口可达":"未确认",
          httpStatus(r)===200&&/^\s*\{/.test(b)?"reachable":"unknown");
      },true);
      reliable("https://ios.chat.openai.com/",function(err,r,b){
        if(err)return each(1,statusError(err)==="timeout"?"超时":"连接异常",statusError(err));
        if(/disallowed isp|have been blocked|unsupported_country/i.test(b)||httpStatus(r)===451)
          return each(1,"地区受限","blocked");
        var signal=b.toLowerCase().indexOf("request is not allowed. please try again later.")!==-1;
        each(1,signal?"接口可达":"未确认",signal?"reachable":"unknown");
      },true);
    } else if(id==="gemini"){
      reliable("https://gemini.google.com/app",function(err,r,b){
        if(err)return finish(statusError(err));
        if(httpStatus(r)===451||restricted(b))return finish("blocked");
        var code=extract(b,/,2,1,200,"([A-Z]{3})"/);
        if(code)return finish("region",code);
        if(knownResponse(r))return finish("reachable","");
        finish("unknown",httpStatus(r)===429?"访问次数受限":"");
      },true);
    } else if(id==="claude"){
      var regionCode="",pageResult="",pending=2;
      function completeClaude(){
        if(--pending)return;
        if(pageResult==="blocked")return finish("blocked");
        if(regionCode)return finish("region",regionCode);
        if(pageResult==="reachable")return finish("reachable","");
        finish(pageResult==="timeout"?"timeout":"unknown");
      }
      reliable("https://claude.ai/cdn-cgi/trace",function(err,r,b){
        if(!err)regionCode=traceRegion(b);
        completeClaude();
      },false);
      reliable("https://claude.ai/",function(err,r,b){
        if(err)pageResult=statusError(err);
        else if(httpStatus(r)===451||restricted(b))pageResult="blocked";
        else pageResult=httpStatus(r)===200?"reachable":"unknown";
        completeClaude();
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
  function value(r,id){
    var names={available:"地区支持",partial:"部分内容",blocked:"地区受限",
      region:"无法确认",reachable:"无法确认",unknown:"无法确认",
      timeout:"检测超时",failed:"连接异常"};
    if(r.code==="available"&&id==="netflix")return "片库可访问";
    if(r.code==="available"&&(id==="bili_hk"||id==="bili_cn"))return "视频地址可获取";
    if(r.code==="reachable")return id==="chatgpt"?"接口可访问 · 网页、iOS":"无法确认 · 网站可访问";
    if(r.code==="region")return "无法确认"+(r.extra?" · 出口 "+r.extra:"");
    if(r.code==="available")return "地区支持"+(r.extra?" · "+r.extra:"");
    if(r.code==="unknown")return "无法确认"+(r.extra?" · "+r.extra:"");
    return (names[r.code]||"无法确认")+(r.extra?" · "+r.extra:"");
  }
  function output(){
    var ms=elapsed(),display=node.length>56?node.slice(0,29)+"…"+node.slice(-12):node;
    var lines=["节点："+display,"耗时："+(ms/1000).toFixed(1)+" 秒"];
    var last="";
    serviceList.forEach(function(s,i){
      if(s[2]!==last){last=s[2];lines.push("","【"+last+"】");}
      lines.push(s[1]+"："+value(result[i]||state("timeout"),s[0]));
    });
    var errors=0,answered=0;
    result.forEach(function(r){if(!r)return;if(r.code==="failed"||r.code==="timeout")errors++;
      else if(r.code!=="unknown")answered++;});
    if(errors>=5&&answered<=1)lines.push("","多项请求连接异常，请检查节点状态或稍后重试。");
    lines.push("","实际播放结果以对应应用为准。","检测器 v6.3.5");
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
      })(idx++);
    }
  }
  setTimeout(function(){done(output());},budget);
  pumpService();
})();