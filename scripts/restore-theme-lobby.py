"""Install only the exact tested public build; never modify game data or source assets."""
from pathlib import Path
import base64,bsdiff4,hashlib,io,json,re,urllib.parse,urllib.request,zipfile,zlib
ROOT=Path('.').resolve()
REQUEST=Path('deploy-assets/theme-lobby-download.json')
SPEC=Path('deploy-assets/theme-lobby.json')
PACKED=Path('deploy-assets/theme-lobby.delta.b64')
sha=lambda b:hashlib.sha256(b).hexdigest()
ART='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
MUSIC='e53b5d3882d57c8e3a4b1f4179b349fd6f849bec454176b264616ca558c99647'
ALLOWED={'site/index.html','site/source-build.json','site/loading-build.json','scripts/verify-game-music.py','scripts/verify-loading-audio.py','scripts/verify-live-loading.py','scripts/verify-combo-browser.py','scripts/verify-burst-refill.py','scripts/verify-codex-order.py','scripts/verify-theme-lobby.py','release-tools/verify-audio-mythic.py'}
def inside(name):
    assert name in ALLOWED or re.fullmatch(r'site/assets/index-[A-Za-z0-9_-]+\.(js|css)',name),name
    p=(ROOT/name).resolve();assert p.is_relative_to(ROOT) and p!=ROOT
    return p
if REQUEST.exists() and not (SPEC.exists() and PACKED.exists()):
    request=json.loads(REQUEST.read_text());url=urllib.parse.urlparse(request['url'])
    assert url.scheme=='https' and (url.hostname or '').endswith('.oaiusercontent.com')
    with urllib.request.urlopen(request['url'],timeout=90) as response: raw=response.read(40000000)
    assert sha(raw)==request['archive_sha256'],'Archive checksum mismatch'
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for name,target in [('build/theme-lobby.json',SPEC),('build/theme-lobby.delta.b64',PACKED)]:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(name))
if SPEC.exists() or PACKED.exists():
    spec=json.loads(SPEC.read_text());packed=''.join(PACKED.read_text().split())
    assert len(packed)==spec['transport_bytes'] and sha(packed.encode())==spec['transport_sha256'],'Transport checksum mismatch'
    data=json.loads(zlib.decompress(base64.b64decode(packed,validate=True)))
    assert data['game_version']==spec['game_version']=='1.7.0'
    assert data['source_commit']==spec['source_commit'] and re.fullmatch('[0-9a-f]{40}',data['source_commit'])
    assert data['source_run']==spec['source_run']
    files=data['files'];assert len(files)==13 and len({f['to'] for f in files})==13
    assert sha(Path('site/audio/kitchen-rush.ogg').read_bytes())==MUSIC
    assert sha(Path('site/giralab-loading-approved-aecda336.jpg').read_bytes())==ART
    if not all(inside(f['to']).is_file() and sha(inside(f['to']).read_bytes())==f['new'] for f in files):
        outputs=[]
        for f in files:
            source=inside(f['from']) if f['from'] is not None else None;target=inside(f['to'])
            before=source.read_bytes() if source is not None else b''
            assert sha(before)==f['old'],'Concurrent change: '+str(f['from'])
            if source is None:assert not target.exists(),'Unexpected existing new verifier'
            after=bsdiff4.patch(before,base64.b64decode(f['patch'],validate=True))
            assert sha(after)==f['new'],'Output checksum mismatch: '+f['to']
            outputs.append((source,target,after))
        meta=json.loads(next(b for _,p,b in outputs if p.name=='source-build.json'))
        assert meta['source_commit']==spec['source_commit'] and meta['game_version']=='1.7.0'
        assert meta['theme_lobby'] and meta['theme_ids']==['burger','music','war','robot']
        assert meta['playable_themes']==['burger'] and meta['payments_enabled'] is False
        assert meta['theme_price_krw']=={'burger':0,'music':1000,'war':1000,'robot':1000}
        assert meta['loading_lab_music'] and meta['audio_controls']=='settings-only' and meta['persistent_loading_mixer']
        assert meta['regeneration_animation']=='burst-rain-v1' and meta['regeneration_completion']=='animation-finished'
        assert meta['regeneration_overlay'] is False and meta['board_regeneration_mode']=='full-new'
        assert meta['recipe_count']==19 and meta['rules_version']==3
        targets={p for _,p,_ in outputs}
        for _,p,b in outputs:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        for p,_,_ in outputs:
            if p is not None and p not in targets:p.unlink()
meta=json.loads(Path('site/source-build.json').read_text())
assert meta['game_version']=='1.7.0' and meta['game_music_title']=='Kitchen Rush'
assert sha(Path('site/audio/kitchen-rush.ogg').read_bytes())==meta['game_music_sha256']==MUSIC
assert sha(Path('site/giralab-loading-approved-aecda336.jpg').read_bytes())==ART
assert meta['regeneration_animation']=='burst-rain-v1' and meta['loading_lab_music']
print('Exact tested theme lobby 1.7.0; existing assets, music, rules and data unchanged.')
