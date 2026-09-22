from pathlib import Path as _DriverPath
_TEST_DRIVER = (_DriverPath(__file__).resolve().parents[1] / "scripts/browser-game-driver.js").read_text()
"""Browser verification for the scoped options/help change. All game API calls are fixtures."""
import argparse, json, os, re, shutil, tempfile
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

HOOK="window.__gameTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__gameTools[t.name]=t}}});"
PROGRESS={'unlocked':['classic','cheese','green','bacon','double'],'bestScore':21350}
PLAYER={'id':'00000000-0000-0000-0000-000000000601','nickname':'기린연구원'}
RANKS={'entries':[{'rank':1,'nickname':'기린연구원','score':21350,'isMe':True}],'me':{'nickname':'기린연구원','score':21350,'rank':1},'updatedAt':0}

class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def verify(base,out):
    out.mkdir(parents=True,exist_ok=True)
    report={'api':'isolated fixtures; no production reads or writes','tests':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required'])
        for width,height in [(320,568),(390,664),(390,844),(412,915),(844,390),(1024,768)]:
            ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<900,has_touch=width<900)
            ctx.add_init_script(_TEST_DRIVER);ctx.add_init_script(HOOK)
            page=ctx.new_page();page.set_default_timeout(20000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            request_failures=[];response_errors=[]
            def resource_url(url):
                parsed=urlsplit(url)
                return f'{parsed.scheme}://{parsed.hostname or ""}{parsed.path}'
            page.on('requestfailed',lambda request:request_failures.append({'url':resource_url(request.url),'error':str(request.failure)[:300]}) if len(request_failures)<30 else None)
            page.on('response',lambda response:response_errors.append({'url':resource_url(response.url),'status':response.status}) if response.status>=400 and len(response_errors)<30 else None)
            state={'progress':dict(PROGRESS),'writes':0}
            def fixture(route):
                path=route.request.url.split('/api/')[-1].split('?')[0]
                if path=='account/status':
                    route.fulfill(status=200,content_type='application/json',body=json.dumps({'enabled':False,'linked':True,'player':PLAYER,'deviceState':'active','devices':1}));return
                if path=='player':data={'player':PLAYER}
                elif path=='leaderboard':data=RANKS
                elif path in ('progress','account/backup'):
                    if route.request.method=='POST':
                        state['writes']+=1
                        posted=route.request.post_data_json
                        state['progress']={'bestScore':max(state['progress']['bestScore'],posted['bestScore']),'unlocked':list(dict.fromkeys(state['progress']['unlocked']+posted['unlocked']))}
                    data=state['progress']
                else:raise AssertionError('Unexpected API endpoint: '+path)
                route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
            page.route('**/api/**',fixture)
            try:
                page.goto(base+'?theme-help-check=1',wait_until='domcontentloaded')
                # The app allows image loading for 15s; expect has its own 5s default.
                expect(page.locator('.home-version')).to_have_text('GiraLab · 1.7.2',timeout=20000)
            except Exception as error:
                diagnostic={'viewport':[width,height],'url':resource_url(page.url),'error':str(error)[:3000],
                    'pageErrors':errors[:30],'requestFailures':request_failures,'responseErrors':response_errors}
                try:
                    diagnostic.update(page.evaluate('''() => {
                        const splash=document.querySelector('.giralab-boot');
                        return {bodyText:document.body?.innerText.slice(0,8000) ?? '',
                            splash:splash ? {text:splash.innerText.slice(0,2000),busy:splash.getAttribute('aria-busy'),
                                progress:splash.querySelector('[role="progressbar"]')?.getAttribute('aria-valuenow')} : null};
                    }'''))
                except Exception as capture_error:diagnostic['snapshotError']=str(capture_error)[:500]
                try:page.screenshot(path=str(out/f'boot-failure-{width}x{height}.png'),timeout=5000)
                except Exception as capture_error:diagnostic['screenshotError']=str(capture_error)[:500]
                failure_path=out/f'boot-failure-{width}x{height}.json'
                failure_path.write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2)+'\n')
                print('BOOT_FAILURE',failure_path,flush=True)
                raise
            expect(page.locator('.theme-lobby')).to_have_attribute('data-lobby-revision','dashboard-20260919')
            expect(page.locator('.theme-carousel-controls, .theme-lobby-note')).to_have_count(0)
            assert '옆으로 넘겨보세요' not in page.locator('.theme-lobby').inner_text()
            assert '같은 연결' not in page.locator('.theme-lobby').inner_text()
            welcome=page.locator('.theme-welcome').bounding_box();heading=page.locator('.theme-section-heading').bounding_box()
            assert heading['y']-(welcome['y']+welcome['height'])>=0,(welcome,heading)
            page.screenshot(path=str(out/f'measured-main-{width}x{height}.png'))
            print('LOBBY_METRICS',width,height,page.locator('.theme-lobby').evaluate('(e)=>({h:e.clientHeight,sh:e.scrollHeight})'),flush=True)
            assert page.locator('.theme-lobby').evaluate('(e)=>e.scrollHeight<=e.clientHeight+1'),f'Lobby inner overflow {width}x{height}'
            page.screenshot(path=str(out/f'clean-main-{width}x{height}.png'))
            rail=page.locator('.theme-grid')
            page.locator('[data-theme-select=burger]').focus()
            for key,theme in [('End','robot'),('Home','burger')]:
                page.keyboard.press(key)
                expect(page.locator('[data-theme-select='+theme+']')).to_be_focused()
                page.wait_for_timeout(400)
            if width<900:
                box=rail.bounding_box();cdp=ctx.new_cdp_session(page)
                x=box['x']+box['width']*.85;y=box['y']+box['height']*.6
                cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
                for i in range(1,9):
                    cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-i*box['width']*.075,'y':y}]})
                cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                page.wait_for_timeout(500)
                assert rail.evaluate('(e)=>e.scrollLeft')>20,'Horizontal swipe was lost'
                cdp.detach()
            page.locator('[data-theme-select=burger]').focus()
            page.keyboard.press('Home');page.wait_for_timeout(400)
            writes_before=state['writes']
            def open_settings():
                page.get_by_role('button',name='옵션',exact=True).click()
                expect(page.locator('.settings-dialog')).to_be_visible()
                expect(page.locator('.settings-dialog').get_by_role('button',name=re.compile('새 게임'))).to_have_count(0)
                expect(page.locator('.sound-setting')).to_be_visible()
            def open_help():
                open_settings()
                page.locator('.settings-row').filter(has_text='게임 설명').click()
                expect(page.get_by_role('tablist',name='게임 설명 테마 선택')).to_be_visible()
                expect(page.locator('[data-help-tab]')).to_have_count(4)
            def fit():
                assert page.evaluate('document.scrollingElement.scrollHeight<=innerHeight+1'),'Page has vertical overflow'
                assert page.evaluate('document.scrollingElement.scrollWidth<=innerWidth+1'),'Page has horizontal overflow'
            fit();open_help()
            expect(page.locator('[data-help-theme]')).to_have_attribute('data-help-theme','burger')
            expect(page.locator('[data-rules-guide]')).to_have_count(1)
            expect(page.locator('[data-guide-section]')).to_have_count(6)
            expect(page.locator('[data-guide-section=score]')).to_contain_text('5초')
            page.screenshot(path=str(out/f'help-burger-{width}x{height}.png'))
            for theme,text in [('burger','점수 계산과 콤보'),('music','화음'),('war','핵의 화면 전체 효과'),('robot','서로 다른 로봇')]:
                page.locator('[data-help-tab='+theme+']').click()
                expect(page.locator('[data-help-theme]')).to_have_attribute('data-help-theme',theme)
                expect(page.locator('[data-help-tab='+theme+']')).to_have_attribute('aria-selected','true')
                expect(page.locator('.game-help')).to_contain_text(text)
                expect(page.locator('[data-rules-guide]')).to_have_count(1 if theme=='burger' else 0)
                if theme!='burger':expect(page.locator('.game-help')).to_contain_text('출시 준비 중')
                metrics=page.locator('.game-help').evaluate('(e)=>({h:e.clientHeight,sh:e.scrollHeight,overflow:getComputedStyle(e).overflowY,touch:getComputedStyle(e).touchAction})')
                assert metrics['h']>50,metrics
                assert metrics['overflow']=='auto' and 'pan-y' in metrics['touch'],metrics
                assert page.locator('.help-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1'),'Help horizontal overflow'
                page.locator('.game-help').evaluate('(e)=>e.scrollTop=e.scrollHeight')
                expect(page.get_by_role('button',name='알겠어요',exact=True)).to_be_in_viewport()
                expect(page.get_by_role('tablist',name='게임 설명 테마 선택')).to_be_in_viewport()
                expect(page.get_by_role('button',name='닫기',exact=True)).to_be_in_viewport()
                page.locator('.game-help').evaluate('(e)=>e.scrollTop=0')
                if theme!='burger':page.screenshot(path=str(out/f'help-{theme}-{width}x{height}.png'))
            page.locator('[data-help-tab=burger]').click()
            scroll=page.locator('.game-help')
            bounds=scroll.bounding_box()
            if width<900 and bounds and bounds['height']>100:
                cdp=ctx.new_cdp_session(page)
                x=bounds['x']+bounds['width']/2;y=bounds['y']+bounds['height']*.8
                cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
                for step in range(1,7):
                    cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-step*min(25,bounds['height']/12)}]})
                cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                page.wait_for_timeout(200)
                assert scroll.evaluate('(e)=>e.scrollTop')>0,'Help touch scrolling was blocked'
                cdp.detach()
            page.locator('[data-help-tab=burger]').focus()
            for key,theme in [('End','robot'),('ArrowRight','burger'),('ArrowLeft','robot'),('Home','burger')]:
                page.keyboard.press(key)
                expect(page.locator('[data-help-tab='+theme+']')).to_be_focused()
                expect(page.locator('[data-help-theme]')).to_have_attribute('data-help-theme',theme)
            expect(page.locator('.game-help')).to_have_js_property('scrollTop',0)
            scroll.evaluate('(e)=>e.scrollTop=e.scrollHeight')
            page.get_by_role('button',name='알겠어요',exact=True).click()
            expect(page.locator('.settings-dialog')).to_be_visible()
            page.screenshot(path=str(out/f'options-{width}x{height}.png'))
            page.locator('.settings-row').filter(has_text='레시피 도감').click()
            expect(page.locator('[data-book-tab]')).to_have_count(4)
            expect(page.locator('.recipe-card')).to_have_count(19)
            page.locator('[data-book-tab=robot]').click()
            expect(page.locator('[data-book-theme]')).to_have_attribute('data-book-theme','robot')
            page.locator('.options-back').click()
            page.locator('.settings-row').filter(has_text='게임 설명').click()
            expect(page.locator('[data-help-theme]')).to_have_attribute('data-help-theme','burger')
            page.get_by_role('button',name='닫기',exact=True).click()
            expect(page.locator('.theme-lobby')).to_have_attribute('data-theme','all')
            fit();assert state['writes']==writes_before,'Help browsing saved progress'
            page.get_by_role('button',name='음악 테마 선택',exact=True).click()
            open_help()
            expect(page.locator('[data-help-theme]')).to_have_attribute('data-help-theme','music')
            page.locator('[data-help-tab=war]').click()
            page.get_by_role('button',name='닫기',exact=True).click()
            expect(page.locator('.theme-lobby')).to_have_attribute('data-theme','music')
            page.get_by_role('button',name='테마 선택으로',exact=True).click()
            page.get_by_role('button',name='햄버거 테마 선택',exact=True).click()
            expect(page.locator('[data-theme-best=burger]')).to_have_text('21,350')
            expect(page.locator('[data-theme-collection=burger]')).to_have_text('5 / 19')
            expect(page.locator('.home-play svg')).to_have_count(0)
            expect(page.locator('.home-play')).to_have_text('게임 시작')
            page.screenshot(path=str(out/f'clean-burger-{width}x{height}.png'))
            page.locator('.home-play').click()
            expect(page.locator('[data-tile-id]')).to_have_count(54)
            fit();open_help()
            frozen=page.evaluate('window.__gameTools.get_game_state.execute({})')
            assert frozen['status']=='paused',frozen
            expect(page.locator('[data-help-theme]')).to_have_attribute('data-help-theme','burger')
            for theme in ['music','war','robot','burger']:page.locator('[data-help-tab='+theme+']').click()
            page.wait_for_timeout(250)
            after=page.evaluate('window.__gameTools.get_game_state.execute({})')
            for field in ['status','board','elapsed','danger','score','combo','slow','unlocked']:
                assert after[field]==frozen[field],('Game changed while browsing help',field)
            page.evaluate('window.dispatchEvent(new Event("burger-native-back"))')
            expect(page.locator('.settings-dialog')).to_be_visible()
            expect(page.locator('.settings-dialog').get_by_role('button',name=re.compile('새 게임'))).to_have_count(0)
            page.get_by_role('button',name='닫기',exact=True).click()
            assert page.evaluate('window.__gameTools.get_game_state.execute({}).status')=='playing'
            expect(page.locator('[data-tile-id]')).to_have_count(54)
            page.get_by_role('button',name='메인으로',exact=True).click()
            expect(page.get_by_role('heading',name='메인으로 돌아갈까요?',exact=True)).to_be_visible()
            page.get_by_role('button',name='돌아가기',exact=True).click()
            expect(page.locator('.home-play')).to_have_text('계속하기')
            expect(page.locator('.home-play svg')).to_have_count(0)
            page.screenshot(path=str(out/f'clean-continue-{width}x{height}.png'))
            fit();assert not errors,errors
            report['tests'].append({'viewport':[width,height],'noSettingsRestart':True,'tabs':4,'burgerGuideUnchanged':True,'upcomingLabels':True,'contextDefault':True,'keyboard':True,'bodyScrollAndFixedTabs':True,'mainGameFit':True,'bookIntact':True,'noBrowsingWrites':True,'pauseResume':True,'errors':errors})
            ctx.close()
        browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--site',default='pages-dist');p.add_argument('--url');p.add_argument('--out',default='theme-help-proof');a=p.parse_args()
    if a.url:verify(a.url.rstrip('/')+'/',Path(a.out))
    else:
        with tempfile.TemporaryDirectory() as root:
            os.symlink(Path(a.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
            server=ThreadingHTTPServer(('127.0.0.1',4189),partial(Handler,directory=root));Thread(target=server.serve_forever,daemon=True).start()
            try:verify('http://127.0.0.1:4189/giralab-web/',Path(a.out))
            finally:server.shutdown();server.server_close()
