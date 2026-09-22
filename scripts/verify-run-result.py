"""End a real web game via DOM controls/clock; all API traffic is intercepted."""
import argparse, base64, json, os, re, shutil, tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright, expect

PROGRESS={'unlocked':['classic','cheese','green','bacon','double'],'bestScore':21350}
PLAYER={'id':'00000000-0000-0000-0000-000000000601','nickname':'분석검증'}
SEQUENCES=[['bun','patty','bun'],['bun','patty','cheese','bun'],['bun','patty','lettuce','bun'],
           ['bun','patty','cheese','cheese','bun'],['bun','cheese','patty','cheese','bun'],
           ['bun','patty','bacon','cheese','bun'],['bun','lettuce','patty','lettuce','bun']]
def find(board,sequence):
    def visit(r,c,path):
        if not (0<=r<9 and 0<=c<6) or (r,c) in path or board[r][c]!=sequence[len(path)]:return None
        path=path+[(r,c)]
        if len(path)==len(sequence):return path
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr or dc:
                    result=visit(r+dr,c+dc,path)
                    if result:return result
    for r in range(9):
        for c in range(6):
            result=visit(r,c,[])
            if result:return result
    return None

def verify(base,out):
    out.mkdir(parents=True,exist_ok=True)
    report={'network':'isolated API fixtures only','input':'actual DOM keyboard and complete button','cases':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage'])
        ctx=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,reduced_motion='reduce')
        ctx.add_init_script("""
          window.fixtureTools=[];document.modelContext={registerTool:t=>window.fixtureTools.push(t.name)};
          window.fixtureShares=[];
          Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});
          Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{
            const file=data.files[0],bytes=new Uint8Array(await file.arrayBuffer());
            const bitmap=await createImageBitmap(file);
            window.fixtureShares.push({text:data.text,name:file.name,type:file.type,width:bitmap.width,height:bitmap.height,
              png:btoa(Array.from(bytes,b=>String.fromCharCode(b)).join(''))});bitmap.close();
          }});
        """)
        saved={'unlocked':list(PROGRESS['unlocked']),'bestScore':PROGRESS['bestScore']};calls=[]
        def fixture(route):
            path=route.request.url.split('/api/')[-1].split('?')[0];calls.append([route.request.method,path])
            if path=='account/status':
                route.fulfill(status=200,content_type='application/json',body=json.dumps({'enabled':False,'linked':True,'player':PLAYER,'deviceState':'active','devices':1}));return
            if path=='player':data={'player':PLAYER}
            elif path in ('progress','account/backup'):
                if route.request.method=='POST':
                    posted=route.request.post_data_json
                    saved['unlocked']=sorted(set(saved['unlocked']+posted['unlocked']))
                    saved['bestScore']=max(saved['bestScore'],posted['bestScore'])
                data=saved
            elif path=='leaderboard':data={'entries':[],'me':None}
            else:raise AssertionError('Unexpected API: '+path)
            route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
        ctx.route('**/api/**',fixture)
        page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_default_timeout(15000)
        page.clock.install()
        page.goto(base+'?run-result=20260921',wait_until='domcontentloaded')
        expect(page.locator('.home-version')).to_have_text('GiraLab · 1.7.2')
        assert page.evaluate('window.fixtureTools')==[], 'Release must not expose AI control tools'
        assert page.evaluate('typeof window.__gameTools')=='undefined', 'Test driver must not ship'
        page.evaluate('()=>{let seed=20260918;Math.random=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296)}')
        page.get_by_role('button',name='햄버거 테마 선택',exact=True).click()
        page.get_by_role('button',name='게임 시작',exact=True).click()
        expect(page.locator('[data-game-status]')).to_have_attribute('data-game-status','playing')
        expected={'normal':[0,0],'advanced':[0,0],'legendary':[0,0],'mythic':[0,0]}
        score=lambda:int(page.locator('.score-main strong').inner_text().replace(',',''))
        for target in ('advanced','normal'):
            board=page.locator('button[data-tile-id]').evaluate_all("els=>{const b=Array.from({length:9},()=>Array(6));for(const e of els)b[+e.dataset.row][+e.dataset.col]=e.dataset.ingredient;return b}")
            choices=[seq for seq in SEQUENCES if (len(seq)==5)==(target=='advanced')]
            path=next((found for seq in choices if (found:=find(board,seq))),None)
            assert path, target+' path absent in deterministic fixture'
            before=score()
            for r,c in path:
                page.locator(f'button[data-row="{r}"][data-col="{c}"]').focus();page.keyboard.press('Space')
            page.get_by_role('button',name='완성',exact=True).click()
            expect(page.locator('.score-main strong')).not_to_have_text(f'{before:,}')
            earned=score()-before;assert earned>0
            expected[target]=[1,earned]
            page.wait_for_timeout(100)
        final=score();assert final==sum(value[1] for value in expected.values())
        # Advance the actual animation clock; do not set score/status or create a fake report.
        page.clock.run_for(60000)
        result=page.get_by_role('dialog',name='이번 판의 기록')
        expect(result).to_be_visible()
        expect(result.get_by_test_id('result-final-score')).to_have_text(f'{final:,}점')
        expect(result.get_by_test_id('result-final-score')).to_be_in_viewport()
        page.screenshot(path=str(out/'result-open.png'))
        for tier,(count,points) in expected.items():
            expect(result.locator(f'[data-result-tier={tier}] td').nth(0)).to_have_text(f'{count}개')
            expect(result.locator(f'[data-result-tier={tier}] td').nth(1)).to_have_text(f'{points:,}점')
        expect(result.get_by_role('img',name=re.compile('누적 점수 차트'))).to_be_visible()
        assert result.locator('.result-chart path').get_attribute('d').count('V')>=2
        expect(result.locator('.result-highlights')).to_contain_text('2개')
        for width,height in [(320,568),(390,844),(844,390)]:
            page.set_viewport_size({'width':width,'height':height});page.clock.run_for(200)
            box=result.bounding_box();assert box and box['x']>=0 and box['y']>=0 and box['x']+box['width']<=width+.5 and box['y']+box['height']<=height+.5,box
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            result.get_by_role('button',name='카카오톡으로 공유',exact=True).scroll_into_view_if_needed()
            expect(result.get_by_role('button',name='한 판 더',exact=True)).to_be_in_viewport()
            page.screenshot(path=str(out/f'result-{width}x{height}.png'))
            report['cases'].append({'viewport':[width,height],'fit':True,'scrollableReport':True})
        result.get_by_role('button',name='카카오톡으로 공유',exact=True).click()
        page.wait_for_function('window.fixtureShares.length===1')
        shared=page.evaluate('window.fixtureShares[0]')
        assert shared['type']=='image/png' and [shared['width'],shared['height']]==[720,1040]
        assert f'{final:,}점' in shared['text'] and '일반 1개' in shared['text'] and '고급 1개' in shared['text']
        assert PLAYER['id'] not in shared['text']
        (out/'shared-result.png').write_bytes(base64.b64decode(shared['png']))
        page.evaluate("Object.defineProperty(navigator,'canShare',{value:()=>false,configurable:true})")
        result.get_by_role('button',name='카카오톡으로 공유',exact=True).click()
        expect(result.locator('.result-share-status')).to_contain_text('이미지 공유를 지원하지 않아요')
        assert len(page.evaluate('window.fixtureShares'))==1
        result.get_by_role('button',name='메인으로',exact=True).click()
        expect(page.locator('[data-theme-best=burger]')).to_have_text('21,350')
        assert saved['bestScore']==PROGRESS['bestScore'] and set(saved['unlocked'])>=set(PROGRESS['unlocked'])
        page.get_by_role('button',name='게임 시작',exact=True).click()
        expect(page.locator('.score-main strong')).to_have_text('0')
        expect(page.locator('.run-result-dialog')).to_have_count(0)
        assert not errors,errors
        report.update(finalScore=final,tiers=expected,sharedPNG=[720,1040],unsupportedShare=True,recordsPreserved=True,noAITools=True,errors=errors,requests=calls)
        ctx.close();browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))

class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--site',default='site');parser.add_argument('--url');parser.add_argument('--out',default='result-proof');args=parser.parse_args()
    if args.url:verify(args.url.rstrip('/')+'/',Path(args.out))
    else:
        with tempfile.TemporaryDirectory() as root:
            os.symlink(Path(args.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=root));Thread(target=server.serve_forever,daemon=True).start()
            try:verify(f'http://127.0.0.1:{server.server_port}/giralab-web/',Path(args.out))
            finally:server.shutdown();server.server_close()
