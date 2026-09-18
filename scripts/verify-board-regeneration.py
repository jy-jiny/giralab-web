"""Exercise the real compiled game; isolate API writes and control only RNG inputs."""
import argparse, importlib.util, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
spec=importlib.util.spec_from_file_location('combo',Path(__file__).with_name('verify-combo-browser.py'))
combo=importlib.util.module_from_spec(spec);spec.loader.exec_module(combo)
ROWS=['LBBPPP','PALCPA','PLALPA','PLLLLC','LLPAAL','LPAALP','APCCLC','ALCPCL','PCPPPP']
TYPES={'L':'lettuce','B':'bun','P':'patty','A':'bacon','C':'cheese'}
DRAWS={'L':.85,'B':.1,'P':.5,'A':.95,'C':.7}


def verify(base,out):
 out.mkdir(parents=True,exist_ok=True)
 report={'version':'1.5.5','base_url':base,'isolated_api':True,'tests':[]}
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
  for width,height in [(360,640),(390,844),(412,915)]:
   ctx=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=2,is_mobile=True,has_touch=True)
   ctx.add_init_script("window.__gameTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__gameTools[t.name]=t}}});")
   page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_default_timeout(20000)
   page.route('**/api/**',combo.fixture)
   page.goto(base+'?regeneration=1.5.5',wait_until='domcontentloaded')
   page.locator('.home-screen').wait_for(state='visible')
   expect(page.locator('.home-version')).to_have_text('GiraLab · 1.5.5')
   # Unlock optional audio before deterministic RNG; audio noise must not consume fixture draws.
   page.locator('.home-version').click()
   initial=page.evaluate('''draws=>{
     let i=0;const original=Math.random;Math.random=()=>draws[i++]??.5;
     try{window.__gameTools.start_game.execute({});return window.__gameTools.get_game_state.execute({});}
     finally{Math.random=original;}
   }''',[DRAWS[c] for row in ROWS for c in row])
   assert initial['board']==[[TYPES[c] for c in row] for row in ROWS],initial
   expect(page.locator('button[data-tile-id]')).to_have_count(54)
   page.screenshot(path=str(out/f'{width}-before.png'))
   result=page.evaluate('''async ()=>{
     const original=Math.random;let calls=0,seed=73;
     const oldIds=[...document.querySelectorAll('button[data-tile-id]')].map(e=>e.dataset.tileId);
     Math.random=()=>++calls<=4?.99:((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
     let submitted;
     try{submitted=window.__gameTools.submit_ingredient_path.execute({cells:[{row:0,col:2},{row:0,col:3},{row:1,col:2},{row:0,col:1}]});}
     finally{Math.random=original;}
     const start=window.__gameTools.get_game_state.execute({});
     await new Promise(resolve=>setTimeout(resolve,80));
     const notice=document.querySelector('.regeneration-notice');
     const tiles=[...document.querySelectorAll('button[data-tile-id]')];
     const styles={icon:getComputedStyle(notice.querySelector('svg')).animationName,iconDuration:getComputedStyle(notice.querySelector('svg')).animationDuration,tile:getComputedStyle(tiles[0]).animationName,tileDuration:getComputedStyle(tiles[0]).animationDuration};
     const newIds=tiles.map(e=>e.dataset.tileId);
     await new Promise(resolve=>setTimeout(resolve,100));
     return {submitted,start,protected:window.__gameTools.get_game_state.execute({}),oldIds,newIds,allDisabled:tiles.every(e=>e.disabled),notice:notice.textContent,styles};
   }''')
   assert result['submitted']['success'] and result['submitted']['recipe']=='그린 버거'
   assert result['start']['score']==300 and result['start']['combo']==1
   assert result['start']['regenerating'] and result['protected']['regenerating']
   for key in ['danger','score','combo','slow','board']:assert result['start'][key]==result['protected'][key],key
   assert not set(result['oldIds'])&set(result['newIds']);assert len(set(result['newIds']))==54
   assert result['allDisabled'] and '재료 재생성 중' in result['notice']
   assert result['styles']=={'icon':'regeneration-turn','iconDuration':'0.6s','tile':'regeneration-arrive','tileDuration':'0.55s'},result['styles']
   board=result['protected']['board']
   assert any(combo.find(board,seq) for _,seq,_ in combo.RECIPES if len(seq)<=5)
   assert sum(t=='bun' for row in board for t in row)>=2
   page.screenshot(path=str(out/f'{width}-transition.png'))
   page.wait_for_timeout(650)
   expect(page.locator('.regeneration-notice')).to_have_count(0)
   expect(page.locator('button[data-tile-id]:disabled')).to_have_count(0)
   page.screenshot(path=str(out/f'{width}-after.png'))
   page.get_by_role('button',name='옵션',exact=True).click()
   page.get_by_role('button',name=re.compile('게임 설명')).click()
   help=page.locator('.game-help');text=help.inner_text()
   assert '판 전체 54칸을 새 재료로 다시 생성' in text
   assert '일반·고급 조합이 모두 0개면 자동 재생성' in text
   assert '재배치' not in text and '32번 섞어서' not in text and '최대 3칸' not in text
   help.locator('[data-guide-section="board"]').scroll_into_view_if_needed()
   page.screenshot(path=str(out/f'{width}-help.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1')
   assert not errors,errors
   meta=ctx.request.get(base+'source-build.json?regeneration=1.5.5').json()
   assert meta['game_version']=='1.5.5' and meta['board_regeneration_mode']=='full-new'
   assert meta['regeneration_animation']=='preserved' and meta['recipe_count']==18 and meta['rules_version']==2
   report['tests'].append({'viewport':[width,height],'replacedTileIds':54,'recipe':'green','score':300,'combo':1,'clocksProtected':True,'animation':result['styles'],'newBuns':sum(t=='bun' for row in board for t in row),'scriptErrors':errors})
   ctx.close()
  browser.close()
 (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--site',default='site');parser.add_argument('--url');parser.add_argument('--out',default='regeneration-proof');args=parser.parse_args()
 if args.url:verify(args.url.rstrip('/')+'/',Path(args.out))
 else:
  with tempfile.TemporaryDirectory() as root:
   os.symlink(Path(args.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
   server=subprocess.Popen(['python3','-m','http.server','4178','--bind','127.0.0.1','--directory',root],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   try:time.sleep(.5);verify('http://127.0.0.1:4178/giralab-web/',Path(args.out))
   finally:server.terminate();server.wait(timeout=5)
