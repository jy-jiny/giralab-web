"""Restore exact build bytes; validate all source and output hashes before writing."""
from pathlib import Path
import base64, bsdiff4, hashlib, json, re, zlib

ROOT=Path('site').resolve()
PACKED=Path('deploy-assets/codex-order-web.delta.b64')
SPEC=Path('deploy-assets/codex-order-web.json')
ARTWORK='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
sha=lambda b:hashlib.sha256(b).hexdigest()

def inside(name):
    path=(ROOT/name).resolve()
    if path==ROOT or not path.is_relative_to(ROOT):raise ValueError('Unsafe build path')
    return path

if not PACKED.exists() and not SPEC.exists():
    print('No pending codex-order transfer')
    raise SystemExit(0)
spec=json.loads(SPEC.read_text())
packed=PACKED.read_text().strip()
assert len(packed)==spec['transport_bytes'] and sha(packed.encode())==spec['transport_sha256'],'Source transfer checksum mismatch'
data=json.loads(zlib.decompress(base64.b64decode(packed,validate=True)))
assert data['format']=='bsdiff4' and data['game_version']==spec['game_version']=='1.5.4'
assert data['source_commit']==spec['source_commit'] and re.fullmatch(r'[0-9a-f]{40}',data['source_commit'])
assert data['source_run']==spec['source_run']==35328895977
files=data['files']
assert len(files)==4 and len({f['to'] for f in files})==4
assert {f['to'] for f in files}>={'index.html','source-build.json'}
assert sha((ROOT/'giralab-loading-approved-aecda336.jpg').read_bytes())==ARTWORK

if not all(inside(f['to']).is_file() and sha(inside(f['to']).read_bytes())==f['new'] for f in files):
    outputs=[]
    for f in files:
        source,target=inside(f['from']),inside(f['to'])
        before=source.read_bytes()
        assert sha(before)==f['old'],'Concurrent site change: '+f['from']
        after=bsdiff4.patch(before,base64.b64decode(f['patch'],validate=True))
        assert sha(after)==f['new'],'Build checksum mismatch: '+f['to']
        outputs.append((source,target,after))
    meta=json.loads(next(content for _,target,content in outputs if target.name=='source-build.json'))
    assert meta['source_commit']==spec['source_commit'] and meta['game_version']=='1.5.4'
    assert meta['codex_grouped'] is True and meta['recipe_badge_position']=='below-name'
    assert meta['rare_display_name']=='전설' and meta['board_validity_max_tier']=='advanced'
    assert meta['rules_version']==2 and meta['automatic_board_hints'] is False
    assert meta['approved_image_sha256']==ARTWORK
    for _,target,content in outputs:
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
    targets={target for _,target,_ in outputs}
    for source,_,_ in outputs:
        if source not in targets and source.exists():source.unlink()

(ROOT/'loading-build.json').write_text(json.dumps({
    'sourceRun':data['source_run'],'sourceCommit':data['source_commit'],'artworkSHA256':ARTWORK,
    'dimensions':[864,1536],'imageUnchanged':True,'rulesVersion':2,
    'gameVersion':'1.5.4','automaticBoardHints':False,'boardValidityMaxTier':'advanced','codexGrouped':True,
},indent=2))
print('Verified web 1.5.4 restored: grouped codex and badges below recipe names')
