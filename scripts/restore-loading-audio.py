"""Apply only checksum-verified build and test bytes, after validating every source."""
from pathlib import Path
import base64,bsdiff4,hashlib,json,re,zlib
ROOT=Path('.').resolve()
SPEC=Path('deploy-assets/loading-audio.json')
PACKED=Path('deploy-assets/loading-audio.delta.b64')
sha=lambda b:hashlib.sha256(b).hexdigest()
ART='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
ALLOWED={'site/index.html','site/source-build.json','site/loading-build.json','scripts/verify-loading-audio.py','scripts/verify-live-loading.py','scripts/verify-combo-browser.py','scripts/verify-board-regeneration.py','scripts/verify-codex-order.py','release-tools/verify-audio-mythic.py'}

def inside(name):
    assert name in ALLOWED or re.fullmatch(r'site/assets/index-[A-Za-z0-9_-]+\.(js|css)',name),name
    path=(ROOT/name).resolve()
    assert path.is_relative_to(ROOT) and path!=ROOT
    return path

if SPEC.exists() or PACKED.exists():
    spec=json.loads(SPEC.read_text());packed=''.join(PACKED.read_text().split())
    assert len(packed)==spec['transport_bytes'] and sha(packed.encode())==spec['transport_sha256'],'Transport checksum mismatch'
    data=json.loads(zlib.decompress(base64.b64decode(packed,validate=True)))
    assert data['game_version']==spec['game_version']=='1.6.2'
    assert data['source_commit']==spec['source_commit'] and re.fullmatch('[0-9a-f]{40}',data['source_commit'])
    assert data['source_run']==spec['source_run']
    files=data['files'];assert len(files)==11 and len({f['to'] for f in files})==11
    assert sha(Path('site/giralab-loading-approved-aecda336.jpg').read_bytes())==ART
    if not all(inside(f['to']).exists() and sha(inside(f['to']).read_bytes())==f['new'] for f in files):
        outputs=[]
        for f in files:
            source=inside(f['from']) if f['from'] is not None else None
            target=inside(f['to']);old=source.read_bytes() if source is not None else b''
            assert sha(old)==f['old'],'Concurrent change: '+str(f['from'])
            if source is None:assert not target.exists(),'Unexpected existing new file'
            new=bsdiff4.patch(old,base64.b64decode(f['patch'],validate=True))
            assert sha(new)==f['new'],'Reconstructed output mismatch: '+f['to']
            outputs.append((source,target,new))
        meta=json.loads(next(b for _,p,b in outputs if p.name=='source-build.json'))
        assert meta['game_version']=='1.6.2' and meta['source_commit']==spec['source_commit']
        assert meta['loading_lab_music'] is True and meta['audio_controls']=='settings-only' and meta['persistent_loading_mixer'] is True
        assert meta['recipe_count']==19 and meta['rules_version']==3 and meta['board_regeneration_mode']=='full-new'
        targets={p for _,p,_ in outputs}
        for _,p,b in outputs:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        for p,_,_ in outputs:
            if p is not None and p not in targets:p.unlink()

meta=json.loads(Path('site/source-build.json').read_text())
assert meta['game_version']=='1.6.2' and meta['audio_controls']=='settings-only' and meta['loading_lab_music']
assert sha(Path('site/giralab-loading-approved-aecda336.jpg').read_bytes())==ART
print('Exact tested loading-audio 1.6.2 files verified; original artwork preserved.')
