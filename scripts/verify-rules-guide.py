"""Read-only browser verification: isolate every API call from production records."""
import argparse, importlib.util, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

spec=importlib.util.spec_from_file_location('combo',Path(__file__).with_name('verify-combo-browser.py'))
combo=importlib.util.module_from_spec(spec);spec.loader.exec_module(combo)
IDS=[r[0] for r in combo.RECIPES]
COLORS={
 'normal': {'background':'rgb(226, 232, 240)','color':'rgb(51, 65, 85)','top':'rgb(148, 163, 184)'},
 'advanced': {'background':'rgb(29, 78, 216)','color':'rgb(255, 255, 255)','top':'rgb(59, 130, 246)'},
 'rare': {'background':'rgb(250, 204, 21)','color':'rgb(66, 32, 6)','top':'rgb(250, 204, 21)'},
}
def contrast(a,b):
 def lum(color):
  values=[int(v)/255 for v in re.findall(r'\d+',color)[:3]]
  values=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
  return sum(v*w for v,w in zip(values,[.2126,.7152,.0722]))
 x,y=sorted([lum(a),lum(b)])
 return (y+.05)/(x+.05)

def verify(base,out):
 out.mkdir(parents=True,exist_ok=True)
 report={'game_version':'1.5.5','base_url':base,'network':'All API calls isolated; no production ranking writes','tests':[]}
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
  for width,height in [(360,640),(390,844),(412,915)]:
   for discovered in (False,True):
    ctx=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=2,is_mobile=True,has_touch=True)
    ctx.add_init_script("window.__gameTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__gameTools[t.name]=t}}});")
    page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_default_timeout(20000)
    def fixture(route):
     name=route.request.url.split('/api/')[-1].split('?')[0]
     data={'player':{'id':'guide-qa','nickname':'설명검증'}} if name=='player' else {'entries':[],'me':None} if name=='leaderboard' else {'unlocked':IDS if discovered else ['classic'],'bestScore':0}
     route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
    page.route('**/api/**',fixture)
    page.goto(base+'?rules-guide=1.5.5',wait_until='domcontentloaded')
    page.locator('.home-screen').wait_for(state='visible')
    expect(page.locator('.home-version')).to_have_text('GiraLab · 1.5.5')
    suffix=f'{width}x{height}-'+('discovered' if discovered else 'undiscovered')
    page.get_by_role('button',name='옵션',exact=True).click()
    page.get_by_role('button',name=re.compile('게임 설명')).click()
    guide=page.locator('.game-help');expect(guide).to_be_visible()
    expect(guide.locator('[data-guide-section]')).to_have_count(5)
    text=guide.inner_text()
    for phrase in ['기본점수 × 콤보 배율 × 난이도 연속 보너스','5초가 되기 전에','3개 → 4개 → 5개','×1.5','25점 단위','55% 느려져요','판 전체 54칸','새 재료로 다시 생성','0.6초','일반·고급 조합이 모두 0개','전설 조합은 재생성 판단에서 제외','시간제 재생성와 자동 정답 힌트는 없어요']:
     assert phrase in text,phrase
    cells=guide.locator('.guide-score-table tbody tr').all_inner_texts()
    for expected,actual in zip(['550점','6,600점','23,100점'],cells):assert expected in actual,(expected,actual)
    for tier,expected in COLORS.items():
     badge=guide.locator(f'.recipe-tier-{tier}')
     styles=badge.evaluate('(el)=>({background:getComputedStyle(el).backgroundColor,color:getComputedStyle(el).color})')
     assert styles=={k:expected[k] for k in ['background','color']},styles
    page.screenshot(path=str(out/f'guide-{suffix}-top.png'))
    guide.locator('[data-guide-section="board"]').scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'guide-{suffix}-board.png'))
    scroll=guide.evaluate('(el)=>({height:el.clientHeight,full:el.scrollHeight,width:el.clientWidth,fullWidth:el.scrollWidth})')
    assert scroll['full']>scroll['height']>100,scroll
    assert scroll['fullWidth']<=scroll['width']+1,scroll
    guide.get_by_role('button',name='알겠어요',exact=True).click()
    expect(page.locator('.settings-content')).to_be_visible()
    page.get_by_role('button',name=re.compile('레시피 도감')).click()
    expect(page.locator('.recipe-card')).to_have_count(18)
    expect(page.locator('.recipe-card.locked')).to_have_count(0 if discovered else 17)
    verified=[]
    for tier,expected in COLORS.items():
     cards=page.locator(f'.recipe-card[data-recipe-tier-card="{tier}"]')
     expect(cards).to_have_count({'normal':5,'advanced':9,'rare':4}[tier])
     for card in cards.all():
      badge=card.locator(f'.recipe-tier-{tier}')
      styles=badge.evaluate('(el)=>({background:getComputedStyle(el).backgroundColor,color:getComputedStyle(el).color})')
      assert styles=={k:expected[k] for k in ['background','color']},(tier,styles)
      ratio=contrast(styles['color'],styles['background']);assert ratio>=4.5,(tier,ratio)
      border=card.evaluate('(el)=>({color:getComputedStyle(el).borderTopColor,width:getComputedStyle(el).borderTopWidth})')
      assert border=={'color':expected['top'],'width':'4px'},(tier,border)
      assert badge.evaluate('(el)=>{const r=el.getBoundingClientRect(),c=el.closest(".recipe-card").getBoundingClientRect();return r.left>=c.left-1&&r.right<=c.right+1}')
     verified.append({'tier':tier,'badge':styles,'text_contrast':round(ratio,2),'card_top':border})
    page.screenshot(path=str(out/f'tier-colors-{suffix}-top.png'))
    page.locator('.recipe-card[data-recipe-tier-card="rare"]').last.scroll_into_view_if_needed()
    page.screenshot(path=str(out/f'tier-colors-{suffix}-rare.png'))
    page.get_by_role('button',name='닫기',exact=True).click()
    page.locator('.home-play').click();page.locator('button[data-tile-id]').first.wait_for(state='visible')
    state=lambda:page.evaluate('window.__gameTools.get_game_state.execute({})')
    s=state();assert any(combo.find(s['board'],seq) for _,seq,_ in combo.RECIPES if len(seq)<6)
    page.get_by_role('button',name='옵션',exact=True).click()
    page.get_by_role('button',name=re.compile('게임 설명')).click()
    before=state();page.wait_for_timeout(1200);after=state()
    assert after['board']==before['board'] and after['score']==before['score']
    for key in ['elapsed','danger','combo','slow']:
     if key in before:assert after[key]==before[key],(key,before,after)
    assert not errors,errors
    meta=ctx.request.get(base+'source-build.json?rules-guide=1.5.5').json()
    assert meta['game_version']=='1.5.5' and meta['board_validity_max_tier']=='advanced'
    assert meta['rules_guide'] is True and meta['tier_palette_version']==2 and meta['automatic_board_hints'] is False
    report['tests'].append({'viewport':[width,height],'all_discovered':discovered,'guide_sections':5,'score_examples_verified':True,'scroll':scroll,'colors':verified,'help_pauses_game':True,'initial_board_has_normal_or_advanced':True,'page_errors':errors})
    ctx.close()
  browser.close()
 (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--site',default='site');parser.add_argument('--url');parser.add_argument('--out',default='rules-guide-proof');args=parser.parse_args()
 if args.url:verify(args.url.rstrip('/')+'/',Path(args.out))
 else:
  with tempfile.TemporaryDirectory() as root:
   os.symlink(Path(args.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
   server=subprocess.Popen(['python3','-m','http.server','4176','--bind','127.0.0.1','--directory',root],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   try:time.sleep(.5);verify('http://127.0.0.1:4176/giralab-web/',Path(args.out))
   finally:server.terminate();server.wait(timeout=5)
