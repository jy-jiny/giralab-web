"""Actual-browser checks; all game API writes are intercepted, never sent to production."""
import argparse, json, os, shutil, subprocess, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

VERSION='1.7.2'
IDS=['classic','cheese','green','bacon','double-patty','double','bacon-cheese','cheese-melt','garden-stack','smoky-green','bacon-first','green-cheese','cheese-bacon-stack','double-bacon','cheese-mad','meat-monster','green-monster','bacon-bomb','forbidden-seven']
MYTH=['bun','bacon','bacon','bacon','bacon','bacon','bun']
HOOK="window.__boardDraws=[];const originalRandom=Math.random;Math.random=()=>window.__boardDraws.length?window.__boardDraws.shift():originalRandom();window.__gameTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__gameTools[t.name]=t;}}});"

def find(board,seq):
    def walk(r,c,path):
        if not (0<=r<9 and 0<=c<6) or (r,c) in path or board[r][c]!=seq[len(path)]:return None
        nxt=path+[(r,c)]
        if len(nxt)==len(seq):return [{'row':r,'col':c} for r,c in nxt]
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr or dc:
                    result=walk(r+dr,c+dc,nxt)
                    if result:return result
    for r in range(9):
        for c in range(6):
            result=walk(r,c,[])
            if result:return result

def verify(base,out):
    out.mkdir(parents=True,exist_ok=True)
    report={'version':VERSION,'api':'isolated fixtures, no production writes','tests':[]}
    with sync_playwright() as p:
        executable=shutil.which('google-chrome') or shutil.which('chromium')
        for policy in ['no-user-gesture-required','document-user-activation-required']:
            browser=p.chromium.launch(executable_path=executable,args=['--no-sandbox','--disable-dev-shm-usage','--disable-features=PreloadMediaEngagementData,MediaEngagementBypassAutoplayPolicies','--autoplay-policy='+policy])
            sizes=[(360,640),(390,844),(412,915)] if policy=='no-user-gesture-required' else [(390,844)]
            for width,height in sizes:
                ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True,device_scale_factor=1)
                ctx.add_init_script(HOOK)
                page=ctx.new_page();page.set_default_timeout(20000);errors=[];saved=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                def fixture(route):
                    name=route.request.url.split('/api/')[-1].split('?')[0]
                    data={'player':{'id':'audio-mythic-qa','nickname':'검증'}} if name=='player' else {'entries':[],'me':None} if name=='leaderboard' else {'unlocked':IDS,'bestScore':0}
                    if name=='progress' and route.request.method=='POST':
                        data=route.request.post_data_json;assert set(data['unlocked'])<=set(IDS);saved.append(data)
                    route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
                page.route('**/api/**',fixture)
                page.goto(base+'?audio-mythic='+VERSION,wait_until='domcontentloaded')
                # Playwright evaluate may count as user activation. Inspect first autoplay via CDP.
                cdp=ctx.new_cdp_session(page)
                def untouched(expression):
                    result=cdp.send('Runtime.evaluate',{'expression':expression,'returnByValue':True,'userGesture':False})
                    assert 'exceptionDetails' not in result,result
                    return result['result'].get('value')
                for attempt in range(100):
                    before=untouched('window.__gameTools.get_audio_state?.execute({})')
                    home=untouched('document.querySelector(".home-version")?.textContent')
                    if before and home=='GiraLab · '+VERSION and (before['labPlaying'] or before['context']=='suspended' or before['musicVolume']==0):break
                    page.wait_for_timeout(100)
                assert before and home=='GiraLab · '+VERSION,(before,home)
                activation=untouched('navigator.userActivation.hasBeenActive')
                assert activation is False,'Autoplay inspection must not synthesize activation'
                (out/f'autoplay-{policy}-{width}.json').write_text(json.dumps({'audio':before,'userActivated':activation},indent=2))
                if policy=='no-user-gesture-required':
                    assert before['labPlaying'] and before['track']=='Laboratory Notes',before
                    assert not untouched('!!document.querySelector(".audio-enable")')
                else:
                    assert before['context']=='suspended',before
                    assert not untouched('!!document.querySelector(".audio-enable")')
                audio=lambda:untouched('window.__gameTools.get_audio_state.execute({})')
                game=lambda:untouched('window.__gameTools.get_game_state.execute({})')
                if page.locator('[data-theme-select=burger]').count(): page.locator('[data-theme-select=burger]').click()
                page.locator('.home-play').click()
                page.wait_for_function('window.__gameTools.get_audio_state.execute({}).gamePlaying')
                page.wait_for_timeout(350)
                assert audio()['track']=='Kitchen Rush' and audio()['gameTime']>0
                assert not audio()['labPlaying']
                expect(page.locator('.audio-enable')).to_have_count(0)
                page.get_by_role('button',name='메인으로',exact=True).click()
                page.wait_for_function('window.__gameTools.get_audio_state.execute({}).labPlaying')
                assert not audio()['gamePlaying']
                if policy=='no-user-gesture-required':
                    page.get_by_role('button',name='옵션',exact=True).click()
                    page.get_by_role('button',name='레시피 도감',exact=False).click()
                    expect(page.locator('.recipe-card')).to_have_count(19)
                    expect(page.locator('.recipe-group-heading>span')).to_have_text(['일반','고급','전설','신화'])
                    expect(page.locator('.recipe-group-heading>small')).to_have_text(['5종','9종','4종','1종'])
                    assert page.locator('.recipe-card').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.recipeId)')==IDS
                    for card in page.locator('.recipe-card').all():
                        assert card.evaluate('(el)=>el.querySelector(".recipe-tier-badge").getBoundingClientRect().top>=el.querySelector("h3").getBoundingClientRect().bottom+3')
                    card=page.locator('[data-recipe-id="forbidden-seven"]');card.scroll_into_view_if_needed()
                    expect(card.locator('h3')).to_have_text('금단의 7층 버거')
                    expect(card.locator('.recipe-tier-badge')).to_have_text('신화 조합')
                    expect(card.locator('.recipe-order>span')).to_have_count(7)
                    assert card.evaluate('(el)=>el.scrollWidth<=el.clientWidth+1')
                    assert card.locator('.recipe-order').evaluate('(el)=>{const r=el.getBoundingClientRect();return [...el.children].every(n=>{const b=n.getBoundingClientRect();return b.left>=r.left-1&&b.right<=r.right+1&&b.top>=r.top-1&&b.bottom<=r.bottom+1})}')
                    page.screenshot(path=str(out/f'mythic-codex-{width}.png'))
                    page.get_by_role('button',name='옵션',exact=True).click()
                    page.get_by_role('button',name='게임 설명',exact=False).click()
                    help=page.locator('.game-help');expect(help.locator('[data-guide-section]')).to_have_count(6)
                    text=help.inner_text()
                    for phrase in ['82,500점','7개 신화','6초 슬로우','전설·신화 조합은 재생성 판단에서 제외','판 전체 54칸을 새 재료로']:
                        assert phrase in text,phrase
                    assert '재배치' not in text
                    assert help.evaluate('(el)=>el.scrollWidth<=el.clientWidth+1')
                    help.locator('[data-guide-section="feedback"]').scroll_into_view_if_needed()
                    page.screenshot(path=str(out/f'mythic-help-{width}.png'))
                    help.get_by_role('button',name='알겠어요',exact=True).click()
                    page.get_by_role('button',name='닫기',exact=True).click()
                    if page.locator('[data-theme-select=burger]').count(): page.locator('[data-theme-select=burger]').click()
                    page.locator('.home-play').click()
                    board=[['lettuce']*6 for _ in range(9)];board[0][0:3]=['bun','patty','bun']
                    cells=[(8,0),(8,1),(8,2),(8,3),(8,4),(8,5),(7,4)]
                    for (r,c),ingredient in zip(cells,MYTH):board[r][c]=ingredient
                    draws=[{'bun':.1,'patty':.5,'cheese':.7,'lettuce':.85,'bacon':.95}[item] for row in board for item in row]
                    page.evaluate('(values)=>{window.__boardDraws=values;window.__gameTools.start_game.execute({})}',draws)
                    assert game()['board']==board
                    path=find(game()['board'],MYTH);assert path
                    result=page.evaluate('(cells)=>window.__gameTools.submit_ingredient_path.execute({cells})',path)
                    assert result['success'] and result['score']==15000,result
                    state=game();assert state['presenting'] and state['danger']==0 and state['slow']==6,state
                    expect(page.locator('.mythic-hit')).to_be_visible()
                    page.screenshot(path=str(out/f'mythic-hit-{width}.png'))
                    page.wait_for_timeout(120)
                    after=game();assert after['elapsed']==state['elapsed'] and after['slow']==state['slow'],(state,after)
                    page.wait_for_function('!window.__gameTools.get_game_state.execute({}).presenting')
                    page.wait_for_timeout(450)
                    expect(page.locator('.mythic-hit')).to_have_count(0)
                    assert any('forbidden-seven' in entry['unlocked'] for entry in saved)
                assert not errors,errors
                meta=ctx.request.get(base+'source-build.json?release='+VERSION).json()
                assert meta['game_version']==VERSION and meta['recipe_count']==19 and meta['rules_version']==3
                assert meta['board_regeneration_mode']=='full-new' and meta['board_validity_max_tier']=='advanced'
                assert meta['audio_scene_tracks'] and meta['autoplay_recovery'] and meta['mythic_recipe']=='forbidden-seven'
                report['tests'].append({'viewport':[width,height],'autoplay_policy':policy,'initial_audio':before,'oneClickGameMusic':True,'returnHomeMusic':True,'errors':errors})
                ctx.close()
            browser.close()
        browser=p.chromium.launch(executable_path=executable,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
        ctx=browser.new_context();ctx.add_init_script(HOOK+"localStorage.setItem('burger-lab-music-volume','0');")
        page=ctx.new_page()
        page.route('**/api/**',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps({'player':{'id':'mute-qa','nickname':'무음'}} if '/api/player' in route.request.url else {'entries':[],'me':None} if '/api/leaderboard' in route.request.url else {'unlocked':['classic'],'bestScore':0})))
        page.goto(base);expect(page.locator('.home-screen')).to_be_visible()
        page.wait_for_function('window.__gameTools.get_audio_state?.execute({})')
        assert page.evaluate('window.__gameTools.get_audio_state.execute({}).musicVolume')==0
        expect(page.locator('.audio-enable')).to_have_count(0)
        if page.locator('[data-theme-select=burger]').count(): page.locator('[data-theme-select=burger]').click()
        page.locator('.home-play').click();page.wait_for_timeout(250)
        assert not page.evaluate('window.__gameTools.get_audio_state.execute({}).gamePlaying')
        report['mutedPreferencePreserved']=True
        ctx.close();browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--site',default='site');parser.add_argument('--url');parser.add_argument('--out',default='audio-mythic-proof');args=parser.parse_args()
    if args.url:verify(args.url.rstrip('/')+'/',Path(args.out))
    else:
        with tempfile.TemporaryDirectory() as root:
            os.symlink(Path(args.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
            server=subprocess.Popen(['python3','-m','http.server','4179','--bind','127.0.0.1','--directory',root],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:time.sleep(.4);verify('http://127.0.0.1:4179/giralab-web/',Path(args.out))
            finally:server.terminate();server.wait(timeout=5)
