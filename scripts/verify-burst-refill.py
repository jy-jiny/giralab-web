from pathlib import Path as _DriverPath
_TEST_DRIVER = (_DriverPath(__file__).resolve().parents[1] / "scripts/browser-game-driver.js").read_text()
"""Real browser verification with isolated API fixtures; no production player writes."""
import argparse,json,os,shutil,subprocess,tempfile,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

VERSION='1.7.2'
PLAYER={'id':'22222222-2222-4222-8222-222222222204','nickname':'연출검증'}
ROWS=['LBBPPP','PALCPA','PLALPA','PLLLLC','LLPAAL','LPAALP','APCCLC','ALCPCL','PCPPPP']
VALUE={'L':.85,'B':.1,'P':.5,'A':.95,'C':.7}
TYPES={'L':'lettuce','B':'bun','P':'patty','A':'bacon','C':'cheese'}
IDS=['classic','cheese','green','bacon','double-patty','double','bacon-cheese','cheese-melt','garden-stack','smoky-green','bacon-first','green-cheese','cheese-bacon-stack','double-bacon','cheese-mad','meat-monster','green-monster','bacon-bomb','forbidden-seven']
HOOK="""window.__draws=[];const original=Math.random;Math.random=()=>window.__draws.length?window.__draws.shift():original();window.__gameTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__gameTools[t.name]=t}}});
// Deliberate frame sampling only. Real-time/lifecycle tests leave this flag false.
const originalPlay=Animation.prototype.play;Animation.prototype.play=function(){
 if(window.__freezeBurst && this.effect?.target?.matches('button[data-tile-id],.regeneration-ghost,.regeneration-wave')){this.pause();return;}
 return originalPlay.call(this);
};
"""
ANIMS="[...document.querySelectorAll('button[data-tile-id],.regeneration-ghost,.regeneration-wave')].flatMap(el=>el.getAnimations()).filter(a=>a.effect)"


def fixture(route):
 name=route.request.url.split('/api/')[-1].split('?')[0]
 if name=='account/status':
     route.fulfill(status=200,content_type='application/json',body=json.dumps({'enabled':False,'linked':True,'player':PLAYER,'deviceState':'active','devices':1}));return
 if name=='player':data={'player':PLAYER}
 elif name=='leaderboard':data={'entries':[],'me':None}
 elif name in ('progress','account/backup'):data={'unlocked':IDS,'bestScore':0}
 else:raise AssertionError('Unexpected API endpoint: '+name)
 if name in ('progress','account/backup') and route.request.method=='POST':data=route.request.post_data_json
 route.fulfill(status=200,content_type='application/json',body=json.dumps(data))


def verify(base,out):
 out.mkdir(parents=True,exist_ok=True)
 report={'version':VERSION,'network':'Isolated game API fixtures; no production writes','cases':[]}
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required'])
  cases=[(360,640,False,False),(390,844,False,False),(412,915,False,False),(390,844,True,False),(390,844,False,True)]
  for width,height,reduced,unsupported in cases:
   print('CHECK',width,height,'reduced',reduced,'unsupported',unsupported,flush=True)
   ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True,reduced_motion='reduce' if reduced else 'no-preference')
   ctx.add_init_script(_TEST_DRIVER);ctx.add_init_script('localStorage.clear();sessionStorage.clear();'+HOOK+('Element.prototype.animate=undefined;' if unsupported else ''))
   page=ctx.new_page();page.set_default_timeout(15000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/api/**',fixture)
   page.goto(base+'?burst-refill='+VERSION,wait_until='domcontentloaded')
   expect(page.locator('.home-version')).to_have_text('GiraLab · '+VERSION)
   page.locator('.home-version').click()
   game=lambda:page.evaluate('window.__gameTools.get_game_state.execute({})')
   def seed_start(first=False):
    # A fresh isolated document replaces the intentionally removed settings restart.
    if not first:
     page.reload(wait_until='domcontentloaded')
     expect(page.locator('.home-version')).to_have_text('GiraLab · '+VERSION)
     page.locator('.home-version').click()
    page.evaluate('(d)=>{window.__draws=d;window.__gameTools.start_game.execute({})}',[VALUE[c] for row in ROWS for c in row])
    assert game()['board']==[[TYPES[c] for c in row] for row in ROWS]
    expect(page.locator('button[data-tile-id]')).to_have_count(54)
   def trigger(freeze=False):
    return page.evaluate('''freeze=>{
     window.__freezeBurst=freeze;
     const original=Math.random;let n=0,seed=73;
     Math.random=()=>++n<=4?.99:((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
     window.__beforeIds=[...document.querySelectorAll('button[data-tile-id]')].map(el=>el.dataset.tileId);
     window.__begin=performance.now();
     try{return window.__gameTools.submit_ingredient_path.execute({cells:[{row:0,col:2},{row:0,col:3},{row:1,col:2},{row:0,col:1}]})}finally{Math.random=original}
    }''',freeze)
   seed_start(True);result=trigger(not unsupported);assert result['success'] and result['recipe']=='그린 버거' and result['score']==300,result
   suffix=f'{width}-'+('reduced' if reduced else 'no-api' if unsupported else 'motion')
   if unsupported:
    page.wait_for_function('!window.__gameTools.get_game_state.execute({}).regenerating')
    expect(page.locator('button[data-tile-id]:disabled')).to_have_count(0)
    report['cases'].append({'viewport':[width,height],'noAnimationAPI':True,'unlocked':True})
    assert not errors,errors;ctx.close();continue
   page.locator('.regeneration-scene').wait_for(state='attached')
   page.evaluate('window.__burstAnimations='+ANIMS+';window.__burstAnimations.forEach(a=>{a.pause();a.currentTime=0})')
   before=game();assert before['regenerating'],(suffix,before)
   expect(page.locator('.regeneration-notice')).to_have_count(0)
   expect(page.locator('.regeneration-ghost')).to_have_count(54)
   expect(page.locator('button[data-tile-id]:disabled')).to_have_count(54)
   assert page.evaluate("document.querySelector('.regeneration-scene').style.backdropFilter==='' ")
   assert page.evaluate("window.__beforeIds.length===54 && [...document.querySelectorAll('button[data-tile-id]')].every(el=>!window.__beforeIds.includes(el.dataset.tileId))")
   frames=[]
   for ms in ([0,90,159] if reduced else [0,85,190,320,470,585]):
    page.evaluate('(ms)=>window.__burstAnimations.forEach(a=>{a.pause();a.currentTime=ms})',ms)
    frame=page.evaluate('''()=>{
     const board=document.querySelector('.board').getBoundingClientRect();
     const visible=[...document.querySelectorAll('button[data-tile-id]')].filter(el=>{const r=el.getBoundingClientRect();return r.bottom>board.top&&r.top<board.bottom&&Number(getComputedStyle(el).opacity)>.03});
     return {incomingVisible:visible.length,ghostsVisible:[...document.querySelectorAll('.regeneration-ghost')].filter(el=>Number(getComputedStyle(el).opacity)>.03).length};
    }''')
    frames.append({'ms':ms,**frame})
    current=game()
    for key in ['score','combo','slow','danger','elapsed','board']:assert current[key]==before[key],(suffix,ms,key)
    page.screenshot(path=str(out/f'{suffix}-{ms:03}.png'))
   if not reduced:
    assert frames[0]['incomingVisible']==0 and frames[0]['ghostsVisible']==54,frames
    assert frames[2]['incomingVisible']>0,'Incoming stream must overlap the end of the burst'
    assert 0<frames[3]['incomingVisible']<54,frames
    assert frames[-1]['incomingVisible']==54,frames
   else:assert frames[-1]['incomingVisible']==54
   completion=page.evaluate('''async ()=>{
    window.__freezeBurst=false;
    const start=performance.now();window.__burstAnimations.forEach(a=>a.finish());
    await Promise.resolve();await new Promise(requestAnimationFrame);await new Promise(requestAnimationFrame);
    return {ms:performance.now()-start,game:window.__gameTools.get_game_state.execute({}),disabled:document.querySelectorAll('button[data-tile-id]:disabled').length,scene:!!document.querySelector('.regeneration-scene')};
   }''')
   assert not completion['game']['regenerating'] and not completion['scene'] and completion['disabled']==0,completion
   assert completion['ms']<200,completion
   assert completion['game']['score']==300 and completion['game']['combo']==1
   page.wait_for_timeout(100);assert game()['elapsed']>before['elapsed']
   if not reduced:
    seed_start();trigger()
    page.wait_for_function('!window.__gameTools.get_game_state.execute({}).regenerating')
    realtime=page.evaluate('performance.now()-window.__begin');assert 450<realtime<1000,realtime
    assert game()['score']==300
    seed_start();trigger();page.locator('.regeneration-scene').wait_for(state='attached')
    page.get_by_role('button',name='일시정지',exact=True).click()
    paused=game();assert paused['status']=='paused'
    page.wait_for_function(ANIMS+".every(a=>a.playState==='paused' && !a.pending)")
    positions=page.evaluate(ANIMS+'.map(a=>a.currentTime)')
    page.wait_for_timeout(700)
    assert game()==paused
    actual=page.evaluate(ANIMS+'.map(a=>a.currentTime)');assert len(actual)==len(positions) and all(abs(a-b)<2 for a,b in zip(actual,positions)),(positions,actual)
    page.get_by_role('button',name='계속하기',exact=False).first.click()
    page.wait_for_function('!window.__gameTools.get_game_state.execute({}).regenerating')
    seed_start();trigger(True);page.locator('.regeneration-scene').wait_for(state='attached')
    page.evaluate(ANIMS+'.forEach(a=>{a.pause();a.currentTime=240})')
    page.get_by_role('button',name='메인으로',exact=True).click();held=game()
    page.wait_for_timeout(700);assert game()['board']==held['board'] and game()['elapsed']==held['elapsed']
    if page.locator('[data-theme-select=burger]').count(): page.locator('[data-theme-select=burger]').click()
    page.locator('.home-play').click();page.locator('.regeneration-scene').wait_for(state='attached')
    assert game()['regenerating'],'Re-entry must resume the visual sequence, not snap to completion'
    assert page.evaluate(ANIMS+'.every(a=>Math.abs(a.currentTime-240)<1)'), 'Preserve the shared animation playhead'
    page.evaluate('window.__freezeBurst=false;'+ANIMS+'.forEach(a=>a.play())')
    page.wait_for_function('!window.__gameTools.get_game_state.execute({}).regenerating')
    assert game()['board']==held['board'] and game()['score']==300
    seed_start();trigger();page.locator('.regeneration-scene').wait_for(state='attached')
    seed_start();fresh=game();page.wait_for_timeout(750)
    assert game()['board']==fresh['board'] and game()['score']==0 and not game()['regenerating']
    expect(page.locator('.regeneration-scene')).to_have_count(0)
   else:realtime=None
   page.get_by_role('button',name='옵션',exact=True).click()
   page.get_by_role('button',name='게임 설명',exact=False).click()
   help=page.locator('.game-help').inner_text();assert '재료가 팡 터지고 위에서 새 재료가 쏟아져요' in help
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   assert not errors,errors
   report['cases'].append({'viewport':[width,height],'reduced':reduced,'frames':frames,'finishToInputMs':completion['ms'],'realTimeMs':realtime,'clocksProtected':True,'all54IdsNew':True,'pauseResumeAndFreshReload':not reduced,'errors':errors})
   print('PASS',suffix,'frames',frames,'resume',completion['ms'],'actual duration',realtime,flush=True)
   ctx.close()
  browser.close()
 (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--site',default='pages-dist');parser.add_argument('--url');parser.add_argument('--out',default='burst-refill-proof');a=parser.parse_args()
 if a.url:verify(a.url.rstrip('/')+'/',Path(a.out))
 else:
  with tempfile.TemporaryDirectory() as root:
   os.symlink(Path(a.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
   server=subprocess.Popen(['python3','-m','http.server','4182','--bind','127.0.0.1','--directory',root],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   try:time.sleep(.3);verify('http://127.0.0.1:4182/giralab-web/',Path(a.out))
   finally:server.terminate();server.wait(timeout=5)
