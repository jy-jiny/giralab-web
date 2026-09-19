"""Verify the approved dashboard using isolated API fixtures; never write real records."""
import argparse, json, shutil
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from playwright.sync_api import sync_playwright, expect
REVISION='dashboard-20260919'
PROGRESS={'unlocked':['classic','cheese','green','bacon','double'],'bestScore':173850}
RANKS={'entries':[{'rank':1,'nickname':'화면확인','score':173850,'isMe':True}],'me':{'nickname':'화면확인','score':173850,'rank':1},'updatedAt':0}
HOOK="window.__gameTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__gameTools[t.name]=t}}});"
def verify(url,out):
    out.mkdir(parents=True,exist_ok=True)
    report={'revision':REVISION,'api':'isolated fixtures; zero production writes','screens':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required'])
        for width,height in [(320,568),(360,640),(390,690),(390,844),(412,915),(844,390)]:
            ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True)
            ctx.add_init_script(HOOK);page=ctx.new_page();page.set_default_timeout(20000)
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            state={'progress':dict(PROGRESS),'writes':0}
            def fixture(route):
                path=route.request.url.split('/api/')[-1].split('?')[0]
                if path=='player':data={'player':{'id':'dashboard-fixture','nickname':'화면확인'}}
                elif path=='leaderboard':data=RANKS
                elif path=='progress':
                    if route.request.method=='POST':state['writes']+=1;state['progress']=route.request.post_data_json
                    data=state['progress']
                else:raise AssertionError('Unexpected API endpoint '+path)
                route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
            page.route('**/api/**',fixture)
            page.goto(url+'?verify='+REVISION,wait_until='domcontentloaded')
            expect(page.locator('.theme-lobby')).to_have_attribute('data-lobby-revision',REVISION)
            expect(page.locator('[data-summary-best="burger"]')).to_have_text('173,850')
            expect(page.locator('[data-summary-collection="burger"]')).to_have_text('5 / 19')
            expect(page.locator('[data-theme-select]')).to_have_count(4)
            expect(page.locator('.research-theme-position i')).to_have_count(4)
            expect(page.locator('.theme-carousel-controls,.theme-lobby-note')).to_have_count(0)
            page.wait_for_timeout(350)
            metrics=page.evaluate('''()=>{const root=document.querySelector('.theme-lobby');const selectors=['.theme-topbar','.theme-welcome','.theme-section-heading','.theme-grid','.research-summary','.theme-version'];return {height:innerHeight,scroll:root.scrollHeight,client:root.clientHeight,body:document.documentElement.scrollHeight,boxes:Object.fromEntries(selectors.map(s=>{const r=document.querySelector(s).getBoundingClientRect();return[s,{top:r.top,bottom:r.bottom,height:r.height}]}))}}''')
            assert metrics['scroll']<=metrics['client']+1,metrics
            assert metrics['body']<=height+1,metrics
            for box in metrics['boxes'].values():assert box['top']>=-1 and box['bottom']<=height+1 and box['height']>0,metrics
            assert metrics['boxes']['.theme-grid']['height']>=90,metrics
            page.screenshot(path=str(out/f'main-{width}x{height}.png'))
            if (width,height)==(390,690):
                page.get_by_role('button',name='새로운 조합을 찾으러 도감 열기',exact=True).click()
                expect(page.locator('.book-dialog .recipe-card')).to_have_count(19)
                page.get_by_role('button',name='닫기',exact=True).click()
                for theme in ['music','war','robot']:
                    page.locator(f'[data-theme-select="{theme}"]').evaluate('(e)=>e.scrollIntoView({block:"nearest",inline:"start"})')
                    expect(page.locator('.research-summary')).to_have_attribute('data-summary-theme',theme)
                    expect(page.locator('[data-summary-best]')).to_have_text('—')
                    expect(page.locator('[data-summary-collection]')).to_have_text('출시 예정')
                    assert '173,850' not in page.locator('.research-summary').inner_text()
                    page.screenshot(path=str(out/f'{theme}-{width}.png'))
                    page.locator('.research-stat').first.click()
                    expect(page.locator('.theme-lobby')).to_have_attribute('data-theme',theme)
                    expect(page.locator('.theme-locked-action')).to_be_disabled()
                    page.get_by_role('button',name='테마 선택으로',exact=True).click()
                page.locator('[data-theme-select="burger"]').evaluate('(e)=>e.scrollIntoView({block:"nearest",inline:"start"})')
                expect(page.locator('[data-summary-best="burger"]')).to_have_text('173,850')
                page.locator('.research-stat').first.click()
                expect(page.locator('[data-theme-best="burger"]')).to_have_text('173,850')
                expect(page.locator('.theme-play svg')).to_have_count(0)
                page.locator('.home-play').click();expect(page.locator('[data-tile-id]')).to_have_count(54)
                game=page.evaluate('window.__gameTools.get_game_state.execute({})')
                assert game['status']=='playing' and game['rulesVersion']==3,game
                page.get_by_role('button',name='메인으로',exact=True).click()
                expect(page.locator('.home-play')).to_have_text('계속하기')
                page.get_by_role('button',name='테마 선택으로',exact=True).click()
                expect(page.locator('[data-summary-best="burger"]')).to_have_text('173,850')
                expect(page.locator('[data-summary-collection="burger"]')).to_have_text('5 / 19')
            assert not errors,errors
            report['screens'].append({'viewport':[width,height],'metrics':metrics,'errors':errors})
            (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
            print('PASS dashboard',width,height,flush=True);ctx.close()
        browser.close()
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--site',default='site');p.add_argument('--url');p.add_argument('--out',default='dashboard-proof');a=p.parse_args()
    if a.url:verify(a.url.rstrip('/')+'/',Path(a.out))
    else:
        server=ThreadingHTTPServer(('127.0.0.1',4187),partial(SimpleHTTPRequestHandler,directory=str(Path(a.site).resolve())))
        Thread(target=server.serve_forever,daemon=True).start()
        try:verify('http://127.0.0.1:4187/',Path(a.out))
        finally:server.shutdown();server.server_close()
