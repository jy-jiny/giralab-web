"""Verify the immutable, independently tested Vite bundle locally or on Pages."""
import hashlib,json,sys,time,urllib.request,urllib.error
from pathlib import Path
root=Path('site').resolve()
meta=json.loads((root/'source-build.json').read_text(encoding='utf-8'))
assert meta['server_authoritative_gameplay'] and meta['hearts_per_game']==1
assert meta['run_result_chart']=='removed' and meta['run_result_actions']=='one-row'
assert meta['server_api']=='https://tqqgnrfklhmxwsphjera.supabase.co/functions/v1/giralab-game'
assert meta['auth_api']=='https://giralab-auth.netlify.app'
def digest(data):return hashlib.sha256(data).hexdigest()
def fetch(name):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(sys.argv[1].rstrip('/')+'/'+name+'?release='+str(time.time_ns()),timeout=30) as r:return r.read()
        except urllib.error.HTTPError as error:
            if error.code not in (429,502,503,504) or attempt==3:raise
            print(json.dumps({'retry':name,'status':error.code,'attempt':attempt+1}),file=sys.stderr,flush=True)
        except (urllib.error.URLError,TimeoutError) as error:
            if attempt==3:raise
            print(json.dumps({'retry':name,'error':type(error).__name__,'attempt':attempt+1}),file=sys.stderr,flush=True)
        time.sleep(attempt+1)
for name,expected in meta['build_files_sha256'].items():
    file=(root/name).resolve();assert file.is_relative_to(root)
    assert digest(file.read_bytes())==expected,('local',name)
assert {str(p.relative_to(root)).replace('\\','/') for p in root.rglob('*') if p.is_file() and p.name not in ('source-build.json','.nojekyll')}==set(meta['build_files_sha256'])
assert meta['build_files_sha256']['giralab-loading-approved-aecda336.jpg']==meta['approved_image_sha256']
assert meta['build_files_sha256']['audio/kitchen-rush.ogg']==meta['game_music_sha256']
if len(sys.argv)>1:
    for attempt in range(6):
        try:
            actual=json.loads(fetch('source-build.json'))
            assert actual==meta,'Published manifest differs'
            for name,expected in meta['build_files_sha256'].items():assert digest(fetch(name))==expected,('live',name)
            break
        except Exception:
            if attempt==5:raise
            time.sleep(5)
print(json.dumps({'verified':True,'files':len(meta['build_files_sha256']),'source':meta['source_commit'],'live':len(sys.argv)>1}))
