/* LoonKit · 解锁检测（简化版）
 * 一项服务优先使用一个有效接口；不能确认时不把网页/CDN 响应冒充解锁。
 * 所有请求使用 Loon 节点菜单指定的节点，账号和付费权益不在检测范围内。
 */
(function () {
  "use strict";
  var a=typeof $argument==="object"&&$argument||{};
  var p=typeof $environment==="object"&&$environment.params||{};
  var info=p.nodeInfo&&typeof p.nodeInfo==="object"?p.nodeInfo:{};
  function text(v){return typeof v==="string"?v.trim():"";}
  var node=text(p.node)||text(info.name)||text(info.tag)||text(p.policyGroup)||text(a.target_policy)||"Proxy";
  var full=a.full_scan===true||a.full_scan==="true";
  var list=[
    ["netflix","Netflix"],["disney","Disney+"],["youtube","YouTube Premium"],
    ["spotify","Spotify"],["tiktok","TikTok"],["chatgpt","ChatGPT"],
    ["gemini","Gemini"],["claude","Claude"]
  ];
  if(full)list=list.concat([
    ["prime","Prime Video"],["apple","Apple 地区"],
    ["bili_hk","Bilibili 港澳台"],["bili_cn","Bilibili 大陆"],
    ["bbc","BBC iPlayer"],["abema","Abema"]
  ]);
  var start=Date.now(),limit=full?26000:18000,closed=false;
  var answers=new Array(list.length),tasks=[],active=0,next=0,completed=0;
  var MAX_HTTP=5;
  function verdict(code,region){return {code:code,region:region||""};}
  function elapsed(){return Date.now()-start;}
  function remaining(){return limit-elapsed();}
  function country(v){var s=String(v||"").trim().toUpperCase();return /^[A-Z]{2,3}$/.test(s)?s:"";}
  function json(s){try{return JSON.parse(s);}catch(e){return null;}}
  function status(r){return Number(r&&r.status)||0;}
  function head(r,key){var h=r&&r.headers||{},keys=Object.keys(h);for(var i=0;i<keys.length;i++)if(keys[i].toLowerCase()===key.toLowerCase())return String(h[keys[i]]||"");return "";}
  function regionOf(s,re){var m=String(s||"").match(re);return m?country(m[1]):"";}
  function restricted(s){return /unsupported_country|forbidden[-_.]location|not available in your (?:country|region)|not supported in your (?:country|region)|service is not available in (?:your|this) (?:country|region)/i.test(String(s||""));}
  function blocked(r,body){return status(r)===451||restricted(body);}
  function issue(err){return /timeout|timed out|time out/i.test(String(err&&err.message||err||""))?"timeout":"error";}
  function request(url,options,callback){
    if(closed)return;
    tasks.push({url:url,options:options||{},callback:callback});
    dispatch();
  }
  function dispatch(){
    while(!closed&&active<MAX_HTTP&&tasks.length){
      (function(task){
        active++;
        var finished=false,opt=task.options;
        var req={url:task.url,node:node,timeout:5500,"auto-cookie":false,
          "auto-redirect":opt.redirect!==false,insecure:false,
          headers:{"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36","Accept-Language":"en-US,en;q=0.8"}};
        var custom=opt.headers||{};
        Object.keys(custom).forEach(function(k){req.headers[k]=custom[k];});
        if(opt.method==="POST")req.body=opt.body;
        function answer(err,r,body){
          if(finished)return;
          finished=true;active--;
          // Some Loon versions return an err together with an actual HTTP response.
          if(!closed)task.callback(status(r)?null:err,r||{},typeof body==="string"?body.slice(0,160000):"");
          if(!closed)dispatch();
        }
        try{
          var fn=opt.method==="POST"?$httpClient.post:$httpClient.get;
          if(typeof fn!=="function")throw new Error("HTTP method unavailable");
          fn.call($httpClient,req,answer);
        }catch(e){answer(e,null,"");}
      })(tasks.shift());
    }
  }
  function get(url,callback,redirect){request(url,{redirect:redirect},callback);}
  function post(url,body,headers,callback){request(url,{method:"POST",body:body,headers:headers,redirect:false},callback);}
  function run(id,finish){
    if(id==="netflix"){
      var films=["81280792","70143836"],seen=0,good=false,bad=false,missing=0,region="";
      function titleOK(r,body,film){
        if(status(r)!==200)return false;
        var originating=head(r,"x-originating-url");
        return (/netflix/i.test(body)&&body.indexOf(film)>=0)||
          originating.indexOf("/title/"+film)>=0&&/netflix\.com/i.test(originating);
      }
      films.forEach(function(film){
        get("https://www.netflix.com/title/"+film,function(err,r,body){
          if(titleOK(r,body,film)){
            good=true;
            var from=head(r,"x-originating-url");
            region=region||regionOf(from,/netflix\.com\/([a-z]{2})\/title\//i);
          }
          if(blocked(r,body))bad=true;
          if(status(r)===404)missing++;
          if(++seen!==2)return;
          if(good)return finish(verdict("support",region));
          if(bad)return finish(verdict("block"));
          if(missing!==2)return finish(verdict(err?"failed":"unknown"));
          // Only report an Originals-only hint if the third title actually loads.
          get("https://www.netflix.com/title/80018499",function(e,r3,b3){
            finish(verdict(titleOK(r3,b3,"80018499")?"limited":"unknown"));
          },false);
        },false);
      });
    } else if(id==="disney"){
      var root="https://disney.api.edge.bamgrid.com/graph/v1/device/graphql";
      var auth="ZGlzbmV5JmJyb3dzZXImMS4wLjA.Cu56AgSfBTDag5NiRA81oLHkDZfu5L3CKadnefEAY84";
      var payload=JSON.stringify({
        query:"mutation registerDevice($input: RegisterDeviceInput!) { registerDevice(registerDevice: $input) { grant { grantType assertion } } }",
        variables:{input:{applicationRuntime:"chrome",deviceFamily:"browser",deviceLanguage:"en",deviceProfile:"windows",
          attributes:{browserName:"chrome",browserVersion:"94.0.4606",manufacturer:"microsoft",
            operatingSystem:"windows",operatingSystemVersion:"10.0",osDeviceIds:[]}}}
      });
      post(root,payload,{"Authorization":auth,"Content-Type":"application/json","User-Agent":"UA"},function(err,r,body){
        var obj=json(body),s=obj&&obj.extensions&&obj.extensions.sdk&&obj.extensions.sdk.session;
        var geo=country(s&&s.location&&s.location.countryCode);
        if(status(r)===200&&geo&&typeof s.inSupportedLocation==="boolean")
          return finish(verdict(s.inSupportedLocation?"support":"block",geo));
        if(blocked(r,body))return finish(verdict("block"));
        // A single site check is enough as fallback; avoid another token-exchange chain.
        get("https://www.disneyplus.com/",function(e,page,html){
          if(blocked(page,html))return finish(verdict("block"));
          var webGeo=regionOf(html,/"region"\s*:\s*"([A-Za-z]{2})"/i);
          finish(verdict(status(page)===200?"unknown":e?"failed":"unknown",webGeo));
        });
      });
    } else if(id==="youtube"){
      get("https://www.youtube.com/premium?hl=en",function(err,r,body){
        if(blocked(r,body)||/premium is not available in your country/i.test(body))return finish(verdict("block"));
        var geo=regionOf(body,/"GL"\s*:\s*"([A-Za-z]{2})"/i)||
          regionOf(body,/"countryCode"\s*:\s*"([A-Za-z]{2})"/i);
        var offer=/"isPremiumAvailable"\s*:\s*true/i.test(body)||
          (/youtube premium/i.test(body)&&/(try premium|individual plan|family plan|student plan|join premium|start trial|get premium)/i.test(body));
        // Recognizable Premium content + YouTube's country code is also a regional signal.
        if(status(r)===200&&(offer||geo&&/youtube premium/i.test(body)))return finish(verdict("support",geo));
        finish(verdict(err?"failed":"unknown",geo));
      });
    } else if(id==="spotify"){
      get("https://www.spotify.com/api/content/v1/country-selector?platform=web&format=json",function(err,r,body){
        if(blocked(r,body))return finish(verdict("block"));
        var obj=json(body);
        var geo=country(obj&&obj.countryCode)||
          regionOf(head(r,"location"),/spotify\.com\/([a-z]{2})(?:[-/]|$)/i);
        if(geo&&status(r)>=200&&status(r)<400)return finish(verdict("support",geo));
        finish(verdict(err?"failed":"unknown"));
      },false);
    } else if(id==="tiktok"||id==="claude"){
      var base=id==="tiktok"?"https://www.tiktok.com":"https://claude.ai";
      var page=null,edge="",count=0;
      function end(){
        if(++count!==2)return;
        if(page.code==="block")return finish(page);
        if(page.code==="support")return finish(verdict("support",edge));
        finish(verdict(page.code,edge));
      }
      get(base+"/",function(err,r,body){
        if(blocked(r,body))page=verdict("block");
        else if(status(r)===200&&new RegExp(id==="tiktok"?"tiktok|SIGI_STATE|webapp":"claude|anthropic","i").test(body)&&!/access denied|verify you are human/i.test(body))page=verdict("support");
        else page=verdict(err?"failed":"unknown");
        end();
      });
      get(base+"/cdn-cgi/trace",function(err,r,body){
        if(status(r)===200)edge=regionOf(body,/^loc=([A-Za-z]{2})\s*$/m);
        end();
      },false);
    } else if(id==="chatgpt"){
      get("https://chatgpt.com/",function(err,r,body){
        if(blocked(r,body)||/disallowed isp/i.test(body))return finish(verdict("block"));
        if(status(r)===200&&/chatgpt|openai/i.test(body))return finish(verdict("support"));
        var redirect=head(r,"location");
        if((status(r)===301||status(r)===302||status(r)===307||status(r)===308)&&
           /^https:\/\/(?:chatgpt\.com|auth\.openai\.com)\//i.test(redirect))
          return finish(verdict("support"));
        // Loon's OpenAI iOS endpoint sometimes intentionally rejects anonymous calls.
        get("https://ios.chat.openai.com/",function(e,ir,ib){
          if(blocked(ir,ib)||/disallowed isp/i.test(ib))return finish(verdict("block"));
          if(/request is not allowed\. please try again later\./i.test(ib))
            return finish(verdict("support"));
          finish(verdict(err&&e?"failed":"unknown"));
        },false);
      },false);
    } else if(id==="gemini"){
      get("https://gemini.google.com/",function(err,r,body){
        if(blocked(r,body))return finish(verdict("block"));
        var geo=regionOf(body,/,2,1,200,"([A-Z]{3})"/);
        if(status(r)===200&&/gemini|google/i.test(body))return finish(verdict("support",geo));
        // An API-key error confirms API reachability, NOT Gemini web access.
        get("https://generativelanguage.googleapis.com/v1beta/models",function(e,ar,ab){
          if(blocked(ar,ab))return finish(verdict("block"));
          finish(verdict(err&&e?"failed":"unknown"));
        },false);
      });
    } else if(id==="prime"){
      get("https://www.primevideo.com/",function(err,r,body){
        var geo=regionOf(body,/"currentTerritory"\s*:\s*"([A-Za-z]{2})"/i);
        if(blocked(r,body)||/"isServiceRestricted"\s*:\s*true/i.test(body))return finish(verdict("block",geo));
        if(geo&&/"isServiceRestricted"\s*:\s*false/i.test(body))return finish(verdict("support",geo));
        finish(verdict(err?"failed":"unknown",geo));
      });
    } else if(id==="apple"){
      get("https://gspe1-ssl.ls.apple.com/pep/gcc",function(err,r,body){
        var geo=country(String(body||"").trim());
        finish(verdict(status(r)===200&&geo.length===2?"region":err?"failed":"unknown",geo));
      });
    } else if(id==="bili_hk"||id==="bili_cn"){
      var q=id==="bili_hk"?
        "avid=18281381&cid=29892777&qn=0&type=&otype=json&ep_id=183799&fourk=1&fnver=0&fnval=16&module=bangumi":
        "avid=82846771&qn=0&type=&otype=json&ep_id=307247&fourk=1&fnver=0&fnval=16&module=bangumi";
      get("https://api.bilibili.com/pgc/player/web/playurl?"+q,function(err,r,body){
        var o=json(body)||{},stream=o.result||o.data||{};
        var playable=o.code===0&&((Array.isArray(stream.durl)&&stream.durl.length)||
          stream.dash&&Array.isArray(stream.dash.video)&&stream.dash.video.length);
        finish(verdict(playable?"support":o.code===-10403?"block":err?"failed":"unknown"));
      });
    } else if(id==="bbc"||id==="abema"){
      get(id==="bbc"?"https://www.bbc.co.uk/iplayer":"https://abema.tv/",function(err,r,body){
        if(blocked(r,body)||/bbc iplayer only works in the uk|only available in the uk|お住まいの地域では視聴できません|outside of japan/i.test(body))
          return finish(verdict("block"));
        finish(verdict(err?"failed":"unknown"));
      });
    } else finish(verdict("unknown"));
  }
  function label(v){
    if(!v)v=verdict("failed");
    var labels={support:"支持",block:"不支持",limited:"部分支持",unknown:"待确认",
      failed:"检测失败",region:"地区"};
    return (labels[v.code]||"待确认")+(country(v.region)?"（"+country(v.region)+"）":"");
  }
  function output(){
    var display=node.length>32?node.slice(0,24)+"…"+node.slice(-5):node;
    var lines=["节点："+display,"耗时："+(elapsed()/1000).toFixed(1)+" 秒"];
    list.forEach(function(item,i){lines.push(item[1]+"："+label(answers[i]));});
    lines.push("","支持指地区或公开服务检测通过，不代表已有会员或登录权限。","检测器 v6.4.3");
    return {title:"解锁检测",content:lines.join("\n")};
  }
  function complete(){if(closed)return;closed=true;$done(output());}
  if(node.length>220||/[\u0000-\u001f\u007f]/.test(node)){
    $done({title:"解锁检测",content:"节点名称无效"});return;
  }
  var i=0;
  list.forEach(function(item,index){
    var once=false;
    try{run(item[0],function(result){
      if(once||closed)return;once=true;answers[index]=result;
      completed++;if(completed===list.length)complete();
    });}catch(e){
      if(!once&&!closed){once=true;answers[index]=verdict("failed");completed++;}
    }
  });
  if(completed===list.length)complete();
  setTimeout(complete,limit);
})();