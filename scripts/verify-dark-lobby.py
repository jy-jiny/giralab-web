"""Dark carousel checks with isolated player API; never writes production records."""
import argparse, importlib.util, json, os, shutil, tempfile
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright, expect

VERSION='1.7.2'
spec=importlib.util.spec_from_file_location('lobby',Path(__file__).with_name('verify-theme-lobby.py'))
lobby=importlib.util.module_from_spec(spec);spec.loader.exec_module(lobby)

def verify(base,out,site=None,memory=False,widths=None):
    out.mkdir(parents=True,exist_ok=True)
    report={'version':VERSION,'api':'isolated fixtures, no production records','mode':'in-memory bundle with static data URLs' if memory else 'unmodified HTTP build','tests':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required'])
        for width,height in [(320,568),(390,844),(412,915),(1024,768)]:
            if widths and width not in widths:continue
            ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=True)
            ctx.add_init_script(lobby.HOOK)
            page=ctx.new_page();page.set_default_timeout(10000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            state={'writes':0}
            def fixture(route):
                path=route.request.url.split('/api/')[-1].split('?')[0]
                if path=='account/status':
                    route.fulfill(status=200,content_type='application/json',body=json.dumps({'enabled':False,'linked':False,'player':None,'deviceState':'active','devices':1}));return
                if path=='player':data={'player':{'id':'dark-carousel-fixture','nickname':'기린연구원'}}
                elif path=='leaderboard':data=lobby.RANKS
                elif path=='progress':
                    if route.request.method=='POST':state['writes']+=1
                    data=lobby.PROGRESS
                else:raise AssertionError('Unexpected API: '+path)
                route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
            page.route('**/api/**',fixture)
            if memory:lobby.memory_load(page,site)
            else:page.goto(base+'?dark-lobby='+VERSION,wait_until='domcontentloaded')
            expect(page.locator('.theme-grid')).to_be_visible()
            expect(page.locator('.theme-lobby')).to_have_attribute('data-lobby-version',VERSION)
            expect(page.locator('.home-version')).to_have_text('GiraLab · '+VERSION)
            expect(page.locator('.theme-carousel-count')).to_have_text('1 / 4')
            rail=page.locator('.theme-grid')
            layout=rail.evaluate('''el=>({overflow:el.scrollWidth>el.clientWidth,snap:getComputedStyle(el).scrollSnapType,tops:[...el.children].map(c=>c.offsetTop),background:getComputedStyle(el.closest('.theme-lobby')).backgroundColor,pageWidth:document.documentElement.scrollWidth,viewport:innerWidth})''')
            assert layout['overflow'] and layout['snap']=='x mandatory',layout
            assert len(set(layout['tops']))==1 and layout['pageWidth']<=layout['viewport'],layout
            assert layout['background']=='rgb(23, 30, 32)',layout
            expect(page.get_by_role('button',name='이전 테마',exact=True)).to_be_disabled()
            page.screenshot(path=str(out/f'select-{width}.png'),animations='disabled')
            # A real touch pan changes the visible card without opening its detail.
            box=rail.bounding_box();x=min(box['x']+box['width']-40,width-30);y=min(box['y']+120,height-60)
            session=ctx.new_cdp_session(page)
            session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
            for step in range(1,11):
                session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-step*19,'y':y}]})
                page.wait_for_timeout(25)
            session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
            page.wait_for_timeout(650)
            assert rail.evaluate('e=>e.scrollLeft')>40,'Touch swipe did not move carousel'
            expect(page.locator('.theme-lobby')).to_have_attribute('data-theme','all')
            page.get_by_role('button',name='음악 카드로 이동',exact=True).click()
            expect(page.locator('.theme-carousel-count')).to_have_text('2 / 4')
            page.wait_for_timeout(450)
            page.screenshot(path=str(out/f'scroll-music-{width}.png'),animations='disabled')
            page.get_by_role('button',name='다음 테마',exact=True).click();page.wait_for_timeout(450)
            expect(page.locator('.theme-carousel-count')).to_have_text('3 / 4')
            page.get_by_role('button',name='다음 테마',exact=True).click();page.wait_for_timeout(450)
            expect(page.locator('.theme-carousel-count')).to_have_text('4 / 4')
            expect(page.get_by_role('button',name='다음 테마',exact=True)).to_be_disabled()
            robot=page.locator('[data-theme-select="robot"]');robot.click()
            expect(page.locator('[data-theme-best="robot"]')).to_have_text('—')
            expect(page.locator('.theme-locked-action')).to_be_disabled()
            assert page.locator('.theme-lobby').evaluate("e=>getComputedStyle(e).backgroundColor")=='rgb(23, 30, 32)'
            page.get_by_role('button',name='테마 선택으로',exact=True).click()
            expect(robot).to_be_focused();expect(page.locator('.theme-carousel-count')).to_have_text('4 / 4')
            rb=robot.bounding_box();fb=rail.bounding_box()
            assert rb["x"]>=fb["x"]-2 and rb["x"]+rb["width"]<=fb["x"]+fb["width"]+2,"Restored card clipped horizontally"
            robot.scroll_into_view_if_needed()
            expect(robot).to_be_in_viewport(ratio=.98)
            robot.press('Home');page.wait_for_timeout(450)
            burger=page.locator('[data-theme-select="burger"]');expect(burger).to_be_focused()
            expect(page.locator('.theme-carousel-count')).to_have_text('1 / 4')
            burger.press('ArrowRight');page.wait_for_timeout(450)
            expect(page.locator('[data-theme-select="music"]')).to_be_focused()
            page.keyboard.press('End');page.wait_for_timeout(450)
            expect(robot).to_be_focused()
            page.emulate_media(reduced_motion='reduce')
            robot.press('Home');expect(burger).to_be_focused()
            expect(page.locator('.theme-carousel-count')).to_have_text('1 / 4')
            assert rail.evaluate('e=>e.scrollLeft')==0
            burger.press('Enter')
            expect(page.locator('[data-theme-best="burger"]')).to_have_text('21,350')
            expect(page.locator('[data-theme-collection="burger"]')).to_have_text('5 / 19')
            page.screenshot(path=str(out/f'burger-{width}.png'),animations='disabled')
            # Preserve options' independent theme tabs and 19 real burger recipes.
            page.get_by_role('button',name='햄버거 레시피 도감 보기',exact=True).click()
            expect(page.locator('.book-dialog .recipe-card')).to_have_count(19)
            page.locator('[data-book-tab="music"]').click()
            expect(page.locator('[data-book-theme]')).to_have_attribute('data-book-theme','music')
            page.get_by_role('button',name='닫기',exact=True).click()
            expect(page.locator('.theme-lobby')).to_have_attribute('data-theme','burger')
            assert not errors,errors
            report['tests'].append({'viewport':[width,height],'darkPalette':True,'oneRowOverflow':True,'touchSwipe':True,'noAccidentalOpen':True,'arrowsAndDots':True,'keyboard':True,'reducedMotion':True,'returnPositionAndFocus':True,'realRecords':True,'themeBookPreserved':True,'noDocumentOverflow':True,'errors':errors})
            ctx.close()
        browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--site',default='pages-dist');p.add_argument('--url');p.add_argument('--out',default='dark-lobby-proof');p.add_argument('--memory',action='store_true');p.add_argument('--width',type=int,action='append');a=p.parse_args();site=Path(a.site).resolve()
    if a.memory:verify('',Path(a.out),site,True,a.width)
    elif a.url:verify(a.url.rstrip('/')+'/',Path(a.out),widths=a.width)
    else:
        spec=importlib.util.spec_from_file_location('media',Path(__file__).with_name('verify-game-music.py'));media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)
        with tempfile.TemporaryDirectory() as root:
            os.symlink(site,Path(root)/'giralab-web',target_is_directory=True)
            server=ThreadingHTTPServer(('127.0.0.1',4187),partial(media.MediaHandler,directory=root));Thread(target=server.serve_forever,daemon=True).start()
            try:verify('http://127.0.0.1:4187/giralab-web/',Path(a.out),site,widths=a.width)
            finally:server.shutdown();server.server_close()
