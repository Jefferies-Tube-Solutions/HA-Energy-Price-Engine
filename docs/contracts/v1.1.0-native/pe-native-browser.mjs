import {chromium} from '/workspace/HA-Energy-Price-Engine/tests/frontend/node_modules/playwright/index.mjs';
import {readFile, mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const root='/tmp/pe-v11-fresh';const token=await readFile(root+'/qa-access-token','utf8');
const out='/workspace/HA-Energy-Price-Engine/docs/images/v1.1.0';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const results=[];
try {
for(const language of ['en','da'])for(const width of [1440,820,390]){
 console.log('Checking',language,width);
 const page=await browser.newPage({viewport:{width,height:1100}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>console.log('page:',m.text()));
 await page.goto('http://127.0.0.1:8134/local/qa.html');
 await page.evaluate(async({token,language})=>{
  console.log('await module');await Promise.race([customElements.whenDefined('energy-price-engine-card'),new Promise((_,r)=>setTimeout(()=>r(Error('module timeout')),10000))]);console.log('module ready');
  const socket=new WebSocket('ws://127.0.0.1:8134/api/websocket');let next=1;const pending=new Map();
  await new Promise((resolve,reject)=>{socket.onmessage=e=>{const m=JSON.parse(e.data);console.log('ws',m.type,m.id);if(m.type==='auth_required')socket.send(JSON.stringify({type:'auth',access_token:token}));else if(m.type==='auth_ok')resolve();else if(m.type==='auth_invalid')reject(Error('auth rejected'));else if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.success?p?.resolve(m.result):p?.reject(Error(JSON.stringify(m.error)));}};});
  window.qaCalls=0;const callWS=m=>new Promise((resolve,reject)=>{window.qaCalls++;const id=next++;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,...m}));});
  console.log('authenticated');const states=Object.fromEntries((await callWS({type:'get_states'})).map(x=>[x.entity_id,x]));
  const resources=await callWS({type:'lovelace/resources'});window.qaResources=resources;
  const owned=resources.filter(x=>x.url.startsWith('/ha_energy_price_engine/'));
  if(owned.length!==1||!owned[0].url.endsWith('?v=1.1.0'))throw Error('wrong native resources');
  const hass={states,locale:{language,number_format:'language'},connection:socket,callWS};window.qaHass=hass;
  for(const unit of ['ore_kwh','dkk_kwh']){const c=document.createElement('energy-price-engine-card');c.setConfig({site_id:'qa_0',unit});document.querySelector('main').append(c);c.hass=hass;}
  window.qaSocket=socket;
 },{token,language});
 const cards=page.locator('energy-price-engine-card');await cards.nth(1).locator('.chart').first().waitFor();
 assert.equal(await cards.count(),2);assert.equal(await cards.nth(0).locator('[data-chart="final"] rect.bar').count(),192);
 assert.equal(await cards.nth(1).locator('[data-chart="final"] rect.bar').count(),192);
 const calls=await page.evaluate(()=>window.qaCalls);
 await page.evaluate(()=>{const c=document.querySelector('energy-price-engine-card');c.setConfig({site_id:'qa_0',unit:'dkk_kwh'});});
 assert.equal(await page.evaluate(()=>window.qaCalls),calls);
 await page.evaluate(()=>document.querySelector('energy-price-engine-card').setConfig({site_id:'qa_0',unit:'ore_kwh'}));
 assert.equal(await page.evaluate(()=>window.qaCalls),calls);
 assert.deepEqual(errors,[]);
 await page.screenshot({path:`${out}/native-${language}-${width}.png`,fullPage:true});
 results.push({language,width,cards:2,quarters_per_card:192,unit_change_provider_reads:0,errors});
 await page.evaluate(()=>window.qaSocket.close());await page.close();
}
await writeFile('/tmp/pe-native-browser-result.json',JSON.stringify(results,null,2));
console.log('Native authenticated card acceptance passed:',results.length,'scenarios');
}finally{await browser.close();}
