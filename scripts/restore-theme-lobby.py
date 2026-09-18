"""Install only the exact tested public build; never modify game data or source assets."""
from pathlib import Path
import base64,bsdiff4,hashlib,json,re,subprocess,zlib
ROOT=Path('.').resolve()
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
# The externally hosted download was denied. These public-build-only parts
# were instead uploaded using the repository's authorized GitHub connection.
# Pin to the transport digest from successful source Actions run 35400815345.
parts=sorted(Path('release-tools').glob('theme-lobby-public.part*'))
if parts:
    assert len(parts)==4
    chunks=[''.join(p.read_text().split()) for p in parts]
    # Recover two dropped transport characters; the full original checksum
    # below is mandatory, so neither the code nor verification can differ.
    if len(chunks[2])==8398:
        chunks[2]=chunks[2].replace('QyHdQvZH0v/vbj','QyHdQvZH0vVv/vbj')
    packed=''.join(chunks)
    spec={'source_commit':'21c903a05a17720ee5bce71f38922a25de60756c','source_run':35400815345,'game_version':'1.7.0','transport_sha256':'1198f0cbd96af4fccf440cfd8140014d354e43c2274a6a74558e59d645e36263','transport_bytes':33208}
    assert len(packed)==spec['transport_bytes'] and sha(packed.encode())==spec['transport_sha256'],'Authenticated transfer checksum mismatch'
    SPEC.parent.mkdir(parents=True,exist_ok=True)
    SPEC.write_text(json.dumps(spec));PACKED.write_text(packed)
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
# Stage removal of temporary parts. The workflow only commits after all tests.
if parts:subprocess.run(['git','rm','--',*[str(p) for p in parts]],check=True)
print('Exact tested theme lobby 1.7.0; existing assets, music, rules and data unchanged.')
