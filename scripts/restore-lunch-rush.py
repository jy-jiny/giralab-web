"""Verify the complete candidate before changing static assets or verifier files."""
from pathlib import Path
import base64,bsdiff4,hashlib,json,re,zlib
ROOT=Path('.').resolve()
SPEC=Path('deploy-assets/lunch-rush.json')
PACKED=Path('deploy-assets/lunch-rush.delta.b64')
ART='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
AUDIO='69cc482d6a5f500d142b8dc636fee97bb700969835b0349a47e42a56a35f827d'
sha=lambda b:hashlib.sha256(b).hexdigest()
ALLOWED={'site/index.html','site/source-build.json','site/loading-build.json','scripts/verify-lunch-rush.py','scripts/verify-loading-audio.py','scripts/verify-live-loading.py','scripts/verify-combo-browser.py','scripts/verify-board-regeneration.py','scripts/verify-codex-order.py','release-tools/verify-audio-mythic.py'}
def inside(name):
    assert name in ALLOWED or re.fullmatch(r'site/assets/index-[A-Za-z0-9_-]+\.(js|css)',name),name
    p=(ROOT/name).resolve();assert p.is_relative_to(ROOT) and p!=ROOT
    return p
if SPEC.exists() or PACKED.exists():
    spec=json.loads(SPEC.read_text());packed=''.join(PACKED.read_text().split())
    assert len(packed)==spec['transport_bytes'] and sha(packed.encode())==spec['transport_sha256'],'Transport checksum mismatch'
    data=json.loads(zlib.decompress(base64.b64decode(packed,validate=True)))
    assert data['game_version']==spec['game_version']=='1.6.3'
    assert data['source_commit']==spec['source_commit'] and re.fullmatch('[0-9a-f]{40}',data['source_commit'])
    assert data['source_run']==spec['source_run'] and data['audio_sha256']==AUDIO
    files=data['files'];assert len(files)==12 and len({f['to'] for f in files})==12
    sound=Path('release-assets/lunch-rush-v1.ogg').read_bytes()
    soundmeta=Path('release-assets/lunch-rush-v1.json').read_bytes()
    assert sha(sound)==json.loads(soundmeta)['ogg_sha256']==AUDIO
    outputs=[]
    if not all(inside(f['to']).exists() and sha(inside(f['to']).read_bytes())==f['new'] for f in files):
        for f in files:
            source=inside(f['from']) if f['from'] is not None else None;target=inside(f['to'])
            old=source.read_bytes() if source is not None else b''
            assert sha(old)==f['old'],'Concurrent change: '+str(f['from'])
            if source is None:assert not target.exists(),'Unexpected existing new file'
            new=bsdiff4.patch(old,base64.b64decode(f['patch'],validate=True))
            assert sha(new)==f['new'],'Output checksum mismatch: '+f['to']
            outputs.append((source,target,new))
        meta=json.loads(next(b for _,p,b in outputs if p.name=='source-build.json'))
        assert meta['source_commit']==spec['source_commit'] and meta['game_version']=='1.6.3'
        assert meta['game_music_title']=='Lunch Rush' and meta['game_music_bpm']==156 and meta['game_music_sha256']==AUDIO
        assert meta['loading_lab_music'] and meta['audio_controls']=='settings-only' and meta['persistent_loading_mixer']
        assert meta['recipe_count']==19 and meta['rules_version']==3 and meta['board_regeneration_mode']=='full-new'
    assert sha(Path('site/giralab-loading-approved-aecda336.jpg').read_bytes())==ART
    targets={p for _,p,_ in outputs}
    for _,p,b in outputs:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    for p,_,_ in outputs:
        if p is not None and p not in targets:p.unlink()
    Path('site/audio/lunch-rush-v1.ogg').write_bytes(sound)
    Path('site/audio/lunch-rush-v1.json').write_bytes(soundmeta)
meta=json.loads(Path('site/source-build.json').read_text())
assert meta['game_version']=='1.6.3' and meta['game_music_title']=='Lunch Rush'
assert sha(Path('site/audio/lunch-rush-v1.ogg').read_bytes())==AUDIO
assert sha(Path('site/giralab-loading-approved-aecda336.jpg').read_bytes())==ART
print('Verified exact 1.6.3 soundtrack release; menu music and game rules preserved.')
