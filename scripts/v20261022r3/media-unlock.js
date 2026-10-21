/*
 * LoonKit · 节点解锁查询
 * 检测项目、接口响应与状态分支参考 KOP-XIAO streaming-ui-check.js 改编版本。
 * 原项目：https://github.com/KOP-XIAO/QuantumultX
 */
(function () {
  "use strict";
  var args=typeof $argument==="object"&&$argument||{};
  var env=typeof $environment==="object"&&$environment.params||{};
  var info=env.nodeInfo&&typeof env.nodeInfo==="object"?env.nodeInfo:{};
  function string(v){return typeof v==="string"?v.trim():"";}
  var node=string(env.node)||string(info.name)||string(info.tag)||string(env.policyGroup)||string(args.target_policy)||"Proxy";
  if(node.length>220||/[\u0000-\u001f\u007f]/.test(node)){
    $done({title:"节点解锁查询",content:"节点名称无效"});return;
  }
  var items=[
    ["dazn","DAZN"],["discovery","Discovery+"],["paramount","Paramount+"],
    ["disney","Disney+"],["netflix","Netflix"],["chatgpt","ChatGPT"],
    ["youtube","YouTube Premium"]
  ];
  var result={},closed=false,completeCount=0,active=0,queue=[],MAX_HTTP=7;
  function status(r){return Number(r&&r.status)||0;}
  function header(r,key){
    var h=r&&r.headers||{},keys=Object.keys(h);
    for(var i=0;i<keys.length;i++)if(keys[i].toLowerCase()===key.toLowerCase())return String(h[keys[i]]||"");
    return "";
  }
  function parse(s){try{return JSON.parse(s);}catch(e){return null;}}
  function region(s){var code=String(s||"").trim().toUpperCase();return /^[A-Z]{2}$/.test(code)?code:"";}
  function find(s,regex){var m=String(s||"").match(regex);return m?region(m[1]):"";}
  function verdict(state,geo){return {state:state,geo:region(geo)};}
  function enqueue(url,options,callback){
    if(closed)return;
    queue.push({url:url,options:options||{},callback:callback});
    pump();
  }
  function pump(){
    while(!closed&&active<MAX_HTTP&&queue.length){
      (function(task){
        active++;var once=false,o=task.options;
        var request={
          url:task.url,node:node,timeout:o.timeout||5000,
          "auto-redirect":o.redirect!==false,"auto-cookie":false,insecure:false,
          headers:{"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/94.0.4606.61 Safari/537.36"}
        };
        var headers=o.headers||{};
        Object.keys(headers).forEach(function(k){request.headers[k]=headers[k];});
        if(o.method==="POST")request.body=o.body;
        function completed(err,response,body){
          if(once)return;once=true;active--;
          if(!closed)task.callback(err,response||{},typeof body==="string"?body.slice(0,200000):"");
          if(!closed)pump();
        }
        try{
          var method=o.method==="POST"?$httpClient.post:$httpClient.get;
          if(typeof method!=="function")throw new Error("No HTTP method");
          method.call($httpClient,request,completed);
        }catch(e){completed(e,null,"");}
      })(queue.shift());
    }
  }
  function get(url,callback,options){enqueue(url,options||{},callback);}
  function post(url,body,headers,callback){
    enqueue(url,{method:"POST",body:body,headers:headers},callback);
  }
  var openAICountries=[
    "T1","XX","AL","DZ","AD","AO","AG","AR","AM","AU","AT","AZ","BS","BD","BB","BE","BZ","BJ","BT","BA",
    "BW","BR","BG","BF","CV","CA","CL","CO","KM","CR","HR","CY","DK","DJ","DM","DO","EC","SV","EE","FJ",
    "FI","FR","GA","GM","GE","DE","GH","GR","GD","GT","GN","GW","GY","HT","HN","HU","IS","IN","ID","IQ",
    "IE","IL","IT","JM","JP","JO","KZ","KE","KI","KW","KG","LV","LB","LS","LR","LI","LT","LU","MG","MW",
    "MY","MV","ML","MT","MH","MR","MU","MX","MC","MN","ME","MA","MZ","MM","NA","NR","NP","NL","NZ","NI",
    "NE","NG","MK","NO","OM","PK","PW","PA","PG","PE","PH","PL","PT","QA","RO","RW","KN","LC","VC","WS",
    "SM","ST","SN","RS","SC","SL","SG","SK","SI","SB","ZA","ES","LK","SR","SE","CH","TH","TG","TO","TT",
    "TN","TR","TV","UG","AE","US","UY","VU","ZM","BO","BN","CG","CZ","VA","FM","MD","PS","KR","TW",
    "TZ","TL","GB"
  ];
  function test(id,finish){
    if(id==="dazn"){
      post("https://startup.core.indazn.com/misl/v5/Startup",
        JSON.stringify({LandingPageKey:"generic",Platform:"web",PlatformAttributes:{},Manufacturer:"",PromoCode:"",Version:"2"}),
        {"Content-Type":"application/json"},function(err,res,body){
          if(err||status(res)!==200)return finish(verdict("failed"));
          var data=parse(body),geo=region(data&&data.GeolocatedCountry)||
            find(body,/"GeolocatedCountry"\s*:\s*"([^"]+)"/);
          finish(verdict(geo?"supported":"unsupported",geo));
        });
    }else if(id==="discovery"){
      get("https://us1-prod-direct.discoveryplus.com/token?deviceId=d1a4a5d25212400d1e6985984604d740&realm=go&shortlived=true",
        function(err,res,body){
          if(err||status(res)!==200)return finish(verdict("failed"));
          var data=parse(body),token=data&&data.data&&data.data.attributes&&data.data.attributes.token;
          if(typeof token!=="string"||!token||token.length>4096)return finish(verdict("failed"));
          get("https://us1-prod-direct.discoveryplus.com/users/me",function(error,response,detail){
            if(error||status(response)!==200)return finish(verdict("failed"));
            var account=parse(detail);
            if(!account||!account.data||!account.data.attributes)return finish(verdict("failed"));
            var location=account.data.attributes.currentLocationTerritory;
            finish(verdict(location==="us"?"supported":"unsupported"));
          },{headers:{"Cookie":"st="+token}});
        });
    }else if(id==="paramount"){
      get("https://www.paramountplus.com/",function(err,res){
        if(err)return finish(verdict("failed"));
        if(status(res)===200)return finish(verdict("supported"));
        if(status(res)===302)return finish(verdict("unsupported"));
        finish(verdict("failed"));
      },{redirect:false});
    }else if(id==="disney"){
      var payload=JSON.stringify({
        query:"mutation registerDevice($input: RegisterDeviceInput!) { registerDevice(registerDevice: $input) { grant { grantType assertion } } }",
        variables:{input:{applicationRuntime:"chrome",deviceFamily:"browser",deviceLanguage:"en",deviceProfile:"windows",
          attributes:{browserName:"chrome",browserVersion:"94.0.4606",manufacturer:"microsoft",
            model:null,operatingSystem:"windows",operatingSystemVersion:"10.0",osDeviceIds:[]}}}
      });
      post("https://disney.api.edge.bamgrid.com/graph/v1/device/graphql",payload,{
        "Authorization":"ZGlzbmV5JmJyb3dzZXImMS4wLjA.Cu56AgSfBTDag5NiRA81oLHkDZfu5L3CKadnefEAY84",
        "Content-Type":"application/json","Accept-Language":"en","User-Agent":"UA"
      },function(err,res,body){
        if(err||status(res)!==200)return finish(verdict("failed"));
        var j=parse(body),session=j&&j.extensions&&j.extensions.sdk&&j.extensions.sdk.session;
        if(!session)return finish(verdict("unsupported"));
        var geo=region(session.location&&session.location.countryCode);
        finish(verdict(session.inSupportedLocation===false?"coming":"supported",geo));
      });
    }else if(id==="netflix"){
      get("https://www.netflix.com/title/81280792",function(err,res){
        if(err)return finish(verdict("failed"));
        var s=status(res);
        if(s===403)return finish(verdict("unsupported"));
        if(s===404)return finish(verdict("originals"));
        if(s===200){
          var origin=header(res,"X-Originating-URL"),geo="";
          if(origin){
            var parts=origin.split("/");
            var part=parts.length>3?parts[3].split("-")[0].toUpperCase():"";
            geo=part==="TITLE"?"US":region(part);
          }
          return finish(verdict("full",geo));
        }
        finish(verdict("failed"));
      },{timeout:6000});
    }else if(id==="youtube"){
      get("https://www.youtube.com/premium",function(err,res,body){
        if(err||status(res)!==200)return finish(verdict("failed"));
        if(body.indexOf("Premium is not available in your country")!==-1)
          return finish(verdict("unsupported"));
        var geo=find(body,/"GL":"(.*?)"/);
        if(!geo)geo=body.indexOf("www.google.cn")!==-1?"CN":"US";
        finish(verdict("supported",geo));
      },{timeout:10000});
    }else if(id==="chatgpt"){
      get("https://chat.openai.com/",function(err,res){
        if(err)return finish(verdict("unsupported"));
        if(JSON.stringify(res).indexOf("text/plain")!==-1)
          return finish(verdict("unsupported"));
        get("https://chat.openai.com/cdn-cgi/trace",function(error,response,body){
          if(error)return finish(verdict("failed"));
          var m=body.match(/(?:^|\n)loc=([A-Za-z0-9]{2})(?:\r?\n|$)/);
          if(!m)return finish(verdict("failed"));
          var geo=m[1].toUpperCase();
          finish(verdict(openAICountries.indexOf(geo)!==-1?"supported":"unsupported",geo));
        });
      },{redirect:false});
    }else finish(verdict("failed"));
  }
  function flag(geo){
    if(!geo)return "未知地区";
    var c=geo==="UK"?"GB":geo;
    return String.fromCodePoint(127397+c.charCodeAt(0),127397+c.charCodeAt(1));
  }
  function present(v,id){
    if(!v)return "检测失败";
    if(v.state==="failed")return "检测失败";
    if(v.state==="unsupported")return "未支持";
    if(v.state==="originals")return "支持自制剧集";
    if(v.state==="full")return "完整支持 ⟦"+flag(v.geo)+"⟧";
    if(v.state==="coming")return "即将登陆 ⟦"+flag(v.geo)+"⟧";
    if(v.state==="supported")return "支持"+(v.geo?" ⟦"+flag(v.geo)+"⟧":"");
    return "检测失败";
  }
  function output(){
    var showNode=node.length>32?node.slice(0,24)+"…"+node.slice(-5):node;
    var lines=[];
    items.forEach(function(s){lines.push(s[1]+"："+present(result[s[0]],s[0]));});
    lines.push("","节点："+showNode,"检测器 v6.4.5");
    return {title:"节点解锁查询",content:lines.join("\n")};
  }
  function done(){if(closed)return;closed=true;$done(output());}
  items.forEach(function(it){
    var once=false;
    try{
      test(it[0],function(v){
        if(once||closed)return;once=true;result[it[0]]=v;
        if(++completeCount===items.length)done();
      });
    }catch(e){
      if(!once&&!closed){once=true;result[it[0]]=verdict("failed");if(++completeCount===items.length)done();}
    }
  });
  setTimeout(done,22000);
})();