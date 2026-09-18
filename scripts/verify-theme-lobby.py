"""Theme navigation/regression proof. All API traffic is isolated; never write test scores live."""
import argparse, base64, hashlib, importlib.util, json, mimetypes, os, re, shutil, tempfile
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright, expect

VERSION='1.7.0'
HOOK="window.__gameTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__gameTools[t.name]=t}}});"
PROGRESS={'unlocked':['classic','cheese','green','bacon','double'],'bestScore':21350}
RANKS={'entries':[{'rank':1,'nickname':'기린연구원','score':21350,'isMe':True},{'rank':2,'nickname':'버거박사','score':16450,'isMe':False}],'me':{'nickname':'기린연구원','score':21350,'rank':1},'updatedAt':0}
ART_SHA='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'

def memory_load(page,site):
    """Offline browser policy permits in-memory documents, not URL navigation.
    Execute the built bundle, remapping only the two static-asset resolvers to data URIs;
    game, lobby and storage implementation remain the production bundle.
    CI/live mode below loads the completely unmodified HTTP build instead.
    """
    assets={}
    for f in site.rglob('*'):
        if f.is_file() and f.suffix in ('.png','.webp','.jpg','.ogg'):
            assets[str(f.relative_to(site))]='data:'+str(mimetypes.guess_type(f)[0])+';base64,'+base64.b64encode(f.read_bytes()).decode()
    css=next((site/'assets').glob('*.css')).read_text();js=next((site/'assets').glob('*.js')).read_text()
    plain='e=>`./${e}`';clean='e=>`./${e.replace(/^\\/+/,``)}`'
    assert plain in js and clean in js,'asset resolver signature changed'
    js=js.replace(plain,'e=>window.__asset[e]').replace(clean,'e=>window.__asset[e.replace(/^\\/+/,``)]')
    page.set_content('<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>'+css+'</style></head><body><div id="root"></div></body></html>')
    page.evaluate(HOOK)
    page.evaluate('''([assets,progress,ranks])=>{
      window.__asset=assets;window.__fixture={progress,ranks,rankFail:false,writes:0};
      const store=new Map();Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,String(v)),removeItem:k=>store.delete(k),clear:()=>store.clear()}});
      window.fetch=async(url,options={})=>{
       const path=String(url).split('/api/')[1]?.split('?')[0];let value;
       if(path==='player')value={player:{id:'theme-lobby-test',nickname:'기린연구원'}};
       else if(path==='leaderboard'){if(window.__fixture.rankFail)return new Response(JSON.stringify({error:'fixture offline'}),{status:503});value=window.__fixture.ranks;}
       else if(path==='progress'){if(options.method==='POST'){window.__fixture.writes++;window.__fixture.progress=JSON.parse(options.body);}value=window.__fixture.progress;}
       else throw new Error('Unexpected external request in offline test: '+url);
       return new Response(JSON.stringify(value),{status:200,headers:{'Content-Type':'application/json'}});
      };
    }''',[assets,PROGRESS,RANKS])
    page.add_script_tag(content=js)

def verify(base,out,site=None,memory=False):
    out.mkdir(parents=True,exist_ok=True);report={'version':VERSION,'api':'isolated fixtures, no production writes','mode':'in-memory production bundle' if memory else 'unmodified HTTP build','tests':[]}
    if site:assert hashlib.sha256((site/'giralab-loading-approved-aecda336.jpg').read_bytes()).hexdigest()==ART_SHA
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required'])
        for width,height in [(320,568),(360,640),(390,844),(412,915)]:
            ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True)
            ctx.add_init_script(HOOK);page=ctx.new_page();page.set_default_timeout(15000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            fixture_state={'progress':dict(PROGRESS),'rankFail':False,'writes':0}
            def fixture(route):
                path=route.request.url.split('/api/')[-1].split('?')[0];status=200
                if path=='player':data={'player':{'id':'theme-lobby-test','nickname':'기린연구원'}}
                elif path=='leaderboard':
                    data=RANKS
                    if fixture_state['rankFail']:status=503;data={'error':'fixture offline'}
                elif path=='progress':
                    if route.request.method=='POST':fixture_state['writes']+=1;fixture_state['progress']=route.request.post_data_json
                    data=fixture_state['progress']
                else:raise AssertionError('Unexpected API endpoint: '+path)
                route.fulfill(status=status,content_type='application/json',body=json.dumps(data))
            page.route('**/api/**',fixture)
            if memory:memory_load(page,site)
            else:page.goto(base+'?theme-lobby='+VERSION,wait_until='domcontentloaded')
            expect(page.locator('.theme-grid')).to_be_visible();expect(page.locator('.home-version')).to_have_text('GiraLab · '+VERSION)
            expect(page.locator('[data-theme-select]')).to_have_count(4)
            expect(page.locator('.theme-price.free')).to_have_text('무료')
            expect(page.locator('.theme-price.paid')).to_have_count(3)
            expect(page.locator('.ranking-panel')).to_have_count(0)
            expect(page.locator('.audio-enable')).to_have_count(0)
            page.wait_for_timeout(400);page.screenshot(path=str(out/f'select-{width}.png'))
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'horizontal overflow'
            for theme,title,collection in [('music','음악','리프'),('war','전쟁','설계도'),('robot','로봇','설계도')]:
                page.get_by_role('button',name=title+' 테마 선택',exact=True).click()
                expect(page.locator('.theme-lobby')).to_have_attribute('data-theme',theme)
                expect(page.locator('[data-theme-best]')).to_have_text('—')
                expect(page.locator('[data-theme-collection]')).to_have_text('0')
                expect(page.locator('.theme-collection-record')).to_contain_text(collection+' 현황')
                expect(page.locator('.theme-locked-action')).to_be_disabled()
                expect(page.locator('.home-play')).to_have_count(0)
                assert '21,350' not in page.locator('.theme-lobby').inner_text(),'burger record leaked to paid theme'
                if theme=='war':expect(page.locator('.theme-special')).to_contain_text('보드 초기화')
                page.screenshot(path=str(out/f'{theme}-{width}.png'))
                page.get_by_role('button',name='테마 선택으로',exact=True).click()
                expect(page.locator('[data-theme-select="'+theme+'"]').locator(':scope')).to_be_focused()
            page.get_by_role('button',name='햄버거 테마 선택',exact=True).click()
            expect(page.locator('[data-theme-best="burger"]')).to_have_text('21,350')
            expect(page.locator('[data-theme-collection="burger"]')).to_have_text('5 / 19')
            expect(page.locator('.theme-ranking')).to_contain_text('버거박사')
            expect(page.locator('.theme-ranking .ranking-status')).to_contain_text('1위')
            page.screenshot(path=str(out/f'burger-{width}.png'))
            page.get_by_role('button',name='햄버거 레시피 도감 보기',exact=True).click()
            expect(page.locator('.book-dialog .recipe-card')).to_have_count(19)
            page.get_by_role('button',name='닫기',exact=True).click()
            if memory:page.evaluate('window.__fixture.rankFail=true')
            else:fixture_state['rankFail']=True
            page.get_by_role('button',name='순위 새로고침',exact=True).click()
            expect(page.locator('.ranking-status')).to_contain_text('다시 시도')
            if memory:page.evaluate('window.__fixture.rankFail=false')
            else:fixture_state['rankFail']=False
            page.locator('.ranking-status button').click();expect(page.locator('.ranking-status')).to_contain_text('1위')
            page.get_by_role('button',name='옵션',exact=True).click()
            expect(page.locator('.settings-dialog [role="slider"]')).to_have_count(2)
            page.get_by_role('button',name='닫기',exact=True).click()
            page.locator('.home-play').click();expect(page.locator('.phone-game')).to_be_visible()
            expect(page.locator('[data-tile-id]')).to_have_count(54)
            page.get_by_role('button',name='메인으로',exact=True).click()
            expect(page.locator('.home-play')).to_have_text('계속하기')
            expect(page.locator('[data-theme-best="burger"]')).to_have_text('21,350')
            page.evaluate('window.dispatchEvent(new Event("burger-native-back"))')
            expect(page.locator('.theme-grid')).to_be_visible()
            page.get_by_role('button',name='음악 테마 선택',exact=True).click()
            expect(page.locator('.theme-locked-action')).to_be_disabled()
            page.get_by_role('button',name='테마 선택으로',exact=True).click()
            page.get_by_role('button',name='햄버거 테마 선택',exact=True).click()
            expect(page.locator('.home-play')).to_have_text('계속하기')
            page.locator('.home-play').click();expect(page.locator('.phone-game')).to_be_visible()
            state=page.evaluate('window.__gameTools.get_game_state.execute({})')
            assert state['status']=='playing' and state['rulesVersion']==3,state
            page.get_by_role('button',name='메인으로',exact=True).click()
            if not memory:
                page.reload(wait_until='domcontentloaded');expect(page.locator('.theme-grid')).to_be_visible()
                page.get_by_role('button',name='햄버거 테마 선택',exact=True).click()
                expect(page.locator('[data-theme-best="burger"]')).to_have_text('21,350')
                expect(page.locator('[data-theme-collection="burger"]')).to_have_text('5 / 19')
            assert not errors,errors
            report['tests'].append({'viewport':[width,height],'themeNavigation':True,'realBurgerRecords':True,'paidThemeIsolation':True,'noCheckout':True,'book19':True,'rankErrorRecovery':True,'settingsOnlyAudio':True,'game54Tiles':True,'resumeAcrossThemes':True,'nativeBack':True,'reloadPersistence':not memory,'errors':errors})
            ctx.close()
        browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--site',default='pages-dist');p.add_argument('--url');p.add_argument('--out',default='theme-lobby-proof');p.add_argument('--memory',action='store_true');a=p.parse_args()
    site=Path(a.site).resolve()
    if a.memory:verify('',Path(a.out),site,True)
    elif a.url:verify(a.url.rstrip('/')+'/',Path(a.out))
    else:
        spec=importlib.util.spec_from_file_location('media',Path(__file__).with_name('verify-game-music.py'));media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)
        with tempfile.TemporaryDirectory() as root:
            os.symlink(site,Path(root)/'giralab-web',target_is_directory=True)
            server=ThreadingHTTPServer(('127.0.0.1',4183),partial(media.MediaHandler,directory=root));Thread(target=server.serve_forever,daemon=True).start()
            try:verify('http://127.0.0.1:4183/giralab-web/',Path(a.out),site)
            finally:server.shutdown();server.server_close()
