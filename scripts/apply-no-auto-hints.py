"""Restore an exact tested source build, with no remote imports or runtime rewrites."""
from pathlib import Path
import base64
import bsdiff4
import hashlib
import json
import re
import zlib

ROOT = Path('site').resolve()
SPEC = Path('deploy-assets/no-auto-hints-web.json')
PACKED = Path('deploy-assets/no-auto-hints-web.delta.b64')
sha = lambda value: hashlib.sha256(value).hexdigest()

def inside(name):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or path == ROOT:
        raise ValueError('Unsafe build path')
    return path

if not SPEC.exists() and not PACKED.exists():
    print('No pending no-auto-hints transfer')
    raise SystemExit(0)

spec = json.loads(SPEC.read_text())
packed = PACKED.read_text().strip()
assert sha(packed.encode()) == spec['transport_sha256'], 'Transport checksum mismatch'
data = json.loads(zlib.decompress(base64.b64decode(packed, validate=True)))
assert data['format'] == 'bsdiff4' and data['game_version'] == '1.5.2'
assert data['source_commit'] == spec['source_commit']
assert re.fullmatch(r'[0-9a-f]{40}', data['source_commit'])
files = data['files']
assert len(files) == 4 and len({f['to'] for f in files}) == 4
assert {f['to'] for f in files} >= {'index.html', 'source-build.json'}
artwork = 'aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
assert sha((ROOT / 'giralab-loading-approved-aecda336.jpg').read_bytes()) == artwork

if not all(inside(f['to']).is_file() and sha(inside(f['to']).read_bytes()) == f['new'] for f in files):
    outputs = []
    for f in files:
        source, target = inside(f['from']), inside(f['to'])
        before = source.read_bytes()
        assert sha(before) == f['old'], 'Concurrent build change: ' + f['from']
        after = bsdiff4.patch(before, base64.b64decode(f['patch'], validate=True))
        assert sha(after) == f['new'], 'Reconstructed build mismatch: ' + f['to']
        outputs.append((source, target, after))
    meta = json.loads(next(content for _, target, content in outputs if target.name == 'source-build.json'))
    assert meta['game_version'] == '1.5.2' and meta['automatic_board_hints'] is False
    assert meta['recipe_tier_badges'] is True and meta['rules_version'] == 2
    assert meta['approved_image_sha256'] == artwork
    # Do not alter the durable site until all input and output hashes have matched.
    for _, target, content in outputs:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    targets = {target for _, target, _ in outputs}
    for source, _, _ in outputs:
        if source not in targets and source.exists():
            source.unlink()

(ROOT / 'loading-build.json').write_text(json.dumps({
    'sourceRun': data['source_run'], 'sourceCommit': data['source_commit'],
    'artworkSHA256': artwork, 'dimensions': [864, 1536], 'imageUnchanged': True,
    'rulesVersion': 2, 'gameVersion': '1.5.2', 'automaticBoardHints': False,
}, indent=2))
print('Verified exact web 1.5.2: no automatic board hints; artwork unchanged')
