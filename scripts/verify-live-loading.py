"""Check the deployed site, without mocking its API or replacing its artwork."""
import asyncio
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.request
from playwright.async_api import async_playwright

BASE = 'https://jy-jiny.github.io/giralab-web/'
ART = 'giralab-loading-d52df73017d8.jpg'
HASH = 'd52df73017d84d2ea77e0f50fae2726b84cdc7cb69376efb96231d124a32d109'
OUT = Path('live-loading-proof')
OUT.mkdir(exist_ok=True)
for attempt in range(24):
    try:
        with urllib.request.urlopen(BASE + '?verify=' + str(time.time_ns()), timeout=15) as response:
            html = response.read().decode()
        if ART not in html:
            raise RuntimeError('Previous HTML still cached')
        with urllib.request.urlopen(BASE + ART, timeout=15) as response:
            image = response.read()
        assert hashlib.sha256(image).hexdigest() == HASH
        break
    except Exception:
        if attempt == 23:
            raise
        time.sleep(5)

async def verify():
    async with async_playwright() as p:
        executable = shutil.which('google-chrome') or shutil.which('chromium')
        browser = await p.chromium.launch(executable_path=executable, args=['--no-sandbox'])
        page = await browser.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
        gate = asyncio.Event()
        async def hold(route):
            await gate.wait()
            await route.continue_()
        await page.route('**/ingredients.png', hold)
        try:
            await page.goto(BASE + '?verify=' + str(time.time_ns()), wait_until='domcontentloaded')
            await page.wait_for_function("document.querySelector('.giralab-loader-art')?.naturalWidth === 864")
            await page.wait_for_function("document.querySelector('[role=progressbar]')?.getAttribute('aria-valuenow') === '80'", timeout=15000)
            await page.wait_for_timeout(700)
            assert await page.locator('[role=progressbar]').get_attribute('aria-valuenow') == '80'
            await page.screenshot(path=str(OUT / 'live-loading-390x844.png'))
            gate.set()
            await page.locator('.giralab-approved-loading').wait_for(state='detached', timeout=20000)
            await page.locator('.home-screen, .nickname-screen').wait_for(timeout=10000)
            (OUT / 'results.json').write_text(json.dumps({'url': BASE, 'artworkSHA256': HASH, 'originalDimensions': [864,1536], 'pendingResourceProgress': 80, 'gameEntryAfterResourceFinished': True, 'apiMocked': False}, indent=2))
            print('LIVE_VERIFIED: exact original artwork, measured progress, and successful game entry')
        finally:
            gate.set()
            await browser.close()

asyncio.run(verify())
