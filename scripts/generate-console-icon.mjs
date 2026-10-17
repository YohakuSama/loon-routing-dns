// Re-render the approved editable Console SVG, avoiding outdated replacement graphics.
import sharp from "sharp";
import fs from "node:fs";
const master="icons/source/Console.svg";
if(!fs.existsSync(master)) throw Error("Missing SVG master: "+master);
fs.mkdirSync("icons",{recursive:true});
await sharp(fs.readFileSync(master)).resize(512,512).png({compressionLevel:9}).toFile("icons/Console.png");
const metadata=await sharp("icons/Console.png").metadata();
if(metadata.width!==512||metadata.height!==512||metadata.channels!==4) throw Error("Invalid Console icon");
console.log("Rendered original Console SVG:",metadata.width,metadata.height);
