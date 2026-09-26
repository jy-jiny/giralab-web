/** Public bundle smoke test. Only static site traffic leaves this process. */
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {createServer} from 'node:http';
import {once} from 'node:events';
import path from 'node:path';
const require=createRequire(path.join(process.env.GIRALAB_BROWSER_TOOLS||process.cwd(),'package.json'));
const {chromium,expect}=require('playwright/test');
const source=JSON.parse(await readFile(new URL('./hearts-fixture.json',import.meta.url),'utf8'));
const site=path.resolve('site'), errors=[], unknown=[];
let server,browser;
try {
 let base=process.argv[2];
 if(!base){
  server=createServer(async(req,res)=>{
   try{const file=path.resolve(site,'.'+new URL(req.url,'http://localhost').pathname.replace(/\/$/,'/index.html'));assert(file.startsWith(site+path.sep));
    const type={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.ogg':'audio/ogg'}[path.extname(file)]||'application/octet-stream';
    res.writeHead(200,{'content-type':type});res.end(await readFile(file));
   }catch{res.writeHead(404);res.end();}
  });server.listen(0,'127.0.0.1');await once(server,'listening');base=`http://127.0.0.1:${server.address().port}/`;
 }
 const origin=new URL(base).origin;
 browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
 let starts=0,current=null,finished=false;
 const fresh=value=>JSON.parse(JSON.stringify(value),(key,v)=>typeof v==='number'&&v>1e12?v+Date.now()-source.now:v);
 const balance=()=>starts===0?fresh(source.initial['/api/runs'].hearts):fresh((starts===1?source.first:source.second).hearts);
 await context.route('**/*',async route=>{
  const req=route.request(),url=new URL(req.url());
  if(url.origin===origin)return route.continue();
  const prefix=['https://tqqgnrfklhmxwsphjera.supabase.co/functions/v1/giralab-game/api/','https://giralab-auth.netlify.app/api/'].find(x=>url.href.startsWith(x));
  if(!prefix)return route.abort('blockedbyclient');
  const api='/api/'+url.href.slice(prefix.length),body=req.postDataJSON();
  const headers={'access-control-allow-origin':origin,'access-control-allow-credentials':'true','access-control-allow-methods':'GET,POST,OPTIONS','access-control-allow-headers':'authorization,content-type,x-giralab-player-id,x-giralab-csrf'};
  if(req.method()==='OPTIONS')return route.fulfill({status:204,headers});
  let data;
  if(api==='/api/auth/cookie-check')data={ok:true};
  else if(api==='/api/account/status')data={enabled:true,providers:['google'],linked:true,player:source.player,deviceState:'active',devices:1};
  else if(api==='/api/account/backup')data=body;
  else if(api==='/api/runs'&&body){starts++;current=fresh(starts===1?source.first:source.second);finished=false;data=current;}
  else if(api==='/api/runs')data={run:current,hearts:balance()};
  else if(api.startsWith('/api/runs/')&&api.endsWith('/commands')){current=fresh(starts===1?source.playing:source.secondPlaying);data=current;}
  else if(api.startsWith('/api/runs/')){if(finished)current=fresh(source.finished);data=current;}
  else if(source.initial[api])data=fresh(source.initial[api]);
  else {unknown.push(api);return route.abort('blockedbyclient');}
  return route.fulfill({status:200,headers,contentType:'application/json',body:JSON.stringify(data)});
 });
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(base);
 await page.getByRole('button',{name:'햄버거 테마 선택',exact:true}).click();
 await expect(page.getByTestId('heart-status')).toContainText('5 / 5');
 await expect(page.getByRole('button',{name:/연습/})).toHaveCount(0);
 await page.getByRole('button',{name:'게임 시작',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('[data-game-status]')?.dataset.gameStatus==='playing');
 assert.equal(starts,1);
 finished=true;await page.evaluate(()=>window.dispatchEvent(new Event('online')));
 const result=page.getByRole('dialog',{name:'이번 판의 기록'});await expect(result).toBeVisible();
 await expect(result.getByText('점수 변화',{exact:true})).toHaveCount(0);
 for(const width of [320,360,390]){
  await page.setViewportSize({width,height:640});
  const boxes=await Promise.all(['결과 공유','한 판 더 · ♥ 1','메인으로'].map(name=>result.getByRole('button',{name,exact:true}).boundingBox()));
  assert(boxes.every(x=>x&&x.x>=0&&x.x+x.width<=width&&x.height>=44));
  assert(Math.max(...boxes.map(x=>x.y))-Math.min(...boxes.map(x=>x.y))<2,'One footer row');
 }
 await result.getByRole('button',{name:'한 판 더 · ♥ 1',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('[data-game-status]')?.dataset.gameStatus==='playing');
 assert.equal(starts,2);assert.equal(balance().available,3);
 assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);
 console.log(JSON.stringify({passed:true,site:base,heartStart:true,paidReplay:true,resultChart:false,footerWidths:[320,360,390],productionApiRequests:0}));
}finally{await browser?.close();server?.close();}
