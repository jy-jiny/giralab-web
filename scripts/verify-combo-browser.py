from pathlib import Path as _DriverPath
_TEST_DRIVER = (_DriverPath(__file__).resolve().parents[1] / "scripts/browser-game-driver.js").read_text()
"""Exercise the published game with isolated API fixtures, never real ranking writes."""
import argparse,json,hashlib,subprocess,time,shutil,tempfile,os
from pathlib import Path
from playwright.sync_api import sync_playwright
EXPECTED='7286b1ff064f1fd9e0e0629c2792859d686e6136'
RECIPES=[
 ('double',['bun','patty','cheese','cheese','bun'],1000),
 ('cheese-melt',['bun','cheese','patty','cheese','bun'],1200),
 ('classic',['bun','patty','bun'],100),
 ('cheese',['bun','patty','cheese','bun'],300),
 ('green',['bun','patty','lettuce','bun'],300),
 ('bacon',['bun','patty','bacon','bun'],300),
 ('bacon-cheese',['bun','patty','bacon','cheese','bun'],1000),
 ('double-patty',['bun','patty','patty','bun'],400),
 ('garden-stack',['bun','lettuce','patty','lettuce','bun'],1200),
 ('smoky-green',['bun','bacon','patty','lettuce','bun'],1200),
 ('bacon-first',['bun','bacon','patty','cheese','bun'],1200),
 ('green-cheese',['bun','lettuce','patty','cheese','bun'],1200),
 ('cheese-bacon-stack',['bun','cheese','patty','bacon','bun'],1400),
 ('double-bacon',['bun','bacon','patty','bacon','bun'],1400),
 ('cheese-mad',['bun','cheese','cheese','cheese','cheese','bun'],4200),
 ('meat-monster',['bun','patty','bacon','patty','bacon','bun'],4000),
 ('green-monster',['bun','lettuce','lettuce','patty','lettuce','bun'],3600),
 ('bacon-bomb',['bun','bacon','bacon','patty','bacon','bun'],4000),
]
def fixture(route):
 name=route.request.url.split('/api/')[-1].split('?')[0]
 data={'player':{'id':'balance-qa','nickname':'밸런스검증'}} if name=='player' else {'entries':[],'me':None} if name=='leaderboard' else {'unlocked':['classic'],'bestScore':0}
 route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
def find(board,sequence):
 def visit(r,c,path):
  if r<0 or r>=9 or c<0 or c>=6 or (r,c) in path or board[r][c]!=sequence[len(path)]:return None
  path=path+[(r,c)]
  if len(path)==len(sequence):return [{'row':r,'col':c} for r,c in path]
  for dr in (-1,0,1):
   for dc in (-1,0,1):
    if dr or dc:
     found=visit(r+dr,c+dc,path)
     if found:return found
  return None
 for r in range(9):
  for c in range(6):
   found=visit(r,c,[])
   if found:return found
 return None
def verify(base,out):
 out.mkdir(parents=True,exist_ok=True)
 report={'base_url':base,'source_commit':EXPECTED,'network':'All API requests isolated; no production ranking writes','tests':[]}
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
  for width,height in [(360,640),(390,844),(412,915)]:
   ctx=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=2,is_mobile=True,has_touch=True)
   ctx.add_init_script(_TEST_DRIVER);ctx.add_init_script("window.__gameTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__gameTools[t.name]=t}}});")
   page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_default_timeout(20000)
   page.route('**/api/**',fixture)
   page.goto(base+'?balance=2',wait_until='domcontentloaded')
   page.locator('.home-screen').wait_for(state='visible')
   assert page.locator('.home-version').inner_text()=='GiraLab · 1.7.2'
   # Deterministic gameplay RNG, set after boot so unrelated framework setup cannot consume it.
   page.evaluate("()=>{let seed=20260918;Math.random=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296)}")
   if page.locator('[data-theme-select=burger]').count(): page.locator('[data-theme-select=burger]').click()
   page.locator('.home-play').click();page.locator('[data-balance-version="3"]').wait_for(state='visible')
   assert page.locator('button[data-tile-id]').count()==54
   state=lambda:page.evaluate('window.__gameTools.get_game_state.execute({})')
   assert state()['rulesVersion']==3
   played=[];ladder_step=0
   for step in range(5):
    s=state();chosen=None
    ordered=RECIPES if step==0 else [RECIPES[2]]+[r for r in RECIPES if r[0]!='classic']
    for name,seq,points in ordered:
     cells=find(s['board'],seq)
     if cells:chosen=(name,seq,points,cells);break
    assert chosen,'Playable board has no legal recipe'
    name,seq,points,cells=chosen;before=s['score']
    ladder=len(seq)==5 and ladder_step==4
    ladder_step=0 if ladder else 3 if len(seq)==3 else 4 if len(seq)==4 and ladder_step==3 else 0
    result=page.evaluate('cells=>window.__gameTools.submit_ingredient_path.execute({cells})',cells)
    assert result['success'],result
    now=state();expected=round(points*(1+step*.5)*(1.5 if ladder else 1))
    assert now['score']-before==expected,(name,now,before,expected)
    assert now['combo']==step+1,now
    assert any(find(now['board'],seq) for _,seq,_ in RECIPES if len(seq)<6), 'Normal/advanced safety path missing after refill'
    if len(seq)>=5:assert now['slow']>0
    played.append({'recipe':name,'combo':now['combo'],'earned':now['score']-before,'slow':now['slow']})
    if step==4:
     page.wait_for_timeout(100);page.screenshot(path=str(out/f'combo-{width}x{height}.png'))
    page.wait_for_timeout(850)
   assert page.locator('.combo-hot,.combo-fever').count()==1
   before=state()['board'];page.wait_for_timeout(8250)
   assert state()['board']==before
   assert page.locator('.hinted-tile,.hint-order').count()==0
   assert not errors,errors
   report['tests'].append({'viewport':[width,height],'played':played,'idle_board_unchanged':True,'hint_tiles':page.locator('.hinted-tile').count(),'page_errors':errors})
   page.screenshot(path=str(out/f'no-hints-{width}x{height}.png'))
   meta=ctx.request.get(base+'source-build.json?balance=2').json()
   assert meta['source_commit']==EXPECTED and meta['rules_version']==3 and meta['automatic_board_hints'] is False,meta
   art=ctx.request.get(base+'giralab-loading-approved-aecda336.jpg').body()
   assert hashlib.sha256(art).hexdigest()=='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
   ctx.close()
  browser.close()
 (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--site',default='site');parser.add_argument('--url');parser.add_argument('--out',default='combo-proof');args=parser.parse_args()
 if args.url:verify(args.url.rstrip('/')+'/',Path(args.out))
 else:
  with tempfile.TemporaryDirectory() as root:
   os.symlink(Path(args.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
   server=subprocess.Popen(['python3','-m','http.server','4174','--bind','127.0.0.1','--directory',root],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   try:time.sleep(.5);verify('http://127.0.0.1:4174/giralab-web/',Path(args.out))
   finally:server.terminate();server.wait(timeout=5)
