"""Restore only the checksum-verified viewport build; all unrelated assets remain identical."""
import base64,hashlib,json,re,zlib
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
plan=json.loads(Path('deploy-assets/viewport-final.json').read_text())
source=plan['source_commit'];assert re.fullmatch('[0-9a-f]{40}',source)
assert isinstance(plan['source_run'],int) and plan['source_run']>0
assert plan['js_sha']=='92f35fdb89dbbc4266ffbe54fdd03c7f6ead8039d3dfade2495df4fe9230ad37'
for key in ('css_file','js_file'):assert re.fullmatch(r'index-[A-Za-z0-9_-]+\.(css|js)',plan[key])
site=Path('site');assets=site/'assets';packed=Path('deploy-assets/viewport-fit.b64')
meta=json.loads((site/'source-build.json').read_text());old_commit=meta['source_commit']
assert meta['game_version']=='1.7.2' and meta['theme_lobby_style']=='original-dark'
assert meta['theme_selection']=='horizontal-scroll' and meta['recipe_count']==19 and meta['rules_version']==3
assert meta['game_music_title']=='Kitchen Rush' and meta['payments_enabled'] is False
if packed.exists():
    text=packed.read_text().strip()
    assert sha(text.encode())=='d1cc0127342cbed2da4f8d156ee801d54ab3afc1fba2f6f6f48c2301db5583f1','Transport checksum mismatch'
    d=json.loads(zlib.decompress(base64.b64decode(text,validate=True)))
    assert d['remove']==0 and d['start']==16278
    for key in ('old_file','js_old'):assert re.fullmatch(r'index-[A-Za-z0-9_-]+\.(css|js)',d[key])
    changed={'index.html','source-build.json','loading-build.json',*[f'assets/{name}' for name in (d['old_file'],d['js_old'],plan['css_file'],plan['js_file'])]}
    untouched={str(p.relative_to(site)):sha(p.read_bytes()) for p in site.rglob('*') if p.is_file() and str(p.relative_to(site)) not in changed}
    if (assets/d['old_file']).exists():
        old=(assets/d['old_file']).read_bytes();assert sha(old)==d['old_sha'],'Concurrent CSS modification'
        result=old[:d['start']]+base64.b64decode(d['insert'],validate=True)+old[d['start']:]
        assert sha(result)==d['new_sha'],'Base viewport CSS mismatch'
        end=len(result)+1
        for edit in sorted(plan['css_changes_after_v1'],key=lambda e:e['offset'],reverse=True):
            pos=edit['offset'];remove=edit['remove'];assert 0<=pos<=len(result) and 0<=remove and pos+remove<end
            result=result[:pos]+edit['text'].encode()+result[pos+remove:];end=pos
        assert sha(result)==plan['css_sha'],'Final CSS differs from tested source artifact'
        js=(assets/d['js_old']).read_bytes();assert sha(js)==plan['js_sha'],'Game JavaScript changed'
        html=d['index'].replace(d['new_file'],plan['css_file']).replace(d['js_new'],plan['js_file'])
        assert plan['css_file'] in html and plan['js_file'] in html
        (assets/plan['css_file']).write_bytes(result);(assets/plan['js_file']).write_bytes(js)
        (site/'index.html').write_text(html)
        (assets/d['old_file']).unlink();(assets/d['js_old']).unlink()
    else:
        assert sha((assets/plan['css_file']).read_bytes())==plan['css_sha']
        assert sha((assets/plan['js_file']).read_bytes())==plan['js_sha']
    meta['source_commit']=source;meta['viewport_fit']='main-and-game-only';meta['dialog_scroll_preserved']=True
    (site/'source-build.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    loading=json.loads((site/'loading-build.json').read_text());loading['sourceCommit']=source;loading['sourceRun']=plan['source_run']
    (site/'loading-build.json').write_text(json.dumps(loading,ensure_ascii=False,indent=2)+'\n')
    for path,digest in untouched.items():assert sha((site/path).read_bytes())==digest,'Unrelated asset changed: '+path
    for name in ('verify-live-loading.py','verify-combo-browser.py'):
        p=Path('scripts')/name;s=p.read_text();assert old_commit in s or source in s;p.write_text(s.replace(old_commit,source))
else:
    assert meta['source_commit']==source and meta['viewport_fit']=='main-and-game-only'
assert sha((assets/plan['css_file']).read_bytes())==plan['css_sha']
assert sha((assets/plan['js_file']).read_bytes())==plan['js_sha']
assert sha((site/'giralab-loading-approved-aecda336.jpg').read_bytes())==meta['approved_image_sha256']
assert sha((site/'audio/kitchen-rush.ogg').read_bytes())==meta['game_music_sha256']
print('Exact source artifact restored: main/game viewport only; JavaScript and unrelated assets unchanged.')
