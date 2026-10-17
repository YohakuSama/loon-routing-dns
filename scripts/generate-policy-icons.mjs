// Loon Routing DNS: self-hosted policy icon generator for test branch.
// Transparent 512x512 PNG; never modifies DNS, proxy rules or user settings.
import fs from "node:fs";
import path from "node:path";
import * as si from "simple-icons";
import sharp from "sharp";

const dir=path.resolve("icons");
fs.mkdirSync(dir,{recursive:true});
const entries=[
 ["Proxy",null,"#0878EA"],["Auto",null,"#08A7B6"],["Fallback",null,"#F08821"],
 ["AdBlock",null,"#F13738"],["Final",null,"#5943D1"],["AI",null,"#5A30CE"],
 ["Google","Google","#4285F4"],["Microsoft","Microsoft","#F35325"],
 ["Apple","Apple","#44484F"],["YouTube","YouTube","#F02B2F"],
 ["Netflix","Netflix","#E50914"],["Disney","Disney","#125AC4"],
 ["PrimeVideo","Prime Video","#168BF1"],["Spotify","Spotify","#1ED760"],
 ["TikTok","TikTok","#101318"],["Twitch","Twitch","#9146FF"],
 ["HBO","HBO","#101319"],["Abema",null,"#208AF4"],
 ["動畫瘋",null,"#151515"],["Dazn","DAZN","#111216"],
 ["BBC",null,"#111216"],["Bilibili","Bilibili","#087DEB"],
 ["Telegram","Telegram","#249DE3"],["Whatsapp","WhatsApp","#20C86A"],
 ["Instagram","Instagram","#C13584"],["Facebook","Facebook","#1877F2"],
 ["Twitter","X","#111216"],["Discord","Discord","#5865F2"],
 ["Line","LINE","#06C755"],["Reddit","Reddit","#FF4500"],
 ["Linkedin","LinkedIn","#0A66C2"],["Steam","Steam","#084A93"],
 ["Paypal","PayPal","#0B65D8"]
];
const frame=(content)=>'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'+content+'</svg>';
const custom={
Proxy:frame('<g fill="#0878EA"><path d="M128 140a155 155 0 0 1 243-20l29-34v102H292l33-37A95 95 0 0 0 160 173z"/><path d="M384 369a155 155 0 0 1-243 20l-29 34V321h108l-33 37a95 95 0 0 0 165-22z"/><circle cx="133" cy="266" r="33"/><circle cx="379" cy="257" r="33"/></g>'),
Auto:frame('<g fill="none" stroke="#08A7B6" stroke-width="43" stroke-linecap="round"><path d="M95 322a168 168 0 0 1 322 0"/><path d="m255 294 103-120"/></g><circle cx="255" cy="293" r="26" fill="#08A7B6"/>'),
Fallback:frame('<g fill="none" stroke-width="44" stroke-linecap="round" stroke-linejoin="round"><path stroke="#F5A019" d="M110 233a145 145 0 0 1 251-91l33 36"/><path stroke="#F5A019" d="m343 174 55 7-6-57"/><path stroke="#F27925" d="M402 283a145 145 0 0 1-251 91l-33-36"/><path stroke="#F27925" d="m168 342-55-7 6 57"/></g>'),
AdBlock:frame('<path fill="#F13738" d="M256 62 415 120v121c0 120-66 185-159 220C163 426 97 361 97 241V120z"/><circle cx="256" cy="247" r="95" fill="none" stroke="#fff" stroke-width="29"/><path d="m192 181 128 132" fill="none" stroke="#fff" stroke-width="30" stroke-linecap="round"/>'),
Final:frame('<circle cx="256" cy="256" r="145" fill="none" stroke="#5943D1" stroke-width="47"/><circle cx="256" cy="256" r="57" fill="#5943D1"/>'),
AI:frame('<rect x="112" y="112" width="288" height="288" rx="29" fill="none" stroke="#6034C4" stroke-width="33"/><g fill="none" stroke="#6034C4" stroke-width="26" stroke-linecap="round"><path d="M164 75v37m92-37v37m92-37v37M164 400v37m92-37v37m92-37v37M75 164h37m-37 92h37m-37 92h37m288-184h37m-37 92h37m-37 92h37"/></g><text x="256" y="291" font-family="DejaVu Sans,Arial,sans-serif" font-weight="bold" font-size="116" text-anchor="middle" fill="#6034C4">AI</text>'),
Microsoft:frame('<rect x="106" y="106" width="139" height="139" fill="#F35325"/><rect x="267" y="106" width="139" height="139" fill="#81BC06"/><rect x="106" y="267" width="139" height="139" fill="#05A6F0"/><rect x="267" y="267" width="139" height="139" fill="#FFBA08"/>'),
Disney:frame('<path d="M93 165c69-66 232-64 294 1 85 90-53 219-188 209-42-3-61-33-37-60 26-29 97-36 127-62m-80-127v261" fill="none" stroke="#125AC4" stroke-width="32" stroke-linecap="round" stroke-linejoin="round"/><path d="M124 208c79 15 195-17 253-42" stroke="#125AC4" stroke-width="15" fill="none" stroke-linecap="round"/>'),
Linkedin:frame('<circle cx="125" cy="129" r="38" fill="#0A66C2"/><rect x="90" y="196" width="70" height="225" rx="6" fill="#0A66C2"/><path d="M198 196h69v32c22-28 48-41 80-41 65 0 93 38 93 117v117h-75V309c0-40-9-57-39-57-31 0-52 19-52 58v111h-76z" fill="#0A66C2"/>'),
Abema:frame('<rect x="94" y="141" width="325" height="244" rx="65" fill="#208AF4"/><path d="m170 116 37 45m117-45-37 45" stroke="#208AF4" stroke-width="25" stroke-linecap="round"/><path d="m224 218 103 53-103 52z" fill="#fff"/>'),
'動畫瘋':frame('<path d="M153 124 193 71l63 53 63-53 40 53" fill="none" stroke="#171717" stroke-width="36" stroke-linecap="round" stroke-linejoin="round"/><rect x="97" y="135" width="318" height="271" rx="95" fill="#171717"/><rect x="151" y="207" width="210" height="137" rx="50" fill="#fff"/><circle cx="211" cy="270" r="18" fill="#171717"/><circle cx="301" cy="270" r="18" fill="#171717"/><path d="M237 304q19 17 38 0" fill="none" stroke="#171717" stroke-width="14" stroke-linecap="round"/>'),
BBC:frame('<g fill="#121212"><rect x="50" y="150" width="123" height="212" rx="8"/><rect x="194" y="150" width="123" height="212" rx="8"/><rect x="338" y="150" width="123" height="212" rx="8"/></g><text x="111" y="297" fill="#fff" font-size="111" font-weight="bold" font-family="DejaVu Sans,Arial" text-anchor="middle">B</text><text x="255" y="297" fill="#fff" font-size="111" font-weight="bold" font-family="DejaVu Sans,Arial" text-anchor="middle">B</text><text x="399" y="297" fill="#fff" font-size="111" font-weight="bold" font-family="DejaVu Sans,Arial" text-anchor="middle">C</text>'),
PrimeVideo:frame('<rect x="73" y="139" width="366" height="237" rx="70" fill="#168BF1"/><path d="m223 191 121 66-121 66z" fill="#fff"/><path d="M111 405q148 78 284-8" stroke="#168BF1" stroke-width="18" fill="none" stroke-linecap="round"/><path d="m382 402 40-8-12 35" fill="#168BF1"/>'),
HBO:frame('<text x="255" y="320" font-size="160" text-anchor="middle" font-weight="900" font-family="DejaVu Sans,Arial,sans-serif" fill="#111318">HBO</text>'),
Dazn:frame('<rect x="101" y="101" width="310" height="310" rx="24" fill="none" stroke="#111216" stroke-width="33"/><text x="256" y="240" font-weight="900" font-size="98" text-anchor="middle" font-family="DejaVu Sans,Arial" fill="#111216">DA</text><text x="256" y="348" font-weight="900" font-size="98" text-anchor="middle" font-family="DejaVu Sans,Arial" fill="#111216">ZN</text>')
};
const normalize=v=>String(v).toLowerCase().replace(/[^a-z0-9]/g,"");
const iconList=Object.values(si).filter(v=>v&&typeof v==="object"&&typeof v.title==="string"&&typeof v.path==="string");
function logo(title,color){
 const ic=iconList.find(x=>normalize(x.title)===normalize(title));
 return ic?{svg:frame('<g transform="translate(76 76) scale(15)"><path d="'+ic.path+'" fill="'+color+'"/></g>'),source:ic.title}:null;
}
function fallback(name,color){
 const word=name==="Linkedin"?"in":name==="Twitter"?"X":name==="Whatsapp"?"WA":name.slice(0,2).toUpperCase();
 return frame('<text x="256" y="306" text-anchor="middle" font-family="DejaVu Sans,Arial,sans-serif" font-weight="bold" font-size="'+(word.length>2?125:170)+'" fill="'+color+'">'+word+'</text>');
}
const report=[];
for(const [name,brand,color] of entries){
 const found=brand?logo(brand,color):null;
 const artwork=custom[name]||found?.svg||fallback(name,color);
 const source=custom[name]?"custom project mark":found?("Simple Icons: "+found.source):"lettermark fallback";
 const fileName=(name==="動畫瘋"?"AnimeCrazy":name)+".png";
 await sharp(Buffer.from(artwork)).png({compressionLevel:9}).toFile(path.join(dir,fileName));
 report.push({name,file:fileName,source});
}
if(report.length!==33||fs.readdirSync(dir).filter(v=>v.endsWith(".png")).length!==33)throw Error("Expected 33 icons");
fs.writeFileSync(path.join(dir,"ICON_SOURCE_REPORT.json"),JSON.stringify(report,null,2)+"\n");
fs.writeFileSync(path.join(dir,"README.md"),
"# Loon Routing DNS pretest icons\n\n33 self-hosted flat transparent 512x512 PNG files. These are **test vector reconstructions** inspired by the approved palette and symbols; they are not byte-identical to the original generated review PNG assets. Some brand vector paths use Simple Icons (CC0), subject to their respective trademarks. No external icon hosting is needed at runtime.\n\nSee ICON_SOURCE_REPORT.json for attribution and any textual fallbacks.\n");
console.log(JSON.stringify({generated:report.length,missing:report.filter(x=>x.source==="lettermark fallback")}));
