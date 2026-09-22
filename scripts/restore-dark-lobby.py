"""Restore only the verified public bundle; preserve all game assets and records."""
from pathlib import Path
import base64, hashlib, io, json, os, re, subprocess, urllib.request, zipfile, zlib
ROOT=Path('.').resolve()
SPEC=Path('deploy-assets/dark-lobby.json')
PACKED=Path('deploy-assets/dark-lobby.delta.b64')
IMPORT=Path('deploy-assets/dark-lobby-import.json')
sha=lambda b:hashlib.sha256(b).hexdigest()
ART='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
MUSIC='e53b5d3882d57c8e3a4b1f4179b349fd6f849bec454176b264616ca558c99647'
# Complete Vite releases are already materialized. Verify every build byte;
# legacy delta migration below must not rewrite a newer source or its verifiers.
current=json.loads(Path('site/source-build.json').read_text())
if current.get('release_revision') in ('results-capture-20260921','accounts-20260922','social-login-reset-20260922','web-google-login-20260922','web-account-layout-20260922','web-linked-ranking-20260922'):
    assert re.fullmatch('[0-9a-f]{40}',current['source_commit'])
    expected_source=os.environ.get('GIRALAB_EXPECTED_SOURCE_COMMIT')
    if expected_source: assert current['source_commit']==expected_source,'Unexpected source commit'
    assert current['run_result_dialog'] and current['release_ai_tools'] is False
    assert current['run_result_tiers']==['normal','advanced','legendary','mythic']
    if current.get('release_revision') in ('accounts-20260922','social-login-reset-20260922','web-google-login-20260922','web-account-layout-20260922','web-linked-ranking-20260922'):
        assert current['account_ui'] and current['email_auth_ready'] is False
        assert 'delete-account.html' in current['build_files_sha256']
    if current.get('release_revision') in ('web-google-login-20260922','web-account-layout-20260922','web-linked-ranking-20260922'):
        assert re.fullmatch('[0-9a-f]{40}',current['source_tree'])
        assert current['social_auth_ready'] and current['account_providers']==['google']
        assert current['first_login']=='google-before-nickname' and current['automatic_login']
        assert current['logout_preserves_server_records'] and current['server_records_reset'] is False
        assert current['server_function']=='giralab-game'
        assert current['server_api']=='https://tqqgnrfklhmxwsphjera.supabase.co/functions/v1/giralab-game'
        assert current['google_web_origin']=='https://jy-jiny.github.io'
        assert isinstance(current['google_origin_verified'],bool) and isinstance(current['actual_google_login_verified'],bool)
    hashes=current['build_files_sha256'];assert 'index.html' in hashes and len(hashes)>=10
    for name,expected in hashes.items():
        path=(ROOT/'site'/name).resolve();assert path.is_relative_to(ROOT/'site')
        assert re.fullmatch('[0-9a-f]{64}',expected) and sha(path.read_bytes())==expected,name
    for entry in ['index.html']+(['delete-account.html'] if current.get('account_ui') else []):
        html=(ROOT/'site'/entry).read_text()
        for name in re.findall(r'(?:src|href)="([^"]+)"',html):
            name=name.removeprefix('/giralab-web/').removeprefix('./')
            assert name in hashes,name
    assert sha(Path('site/audio/kitchen-rush.ogg').read_bytes())==MUSIC
    assert sha(Path('site/giralab-loading-approved-aecda336.jpg').read_bytes())==ART
    print('Verified complete results build, approved art/music and production tools boundary.')
    raise SystemExit(0)
import bsdiff4
ALLOWED={'site/index.html','site/source-build.json','site/loading-build.json','scripts/verify-game-music.py','scripts/verify-loading-audio.py','scripts/verify-live-loading.py','scripts/verify-combo-browser.py','scripts/verify-burst-refill.py','scripts/verify-codex-order.py','scripts/verify-theme-lobby.py','scripts/verify-theme-book.py','scripts/verify-dark-lobby.py','release-tools/verify-audio-mythic.py'}
def inside(name):
    assert name in ALLOWED or re.fullmatch(r'site/assets/index-[A-Za-z0-9_-]+\.(js|css)',name),name
    p=(ROOT/name).resolve();assert p.is_relative_to(ROOT) and p!=ROOT
    return p
if IMPORT.exists() and not (SPEC.exists() and PACKED.exists()):
    spec=json.loads(IMPORT.read_text())
    assert spec['game_version']=='1.7.2'
    req=urllib.request.Request(spec['url'],headers={'User-Agent':'GiraLab-Public-Build-Import'})
    with urllib.request.urlopen(req,timeout=90) as response:archive=response.read(30_000_001)
    assert len(archive)<=30_000_000 and sha(archive)==spec['archive_sha256'],'Build archive checksum mismatch'
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        manifest=z.read('build/dark-lobby.json');packed=z.read('build/dark-lobby.delta.b64')
    m=json.loads(manifest)
    assert m['source_commit']==spec['source_commit'] and m['source_run']==spec['source_run']
    assert m['game_version']=='1.7.2' and sha(packed)==m['transport_sha256'] and len(packed)==m['transport_bytes']
    SPEC.parent.mkdir(parents=True,exist_ok=True);SPEC.write_bytes(manifest);PACKED.write_bytes(packed)
parts=sorted(Path('release-tools').glob('dark-lobby-public.part*'))
if parts:
    packed=''.join(''.join(p.read_text().split()) for p in parts)
    assert SPEC.exists(),'Missing independently checksummed build manifest'
    PACKED.write_text(packed)
if SPEC.exists() or PACKED.exists():
    spec=json.loads(SPEC.read_text());packed=''.join(PACKED.read_text().split())
    assert len(packed)==spec['transport_bytes'] and sha(packed.encode())==spec['transport_sha256'],'Transport checksum mismatch'
    data=json.loads(zlib.decompress(base64.b64decode(packed,validate=True)))
    assert data['game_version']==spec['game_version']=='1.7.2'
    assert data['source_commit']==spec['source_commit'] and re.fullmatch('[0-9a-f]{40}',data['source_commit'])
    assert data['source_run']==spec['source_run']
    files=data['files'];assert len(files)==15 and len({f['to'] for f in files})==15
    assert [{k:v for k,v in f.items() if k!='patch'} for f in files]==spec['files']
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
        assert meta['source_commit']==spec['source_commit'] and meta['game_version']=='1.7.2'
        assert meta['theme_lobby_style']=='original-dark' and meta['theme_selection']=='horizontal-scroll'
        assert meta['theme_book'] and meta['theme_book_ids']==['burger','music','war','robot']
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
# UI-only release-state migration: hide planned locked-theme pricing until launch.
for bundle in Path('site/assets').glob('index-*.js'):
    if not bundle.is_file(): continue
    text=bundle.read_text()
    if '1,000원' in text: bundle.write_text(text.replace('1,000원','출시예정'))
book_verify=Path('scripts/verify-theme-book.py')
if book_verify.is_file():
    text=book_verify.read_text()
    if '1,000원' in text: book_verify.write_text(text.replace('1,000원','출시예정'))

audio_verify=Path('release-tools/verify-audio-mythic.py')
if audio_verify.is_file():
    text=audio_verify.read_text()
    text=text.replace("                    page.locator('.home-play').click()\n                    page.get_by_role('button',name='옵션',exact=True).click()","                    page.locator('.home-play').click()")
    text=text.replace("                    page.evaluate('(values)=>{window.__boardDraws=values}',draws)\n                    page.get_by_role('button',name='새 게임',exact=False).click()","                    page.evaluate('(values)=>{window.__boardDraws=values;window.__gameTools.start_game.execute({})}',draws)")
    text=text.replace("                    page.get_by_role('button',name='닫기',exact=True).click()\n                    if page.locator('[data-theme-select=burger]').count(): page.locator('[data-theme-select=burger]').click()\n                    page.locator('.home-play').click()\n                    board=[['lettuce']*6 for _ in range(9)]","                    page.get_by_role('button',name='닫기',exact=True).click()\n                    page.reload(wait_until='domcontentloaded')\n                    expect(page.locator('.home-version')).to_have_text('GiraLab · '+VERSION)\n                    page.locator('.home-version').click()\n                    board=[['lettuce']*6 for _ in range(9)]")
    audio_verify.write_text(text)

burst_verify=Path('scripts/verify-burst-refill.py')
if burst_verify.is_file():
    text=burst_verify.read_text()
    text=text.replace("assert page.evaluate(ANIMS+'.map(a=>a.currentTime)')==positions","actual=page.evaluate(ANIMS+'.map(a=>a.currentTime)');assert len(actual)==len(positions) and all(abs(a-b)<2 for a,b in zip(actual,positions)),(positions,actual)")
    burst_verify.write_text(text)

combo_verify=Path('scripts/verify-combo-browser.py')
if combo_verify.is_file():
    text=combo_verify.read_text()
    text=text.replace("EXPECTED='e5df00ab0a7077fd846003beeca9f47290aa44ac'","EXPECTED='75fd1a5feb8baed95fe34a1b3c568d86c376f9ca'")
    combo_verify.write_text(text)

loading_verify=Path('scripts/verify-live-loading.py')
if loading_verify.is_file():
    text=loading_verify.read_text()
    text=text.replace("COMMIT = 'e5df00ab0a7077fd846003beeca9f47290aa44ac'","COMMIT = '75fd1a5feb8baed95fe34a1b3c568d86c376f9ca'")
    loading_verify.write_text(text)

meta=json.loads(Path('site/source-build.json').read_text())
assert meta['game_version']=='1.7.2' and meta['game_music_title']=='Kitchen Rush'
assert meta['theme_book'] and meta['theme_book_ids']==['burger','music','war','robot']
assert meta['theme_lobby_style']=='original-dark' and meta['theme_selection']=='horizontal-scroll'
assert sha(Path('site/audio/kitchen-rush.ogg').read_bytes())==meta['game_music_sha256']==MUSIC
assert sha(Path('site/giralab-loading-approved-aecda336.jpg').read_bytes())==ART
if parts:subprocess.run(['git','rm','--',*[str(p) for p in parts]],check=True)
print('Verified dark scrollable lobby 1.7.2; existing assets, music, rules and data unchanged.')
