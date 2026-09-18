"""Restore an exact tested build; validate all input/output hashes before changes."""
from pathlib import Path
import base64, bsdiff4, hashlib, json, re, zlib

ROOT=Path('site').resolve()
PACKED=Path('deploy-assets/rules-guide-web.delta.b64')
EXPECTED='a757bae0254eda1d8dc609f33d27f4e85e0e58be5bda5d4a394925c6b48778d4'
SOURCE='a234e8d417acaf532d5ffe75825a7c46ff4261f8'
ARTWORK='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
sha=lambda b:hashlib.sha256(b).hexdigest()

def inside(name):
    path=(ROOT/name).resolve()
    if not path.is_relative_to(ROOT) or path==ROOT:
        raise ValueError('Unsafe build path')
    return path

if not PACKED.exists():
    print('No pending rules-guide transfer')
    raise SystemExit(0)
packed=PACKED.read_text().strip()
# Correct the identified text-transfer transcription, then enforce the original
# source builder checksum. No unverified transport or output is ever accepted.
packed=packed.replace('GfJG3/JjxN/VL3Cco','GfJG3/jxN/VL3Cco')
assert len(packed)==21552 and sha(packed.encode())==EXPECTED, 'Source transport checksum mismatch'
data=json.loads(zlib.decompress(base64.b64decode(packed,validate=True)))
assert data['format']=='bsdiff4' and data['game_version']=='1.5.3'
assert data['source_commit']==SOURCE and data['source_run']==35326859620
files=data['files']
assert len(files)==4 and len({f['to'] for f in files})==4
assert {f['to'] for f in files}>={'index.html','source-build.json'}
assert sha((ROOT/'giralab-loading-approved-aecda336.jpg').read_bytes())==ARTWORK

if not all(inside(f['to']).is_file() and sha(inside(f['to']).read_bytes())==f['new'] for f in files):
    outputs=[]
    for f in files:
        source,target=inside(f['from']),inside(f['to'])
        before=source.read_bytes()
        assert sha(before)==f['old'], 'Concurrent site change: '+f['from']
        after=bsdiff4.patch(before,base64.b64decode(f['patch'],validate=True))
        assert sha(after)==f['new'], 'Build checksum mismatch: '+f['to']
        outputs.append((source,target,after))
    meta=json.loads(next(content for _,target,content in outputs if target.name=='source-build.json'))
    assert meta['source_commit']==SOURCE and meta['game_version']=='1.5.3'
    assert meta['board_validity_max_tier']=='advanced' and meta['rules_guide'] is True
    assert meta['tier_palette_version']==2 and meta['recipe_tier_badges'] is True
    assert meta['automatic_board_hints'] is False and meta['approved_image_sha256']==ARTWORK
    for _,target,content in outputs:
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    targets={target for _,target,_ in outputs}
    for source,_,_ in outputs:
        if source not in targets and source.exists():source.unlink()

(ROOT/'loading-build.json').write_text(json.dumps({
    'sourceRun':35326859620,'sourceCommit':SOURCE,'artworkSHA256':ARTWORK,
    'dimensions':[864,1536],'imageUnchanged':True,'rulesVersion':2,
    'gameVersion':'1.5.3','automaticBoardHints':False,'boardValidityMaxTier':'advanced',
},indent=2))
print('Exact tested web 1.5.3 restored: rules guide, clear tiers, normal/advanced board safety')
