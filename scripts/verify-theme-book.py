from pathlib import Path as _DriverPath
_TEST_DRIVER = (_DriverPath(__file__).resolve().parents[1] / "scripts/browser-game-driver.js").read_text()
"""Exercise the unmodified HTTP game with isolated API fixtures; never write real scores."""
import argparse, importlib.util, json, os, shutil, tempfile
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright, expect

VERSION='1.7.2'
PLAYER={'id':'22222222-2222-4222-8222-222222222201','nickname':'기린연구원'}
HOOK="window.__gameTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__gameTools[t.name]=t}}});"
PROGRESS={'unlocked':['classic','cheese','green','bacon','double'],'bestScore':21350}
RANKS={'entries':[{'rank':1,'nickname':'기린연구원','score':21350,'isMe':True}],'me':{'nickname':'기린연구원','score':21350,'rank':1},'updatedAt':0}

def verify(base,out):
    out.mkdir(parents=True,exist_ok=True)
    report={'version':VERSION,'api':'isolated fixtures; no production writes','tests':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required'])
        for width,height in [(320,568),(390,844),(412,915),(1024,768)]:
            ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=width<600)
            ctx.add_init_script(_TEST_DRIVER);ctx.add_init_script(HOOK)
            page=ctx.new_page();page.set_default_timeout(15000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            state={'progress':dict(PROGRESS),'writes':0}
            def fixture(route):
                path=route.request.url.split('/api/')[-1].split('?')[0]
                if path=='account/status':
                    route.fulfill(status=200,content_type='application/json',body=json.dumps({'enabled':False,'linked':True,'player':PLAYER,'deviceState':'active','devices':1}));return
                if path=='player':data={'player':PLAYER}
                elif path=='leaderboard':data=RANKS
                elif path in ('progress','account/backup'):
                    if route.request.method=='POST':state['writes']+=1;state['progress']=route.request.post_data_json
                    data=state['progress']
                else:raise AssertionError('Unexpected API endpoint: '+path)
                route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
            page.route('**/api/**',fixture)
            page.goto(base+'?theme-book='+VERSION,wait_until='domcontentloaded')
            expect(page.locator('.home-version')).to_have_text('GiraLab · '+VERSION)
            writes_before=state['writes']
            def open_book():
                page.get_by_role('button',name='옵션',exact=True).click()
                page.locator('.settings-row').filter(has_text='레시피 도감').click()
                expect(page.locator('[role=tablist][aria-label="도감 테마 선택"]')).to_be_visible()
                expect(page.locator('[data-book-tab]')).to_have_count(4)
            def burger():
                expect(page.locator('[data-book-theme]')).to_have_attribute('data-book-theme','burger')
                expect(page.locator('.book-dialog [data-slot=dialog-title]')).to_have_text('햄버거 레시피 도감')
                expect(page.locator('.book-dialog [data-slot=dialog-description]')).to_contain_text('5 / 19 발견')
                expect(page.locator('.book-dialog .recipe-card')).to_have_count(19)
                expect(page.locator('.book-dialog .recipe-card.unlocked')).to_have_count(5)
                expect(page.locator('.recipe-card.locked .recipe-hint-toggle')).to_have_count(14)
                assert page.locator('[data-recipe-group-tier]').evaluate_all('(els)=>els.map(e=>e.dataset.recipeGroupTier)')==['normal','advanced','rare','mythic']
            open_book();burger()
            page.screenshot(path=str(out/f'book-burger-{width}.png'))
            for theme,title,collection in [('music','음악','화음'),('war','전쟁','전략'),('robot','로봇','설계도')]:
                page.locator('[data-book-tab='+theme+']').click()
                expect(page.locator('[data-book-theme]')).to_have_attribute('data-book-theme',theme)
                expect(page.locator('[data-book-tab='+theme+']')).to_have_attribute('aria-selected','true')
                expect(page.locator('.book-dialog [data-slot=dialog-title]')).to_have_text(title+' '+collection+' 도감')
                expect(page.locator('.theme-book-preview')).to_contain_text('출시 준비 중')
                expect(page.locator('.theme-book-preview')).to_contain_text('출시예정')
                expect(page.locator('.recipe-card')).to_have_count(0)
                expect(page.locator('.recipe-hint-toggle')).to_have_count(0)
                expect(page.locator('.book-save-status')).to_have_count(0)
                text=page.locator('.book-dialog').inner_text()
                assert '21,350' not in text and '5 / 19' not in text and '아직 모르는 맛' not in text,text
                assert page.locator('.book-dialog').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1'),'dialog horizontal overflow'
                expect(page.get_by_role('button',name='닫기',exact=True)).to_be_in_viewport()
                page.screenshot(path=str(out/f'book-{theme}-{width}.png'))
                page.locator('.theme-book-preview').evaluate('(el)=>el.scrollTop=el.scrollHeight')
                expect(page.locator('.theme-book-preview footer')).to_be_in_viewport()
            page.locator('[data-book-tab=burger]').click();burger()
            hint=page.locator('.recipe-card.locked .recipe-hint-toggle').first
            hint.click();expect(hint).to_have_attribute('aria-expanded','true')
            page.locator('[data-book-tab=music]').click()
            page.locator('[data-book-tab=burger]').click();burger()
            page.locator('[data-book-tab=burger]').focus()
            page.keyboard.press('End');expect(page.locator('[data-book-tab=robot]')).to_be_focused()
            page.keyboard.press('ArrowRight');expect(page.locator('[data-book-tab=burger]')).to_be_focused()
            page.keyboard.press('ArrowLeft');expect(page.locator('[data-book-tab=robot]')).to_be_focused()
            page.keyboard.press('Home');expect(page.locator('[data-book-tab=burger]')).to_be_focused();burger()
            page.locator('.options-back').click()
            expect(page.locator('.settings-dialog')).to_be_visible()
            page.get_by_role('button',name='닫기',exact=True).click()
            expect(page.locator('.theme-lobby')).to_have_attribute('data-theme','all')
            assert state['writes']==writes_before,'Browsing the codex must not save progress'
            page.get_by_role('button',name='음악 테마 선택',exact=True).click();open_book()
            expect(page.locator('[data-book-theme]')).to_have_attribute('data-book-theme','music')
            page.locator('[data-book-tab=war]').click()
            page.get_by_role('button',name='닫기',exact=True).click()
            expect(page.locator('.theme-lobby')).to_have_attribute('data-theme','music')
            page.get_by_role('button',name='테마 선택으로',exact=True).click()
            page.get_by_role('button',name='햄버거 테마 선택',exact=True).click()
            expect(page.locator('[data-theme-best=burger]')).to_have_text('21,350')
            expect(page.locator('[data-theme-collection=burger]')).to_have_text('5 / 19')
            page.locator('.home-play').click()
            expect(page.locator('[data-tile-id]')).to_have_count(54)
            open_book();burger()
            frozen=page.evaluate('window.__gameTools.get_game_state.execute({})')
            assert frozen['status']=='paused',frozen
            page.locator('[data-book-tab=war]').click();page.wait_for_timeout(350)
            after=page.evaluate('window.__gameTools.get_game_state.execute({})')
            for field in ['status','board','elapsed','danger','score','combo','slow','unlocked']:
                assert after[field]==frozen[field],('Game changed while browsing',field)
            page.evaluate('window.dispatchEvent(new Event("burger-native-back"))')
            expect(page.locator('.settings-dialog')).to_be_visible()
            page.get_by_role('button',name='닫기',exact=True).click()
            assert page.evaluate('window.__gameTools.get_game_state.execute({}).status')=='playing'
            expect(page.locator('[data-tile-id]')).to_have_count(54)
            assert not errors,errors
            report['tests'].append({'viewport':[width,height],'tabs':4,'burgerCards':19,'knownCards':5,'lockedHints':14,'themeIsolation':True,'noCheckout':True,'noProgressWritesForBrowsing':True,'contextDefault':True,'keyboard':True,'nativeBack':True,'scrollAndClose':True,'pausedBoardPreserved':True,'resume':True,'errors':errors})
            ctx.close()
        browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--site',default='pages-dist');p.add_argument('--url');p.add_argument('--out',default='theme-book-proof');a=p.parse_args()
    if a.url:verify(a.url.rstrip('/')+'/',Path(a.out))
    else:
        spec=importlib.util.spec_from_file_location('media',Path(__file__).with_name('verify-game-music.py'));media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)
        with tempfile.TemporaryDirectory() as root:
            os.symlink(Path(a.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
            server=ThreadingHTTPServer(('127.0.0.1',4187),partial(media.MediaHandler,directory=root));Thread(target=server.serve_forever,daemon=True).start()
            try:verify('http://127.0.0.1:4187/giralab-web/',Path(a.out))
            finally:server.shutdown();server.server_close()
