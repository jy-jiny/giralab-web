"""Install only the three theme illustrations, preserving all game/UI behavior.
The public build gets an additive stylesheet, not a modified JS bundle.
The original source gets the equivalent CSS so subsequent builds keep the art.
"""
import argparse, hashlib, json, urllib.request
from pathlib import Path

REVISION = 'glossy-20260919'
BASE = 'https://d2ol7oe51mr4n9.cloudfront.net/user_3JNsHXInsB0cN2TvhDobPpxWK8A/'
ASSETS = {
    'music': ('4769ceb5-f73d-4eed-bdd1-a1a9b9ec17fa.webp', 'c78be11c6f37d8ddc392681f7001ea1ec3776933971b58dcc7f4fc98d79e24cf'),
    'war': ('82d7a0cd-5954-4c98-8cce-c4d0012af479.webp', '1bdb007a6250759f3bab54399d324e2c7e7802f611e0239fe83e558a8f0133a7'),
    'robot': ('09501ba8-1baa-434f-8619-4112c65338ae.webp', 'b532ce013059429ee7eca958c85c9139744125660b90498c3f62b9af274ee989'),
}
MARKER = '/* GiraLab theme artwork: glossy-20260919; illustrations only. */'
CSS = '''
/* GiraLab theme artwork: glossy-20260919; illustrations only. */
.theme-lobby .theme-art:is(.theme-art-music, .theme-art-war, .theme-art-robot) > :not(.theme-orbit) {
  visibility: hidden;
}
.theme-lobby .theme-art:is(.theme-art-music, .theme-art-war, .theme-art-robot)::after {
  content: "";
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  max-width: 200px;
  height: 100%;
  margin: auto;
  background-image: var(--theme-illustration);
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;
  filter: drop-shadow(0 8px 8px #0004);
  pointer-events: none;
}
'''

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def install(source, site):
    root = Path('public') if source else Path(site)
    before = {str(p.relative_to(root)): digest(p) for p in root.rglob('*') if p.is_file()}
    dest = root / 'theme-art'
    dest.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, (remote, expected) in ASSETS.items():
        path = dest / f'{name}-{REVISION}.webp'
        if not path.exists():
            request = urllib.request.Request(BASE + remote, headers={'User-Agent': 'GiraLab-art-release'})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
            assert hashlib.sha256(data).hexdigest() == expected, name + ': asset checksum mismatch'
            assert data[:4] == b'RIFF' and data[8:12] == b'WEBP', name + ': not WebP'
            path.write_bytes(data)
        assert digest(path) == expected, name + ': existing asset mismatch'
        hashes[name] = expected
    css = CSS
    for name in ASSETS:
        prefix = '/theme-art/' if source else './'
        css += f'.theme-lobby .theme-art-{name} {{ --theme-illustration: url("{prefix}{name}-{REVISION}.webp"); }}\n'
    if source:
        path = Path('components/theme-lobby.css')
        original = path.read_text()
        if MARKER not in original:
            path.write_text(original.rstrip() + '\n' + css)
        design = Path('docs/game/DESIGN.md')
        if '### 테마 대표 일러스트 (2026-09-19)' not in design.read_text():
            with design.open('a') as f:
                f.write('\n\n### 테마 대표 일러스트 (2026-09-19)\n\n음악·전쟁·로봇의 선 아이콘만 햄버거와 어울리는 입체 일러스트로 교체합니다. 음악은 헤드폰과 음표, 전쟁은 장난감 탱크·비행기·설계도, 로봇은 둥근 흰색 로봇입니다. 자산은 public/theme-art/*-glossy-20260919.webp입니다. 원본은 대화에서 생성한 시안에서 그림만 분리한 투명 WebP이며 시안의 가짜 점수·닉네임·UI는 사용하지 않습니다.\n\nCSS는 해당 세 theme-art 요소 내부만 변경합니다. 햄버거 재료 스프라이트·기린·로딩 이미지·모든 레이아웃·게임·음악·가격·출시 준비 중 상태·저장 기록을 유지합니다. 공개 웹에는 같은 규칙을 별도 CSS로 추가하며 원래 JS와 CSS 번들은 바꾸지 않습니다.\n')
    else:
        (dest / f'theme-art-{REVISION}.css').write_text(css)
        index = root / 'index.html'
        html = index.read_text()
        link = f'<link rel="stylesheet" data-theme-art="{REVISION}" href="./theme-art/theme-art-{REVISION}.css">'
        if link not in html:
            assert html.count('</head>') == 1
            index.write_text(html.replace('</head>', '  ' + link + '\n</head>'))
        meta = root / 'source-build.json'
        data = json.loads(meta.read_text())
        data['theme_art_updated'] = True
        data['theme_art_revision'] = REVISION
        data['theme_art_assets'] = hashes
        data['theme_art_delivery'] = 'additive stylesheet; existing JS/CSS and source_commit preserved'
        meta.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    changed = [name for name, expected in before.items() if not (root / name).exists() or digest(root / name) != expected]
    allowed = set() if source else {'index.html', 'source-build.json'}
    assert set(changed) <= allowed, 'Unrelated published files changed: ' + repr(changed)
    print(json.dumps({'revision': REVISION, 'assets': hashes, 'changedExistingFiles': changed, 'allExistingGameAndAudioAssetsUnchanged': True}, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', action='store_true')
    parser.add_argument('--site', default='site')
    args = parser.parse_args()
    install(args.source, args.site)
