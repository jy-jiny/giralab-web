/** Built login/account UI; all HTTP and Google credentials use disposable fixtures. */
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { mkdir, readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { once } from 'node:events';
import path from 'node:path';
const require=createRequire(process.env.GIRALAB_BROWSER_TOOLS ? path.join(process.env.GIRALAB_BROWSER_TOOLS,'package.json') : import.meta.url);
const {chromium,expect}=require('playwright/test');
const args=process.argv.slice(2),value=flag=>args.includes(flag)?args[args.indexOf(flag)+1]:null;
const root=path.resolve(value('--site')||'pages-dist');let server,browser;
const screenshots=value('--out');
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
  async function setup({fresh=false,enabled=true,loseDelete=false,loseSignin=false,loseLogout=false,newGoogle=false,linked=true,ranking=false,reducedMotion='reduce'}={}){
    const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion});
    await context.addInitScript(({fresh,ranking})=>{
      if(!localStorage.getItem('fixture-init')){
        localStorage.setItem('fixture-init','1');localStorage.setItem('giralab-player-token-v2','A'.repeat(43));
        localStorage.setItem('burger-lab-volume','25');localStorage.setItem('burger-lab-music-volume','30');
        if(!fresh)localStorage.setItem('giralab-progress-v3',JSON.stringify({bestScore:ranking?205050:2000,unlocked:['classic','cheese']}));
      }
      let callback;
      window.google={accounts:{id:{initialize(options){callback=options.callback;},renderButton(container){localStorage.setItem('fixture-google-opens',String(Number(localStorage.getItem('fixture-google-opens')||0)+1));const button=document.createElement('button');button.textContent='테스트 Google 계정 선택';button.onclick=()=>callback({credential:'eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJmaXh0dXJlIn0.c2lnbmF0dXJl'});container.append(button);},cancel(){}}}};
    },{fresh,ranking});
    const state={player:fresh?null:owner,linked:!fresh&&linked,deleted:false,progress:{bestScore:newGoogle?0:500,unlocked:['classic']},backup:newGoogle?{bestScore:0,unlocked:['classic']}:{bestScore:9000,unlocked:['classic','cheese','green']},requests:new Map(),calls:[],lost:false,googlePlayer:newGoogle?null:owner};
    if(ranking){state.progress.bestScore=0;state.backup.bestScore=205050;}
    await context.route('**/*',async route=>{
      const req=route.request(),url=new URL(req.url());
      if(url.origin===new URL(base).origin && url.pathname.startsWith(new URL(base).pathname))return route.continue();
      if(url.href==='https://accounts.google.com/gsi/client')return route.fulfill({contentType:'text/javascript',body:'/* isolated Google credential fixture */'});
      const marker='/functions/v1/giralab-game/api/';
      if(url.hostname!=='tqqgnrfklhmxwsphjera.supabase.co'||!url.pathname.startsWith(marker))return route.abort('blockedbyclient');
      const endpoint=url.pathname.slice(marker.length),body=req.postDataJSON();
      const headers={'access-control-allow-origin':new URL(base).origin,'access-control-allow-headers':'authorization,content-type,x-giralab-player-id','access-control-allow-methods':'GET,POST,OPTIONS'};
      if(req.method()==='OPTIONS')return route.fulfill({status:204,headers});
      state.calls.push({endpoint,body,method:req.method()});
      let data,status=200;
      if(endpoint==='player'){
        assert.equal(req.method(),'GET','Account management never registers a replacement guest');
        if(state.deleted){status=401;data={code:'ACCOUNT_DELETED',error:'삭제된 계정이에요.'};}else data={player:state.player};
      }else if(endpoint==='progress'){
        if(body){
          if(state.linked){assert(ranking,'Linked private progress cannot write legacy ranking');assert.equal(req.headers()['x-giralab-player-id'],owner.id);assert.deepEqual(body.unlocked,[]);assert(body.bestScore>0&&body.bestScore<205050,'Only fresh gameplay, never recovered personal best, enters TOP 5');}
          state.progress={bestScore:Math.max(state.progress.bestScore,body.bestScore),unlocked:[...new Set([...state.progress.unlocked,...body.unlocked])]};
        }
        data=state.progress;
      }else if(endpoint==='leaderboard')data=ranking&&state.progress.bestScore>0?{entries:[{rank:1,nickname:owner.nickname,score:state.progress.bestScore,isMe:true}],me:{rank:1,nickname:owner.nickname,score:state.progress.bestScore},updatedAt:Date.now()}:{entries:[],me:null};
      else if(endpoint==='account/status')data={enabled,providers:enabled?['google']:[],linked:state.linked,player:state.player,deviceState:state.deleted?'deleted':state.player?'active':'new',devices:state.linked?2:1};
      else if(endpoint==='account/backup'){
        state.backup={bestScore:Math.max(state.backup.bestScore,body.bestScore),unlocked:[...new Set([...state.backup.unlocked,...body.unlocked])]};data=state.backup;
      }else if(endpoint==='account/social-challenge'){
        assert(enabled);assert.equal(body.provider,'google');assert.match(body.nonce,/^[a-f0-9]{64}$/);state.requests.set(body.requestId,{action:body.action,nonce:body.nonce});data={requestId:body.requestId,expiresAt:new Date(Date.now()+600000).toISOString()};
      }else if(endpoint==='account/social-verify'){
        assert.equal(body.provider,'google');assert(body.idToken);const item=state.requests.get(body.requestId);assert(item);assert.equal(body.nonce,item.nonce);item.verified=true;item.player=state.googlePlayer;data={ready:true,action:item.action,player:state.googlePlayer,needsNickname:item.action==='signin'&&!state.googlePlayer};
      }else if(endpoint==='account/guest-delete'){
        assert(state.player&&!state.linked);state.requests.set(body.requestId,{action:'delete',verified:true});data={ready:true,action:'delete',player:owner};
      }else if(endpoint==='account/confirm'){
        assert.equal(body.confirm,true);const item=state.requests.get(body.requestId);assert(item?.verified);
        if(!item.result){
          if(item.action==='delete'){state.player=null;state.deleted=true;state.linked=false;}
          else{
            if(item.action==='signin'&&!item.player){assert.equal(typeof body.nickname,'string');assert(body.nickname.trim());state.googlePlayer={id:'00000000-0000-0000-0000-000000000502',nickname:body.nickname};}
            state.player=item.player||state.googlePlayer||owner;state.linked=true;
          }
          item.nickname=body.nickname;
          item.result={state:'complete',action:item.action,player:state.player,requestId:body.requestId,...(state.player?{progress:state.backup}:{})};
        }
        if(item.action==='signin')assert.equal(body.nickname,item.nickname,'Confirmation retry preserves its exact nickname');
        data=item.result;
        if(loseDelete&&item.action==='delete'&&!state.lost){state.lost=true;return route.abort('failed');}
        if(loseSignin&&item.action==='signin'&&!state.lost){state.lost=true;return route.abort('failed');}
      }else if(endpoint==='account/logout'){
        assert.equal(body.expectedPlayerId,owner.id);
        let item=state.requests.get(body.requestId);
        if(!item){item={result:{state:'complete',action:'logout',player:null,requestId:body.requestId}};state.requests.set(body.requestId,item);state.player=null;state.linked=false;}
        data=item.result;
        if(loseLogout&&!state.lost){state.lost=true;return route.abort('failed');}
      }else throw Error('Unexpected fixture endpoint: '+endpoint);
      return route.fulfill({status,headers,contentType:'application/json',body:JSON.stringify(data)});
    });
    const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(15000);
    return {context,page,state};
  }
  async function openAccount(page){await page.getByRole('button',{name:'옵션',exact:true}).click();await page.getByRole('button',{name:/계정 관리/}).click();await expect(page.locator('.account-panel')).toBeVisible();}
  async function closeWithoutChangingContent(page,close){
    await page.evaluate(()=>{
      const frames=[];
      const sample=()=>{
        const dialog=document.querySelector('.game-dialog');
        if(dialog)frames.push({state:dialog.dataset.state,title:dialog.querySelector('[data-slot="dialog-title"]')?.textContent,
          description:dialog.querySelector('[data-slot="dialog-description"]')?.textContent,
          panelClass:[...dialog.classList].find(name=>/^(account|settings|book|help)-dialog$/.test(name)),
          account:!!dialog.querySelector('.account-panel'),settings:!!dialog.querySelector('.settings-content'),book:!!dialog.querySelector('.theme-book-panel')});
      };
      const observer=new MutationObserver(sample);observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true});
      sample();window.__panelCloseProbe={frames,observer};
    });
    await close();
    await expect(page.locator('.game-dialog')).toHaveCount(0);
    const frames=await page.evaluate(()=>{const probe=window.__panelCloseProbe;probe.observer.disconnect();delete window.__panelCloseProbe;return probe.frames;});
    assert(frames.some(frame=>frame.state==='closed'),'The normal-motion exit animation was observed');
    const content=({state,...frame})=>frame;
    for(const frame of frames)assert.deepEqual(content(frame),content(frames[0]),'Closing retains its own title, description, layout and panel until it disappears');
  }
  async function prove(page){
    await page.getByRole('button',{name:'Google로 계속하기',exact:true}).click();
    await page.getByRole('button',{name:'테스트 Google 계정 선택',exact:true}).click();
    await expect(page.locator('.account-panel strong')).toHaveText(owner.nickname);
  }
  async function googleLogin(page){
    await expect(page.locator('.login-screen')).toBeVisible();
    await expect(page.locator('#nickname')).toHaveCount(0);
    await page.getByRole('button',{name:'Google로 계속하기',exact:true}).click();
    await page.getByRole('button',{name:'테스트 Google 계정 선택',exact:true}).click();
  }
  async function fit(page){for(const width of [320,390]){await page.setViewportSize({width,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Account UI fits phone');}}
  async function accountFits(page,{provider=false}={}){
    for(const width of [320,390]){
      await page.setViewportSize({width,height:740});
      const bounds=await page.locator('.account-panel').evaluate(panel=>{
        const rect=element=>{const r=element.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};};
        const social=panel.querySelector('.account-social-actions');
        return {width:innerWidth,pageWidth:document.documentElement.scrollWidth,panel:rect(panel),buttons:[...panel.querySelectorAll('button')].map(rect),social:social?{buttons:[...social.querySelectorAll('button')].map(rect),hint:social.querySelector('.account-auth-hint')?rect(social.querySelector('.account-auth-hint')):null}:null};
      });
      assert(bounds.pageWidth<=bounds.width,'Account content never widens the mobile page');
      assert(bounds.panel.left>=0&&bounds.panel.right<=width,'Account panel fits the mobile viewport');
      for(const button of bounds.buttons){assert(button.left>=bounds.panel.left-1&&button.right<=bounds.panel.right+1,'Account buttons stay inside the panel');assert(button.height>=44,'Account actions retain a usable touch target');}
      if(provider){assert(bounds.social?.buttons.length,'Selected action has its provider button');assert(bounds.social.hint,'Selected action explains which account to use');for(const button of bounds.social.buttons)assert(bounds.social.hint.bottom<=button.top+1,'Provider explanation stays above the button, never beside or behind it');}
      if(screenshots){await mkdir(screenshots,{recursive:true});await page.screenshot({path:path.join(screenshots,`account-${provider?'recovery':'overview'}-${width}.png`),fullPage:true});}
    }
  }
  const overview=await setup();await overview.page.goto(base);await openAccount(overview.page);
  await expect(overview.page.locator('.account-overview')).toBeVisible();await expect(overview.page.locator('.account-profile-name')).toHaveText(owner.nickname);
  await expect(overview.page.locator('.account-social-actions')).toHaveCount(0);await expect(overview.page.locator('.account-operation')).toHaveCount(0);
  await accountFits(overview.page);
  for(const action of ['로그인으로 기록 복구','다른 기기 연결 해제','계정과 기록 삭제']){
    await overview.page.getByRole('button',{name:action,exact:true}).click();
    await expect(overview.page.locator('.account-operation').getByRole('heading',{name:action,exact:true})).toBeVisible();
    await expect(overview.page.locator('.account-overview')).toHaveCount(0);
    if(action==='로그인으로 기록 복구')await accountFits(overview.page,{provider:true});
    await overview.page.getByRole('button',{name:'계정 관리로 돌아가기',exact:true}).click();
    await expect(overview.page.locator('.account-overview')).toBeVisible();
  }
  assert(!overview.state.calls.some(c=>['account/social-challenge','account/social-verify','account/confirm','account/logout','account/guest-delete'].includes(c.endpoint)),'Opening or backing out of actions never starts an account mutation');
  cases.push('linked overview opens without a recovery form; action navigation is read-only and fits 320/390px');await overview.context.close();
  const closing=await setup({reducedMotion:'no-preference'});await closing.page.goto(base);
  await openAccount(closing.page);
  await closing.page.locator('.game-dialog').getByRole('button',{name:'옵션',exact:true}).click();
  await expect(closing.page.locator('.game-dialog [data-slot="dialog-title"]')).toHaveText('옵션');
  await closing.page.getByRole('button',{name:/계정 관리/}).click();
  await closeWithoutChangingContent(closing.page,()=>closing.page.getByRole('button',{name:'닫기',exact:true}).click());
  await expect(closing.page.locator('.home-version')).toBeVisible();
  await openAccount(closing.page);
  await closeWithoutChangingContent(closing.page,()=>closing.page.keyboard.press('Escape'));
  await openAccount(closing.page);
  await closeWithoutChangingContent(closing.page,()=>closing.page.mouse.click(5,5));
  for(const panel of ['게임 설명','레시피 도감']){
    await closing.page.getByRole('button',{name:'옵션',exact:true}).click();
    await closing.page.getByRole('button',{name:new RegExp(panel)}).click();
    await closeWithoutChangingContent(closing.page,()=>closing.page.getByRole('button',{name:'닫기',exact:true}).click());
  }
  assert(!closing.state.calls.some(c=>['account/social-challenge','account/social-verify','account/confirm','account/logout','account/guest-delete'].includes(c.endpoint)),'Closing panels never starts an account operation');
  cases.push('account X, Escape and backdrop close directly without intermediate content; back still opens options and help/book retain their exit content');
  await closing.page.getByRole('button',{name:'햄버거 테마 선택',exact:true}).click();
  await closing.page.getByRole('button',{name:'게임 시작',exact:true}).click();
  await expect(closing.page.locator('[data-game-status]')).toHaveAttribute('data-game-status','playing');
  await closing.page.getByRole('button',{name:'옵션',exact:true}).click();
  await expect(closing.page.locator('[data-game-status]')).toHaveAttribute('data-game-status','paused');
  await expect(closing.page.getByRole('button',{name:/계정 관리/})).toBeDisabled();
  await closeWithoutChangingContent(closing.page,()=>closing.page.getByRole('button',{name:'닫기',exact:true}).click());
  await expect(closing.page.locator('[data-game-status]')).toHaveAttribute('data-game-status','playing');
  await closing.page.getByRole('button',{name:'일시정지',exact:true}).click();
  await closing.page.getByRole('button',{name:'옵션',exact:true}).click();
  await closeWithoutChangingContent(closing.page,()=>closing.page.getByRole('button',{name:'닫기',exact:true}).click());
  await expect(closing.page.locator('[data-game-status]')).toHaveAttribute('data-game-status','paused');
  cases.push('closing options resumes only a game it paused; an already paused game remains paused and account changes stay disabled during play');
  await closing.context.close();
  const saved=await setup();await saved.page.goto(base);await expect(saved.page.locator('.home-version')).toBeVisible();
  await saved.page.reload();await expect(saved.page.locator('.home-version')).toBeVisible();
  assert.equal(await saved.page.evaluate(()=>localStorage.getItem('fixture-google-opens')),null);
  assert(!saved.state.calls.some(c=>c.endpoint==='account/social-challenge'));cases.push('saved linked installation enters automatically without Google UI');await saved.context.close();
  const ranked=await setup({ranking:true});
  try {
  await ranked.page.goto(base);await expect(ranked.page.locator('.home-version')).toBeVisible();
  assert(!ranked.state.calls.some(c=>c.endpoint==='progress'&&c.body),'Linked boot does not promote personal 205050 to legacy ranking');
  await ranked.page.getByRole('button',{name:'햄버거 테마 선택',exact:true}).click();
  await ranked.page.getByRole('button',{name:'게임 시작',exact:true}).click();
  await expect(ranked.page.locator('[data-game-status]')).toHaveAttribute('data-game-status','playing');
  const cells=await ranked.page.evaluate(()=>{
    const board=Array.from({length:9},()=>Array(6).fill(null));
    document.querySelectorAll('button[data-tile-id]').forEach(el=>{board[+el.dataset.row][+el.dataset.col]=el.dataset.ingredient;});
    const recipes=[['bun','patty','bun'],...['cheese','lettuce','bacon','patty'].map(x=>['bun','patty',x,'bun']),
      ['bun','patty','cheese','cheese','bun'],['bun','patty','bacon','cheese','bun'],
      ['bun','cheese','patty','cheese','bun'],['bun','lettuce','patty','lettuce','bun'],
      ['bun','bacon','patty','lettuce','bun'],['bun','bacon','patty','cheese','bun'],
      ['bun','lettuce','patty','cheese','bun'],['bun','cheese','patty','bacon','bun'],['bun','bacon','patty','bacon','bun']];
    for(const recipe of recipes){
      const visit=(row,col,path)=>{
        if(board[row]?.[col]!==recipe[path.length]||path.some(p=>p.row===row&&p.col===col))return null;
        const next=[...path,{row,col}];if(next.length===recipe.length)return next;
        for(let dr=-1;dr<=1;dr++)for(let dc=-1;dc<=1;dc++){if(!dr&&!dc)continue;const found=visit(row+dr,col+dc,next);if(found)return found;}
        return null;
      };
      for(let row=0;row<9;row++)for(let col=0;col<6;col++){const found=visit(row,col,[]);if(found)return found;}
    }
    return null;
  });
  assert(cells,'Visible playable board contains a recipe');
  for(const [index,cell] of cells.entries()){
    await ranked.page.locator(`button[data-row="${cell.row}"][data-col="${cell.col}"]`).focus();
    // The shared selector corrects drag corners within 110ms. Deliberate keyboard steps must exceed it.
    await ranked.page.keyboard.press('Space',{delay:140});
    await expect(ranked.page.locator('button[data-tile-id][aria-pressed="true"]')).toHaveCount(index+1);
  }
  await ranked.page.getByRole('button',{name:'완성',exact:true}).click();
  await expect.poll(async()=>Number((await ranked.page.locator('.score-main strong').innerText()).replaceAll(',',''))).toBeGreaterThan(0);
  await expect.poll(()=>ranked.state.progress.bestScore).toBeGreaterThan(0);
  const earned=Number((await ranked.page.locator('.score-main strong').innerText()).replaceAll(',',''));
  assert.equal(ranked.state.progress.bestScore,earned);assert(earned<205050);assert.equal(ranked.state.backup.bestScore,205050);
  const personal=await ranked.page.evaluate(()=>Object.entries(localStorage).filter(([k])=>k.startsWith('giralab-progress-v4:')).map(([,v])=>JSON.parse(v)));
  assert(personal.some(p=>p.bestScore===205050),'Fresh lower ranking never overwrites personal best');
  await ranked.page.reload();await expect(ranked.page.locator('.home-version')).toBeVisible();
  assert(ranked.state.calls.filter(c=>c.endpoint==='progress'&&c.body).every(c=>c.body.bestScore===earned),'Reload never submits a merged private score');
  cases.push('linked account with personal 205050 and rank 0 ranks fresh gameplay only; private best and reload remain isolated');await ranked.context.close();
  } catch(error) {
    console.error(JSON.stringify({rankingFixtureFailure:{calls:ranked.state.calls,rankBest:ranked.state.progress.bestScore,privateBest:ranked.state.backup.bestScore,errors,
      screen:await ranked.page.evaluate(()=>({status:document.querySelector('[data-game-status]')?.dataset.gameStatus,score:document.querySelector('.score-main strong')?.textContent,
        selected:[...document.querySelectorAll('button[data-tile-id][aria-pressed="true"]')].map(el=>({row:el.dataset.row,col:el.dataset.col,ingredient:el.dataset.ingredient})),
        pending:Object.fromEntries(Object.entries(localStorage).filter(([key])=>key.startsWith('giralab-web-ranking-v1:'))),text:document.body.innerText})).catch(()=>null)}}));
    throw error;
  }
  const cancelled=await setup({fresh:true,newGoogle:true});await cancelled.page.goto(base);await fit(cancelled.page);
  await expect(cancelled.page.locator('#nickname')).toHaveCount(0);
  await cancelled.page.getByRole('button',{name:'Google로 계속하기',exact:true}).click();
  await cancelled.page.getByRole('dialog').getByRole('button',{name:'취소',exact:true}).click();
  await expect(cancelled.page.locator('.login-screen')).toBeVisible();await expect(cancelled.page.locator('#nickname')).toHaveCount(0);
  assert(!cancelled.state.calls.some(c=>c.endpoint==='account/social-challenge'||c.endpoint==='account/confirm'||c.endpoint==='account/social-verify'||(c.endpoint==='player'&&c.method==='POST')));
  cases.push('cancelled Google selection consumes no server challenge and creates no anonymous nickname/player');await cancelled.context.close();
  const first=await setup({fresh:true,newGoogle:true,loseSignin:true});await first.page.goto(base);await googleLogin(first.page);
  await expect(first.page.locator('#nickname')).toBeVisible();assert.equal(first.state.player,null,'Google proof alone creates no player');
  await first.page.locator('#nickname').fill('처음로그인');await first.page.getByRole('button',{name:'이 이름으로 시작',exact:true}).click();
  await expect(first.page.getByRole('alert')).toBeVisible();
  const initial=first.state.calls.filter(c=>c.endpoint==='account/confirm').at(-1).body;
  await first.page.reload();
  await expect(first.page.locator('.home-version')).toBeVisible();
  assert.deepEqual(first.state.calls.filter(c=>c.endpoint==='account/confirm').at(-1).body,initial);
  assert.equal(first.state.player.nickname,'처음로그인');assert(!first.state.calls.some(c=>c.endpoint==='player'&&c.method==='POST'));
  cases.push('new Google identity asks nickname after proof; lost confirm reuses exact ID and nickname');await first.context.close();
  const recovered=await setup({fresh:true,loseDelete:true});await recovered.page.goto(base);
  await googleLogin(recovered.page);await expect(recovered.page.locator('.home-version')).toBeVisible();
  assert.equal(recovered.state.player.id,owner.id);assert(!recovered.state.calls.some(c=>c.endpoint==='account/confirm'&&c.body.nickname));
  const restored=await recovered.page.evaluate(()=>Object.entries(localStorage).filter(([k])=>k.startsWith('giralab-progress-v4:')).map(([,v])=>JSON.parse(v)));
  assert(restored.some(p=>p.bestScore===9000&&p.unlocked.includes('green')));cases.push('fresh-device recovery keeps original UUID and private progress');
  await openAccount(recovered.page);await recovered.page.getByRole('button',{name:'계정과 기록 삭제',exact:true}).click();await prove(recovered.page);
  const confirm=recovered.page.getByRole('button',{name:'계정과 기록 삭제',exact:true});await expect(confirm).toBeDisabled();
  await recovered.page.getByRole('checkbox').check();await confirm.click();await expect(recovered.page.getByRole('alert')).toContainText('인터넷');
  const deleteRequest=recovered.state.calls.filter(c=>c.endpoint==='account/confirm').at(-1).body.requestId;
  await recovered.page.reload();await recovered.page.getByRole('button',{name:'작업 이어서 확인',exact:true}).click();
  await expect(recovered.page.getByRole('heading',{name:'계정 삭제가 완료됐어요'})).toBeVisible();
  assert.equal(recovered.state.calls.filter(c=>c.endpoint==='account/confirm').at(-1).body.requestId,deleteRequest);
  assert.equal(await recovered.page.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('giralab-progress-v4:')).length),0);
  assert.equal(await recovered.page.evaluate(()=>localStorage.getItem('burger-lab-volume')),'25');cases.push('lost delete reply survives reload, reuses request and preserves volume');await recovered.context.close();
  const loggedOut=await setup({loseLogout:true});await loggedOut.page.goto(base);await openAccount(loggedOut.page);
  await loggedOut.page.getByRole('button',{name:'로그아웃',exact:true}).click();await loggedOut.page.getByRole('button',{name:'로그아웃',exact:true}).click();
  await expect(loggedOut.page.getByRole('alert')).toBeVisible();
  const logoutRequest=loggedOut.state.calls.filter(c=>c.endpoint==='account/logout').at(-1).body.requestId;
  await loggedOut.page.reload();
  await expect(loggedOut.page.locator('.login-screen')).toBeVisible();
  assert.equal(loggedOut.state.calls.filter(c=>c.endpoint==='account/logout').at(-1).body.requestId,logoutRequest);
  assert.equal(await loggedOut.page.evaluate(()=>localStorage.getItem('burger-lab-volume')),'25');
  assert.equal(await loggedOut.page.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('giralab-progress-v4:')).length),0);
  await googleLogin(loggedOut.page);await expect(loggedOut.page.locator('.home-version')).toBeVisible();assert.equal(loggedOut.state.player.id,owner.id);
  cases.push('logout response loss resumes safely and the same Google account restores its nickname');await loggedOut.context.close();
  const guest=await setup({enabled:false,linked:false});await guest.page.goto(new URL('delete-account.html',base).href);
  await guest.page.getByRole('button',{name:'이 기기의 기록 삭제 준비'}).click();await guest.page.getByRole('checkbox').check();
  await guest.page.getByRole('button',{name:'계정과 기록 삭제',exact:true}).click();await expect(guest.page.getByRole('heading',{name:'계정 삭제가 완료됐어요'})).toBeVisible();cases.push('guest deletion works when social readiness is off');await guest.context.close();
  const external=await setup({fresh:true,enabled:false});await external.page.goto(new URL('delete-account.html',base).href);
  await expect(external.page.getByRole('heading',{name:'GiraLab 계정 삭제'})).toBeVisible();await expect(external.page.getByRole('button',{name:'Google로 계속하기'})).toBeDisabled();
  assert(!external.state.calls.some(c=>['player','progress'].includes(c.endpoint)));await fit(external.page);cases.push('external deletion page opens without game registration');await external.context.close();
  const disabled=await setup({fresh:true,enabled:false});await disabled.page.goto(base);await expect(disabled.page.locator('.login-screen')).toBeVisible();
  await expect(disabled.page.getByRole('button',{name:'Google로 계속하기',exact:true})).toBeDisabled();await expect(disabled.page.locator('#nickname')).toHaveCount(0);
  cases.push('unconfigured Google stays at login instead of anonymous nickname fallback');await disabled.context.close();
  const reset=await setup({enabled:false});reset.state.deleted=true;reset.state.player=null;
  await reset.page.goto(base);await expect(reset.page.getByRole('heading',{name:'삭제된 계정이에요'})).toBeVisible();
  await expect(reset.page.getByRole('button',{name:'새 계정으로 시작',exact:true})).toBeEnabled();
  cases.push('server reset without local deletion journal opens new-account flow');await reset.context.close();
  assert.deepEqual(errors,[]);console.log(JSON.stringify({passed:true,cases,noProductionRequests:true}));
}finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}
