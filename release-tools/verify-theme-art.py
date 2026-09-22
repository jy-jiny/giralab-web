"""Verify theme artwork with isolated API fixtures; never modify production records."""
import argparse, json, os, re, shutil, tempfile
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright, expect

REVISION = 'glossy-20260919'
RANKS = {'entries': [{'rank': 1, 'nickname': '테스트연구원', 'score': 21350, 'isMe': True}], 'me': {'nickname': '테스트연구원', 'score': 21350, 'rank': 1}, 'updatedAt': 0}
NEUTRAL = '.theme-lobby .theme-art:is(.theme-art-music,.theme-art-war,.theme-art-robot)::after{display:none!important}.theme-lobby .theme-art:is(.theme-art-music,.theme-art-war,.theme-art-robot)>:not(.theme-orbit){visibility:visible!important}'
class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

def verify(base, out):
    out.mkdir(parents=True, exist_ok=True)
    report = {'revision': REVISION, 'api': 'isolated fixtures; no production API traffic', 'tests': []}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'), args=['--no-sandbox', '--disable-dev-shm-usage', '--autoplay-policy=no-user-gesture-required'])
        for width, height in [(320, 568), (390, 664), (390, 844), (844, 390)]:
            ctx = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=True, has_touch=True)
            page = ctx.new_page(); page.set_default_timeout(25000)
            errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
            writes = []
            def fixture(route):
                path = route.request.url.split('/api/')[-1].split('?')[0]
                if path=='account/status':
                    route.fulfill(status=200,content_type='application/json',body=json.dumps({'enabled':False,'linked':False,'player':None,'deviceState':'active','devices':1}));return
                if route.request.method != 'GET': writes.append(path)
                if path == 'player': data = {'player': {'id': 'theme-art-fixture', 'nickname': '테스트연구원'}}
                elif path == 'leaderboard': data = RANKS
                elif path == 'progress': data = {'unlocked': ['classic', 'cheese', 'green', 'bacon', 'double'], 'bestScore': 21350}
                else: raise AssertionError('Unexpected API endpoint: ' + path)
                route.fulfill(status=200, content_type='application/json', body=json.dumps(data))
            page.route('**/api/**', fixture)
            page.goto(base + '?theme-art-check=' + REVISION, wait_until='domcontentloaded')
            expect(page.locator('.theme-lobby')).to_have_attribute('data-theme', 'all')
            page.evaluate('document.fonts.ready')
            expect(page.locator('.theme-carousel-controls, .theme-lobby-note')).to_have_count(0)
            assert '옆으로 넘겨보세요' not in page.locator('.theme-lobby').inner_text()
            assert page.evaluate('document.scrollingElement.scrollHeight <= innerHeight + 1')
            assert page.locator('.theme-lobby').evaluate('(e)=>e.scrollHeight<=e.clientHeight+1')
            selectors = ['.theme-welcome', '.theme-section-heading', '.theme-grid', '.theme-card', '.theme-art']
            def geometry(ss):
                return page.evaluate('(ss)=>ss.flatMap(s=>Array.from(document.querySelectorAll(s),e=>{const r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height]}))', ss)
            # Screenshot waits for the existing slide-in animation to settle.
            # Measure after that wait, not while the whole lobby is still moving.
            burger = page.locator('.theme-burger-sprite').screenshot()
            before = geometry(selectors)
            neutral = page.add_style_tag(content=NEUTRAL)
            assert before == geometry(selectors), ('Artwork affected layout geometry', before, geometry(selectors))
            assert burger == page.locator('.theme-burger-sprite').screenshot(), 'Burger artwork changed'
            neutral.evaluate('(e)=>e.remove()')
            initial_writes = len(writes)
            page.screenshot(path=str(out/f'main-burger-{width}x{height}.png'))
            detail_metrics = {}
            for theme in ['music', 'war', 'robot']:
                card = page.locator('[data-theme-select=' + theme + ']')
                card.scroll_into_view_if_needed(); page.wait_for_timeout(300)
                art = card.locator('.theme-art-' + theme)
                bg = art.evaluate('(e)=>getComputedStyle(e,"::after").backgroundImage')
                assert theme + '-' + REVISION + '.webp' in bg, bg
                url = re.search(r'url\([\"\']?(.*?)[\"\']?\)', bg).group(1)
                dimensions = page.evaluate('(url)=>new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve([i.naturalWidth,i.naturalHeight]);i.onerror=()=>reject(new Error(url));i.src=url})', url)
                assert min(dimensions) >= 200, dimensions
                assert art.locator('.theme-main-symbol').evaluate('(e)=>getComputedStyle(e).visibility') == 'hidden'
                page.screenshot(path=str(out/f'{theme}-card-{width}x{height}.png'))
                card.click()
                expect(page.locator('.theme-lobby')).to_have_attribute('data-theme', theme)
                expect(page.locator('[data-theme-best=' + theme + ']')).to_have_text('—')
                expect(page.locator('[data-theme-collection=' + theme + ']')).to_have_text('0')
                expect(page.locator('.theme-lobby')).to_contain_text('출시 준비 중')
                expect(page.locator('.theme-lobby')).to_contain_text('1,000원')
                detail = page.locator('.theme-detail-hero .theme-art-' + theme)
                assert theme + '-' + REVISION + '.webp' in detail.evaluate('(e)=>getComputedStyle(e,"::after").backgroundImage')
                page.screenshot(path=str(out/f'{theme}-detail-{width}x{height}.png'))
                assert page.evaluate('document.scrollingElement.scrollHeight<=innerHeight+1')
                # Preserve the existing detail geometry, including any baseline
                # short-screen clipping, rather than changing unrelated layout.
                ds=['.theme-topbar','.theme-detail-hero','.theme-records','.theme-preview','.theme-empty-ranking','.theme-cta','.theme-version']
                old_geometry=geometry(ds)
                metrics=page.locator('.theme-lobby').evaluate('(e)=>({h:e.clientHeight,sh:e.scrollHeight,w:e.clientWidth,sw:e.scrollWidth,overflow:getComputedStyle(e).overflowY})')
                neutral=page.add_style_tag(content=NEUTRAL)
                baseline=page.locator('.theme-lobby').evaluate('(e)=>({h:e.clientHeight,sh:e.scrollHeight,w:e.clientWidth,sw:e.scrollWidth,overflow:getComputedStyle(e).overflowY})')
                assert metrics==baseline,(width,height,theme,'New overflow',metrics,baseline)
                assert old_geometry==geometry(ds),(width,height,theme,'Detail layout changed')
                assert metrics['overflow']=='hidden',metrics
                neutral.evaluate('(e)=>e.remove()')
                detail_metrics[theme]=metrics
                page.get_by_role('button', name='테마 선택으로', exact=True).click()
            assert len(writes) == initial_writes, 'Browsing themes wrote progress'
            page.get_by_role('button', name='햄버거 테마 선택', exact=True).click()
            expect(page.locator('[data-theme-best=burger]')).to_have_text('21,350')
            expect(page.locator('[data-theme-collection=burger]')).to_have_text('5 / 19')
            expect(page.locator('.home-play svg')).to_have_count(0)
            assert not errors, errors
            report['tests'].append({'viewport': [width, height], 'threeImagesLoaded': True, 'geometryUnchanged': True, 'burgerPixelsUnchanged': True, 'mainFitAndDetailGeometryPreserved': True, 'detailMetrics':detail_metrics, 'noFakeUpcomingRecords': True, 'noProgressWrites': True, 'errors': errors})
            ctx.close()
        browser.close()
    (out/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--site', default='site'); parser.add_argument('--url'); parser.add_argument('--out', default='theme-art-proof'); args=parser.parse_args()
    if args.url: verify(args.url.rstrip('/')+'/', Path(args.out))
    else:
        with tempfile.TemporaryDirectory() as root:
            os.symlink(Path(args.site).resolve(), Path(root)/'giralab-web', target_is_directory=True)
            server=ThreadingHTTPServer(('127.0.0.1',4197),partial(Handler,directory=root)); Thread(target=server.serve_forever,daemon=True).start()
            try: verify('http://127.0.0.1:4197/giralab-web/',Path(args.out))
            finally: server.shutdown(); server.server_close()
