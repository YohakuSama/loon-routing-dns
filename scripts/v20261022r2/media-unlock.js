/* LoonKit · 节点解锁检测
 * 检测项与 KOP-XIAO streaming-ui-check 系列的七项实际任务一致。
 * 仅向所选节点发起请求；地区/公开接口检测不代表会员权益。
 */
(function () {
  "use strict";
  var args=(typeof $argument==="object"&&$argument)||{};
  var env=(typeof $environment==="object"&&$environment.params)||{};
  var info=env.nodeInfo&&typeof env.nodeInfo==="object"?env.nodeInfo:{};
  function str(v){return typeof v==="string"?v.trim():"";}
  var node=str(env.node)||str(info.name)||str(info.tag)||str(env.policyGroup)||str(args.target_policy)||"Proxy";
  if(node.length>220||/[\u0000-\u001f\u007f]/.test(node)){
    $done({title:"解锁检测",content:"节点名称无效"});return;
  }
  var items=[
    ["dazn","DAZN"],["discovery","Discovery+"],["paramount","Paramount+"],
    ["disney","Disney+"],["netflix","Netflix"],["chatgpt","ChatGPT"],
    ["youtube","YouTube Premium"]
  ];
  var results={},started=Date.now(),finished=false,completed=0;
  var queue=[],active=0,MAX_HTTP=6;
  function country(s){var x=String(s||"").trim().toUpperCase();return /^[A-Z]{2}$/.test(x)?x:"";}
  function status(r){return Number(r&&r.status)||0;}
  function header(r,key){var h=r&&r.headers||{};var names=Object.keys(h);
    for(var i=0;i<names.length;i++)if(names[i].toLowerCase()===key.toLowerCase())return String(h[names[i]]||"");
    return "";
  }
  function parseJSON(s){try{return JSON.parse(s);}catch(e){return null;}}
  function regionFrom(s,re){var m=String(s||"").match(re);return m?country(m[1]):"";}
  function geoBlocked(body){return /unsupported_country|forbidden[-_.]location|premium is not available in your country|not available in your (?:country|region)|not supported in your (?:country|region)/i.test(String(body||""));}
  function verdict(type,geo){return {type:type,geo:country(geo)};}
  function request(url,options,callback){
    if(finished)return;
    queue.push({url:url,options:options||{},callback:callback});dispatch();
  }
  function dispatch(){
    while(!finished&&active<MAX_HTTP&&queue.length){
      (function(task){
        active++;var done=false,o=task.options;
        var req={url:task.url,node:node,timeout:o.timeout||6000,
          "auto-redirect":o.redirect===true,"auto-cookie":false,insecure:false,
          headers:{"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36","Accept-Language":"en-US,en;q=0.8"}};
        var extra=o.headers||{};Object.keys(extra).forEach(function(k){req.headers[k]=extra[k];});
        if(o.method==="POST")req.body=o.body;
        function complete(err,res,data){
          if(done)return;done=true;active--;
          if(!finished)task.callback(status(res)?null:err,res||{},typeof data==="string"?data.slice(0,140000):"");
          if(!finished)dispatch();
        }
        try{
          var call=o.method==="POST"?$httpClient.post:$httpClient.get;
          if(typeof call!=="function")throw new Error("No HTTP method");
          call.call($httpClient,req,complete);
        }catch(e){complete(e,null,"");}
      })(queue.shift());
    }
  }
  function get(url,cb,opts){request(url,opts||{},cb);}
  function post(url,body,headers,cb){request(url,{method:"POST",body:body,headers:headers},cb);}
  function run(id,finish){
    if(id==="netflix"){
      // Like the reference: a title-page check, not a CDN or homepage guess.
      var film="81280792";
      get("https://www.netflix.com/title/"+film,function(err,r,body){
        var s=status(r);
        if(s===403||s===451||geoBlocked(body))return finish(verdict("locked"));
        if(s===404)return finish(verdict("partial"));
        if(s===200){
          var origin=header(r,"x-originating-url");
          return finish(verdict("unlocked",regionFrom(origin,/netflix\.com\/([a-z]{2})\/title\//i)));
        }
        finish(verdict("failed"));
      });
    } else if(id==="disney"){
      var payload=JSON.stringify({query:"mutation registerDevice($input: RegisterDeviceInput!) { registerDevice(registerDevice: $input) { grant { grantType assertion } } }",
        variables:{input:{applicationRuntime:"chrome",deviceFamily:"browser",deviceLanguage:"en",deviceProfile:"windows",
          attributes:{browserName:"chrome",browserVersion:"94.0.4606",manufacturer:"microsoft",
            operatingSystem:"windows",operatingSystemVersion:"10.0",osDeviceIds:[]}}}});
      post("https://disney.api.edge.bamgrid.com/graph/v1/device/graphql",payload,
        {"Authorization":"ZGlzbmV5JmJyb3dzZXImMS4wLjA.Cu56AgSfBTDag5NiRA81oLHkDZfu5L3CKadnefEAY84",
          "Content-Type":"application/json","User-Agent":"UA"},
        function(err,r,body){
          var obj=parseJSON(body),s=obj&&obj.extensions&&obj.extensions.sdk&&obj.extensions.sdk.session;
          if(status(r)===200&&s&&typeof s.inSupportedLocation==="boolean"){
            return finish(verdict(s.inSupportedLocation?"unlocked":"locked",s.location&&s.location.countryCode));
          }
          if(status(r)===451||geoBlocked(body))return finish(verdict("locked"));
          finish(verdict("failed"));
        });
    } else if(id==="youtube"){
      get("https://www.youtube.com/premium",function(err,r,body){
        var s=status(r);
        if(s===451||geoBlocked(body))return finish(verdict("locked"));
        if(s===200){
          // The reference treats a normal Premium page without the unavailable notice as region-supported.
          var geo=regionFrom(body,/"GL"\s*:\s*"([A-Za-z]{2})"/i)||
            regionFrom(body,/"countryCode"\s*:\s*"([A-Za-z]{2})"/i);
          return finish(verdict("unlocked",geo));
        }
        finish(verdict("failed"));
      });
    } else if(id==="dazn"){
      post("https://startup.core.indazn.com/misl/v5/Startup",
        JSON.stringify({LandingPageKey:"generic",Platform:"web",PlatformAttributes:{},
          Manufacturer:"",PromoCode:"",Version:"2"}),
        {"Content-Type":"application/json"},
        function(err,r,body){
          if(status(r)===451||geoBlocked(body))return finish(verdict("locked"));
          var j=parseJSON(body),geo=country(j&&j.GeolocatedCountry)||
            regionFrom(body,/"GeolocatedCountry"\s*:\s*"([A-Za-z]{2})"/i);
          if(status(r)===200&&geo)return finish(verdict("unlocked",geo));
          finish(verdict("failed"));
        });
    } else if(id==="paramount"){
      get("https://www.paramountplus.com/",function(err,r,body){
        var s=status(r);
        if(s===200)return finish(verdict("unlocked"));
        if(s===302||s===451||geoBlocked(body))return finish(verdict("locked"));
        finish(verdict("failed"));
      });
    } else if(id==="discovery"){
      get("https://us1-prod-direct.discoveryplus.com/token?deviceId=d1a4a5d25212400d1e6985984604d740&realm=go&shortlived=true",
        function(err,r,body){
          if(status(r)===451||geoBlocked(body))return finish(verdict("locked"));
          var j=parseJSON(body),token=j&&j.data&&j.data.attributes&&j.data.attributes.token;
          if(status(r)!==200||typeof token!=="string"||!token||token.length>4096)
            return finish(verdict("failed"));
          get("https://us1-prod-direct.discoveryplus.com/users/me",function(e,reply,data){
            if(status(reply)===451||geoBlocked(data))return finish(verdict("locked"));
            var o=parseJSON(data),loc=o&&o.data&&o.data.attributes&&o.data.attributes.currentLocationTerritory;
            if(status(reply)===200&&typeof loc==="string")
              return finish(verdict(loc.toLowerCase()==="us"?"unlocked":"locked",loc));
            finish(verdict("failed"));
          },{headers:{Cookie:"st="+encodeURIComponent(token)}});
        });
    } else if(id==="chatgpt"){
      // Keep the reference's redirect handling and country trace, not a Gemini test.
      get("https://chatgpt.com/",function(err,r,body){
        var s=status(r);
        if(s===451||geoBlocked(body)||/disallowed isp/i.test(body))return finish(verdict("locked"));
        // Root may redirect to sign-in (308), so inspect exit region instead of treating it as failure.
        get("https://chatgpt.com/cdn-cgi/trace",function(e,traceRes,data){
          var geo=status(traceRes)===200?regionFrom(data,/^loc=([A-Za-z]{2})\s*$/m):"";
          // Country list follows the reference script; no inference from a generic IP trace alone.
          var supported="AL DZ AD AO AG AR AM AU AT AZ BS BD BB BE BZ BJ BT BA BW BR BG BF CV CA CL CO KM CR HR CY DK DJ DM DO EC SV EE FJ FI FR GA GM GE DE GH GR GD GT GN GW GY HT HN HU IS IN ID IQ IE IL IT JM JP JO KZ KE KI KW KG LV LB LS LR LI LT LU MG MW MY MV ML MT MH MR MU MX MC MN ME MA MZ MM NA NR NP NL NZ NI NG MK NO OM PK PW PA PG PE PH PL PT QA RO RW KN LC VC WS SM ST SN RS SC SL SG SK SI SB ZA ES LK SR SE CH TH TG TO TT TN TR TV UG AE US UY VU ZM BO BN CG CZ VA FM MD PS KR TW TZ TL GB";
          if(geo)return finish(verdict((" "+supported+" ").indexOf(" "+geo+" ")>=0?"unlocked":"locked",geo));
          if(s===200&&/chatgpt|openai/i.test(body))return finish(verdict("unlocked"));
          if([301,302,307,308].indexOf(s)>=0&&/^https:\/\/(?:chatgpt\.com|auth\.openai\.com)\//i.test(header(r,"location")))
            return finish(verdict("unlocked"));
          finish(verdict("failed"));
        });
      });
    } else finish(verdict("failed"));
  }
  function show(v){
    if(!v)return "检测失败";
    if(v.type==="partial")return "仅自制剧";
    var name=v.type==="unlocked"?"已解锁":v.type==="locked"?"未解锁":"检测失败";
    return name+(v.geo?"（"+v.geo+"）":"");
  }
  function output(){
    var name=node.length>32?node.slice(0,24)+"…"+node.slice(-5):node;
    var rows=["节点："+name,"耗时："+((Date.now()-started)/1000).toFixed(1)+" 秒"];
    items.forEach(function(item){rows.push(item[1]+"："+show(results[item[0]]));});
    rows.push("","仅检测公开地区信号，不验证会员播放。","检测器 v6.4.4");
    return {title:"解锁检测",content:rows.join("\n")};
  }
  function done(){if(finished)return;finished=true;$done(output());}
  items.forEach(function(item){
    var once=false;
    try{run(item[0],function(v){
      if(once||finished)return;once=true;results[item[0]]=v;
      if(++completed===items.length)done();
    });}catch(e){if(!once&&!finished){once=true;results[item[0]]=verdict("failed");if(++completed===items.length)done();}}
  });
  setTimeout(done,17500);
})();