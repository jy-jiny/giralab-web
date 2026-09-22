"""Verify the exact approved artwork and real boot UI without production account writes."""
import argparse, asyncio, hashlib, json, os, shutil, subprocess, tempfile, time
from pathlib import Path
from playwright.async_api import async_playwright

SHA = 'aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
COMMIT='546c8b583e812f5d37a0d8f4056e495801ad319a'
PLAYER={'id':'00000000-0000-0000-0000-000000000603','nickname':'로딩검증'}

async def main(base, out):
    out.mkdir(parents=True, exist_ok=True)
    report = {'base_url':base,'image_sha256':SHA,'source_commit':COMMIT,'tests':[]}
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium') or None,
            args=['--no-sandbox','--disable-dev-shm-usage'])
        for width,height in [(360,640),(390,844),(412,915)]:
            ctx = await browser.new_context(viewport={'width':width,'height':height},device_scale_factor=3,is_mobile=True,has_touch=True)
            page = await ctx.new_page(); page.set_default_timeout(20000)
            errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
            ingredients_ready,profile_ready=asyncio.Event(),asyncio.Event()
            async def gate_ingredients(route):
                await ingredients_ready.wait(); await route.continue_()
            async def gate_profile(route):
                endpoint=route.request.url.split('/api/')[-1].split('?')[0]
                if endpoint=='player':
                    await profile_ready.wait(); data={'player':None}
                elif endpoint=='account/status':
                    data={'enabled':True,'providers':['google'],'linked':False,'player':None,'deviceState':'new','devices':0}
                else:
                    await route.abort(); return
                await route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
            await page.route('**/ingredients.png',gate_ingredients)
            await page.route('**/api/**',gate_profile)
            await page.goto(base+'?v='+COMMIT[:12],wait_until='domcontentloaded')
            art=page.locator('.giralab-boot__art')
            await art.wait_for(state='visible')
            await page.wait_for_function("document.querySelector('.giralab-boot__art')?.naturalWidth === 864")
            await page.wait_for_function("document.querySelector('[role=progressbar]')?.getAttribute('aria-valuenow') === '50'")
            await page.wait_for_timeout(230)
            first=await page.locator('.giralab-boot__fill').bounding_box()
            img_info=await art.evaluate('(e)=>({w:e.naturalWidth,h:e.naturalHeight,url:e.currentSrc,fit:getComputedStyle(e).objectFit})')
            rect=await art.bounding_box()
            assert img_info['w']==864 and img_info['h']==1536 and img_info['fit']=='contain',img_info
            assert rect['x']>=-1 and rect['y']>=-1 and rect['x']+rect['width']<=width+1 and rect['y']+rect['height']<=height+1,rect
            response=await ctx.request.get(img_info['url']); raw=await response.body()
            assert response.ok and hashlib.sha256(raw).hexdigest()==SHA,'Not the exact approved attachment'
            assert len(raw)==195444,len(raw)
            assert not await page.locator('.giralab-live-loading,.boot-full-image,.boot-mascot-hq').count(),'Old loader remains'
            await page.screenshot(path=str(out/f'loading-{width}x{height}-50.png'))
            ingredients_ready.set()
            await page.wait_for_function("document.querySelector('[role=progressbar]')?.getAttribute('aria-valuenow') === '70'")
            await page.wait_for_timeout(230)
            second=await page.locator('.giralab-boot__fill').bounding_box()
            assert second['width']>first['width']*1.25,(first,second)
            await page.screenshot(path=str(out/f'loading-{width}x{height}-70.png'))
            profile_ready.set()
            await page.wait_for_function("document.querySelector('[role=progressbar]')?.getAttribute('aria-valuenow') === '100'")
            await page.locator('.login-screen').wait_for(state='visible')
            assert await page.locator('#nickname').count()==0,'Nickname entry must follow Google proof'
            assert await page.get_by_role('button',name='Google로 계속하기',exact=True).is_enabled()
            assert await page.locator('.giralab-boot').count()==0,'Boot never closes'
            assert not errors,errors
            await page.screenshot(path=str(out/f'ready-{width}x{height}.png'))
            report['tests'].append({'viewport':[width,height],'device_pixel_ratio':3,'source':img_info,'progress':[50,70,100],
                'fill_widths':[first['width'],second['width']],'next_screen':'Google login before nickname','page_errors':errors,'profile':'isolated fixture'})
            await ctx.close()
        ctx=await browser.new_context(viewport={'width':390,'height':844})
        page=await ctx.new_page(); errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        progress={'unlocked':['classic'],'bestScore':0}
        async def api_fixture(route):
            path=route.request.url.split('/api/')[-1].split('?')[0]
            if path=='account/status':
                data={'enabled':True,'providers':['google'],'linked':True,'player':PLAYER,'deviceState':'active','devices':1}
            elif path=='player': data={'player':PLAYER}
            elif path=='leaderboard': data={'entries':[],'me':None}
            elif path in ('progress','account/backup'):
                if route.request.method=='POST':
                    incoming=route.request.post_data_json
                    progress['bestScore']=max(progress['bestScore'],incoming['bestScore'])
                    progress['unlocked']=sorted(set(progress['unlocked'])|set(incoming['unlocked']))
                data=progress
            else:
                await route.abort(); return
            await route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
        await page.route('**/api/**',api_fixture)
        await page.goto(base,wait_until='domcontentloaded')
        await page.locator('.home-screen').wait_for(state='visible')
        if await page.locator('[data-theme-select=burger]').count(): await page.locator('[data-theme-select=burger]').click()
        await page.locator('.home-play').click()
        await page.locator('[data-testid=game-board]').wait_for(state='visible')
        await page.wait_for_timeout(250)
        assert not errors,errors
        report['tests'].append({'flow':'returning player -> home -> game','network':'isolated API fixtures','page_errors':errors})
        await ctx.close()
        ctx=await browser.new_context(viewport={'width':390,'height':844})
        page=await ctx.new_page()
        await page.route('**/api/**',api_fixture)
        await page.route('**/ingredients.png',lambda route:route.fulfill(status=404,body='missing'))
        await page.goto(base,wait_until='domcontentloaded')
        await page.get_by_role('button',name='다시 불러오기').wait_for(state='visible')
        assert await page.locator('.giralab-boot').is_visible()
        assert int(await page.get_by_role('progressbar').get_attribute('aria-valuenow'))<100
        report['tests'].append({'flow':'asset failure','result':'visible retry, no false 100%'})
        await ctx.close()
        # Normal fresh loading still uses the real site assets, with every API request isolated.
        ctx=await browser.new_context(viewport={'width':390,'height':844})
        page=await ctx.new_page(); errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        await page.route('**/api/**',gate_profile)
        await page.goto(base+'?v='+COMMIT[:12],wait_until='domcontentloaded')
        await page.locator('.login-screen').wait_for(state='visible',timeout=20000)
        assert await page.locator('#nickname').count()==0
        assert not errors,errors
        report['normal_open']={'boot_closed':await page.locator('.giralab-boot').count()==0,'page_errors':errors,'network':'isolated API fixture'}
        await ctx.close(); await browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--site',default='site'); parser.add_argument('--url'); parser.add_argument('--out',default='live-loading-proof'); parser.add_argument('--source-commit',default=COMMIT)
    args=parser.parse_args()
    assert len(args.source_commit)==40 and all(c in '0123456789abcdef' for c in args.source_commit),'Expected source commit must be an exact SHA'
    COMMIT=args.source_commit
    if args.url:
        asyncio.run(main(args.url.rstrip('/')+'/',Path(args.out)))
    else:
        with tempfile.TemporaryDirectory() as root:
            os.symlink(Path(args.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
            server=subprocess.Popen(['python3','-m','http.server','4173','--bind','127.0.0.1','--directory',root],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                time.sleep(.6); asyncio.run(main('http://127.0.0.1:4173/giralab-web/',Path(args.out)))
            finally:
                server.terminate(); server.wait(timeout=5)
