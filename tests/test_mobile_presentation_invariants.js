"use strict";
const fs=require("node:fs"),assert=require("node:assert/strict");
function read(p){return fs.readFileSync(p,"utf8");}
function strip(s,start,end){
  const a=s.indexOf(start),b=s.indexOf(end,a+start.length);
  assert(a>=0&&b>a,"presentation boundary exists");
  return s.slice(0,a)+"<DISPLAY>"+s.slice(b);
}
const n0=read("scripts/v20261021r3/node-intelligence.js");
const n1=read("scripts/v20261022r10/node-intelligence.js");
assert.equal(strip(n0,"  function show(item,direct) {","  function done(msg){"),
  strip(n1,"  function show(item,direct) {","  function done(msg){"),"Node data logic must be unchanged");
const w0=read("scripts/v20261022r9/network-diagnostics.js");
const w1=read("scripts/v20261022r10/network-diagnostics.js").replaceAll("v6.5.2","v6.5.1");
assert.equal(strip(w0,"  // Loon generic script dialogs render title/content reliably; do not use HTML.","  function manual() {"),
  strip(w1,"  // Loon generic script dialogs render title/content reliably; do not use HTML.","  function manual() {"),
  "Network request, DNS and automatic monitor must be unchanged");
const u0=read("scripts/v20261022r9/media-unlock.js");
const u1=read("scripts/v20261022r10/media-unlock.js");
assert.equal(strip(u0,"  function output(){","  function done(){"),
  strip(u1,"  function output(){","  function done(){"),"Seven platform probe logic must be unchanged");
for(const source of [n1,w1,u1]){assert(!source.includes("htmlMessage"));assert(source.includes("v6.5.2"));}
const p=read("release/Network_Diagnostics.plugin");
assert.equal((p.match(/^generic then script\(/gm)||[]).length,3);
assert.equal((p.match(/^network-changed then script\(/gm)||[]).length,1);
console.log("Presentation-only regression: PASS");
