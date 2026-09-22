/** Built app account UI; every API request uses a disposable fixture. No real mail/accounts. */
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { once } from 'node:events';
import path from 'node:path';
const require=createRequire(process.env.GIRALAB_BROWSER_TOOLS ? path.join(process.env.GIRALAB_BROWSER_TOOLS,'package.json') : import.meta.url);
const {chromium,expect}=require('playwright/test');
const args=process.argv.slice(2),value=flag=>args.includes(flag)?args[args.indexOf(flag)+1]:null;
const root=path.resolve(value('--site')||'pages-dist');let server,browser;
let base=value('--url');
if(!base){
  server=createServer(async(req,res)=>{
    try{
      const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname.replace(/\/$/,'/index.html'));
      assert(file.startsWith(root+path.sep));
      const type={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.ogg':'audio/ogg'}[path.extname(file)]||'application/octet-stream';
      res.writeHead(200,{'content-type':type});res.end(await readFile(file));
    }catch{res.writeHead(404);res.end();}
  });server.listen(0,'127.0.0.1');await once(server,'listening');base=`http://127.0.0.1:${server.address().port}/`;
}
const owner={id:'00000000-0000-0000-0000-000000000501',nickname:'로그인검증'};
const errors=[],cases=[];
try{
  const systemChrome=process.env.GIRALAB_CHROMIUM || ['/usr/bin/google-chrome','/usr/bin/chromium'].find(existsSync);
  browser=await chromium.launch({headless:true,...(systemChrome?{executablePath:systemChrome}:{}),args:['--no-sandbox']});
  async function setup({fresh=false,enabled=true,loseDelete=false}={}){
    const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
    await context.addInitScript(({fresh})=>{
      if(!localStorage.getItem('fixture-init')){
        localStorage.setItem('fixture-init','1');localStorage.setItem('giralab-player-token-v2','A'.repeat(43));
        localStorage.setItem('burger-lab-volume','25');localStorage.setItem('burger-lab-music-volume','30');
        if(!fresh)localStorage.setItem('giralab-progress-v3',JSON.stringify({bestScore:2000,unlocked:['classic','cheese']}));
      }
      let callback;
      window.google={accounts:{id:{initialize(options){callback=options.callback;},renderButton(container){const button=document.createElement('button');button.textContent='테스트 Google 계정 선택';button.onclick=()=>callback({credential:'eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJmaXh0dXJlIn0.c2lnbmF0dXJl'});container.append(button);},cancel(){}}}};
    },{fresh});
    const state={player:fresh?null:owner,linked:false,deleted:false,progress:{bestScore:500,unlocked:['classic']},backup:{bestScore:9000,unlocked:['classic','cheese','green']},requests:new Map(),calls:[],lost:false};
    await context.route('**/*',async route=>{
      const req=route.request(),url=new URL(req.url());
      if(url.origin===new URL(base).origin && url.pathname.startsWith(new URL(base).pathname))return route.continue();
      if(url.href==='https://accounts.google.com/gsi/client')return route.fulfill({contentType:'text/javascript',body:'/* isolated Google credential fixture */'});
      const marker='/functions/v1/giralab-game/api/';
      if(url.hostname!=='tqqgnrfklhmxwsphjera.supabase.co'||!url.pathname.startsWith(marker))return route.abort('blockedbyclient');
      const endpoint=url.pathname.slice(marker.length),body=req.postDataJSON();state.calls.push({endpoint,body});
      const headers={'access-control-allow-origin':new URL(base).origin,'access-control-allow-headers':'authorization,content-type,x-giralab-player-id','access-control-allow-methods':'GET,POST,OPTIONS'};
      if(req.method()==='OPTIONS')return route.fulfill({status:204,headers});
      let data,status=200;
      if(endpoint==='player'){
        assert.equal(req.method(),'GET','Account management never registers a replacement guest');
        if(state.deleted){status=401;data={code:'ACCOUNT_DELETED',error:'삭제된 계정이에요.'};}else data={player:state.player};
      }else if(endpoint==='progress'){
        if(body){assert(!state.linked,'Linked private progress cannot write legacy ranking');state.progress={bestScore:Math.max(state.progress.bestScore,body.bestScore),unlocked:[...new Set([...state.progress.unlocked,...body.unlocked])]};}
        data=state.progress;
      }else if(endpoint==='leaderboard')data={entries:[],me:null};
      else if(endpoint==='account/status')data={enabled,providers:enabled?['google']:[],linked:state.linked,player:state.player,deviceState:state.deleted?'deleted':state.player?'active':'new',devices:state.linked?2:1};
      else if(endpoint==='account/backup'){
        state.backup={bestScore:Math.max(state.backup.bestScore,body.bestScore),unlocked:[...new Set([...state.backup.unlocked,...body.unlocked])]};data=state.backup;
      }else if(endpoint==='account/social-challenge'){
        assert(enabled);assert.equal(body.provider,'google');assert.match(body.nonce,/^[a-f0-9]{64}$/);state.requests.set(body.requestId,{action:body.action,nonce:body.nonce});data={requestId:body.requestId,expiresAt:new Date(Date.now()+600000).toISOString()};
      }else if(endpoint==='account/social-verify'){
        assert.equal(body.provider,'google');assert(body.idToken);const item=state.requests.get(body.requestId);assert(item);assert.equal(body.nonce,item.nonce);item.verified=true;data={ready:true,action:item.action,player:owner};
      }else if(endpoint==='account/guest-delete'){
        assert(state.player&&!state.linked);state.requests.set(body.requestId,{action:'delete',verified:true});data={ready:true,action:'delete',player:owner};
      }else if(endpoint==='account/confirm'){
        assert.equal(body.confirm,true);const item=state.requests.get(body.requestId);assert(item?.verified);
        if(!item.result){
          if(item.action==='delete'){state.player=null;state.deleted=true;state.linked=false;}
          else{state.player=owner;state.linked=true;}
          item.result={state:'complete',action:item.action,player:state.player,requestId:body.requestId,...(state.player?{progress:state.backup}:{})};
        }
        data=item.result;
        if(loseDelete&&item.action==='delete'&&!state.lost){state.lost=true;return route.abort('failed');}
      }else throw Error('Unexpected fixture endpoint: '+endpoint);
      return route.fulfill({status,headers,contentType:'application/json',body:JSON.stringify(data)});
    });
    const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(15000);
    return {context,page,state};
  }
  async function openAccount(page){await page.getByRole('button',{name:'옵션',exact:true}).click();await page.getByRole('button',{name:/계정 관리/}).click();await expect(page.locator('.account-panel')).toBeVisible();}
  async function prove(page){
    await page.getByRole('button',{name:'Google로 계속하기',exact:true}).click();
    await page.getByRole('button',{name:'테스트 Google 계정 선택',exact:true}).click();
    await expect(page.locator('.account-panel strong')).toHaveText(owner.nickname);
  }
  async function fit(page){for(const width of [320,390]){await page.setViewportSize({width,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Account UI fits phone');}}
  const linked=await setup();await linked.page.goto(base);await openAccount(linked.page);await prove(linked.page);await fit(linked.page);
  await linked.page.getByRole('button',{name:'현재 기록에 계정 연결',exact:true}).click();await expect(linked.page.locator('.home-version')).toBeVisible();
  assert.equal(linked.state.player.id,owner.id);assert(linked.state.backup.bestScore>=2000&&linked.state.backup.unlocked.includes('cheese'));
  await openAccount(linked.page);await expect(linked.page.locator('.account-panel')).toContainText('로그인 연결됨');cases.push('link preserves owner and progress');await linked.context.close();
  const recovered=await setup({fresh:true,loseDelete:true});await recovered.page.goto(base);
  await recovered.page.getByRole('button',{name:'이미 플레이했나요? 로그인으로 기록 복구 · 계정 관리',exact:true}).click();await prove(recovered.page);
  await recovered.page.getByRole('button',{name:'로그인으로 기록 복구',exact:true}).click();await expect(recovered.page.locator('.home-version')).toBeVisible();
  const restored=await recovered.page.evaluate(()=>Object.entries(localStorage).filter(([k])=>k.startsWith('giralab-progress-v4:')).map(([,v])=>JSON.parse(v)));
  assert(restored.some(p=>p.bestScore===9000&&p.unlocked.includes('green')));cases.push('fresh-device recovery keeps original UUID and private progress');
  await openAccount(recovered.page);await recovered.page.getByRole('button',{name:'계정과 기록 삭제',exact:true}).click();await prove(recovered.page);
  const confirm=recovered.page.getByRole('button',{name:'계정과 기록 삭제',exact:true});await expect(confirm).toBeDisabled();
  await recovered.page.getByRole('checkbox').check();await confirm.click();await expect(recovered.page.getByRole('alert')).toContainText('인터넷');
  const first=recovered.state.calls.filter(c=>c.endpoint==='account/confirm').at(-1).body.requestId;
  await recovered.page.reload();await recovered.page.getByRole('button',{name:'작업 이어서 확인',exact:true}).click();
  await expect(recovered.page.getByRole('heading',{name:'계정 삭제가 완료됐어요'})).toBeVisible();
  assert.equal(recovered.state.calls.filter(c=>c.endpoint==='account/confirm').at(-1).body.requestId,first);
  assert.equal(await recovered.page.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('giralab-progress-v4:')).length),0);
  assert.equal(await recovered.page.evaluate(()=>localStorage.getItem('burger-lab-volume')),'25');cases.push('lost delete reply survives reload, reuses request and preserves volume');await recovered.context.close();
  const guest=await setup({enabled:false});await guest.page.goto(base);await openAccount(guest.page);
  await expect(guest.page.getByRole('button',{name:'Google로 계속하기'})).toBeDisabled();await guest.page.getByRole('button',{name:'계정과 기록 삭제',exact:true}).click();
  await guest.page.getByRole('button',{name:'이 기기의 기록 삭제 준비'}).click();await guest.page.getByRole('checkbox').check();
  await guest.page.getByRole('button',{name:'계정과 기록 삭제',exact:true}).click();await expect(guest.page.getByRole('heading',{name:'계정 삭제가 완료됐어요'})).toBeVisible();cases.push('guest deletion works when social readiness is off');await guest.context.close();
  const external=await setup({fresh:true,enabled:false});await external.page.goto(new URL('delete-account.html',base).href);
  await expect(external.page.getByRole('heading',{name:'GiraLab 계정 삭제'})).toBeVisible();await expect(external.page.getByRole('button',{name:'Google로 계속하기'})).toBeDisabled();
  assert(!external.state.calls.some(c=>['player','progress'].includes(c.endpoint)));await fit(external.page);cases.push('external deletion page opens without game registration');await external.context.close();
  const reset=await setup({enabled:false});reset.state.deleted=true;reset.state.player=null;
  await reset.page.goto(base);await expect(reset.page.getByRole('heading',{name:'삭제된 계정이에요'})).toBeVisible();
  await expect(reset.page.getByRole('button',{name:'새 계정으로 시작',exact:true})).toBeEnabled();
  cases.push('server reset without local deletion journal opens new-account flow');await reset.context.close();
  assert.deepEqual(errors,[]);console.log(JSON.stringify({passed:true,cases,noProductionRequests:true}));
}finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}
