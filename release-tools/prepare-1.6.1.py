"""Reconstruct the verified build atomically in the CI workspace; no remote code imports."""
from pathlib import Path
import base64, bsdiff4, hashlib, json, re
import zlib

ROOT=Path('site').resolve()
SPEC=Path('deploy-assets/release-1.6.1.json')
PARTS=Path('deploy-assets/release-1.6.1.delta.b64')
VERSION='1.6.1'
ART='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
sha=lambda b:hashlib.sha256(b).hexdigest()

def inside(name):
    p=(ROOT/name).resolve()
    if not p.is_relative_to(ROOT) or p==ROOT:raise ValueError('Unsafe output path')
    return p

if SPEC.exists() or PARTS.exists():
    spec=json.loads(SPEC.read_text())
    packed=''.join(PARTS.read_text().split())
    assert len(packed)==spec['transport_bytes'] and sha(packed.encode())==spec['transport_sha256'],'Transfer checksum mismatch'
    data=json.loads(zlib.decompress(base64.b64decode(packed,validate=True)))
    assert data['game_version']==spec['game_version']==VERSION and data['format']=='bsdiff4'
    assert data['source_commit']==spec['source_commit'] and re.fullmatch('[0-9a-f]{40}',data['source_commit'])
    assert data['source_run']==spec['source_run']
    files=data['files'];assert len(files)==5 and len({f['to'] for f in files})==5
    assert {f['to'] for f in files}>={'index.html','source-build.json','loading-build.json'}
    assert sha(inside('giralab-loading-approved-aecda336.jpg').read_bytes())==ART
    if not all(inside(f['to']).is_file() and sha(inside(f['to']).read_bytes())==f['new'] for f in files):
        outputs=[]
        for f in files:
            source,target=inside(f['from']),inside(f['to'])
            old=source.read_bytes();assert sha(old)==f['old'],'Concurrent site change: '+f['from']
            new=bsdiff4.patch(old,base64.b64decode(f['patch'],validate=True))
            assert sha(new)==f['new'],'Output differs from tested build: '+f['to']
            outputs.append((source,target,new))
        meta=json.loads(next(b for _,p,b in outputs if p.name=='source-build.json'))
        assert meta['source_commit']==spec['source_commit']
        assert meta['recipe_count']==19 and meta['rules_version']==3
        assert meta['board_regeneration_mode']=='full-new' and meta['regeneration_animation']=='preserved'
        assert meta['audio_scene_tracks'] and meta['autoplay_recovery'] and meta['mythic_recipe']=='forbidden-seven'
        targets={p for _,p,_ in outputs}
        for _,p,b in outputs:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        for p,_,_ in outputs:
            if p not in targets:p.unlink()

meta=json.loads(inside('source-build.json').read_text())
assert meta['game_version']==VERSION and meta['rules_version']==3 and meta['recipe_count']==19
assert meta['board_validity_max_tier']=='advanced' and meta['board_regeneration_mode']=='full-new'
assert meta['automatic_board_hints'] is False and meta['recipe_badge_position']=='below-name'
assert sha(inside('giralab-loading-approved-aecda336.jpg').read_bytes())==ART
revision=meta['source_commit']

# Existing regressions keep testing the same features against the current release.
p=Path('scripts/verify-live-loading.py');s=p.read_text()
s=re.sub(r"^COMMIT = '[0-9a-f]+'$",'COMMIT = '+repr(revision),s,flags=re.M);p.write_text(s)
p=Path('scripts/verify-combo-browser.py');s=p.read_text().replace('1.5.5',VERSION)
s=re.sub(r"^EXPECTED='[0-9a-f]+'$",'EXPECTED='+repr(revision),s,flags=re.M)
s=s.replace('data-balance-version="2"','data-balance-version="3"').replace("['rulesVersion']==2","['rulesVersion']==3").replace("['rules_version']==2","['rules_version']==3")
p.write_text(s)
p=Path('scripts/verify-board-regeneration.py');s=p.read_text().replace('1.5.5',VERSION).replace("['recipe_count']==18","['recipe_count']==19").replace("['rules_version']==2","['rules_version']==3");p.write_text(s)
p=Path('scripts/verify-codex-order.py');s=p.read_text().replace('1.5.5',VERSION)
if "('forbidden-seven','금단의 7층 버거'" not in s:
    anchor="]\nLABELS="
    assert s.count(anchor)==1
    s=s.replace(anchor," ('forbidden-seven','금단의 7층 버거','mythic','일곱 층의 금단 실험. 빵 사이를 다섯 장의 베이컨으로만 채워보세요.'),\n"+anchor)
    anchor='\n\ndef verify(base,out):'
    assert s.count(anchor)==1
    s=s.replace(anchor,"\nLABELS['mythic']='신화 조합'\nCOLORS['mythic']='rgb(107, 33, 168)'\n"+anchor)
s=s.replace('to_have_count(18)','to_have_count(len(ROWS))').replace('to_have_count(18-len(unlocked))','to_have_count(len(ROWS)-len(unlocked))')
s=s.replace('expect(headings).to_have_count(3)','expect(headings).to_have_count(4)')
s=s.replace("['일반','고급','전설']","['일반','고급','전설','신화']").replace("['5종','9종','4종']","['5종','9종','4종','1종']")
s=s.replace('if i in (0,5,14):','if i in (0,5,14,18):')
s=s.replace("else '슬로우 4초'","else '슬로우 6초' if tier=='mythic' else '슬로우 4초'") if "else '슬로우 6초'" not in s else s
s=s.replace("'badgesBelowNames':18","'badgesBelowNames':len(ROWS)")
p.write_text(s)
# The detailed audio/mythic guide supersedes the old 3-tier/5-section guide verifier.
p=Path('scripts/verify-rules-guide.py')
p.write_text('import runpy\nfrom pathlib import Path\nif __name__ == "__main__":\n    runpy.run_path(str(Path(__file__).resolve().parents[1]/"release-tools/verify-audio-mythic.py"),run_name="__main__")\n')
print('Exact 1.6.1 build and all regression bindings prepared:',revision)
