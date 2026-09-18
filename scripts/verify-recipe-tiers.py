"""Verify recipe tier labels and responsive layout without production writes."""
import argparse, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

IDS = ['classic','cheese','green','bacon','double','bacon-cheese','double-patty','cheese-melt','garden-stack','smoky-green','bacon-first','green-cheese','cheese-bacon-stack','double-bacon','cheese-mad','meat-monster','green-monster','bacon-bomb']
TIERS = ['normal','normal','normal','normal','advanced','advanced','normal','advanced','advanced','advanced','advanced','advanced','advanced','advanced','rare','rare','rare','rare']
LABELS = {'normal':'일반 조합','advanced':'고급 조합','rare':'레어 조합'}

def verify(base, out):
    out.mkdir(parents=True, exist_ok=True)
    report = {'base_url':base, 'game_version':'1.5.1', 'network':'Isolated API fixtures; no production writes', 'tests':[]}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium') or None, args=['--no-sandbox','--disable-dev-shm-usage'])
        for width, height in [(360,640),(390,844),(412,915)]:
            for discovered in (False, True):
                ctx = browser.new_context(viewport={'width':width,'height':height}, device_scale_factor=2, is_mobile=True, has_touch=True)
                page = ctx.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.set_default_timeout(20000)
                def fixture(route):
                    name = route.request.url.split('/api/')[-1].split('?')[0]
                    data = {'player':{'id':'recipe-tier-qa','nickname':'도감검증'}} if name == 'player' else {'entries':[],'me':None} if name == 'leaderboard' else {'unlocked':IDS if discovered else ['classic'],'bestScore':0}
                    route.fulfill(status=200, content_type='application/json', body=json.dumps(data))
                page.route('**/api/**', fixture)
                page.goto(base+'?recipe-tiers=1.5.1', wait_until='domcontentloaded')
                page.locator('.home-screen').wait_for(state='visible')
                assert page.locator('.home-version').inner_text() == 'GiraLab · 1.5.1'
                page.get_by_role('button', name='옵션', exact=True).click()
                page.get_by_role('button', name=re.compile('레시피 도감')).click()
                page.locator('.recipe-grid').wait_for(state='visible')
                cards = page.locator('.recipe-card')
                assert cards.count() == 18
                assert page.locator('.recipe-card.locked').count() == (0 if discovered else 17)
                for i, tier in enumerate(TIERS):
                    card = cards.nth(i)
                    badge = card.locator('.recipe-heading .recipe-tier-badge')
                    assert badge.count() == 1
                    assert badge.inner_text() == LABELS[tier]
                    assert badge.get_attribute('data-recipe-tier') == tier
                    expected_slow = '슬로우 없음' if tier == 'normal' else '슬로우 3초' if tier == 'advanced' else '슬로우 4초'
                    assert expected_slow in badge.get_attribute('aria-label')
                    if not discovered and i > 0:
                        assert card.locator('h3').inner_text() == '아직 모르는 맛'
                        assert card.locator('.recipe-order').count() == 0
                assert cards.nth(0).locator('h3').inner_text() == '클래식 버거'
                if discovered:
                    assert cards.nth(7).locator('h3').inner_text() == '치즈 멜트 버거'
                    assert cards.nth(14).locator('h3').inner_text() == '치즈에 미친 햄버거'
                overflow = page.evaluate('''() => [...document.querySelectorAll('.recipe-card')].flatMap(card => {
                    const bounds = card.getBoundingClientRect();
                    return [...card.querySelectorAll('.recipe-heading h3,.recipe-tier-badge')].filter(el => {
                        const r=el.getBoundingClientRect(); return r.left < bounds.left-1 || r.right > bounds.right+1;
                    }).map(el => el.textContent);
                })''')
                assert not overflow, overflow
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
                suffix = f'{width}x{height}-' + ('discovered' if discovered else 'undiscovered')
                page.screenshot(path=str(out/f'recipe-tiers-{suffix}-top.png'))
                cards.nth(17).scroll_into_view_if_needed()
                page.screenshot(path=str(out/f'recipe-tiers-{suffix}-rare.png'))
                assert not errors, errors
                report['tests'].append({'viewport':[width,height], 'all_discovered':discovered, 'badges':18, 'counts':{'normal':5,'advanced':9,'rare':4}, 'overflow':overflow, 'page_errors':errors})
                ctx.close()
        browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--site',default='site'); parser.add_argument('--url'); parser.add_argument('--out',default='recipe-tier-proof')
    args=parser.parse_args()
    if args.url:
        verify(args.url.rstrip('/')+'/',Path(args.out))
    else:
        with tempfile.TemporaryDirectory() as root:
            os.symlink(Path(args.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
            server=subprocess.Popen(['python3','-m','http.server','4175','--bind','127.0.0.1','--directory',root],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                time.sleep(.5); verify('http://127.0.0.1:4175/giralab-web/',Path(args.out))
            finally:
                server.terminate(); server.wait(timeout=5)
