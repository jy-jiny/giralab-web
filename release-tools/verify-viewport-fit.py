"""Main/game viewport proof; all API traffic uses isolated fixtures."""
import argparse, importlib.util, json, os, shutil, tempfile
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright, expect
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
spec=importlib.util.spec_from_file_location('lobby',SCRIPTS/'verify-theme-lobby.py')
lobby=importlib.util.module_from_spec(spec);spec.loader.exec_module(lobby)
lobby.RANKS['entries']=[{'rank':i,'nickname':'기린연구원' if i==1 else '버거연구원'+str(i),'score':21350 if i==1 else 18000-i*1000,'isMe':i==1} for i in range(1,6)]
def fits(page,selector):
    b=page.locator(selector).evaluate('''e=>{const r=e.getBoundingClientRect();return {y:r.y,h:r.height,client:e.clientHeight,scroll:e.scrollHeight,top:e.scrollTop,overflow:getComputedStyle(e).overflowY,vh:innerHeight,page:[scrollY,document.documentElement.scrollHeight,document.documentElement.clientHeight]}}''')
    assert b['scroll']<=b['client']+1 and b['top']==0 and b['overflow']=='hidden',(selector,b)
    assert b['y']>=-1 and b['y']+b['h']<=b['vh']+1,(selector,b)
    assert b['page'][0]==0 and b['page'][1]<=b['page'][2]+1,b
    return b

def swipe(page,ctx,selector,vertical=True):
    r=page.locator(selector).bounding_box();x=r['x']+r['width']*.7;y=r['y']+r['height']*.75
    c=ctx.new_cdp_session(page);c.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
    for i in range(1,9):
        c.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x if vertical else x-i*22,'y':y-i*14 if vertical else y}]});page.wait_for_timeout(15)
    c.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});c.detach();page.wait_for_timeout(300)

def verify(base,out):
    out.mkdir(parents=True,exist_ok=True);report={'base_url':base,'change':'main/game viewport only','api':'isolated; no production writes','tests':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage'])
        for w,h in [(320,568),(360,640),(390,667),(390,844),(412,915),(1024,768)]:
            ctx=browser.new_context(viewport={'width':w,'height':h},is_mobile=w<600,has_touch=True);ctx.add_init_script(lobby.HOOK)
            page=ctx.new_page();page.set_default_timeout(12000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            def fixture(route):
                path=route.request.url.split('/api/')[-1].split('?')[0]
                if path=='player':data={'player':{'id':'viewport-fixture','nickname':'기린연구원'}}
                elif path=='leaderboard':data=lobby.RANKS
                elif path=='progress':data=lobby.PROGRESS
                else:raise AssertionError('Unexpected API: '+path)
                route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
            page.route('**/api/**',fixture);page.goto(base+'?viewport-fit=1',wait_until='domcontentloaded')
            expect(page.locator('.theme-grid')).to_be_visible();page.wait_for_timeout(450)
            layouts={'main':fits(page,'.theme-lobby')}
            swipe(page,ctx,'.theme-grid');fits(page,'.theme-lobby');swipe(page,ctx,'.theme-grid',False)
            assert page.locator('.theme-grid').evaluate('e=>e.scrollLeft')>20
            page.get_by_role('button',name='햄버거 카드로 이동',exact=True).click();page.wait_for_timeout(350)
            page.screenshot(path=str(out/f'main-{w}-{h}.png'),animations='disabled')
            for theme,title in [('music','음악'),('war','전쟁'),('robot','로봇'),('burger','햄버거')]:
                page.get_by_role('button',name=title+' 카드로 이동',exact=True).click();page.wait_for_timeout(350)
                page.locator('[data-theme-select="'+theme+'"]').click();page.wait_for_timeout(350)
                layouts[theme]=fits(page,'.theme-lobby');cta=page.locator('.theme-cta').bounding_box();assert cta['y']+cta['height']<=h-3
                page.screenshot(path=str(out/f'{theme}-{w}-{h}.png'),animations='disabled')
                if theme!='burger':page.get_by_role('button',name='테마 선택으로',exact=True).click()
            expect(page.locator('[data-theme-best="burger"]')).to_have_text('21,350')
            expect(page.locator('[data-theme-collection="burger"]')).to_have_text('5 / 19')
            expect(page.locator('.theme-ranking li')).to_have_count(5)
            page.get_by_role('button',name='옵션',exact=True).click();expect(page.locator('.settings-content')).to_be_visible()
            page.get_by_role('button',name='레시피 도감',exact=False).click();expect(page.locator('.book-dialog .recipe-card')).to_have_count(19)
            grid=page.locator('.recipe-grid');assert grid.evaluate('e=>getComputedStyle(e).overflowY')=='auto'
            swipe(page,ctx,'.recipe-grid');assert grid.evaluate('e=>e.scrollTop')>5
            grid.evaluate('e=>e.scrollTop=e.scrollHeight');assert grid.evaluate('e=>e.scrollTop>e.clientHeight')
            page.screenshot(path=str(out/f'codex-scroll-{w}-{h}.png'),animations='disabled')
            page.get_by_role('button',name='닫기',exact=True).click();page.get_by_role('button',name='옵션',exact=True).click()
            page.get_by_role('button',name='게임 설명',exact=False).click();expect(page.locator('.game-help')).to_be_visible()
            assert page.locator('.game-help').evaluate('e=>getComputedStyle(e).overflowY')=='auto'
            swipe(page,ctx,'.game-help');assert page.locator('.game-help').evaluate('e=>e.scrollTop')>5
            page.get_by_role('button',name='닫기',exact=True).click();fits(page,'.theme-lobby')
            page.locator('.theme-play').click();expect(page.locator('.phone-game')).to_be_visible();page.wait_for_timeout(350)
            layouts['game']=fits(page,'.phone-game');r=page.locator('.board').bounding_box()
            assert abs(r['width']/r['height']-6/9)<.001 and r['height']>300,r
            expect(page.locator('.ingredient-tile')).to_have_count(54);swipe(page,ctx,'.phone-game');fits(page,'.phone-game')
            page.screenshot(path=str(out/f'game-{w}-{h}.png'),animations='disabled')
            page.get_by_role('button',name='메인으로',exact=True).click();expect(page.locator('.theme-play')).to_have_text('계속하기')
            fits(page,'.theme-lobby');assert not errors,errors
            report['tests'].append({'viewport':[w,h],'layouts':layouts,'verticalTouchLocked':True,'horizontalThemes':True,'codexTouchScroll':True,'helpTouchScroll':True,'all19Recipes':True,'top5Preserved':True,'all54TilesVisible':True,'continueGame':True,'errors':errors});ctx.close()
        browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--site',default='site');p.add_argument('--url');p.add_argument('--out',default='viewport-proof');a=p.parse_args();site=Path(a.site).resolve()
    if a.url:verify(a.url.rstrip('/')+'/',Path(a.out))
    else:
        spec=importlib.util.spec_from_file_location('media',SCRIPTS/'verify-game-music.py');media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)
        with tempfile.TemporaryDirectory() as root:
            os.symlink(site,Path(root)/'giralab-web',target_is_directory=True)
            server=ThreadingHTTPServer(('127.0.0.1',4188),partial(media.MediaHandler,directory=root));Thread(target=server.serve_forever,daemon=True).start()
            try:verify('http://127.0.0.1:4188/giralab-web/',Path(a.out))
            finally:server.shutdown();server.server_close()
