from pathlib import Path as _DriverPath
_TEST_DRIVER = (_DriverPath(__file__).resolve().parents[1] / "scripts/browser-game-driver.js").read_text()
"""Verify help/options against an isolated API on both the candidate and live site."""
import argparse,importlib.util,json,os,re,shutil,tempfile
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright,expect

spec=importlib.util.spec_from_file_location('book',Path(__file__).resolve().parents[1]/'scripts/verify-theme-book.py')
book=importlib.util.module_from_spec(spec);spec.loader.exec_module(book)
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def verify(base,out):
    out.mkdir(parents=True,exist_ok=True)
    report={'api':'isolated fixture; no production writes','tests':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required'])
        for w,h in [(320,568),(390,664),(390,844),(412,915),(844,390),(1024,768)]:
            ctx=browser.new_context(viewport={'width':w,'height':h},is_mobile=w<900,has_touch=w<900)
            ctx.add_init_script(_TEST_DRIVER);ctx.add_init_script(book.HOOK);page=ctx.new_page();page.set_default_timeout(20000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            state={'writes':0,'progress':dict(book.PROGRESS)}
            def fixture(route):
                endpoint=route.request.url.split('/api/')[-1].split('?')[0]
                if endpoint=='player':data={'player':{'id':'theme-help-live-test','nickname':'기린연구원'}}
                elif endpoint=='leaderboard':data=book.RANKS
                elif endpoint=='progress':
                    if route.request.method=='POST':state['writes']+=1;state['progress']=route.request.post_data_json
                    data=state['progress']
                else:raise AssertionError(endpoint)
                route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
            page.route('**/api/**',fixture)
            page.goto(base+'?theme-help-verified=1',wait_until='domcontentloaded')
            expect(page.locator('.home-version')).to_have_text('GiraLab · 1.7.2')
            before=state['writes']
            def open_help():
                page.get_by_role('button',name='옵션',exact=True).click()
                expect(page.locator('.settings-dialog').get_by_role('button',name=re.compile('새 게임'))).to_have_count(0)
                page.locator('.settings-row').filter(has_text='게임 설명').click()
                expect(page.get_by_role('tablist',name='게임 설명 테마 선택')).to_be_visible()
                expect(page.locator('[data-help-tab]')).to_have_count(4)
            def fit():
                assert page.evaluate('document.scrollingElement.scrollHeight<=innerHeight+1'),'vertical page overflow'
            fit();open_help()
            expect(page.locator('[data-help-theme]')).to_have_attribute('data-help-theme','burger')
            expect(page.locator('[data-guide-section]')).to_have_count(6)
            for theme in ['burger','music','war','robot']:
                page.locator('[data-help-tab='+theme+']').click()
                expect(page.locator('[data-help-theme]')).to_have_attribute('data-help-theme',theme)
                expect(page.locator('[data-help-tab='+theme+']')).to_have_attribute('aria-selected','true')
                expect(page.locator('[data-rules-guide]')).to_have_count(1 if theme=='burger' else 0)
                if theme!='burger':expect(page.locator('.game-help')).to_contain_text('출시 준비 중')
                assert page.locator('.game-help').evaluate('(e)=>e.clientHeight>50 && getComputedStyle(e).overflowY==="auto" && getComputedStyle(e).touchAction.includes("pan-y")')
                assert page.locator('.help-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
                page.screenshot(path=str(out/f'help-{theme}-{w}x{h}.png'))
                page.locator('.game-help').evaluate('(e)=>e.scrollTop=e.scrollHeight')
                expect(page.get_by_role('button',name='알겠어요',exact=True)).to_be_in_viewport()
                expect(page.get_by_role('tablist',name='게임 설명 테마 선택')).to_be_in_viewport()
                expect(page.get_by_role('button',name='닫기',exact=True)).to_be_in_viewport()
            page.locator('[data-help-tab=burger]').focus()
            for key,theme in [('End','robot'),('ArrowRight','burger'),('ArrowLeft','robot'),('Home','burger')]:
                page.keyboard.press(key);expect(page.locator('[data-help-tab='+theme+']')).to_be_focused()
            page.locator('.game-help').evaluate('(e)=>e.scrollTop=e.scrollHeight')
            page.get_by_role('button',name='알겠어요',exact=True).click()
            expect(page.locator('.settings-dialog')).to_be_visible()
            page.screenshot(path=str(out/f'options-{w}x{h}.png'))
            page.locator('.settings-row').filter(has_text='레시피 도감').click()
            expect(page.locator('.recipe-card')).to_have_count(19)
            expect(page.locator('[data-book-tab]')).to_have_count(4)
            page.get_by_role('button',name='닫기',exact=True).click()
            assert state['writes']==before
            page.get_by_role('button',name='음악 테마 선택',exact=True).click();open_help()
            expect(page.locator('[data-help-theme]')).to_have_attribute('data-help-theme','music')
            page.locator('[data-help-tab=robot]').click()
            page.get_by_role('button',name='닫기',exact=True).click()
            expect(page.locator('.theme-lobby')).to_have_attribute('data-theme','music')
            page.get_by_role('button',name='테마 선택으로',exact=True).click()
            page.get_by_role('button',name='햄버거 테마 선택',exact=True).click()
            expect(page.locator('[data-theme-best=burger]')).to_have_text('21,350')
            expect(page.locator('[data-theme-collection=burger]')).to_have_text('5 / 19')
            page.locator('.home-play').click();expect(page.locator('[data-tile-id]')).to_have_count(54)
            fit();open_help()
            frozen=page.evaluate('window.__gameTools.get_game_state.execute({})');assert frozen['status']=='paused'
            expect(page.locator('[data-help-theme]')).to_have_attribute('data-help-theme','burger')
            for theme in ['music','war','robot','burger']:page.locator('[data-help-tab='+theme+']').click()
            page.wait_for_timeout(200)
            after=page.evaluate('window.__gameTools.get_game_state.execute({})')
            for key in ['status','board','elapsed','danger','score','combo','slow','unlocked']:assert after[key]==frozen[key],key
            page.evaluate('window.dispatchEvent(new Event("burger-native-back"))')
            expect(page.locator('.settings-dialog')).to_be_visible()
            page.get_by_role('button',name='닫기',exact=True).click()
            assert page.evaluate('window.__gameTools.get_game_state.execute({}).status')=='playing'
            fit();assert not errors,errors
            report['tests'].append({'viewport':[w,h],'settingsRestartRemoved':True,'helpTabs':4,'burgerGuidePreserved':True,'upcomingLabels':True,'scrollAndClose':True,'keyboard':True,'contextAndRecordIsolation':True,'pauseResume':True,'mainGameFit':True,'errors':errors})
            ctx.close()
        browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--site',default='site');p.add_argument('--url');p.add_argument('--out',default='theme-help-proof');a=p.parse_args()
    if a.url:verify(a.url.rstrip('/')+'/',Path(a.out))
    else:
        with tempfile.TemporaryDirectory() as root:
            os.symlink(Path(a.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
            server=ThreadingHTTPServer(('127.0.0.1',4191),partial(Handler,directory=root));Thread(target=server.serve_forever,daemon=True).start()
            try:verify('http://127.0.0.1:4191/giralab-web/',Path(a.out))
            finally:server.shutdown();server.server_close()
