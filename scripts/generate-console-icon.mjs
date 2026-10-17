// Generate a simple 512px project-owned Console icon. No remote image dependencies.
import sharp from "sharp";
import fs from "node:fs";
const svg=String.raw`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<g fill="none" stroke-linecap="round" stroke-linejoin="round">
  <rect x="69" y="95" width="374" height="315" rx="43" stroke="#0A77DF" stroke-width="35"/>
  <path d="M87 168h338" stroke="#0A77DF" stroke-width="25"/>
  <circle cx="125" cy="132" r="11" fill="#0A77DF" stroke="none"/>
  <circle cx="163" cy="132" r="11" fill="#12B8C5" stroke="none"/>
  <path d="M117 335a111 111 0 0 1 185-114" stroke="#0A77DF" stroke-width="30"/>
  <path d="m187 307 58-61" stroke="#12B8C5" stroke-width="27"/>
  <circle cx="185" cy="309" r="17" fill="#0A77DF" stroke="none"/>
  <path d="M332 235h74M332 290h74M332 345h74" stroke="#0A77DF" stroke-width="16"/>
  <circle cx="372" cy="235" r="17" fill="#0A77DF" stroke="none"/>
  <circle cx="358" cy="290" r="17" fill="#12B8C5" stroke="none"/>
  <circle cx="386" cy="345" r="17" fill="#0A77DF" stroke="none"/>
</g></svg>`;
fs.mkdirSync("icons",{recursive:true});
await sharp(Buffer.from(svg)).png({compressionLevel:9}).toFile("icons/Console.png");
const meta=await sharp("icons/Console.png").metadata();
if(meta.width!==512||meta.height!==512||meta.channels!==4)throw Error("Not a transparent 512x512 PNG");
console.log("Console icon generated and verified",meta.width,meta.height,meta.channels);
