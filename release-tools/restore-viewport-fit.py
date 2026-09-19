"""Apply only the independently verified CSS insertion from the original source build."""
import base64,hashlib,json,os,re,zlib
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
source=os.environ['VIEWPORT_SOURCE_COMMIT'];assert re.fullmatch('[0-9a-f]{40}',source)
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
    for k in ('old_file','new_file','js_old','js_new'):assert re.fullmatch(r'index-[A-Za-z0-9_-]+\.(css|js)',d[k])
    changed={'index.html','source-build.json','loading-build.json',*[f'assets/{d[k]}' for k in ('old_file','new_file','js_old','js_new')]}
    untouched={str(p.relative_to(site)):sha(p.read_bytes()) for p in site.rglob('*') if p.is_file() and str(p.relative_to(site)) not in changed}
    if (assets/d['old_file']).exists():
        old=(assets/d['old_file']).read_bytes();assert sha(old)==d['old_sha'],'Concurrent CSS modification'
        result=old[:d['start']]+base64.b64decode(d['insert'],validate=True)+old[d['start']:]
        assert sha(result)==d['new_sha'],'Unexpected CSS output'
        js=(assets/d['js_old']).read_bytes();assert sha(js)==d['js_sha'],'Game JavaScript changed'
        assert d['new_file'] in d['index'] and d['js_new'] in d['index']
        (assets/d['new_file']).write_bytes(result);(assets/d['js_new']).write_bytes(js)
        (site/'index.html').write_text(d['index'])
        (assets/d['old_file']).unlink();(assets/d['js_old']).unlink()
    else:
        assert sha((assets/d['new_file']).read_bytes())==d['new_sha']
        assert sha((assets/d['js_new']).read_bytes())==d['js_sha']
    meta['source_commit']=source;meta['viewport_fit']='main-and-game-only';meta['dialog_scroll_preserved']=True
    (site/'source-build.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    loading=json.loads((site/'loading-build.json').read_text());loading['sourceCommit']=source;loading['sourceRun']=35409710370
    (site/'loading-build.json').write_text(json.dumps(loading,ensure_ascii=False,indent=2)+'\n')
    for path,digest in untouched.items():assert sha((site/path).read_bytes())==digest,'Unrelated asset changed: '+path
    for name in ('verify-live-loading.py','verify-combo-browser.py'):
        p=Path('scripts')/name;s=p.read_text();assert old_commit in s or source in s;p.write_text(s.replace(old_commit,source))
else:
    assert meta['source_commit']==source and meta['viewport_fit']=='main-and-game-only'
assert sha((assets/'index-CzbeaWCc.css').read_bytes())=='fa5d2c3bc40633bd8f6f5cbe8e850bdb7bf3d1dca36ce1845d3f150a53b7b3d3'
assert sha((assets/'index-C7cJDBlB.js').read_bytes())=='92f35fdb89dbbc4266ffbe54fdd03c7f6ead8039d3dfade2495df4fe9230ad37'
assert sha((site/'giralab-loading-approved-aecda336.jpg').read_bytes())==meta['approved_image_sha256']
assert sha((site/'audio/kitchen-rush.ogg').read_bytes())==meta['game_music_sha256']
print('Exact CSS-only viewport release verified; game JavaScript and every unrelated asset unchanged.')
