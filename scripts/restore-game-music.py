"""Restore the exact tested build and verifier bytes, not an old game release."""
from pathlib import Path
import base64,bsdiff4,hashlib,json,re,zlib
ROOT=Path('.').resolve()
SPEC=Path('deploy-assets/restore-game-music.json')
PACKED=Path('deploy-assets/restore-game-music.delta.b64')
sha=lambda b:hashlib.sha256(b).hexdigest()
ART='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
ALLOWED={'site/index.html','site/source-build.json','site/loading-build.json','scripts/verify-game-music.py','scripts/verify-loading-audio.py','scripts/verify-live-loading.py','scripts/verify-combo-browser.py','scripts/verify-burst-refill.py','scripts/verify-codex-order.py','release-tools/verify-audio-mythic.py'}

def inside(name):
    assert name in ALLOWED or re.fullmatch(r'site/assets/index-[A-Za-z0-9_-]+\.(js|css)',name),name
    p=(ROOT/name).resolve();assert p.is_relative_to(ROOT) and p!=ROOT
    return p

if SPEC.exists() or PACKED.exists():
    spec=json.loads(SPEC.read_text());packed=''.join(PACKED.read_text().split())
    assert len(packed)==spec['transport_bytes'] and sha(packed.encode())==spec['transport_sha256'],'Transport checksum mismatch'
    data=json.loads(zlib.decompress(base64.b64decode(packed,validate=True)))
    assert data['game_version']==spec['game_version']=='1.6.5'
    assert data['source_commit']==spec['source_commit'] and re.fullmatch('[0-9a-f]{40}',data['source_commit'])
    assert data['source_run']==spec['source_run']
    files=data['files'];assert len(files)==12 and len({f['to'] for f in files})==12
    assert sha(Path('site/audio/kitchen-rush.ogg').read_bytes())==spec['game_music_sha256']
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
        assert meta['source_commit']==spec['source_commit'] and meta['game_version']=='1.6.5'
        assert meta['game_music_title']=='Kitchen Rush' and meta['game_music_asset']=='audio/kitchen-rush.ogg'
        assert meta['game_music_sha256']==spec['game_music_sha256']
        assert meta['loading_lab_music'] and meta['audio_controls']=='settings-only' and meta['persistent_loading_mixer']
        assert meta['regeneration_animation']=='burst-rain-v1' and meta['regeneration_completion']=='animation-finished'
        assert meta['regeneration_overlay'] is False and meta['board_regeneration_mode']=='full-new'
        assert meta['recipe_count']==19 and meta['rules_version']==3
        targets={p for _,p,_ in outputs}
        for _,p,b in outputs:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        for p,_,_ in outputs:
            if p is not None and p not in targets:p.unlink()

meta=json.loads(Path('site/source-build.json').read_text())
assert meta['game_version']=='1.6.5' and meta['game_music_title']=='Kitchen Rush'
assert sha(Path('site/audio/kitchen-rush.ogg').read_bytes())==meta['game_music_sha256']
assert meta['regeneration_animation']=='burst-rain-v1' and meta['loading_lab_music']
print('Exact tested 1.6.5: previous gameplay track restored, latest features unchanged.')
