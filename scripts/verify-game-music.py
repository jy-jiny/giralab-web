"""Read-only audio smoke tests; local media uses production-like byte-range responses."""
import argparse, hashlib, json, os, re, shutil, tempfile, time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

VERSION='1.6.5'
HOOK="window.__gameTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__gameTools[t.name]=t}}});"

class MediaHandler(SimpleHTTPRequestHandler):
    """A local static server with byte ranges, including suffix ranges for Ogg metadata."""
    def send_head(self):
        path=Path(self.translate_path(self.path));self.span=None
        if not path.is_file():return super().send_head()
        size=path.stat().st_size;start=0;end=size-1
        requested=self.headers.get('Range');match=re.fullmatch(r'bytes=(\d*)-(\d*)',requested or '')
        if requested:
            if not match or not any(match.groups()):self.send_error(416);return None
            left,right=match.groups()
            if left:start=int(left);end=min(int(right),size-1) if right else size-1
            else:start=max(0,size-int(right))
            if start>end or start>=size:self.send_error(416);return None
            self.span=(start,end)
        self.send_response(206 if requested else 200)
        self.send_header('Content-type',self.guess_type(str(path)))
        self.send_header('Content-Length',str(end-start+1));self.send_header('Accept-Ranges','bytes')
        if requested:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers();file=path.open('rb');file.seek(start);return file
    def copyfile(self,source,output):
        if self.span is None:return super().copyfile(source,output)
        left=self.span[1]-self.span[0]+1
        while left:
            chunk=source.read(min(left,65536))
            if not chunk:break
            output.write(chunk);left-=len(chunk)
    def log_message(self,*args):pass

def verify(base,out):
    out.mkdir(parents=True,exist_ok=True)
    report={'version':VERSION,'api':'Isolated fixtures; no production writes','tests':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required'])
        for width,height in [(360,640),(390,844),(412,915)]:
            ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True)
            ctx.add_init_script(HOOK)
            page=ctx.new_page();page.set_default_timeout(15000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            def fixture(route):
                name=route.request.url.split('/api/')[-1].split('?')[0]
                data={'player':{'id':'soundtrack-qa','nickname':'점심검증'}} if name=='player' else {'entries':[],'me':None} if name=='leaderboard' else {'unlocked':['classic'],'bestScore':0}
                if name=='progress' and route.request.method=='POST':data=route.request.post_data_json
                route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
            page.route('**/api/**',fixture)
            page.goto(base+'?soundtrack='+VERSION,wait_until='domcontentloaded')
            expect(page.locator('.home-version')).to_have_text('GiraLab · '+VERSION)
            page.wait_for_function('window.__gameTools.get_audio_state.execute({}).labPlaying')
            audio=lambda:page.evaluate('window.__gameTools.get_audio_state.execute({})')
            assert audio()['track']=='Laboratory Notes'
            assert audio()['musicVolume']==45 and audio()['effectsVolume']==65
            expect(page.locator('.audio-enable')).to_have_count(0)
            page.locator('.home-play').click()
            page.wait_for_function('window.__gameTools.get_audio_state.execute({}).gamePlaying')
            page.wait_for_function('document.querySelector("audio").readyState>=3 && document.querySelector("audio").currentTime>0.1 && Number.isFinite(document.querySelector("audio").duration)')
            state=audio();assert state['track']=='Kitchen Rush' and not state['labPlaying'],state
            media=page.locator('audio').evaluate('(el)=>({src:el.currentSrc,duration:el.duration,loop:el.loop,rate:el.playbackRate,error:el.error?.code??null})')
            print('Actual media:',media,flush=True)
            (out/f'media-{width}.json').write_text(json.dumps(media,indent=2))
            assert urlsplit(media['src']).path.endswith('/audio/kitchen-rush.ogg') and 0<media['duration']<600,media
            assert media['loop'] and media['rate']==1 and media['error'] is None
            page.locator('audio').evaluate('(el)=>{el.currentTime=el.duration-.15}')
            page.wait_for_function('document.querySelector("audio").currentTime<2 && !document.querySelector("audio").seeking')
            page.wait_for_timeout(100)
            looped=audio();assert looped['gamePlaying'] and looped['gameTime']<2,looped
            page.get_by_role('button',name='옵션',exact=True).click();page.wait_for_timeout(150)
            assert not audio()['gamePlaying']
            expect(page.locator('.settings-dialog [role="slider"]')).to_have_count(2)
            page.get_by_role('button',name='닫기',exact=True).click()
            page.wait_for_function('window.__gameTools.get_audio_state.execute({}).gamePlaying')
            page.get_by_role('button',name='메인으로',exact=True).click()
            page.wait_for_function('window.__gameTools.get_audio_state.execute({}).labPlaying')
            assert audio()['track']=='Laboratory Notes' and not audio()['gamePlaying']
            response=ctx.request.get(base+'audio/kitchen-rush.ogg')
            assert response.ok and hashlib.sha256(response.body()).hexdigest()=='e53b5d3882d57c8e3a4b1f4179b349fd6f849bec454176b264616ca558c99647'
            assert not errors,errors
            report['tests'].append({'viewport':[width,height],'track':'Kitchen Rush','duration':media['duration'],'actualLoopPlayback':True,'homeTrackUnchanged':True,'settingsOnly':True,'audioSha256':'e53b5d3882d57c8e3a4b1f4179b349fd6f849bec454176b264616ca558c99647','errors':errors})
            ctx.close()
        browser.close()
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--site',default='pages-dist');p.add_argument('--url');p.add_argument('--out',default='lunch-rush-proof');a=p.parse_args()
    if a.url:verify(a.url.rstrip('/')+'/',Path(a.out))
    else:
        with tempfile.TemporaryDirectory() as root:
            os.symlink(Path(a.site).resolve(),Path(root)/'giralab-web',target_is_directory=True)
            server=ThreadingHTTPServer(('127.0.0.1',4181),partial(MediaHandler,directory=root))
            Thread(target=server.serve_forever,daemon=True).start()
            try:verify('http://127.0.0.1:4181/giralab-web/',Path(a.out))
            finally:server.shutdown();server.server_close()
