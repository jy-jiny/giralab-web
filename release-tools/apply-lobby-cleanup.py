"""Import only the checksum-verified lobby build; never touch player data or other assets."""
import base64
import hashlib
import json
from pathlib import Path
import zlib
import bsdiff4

ROOT = Path('site')
TRANSFER = Path('deploy-assets/lobby-cleanup-release.b64')
MANIFEST = Path('deploy-assets/lobby-cleanup-release.json')
digest = lambda data: hashlib.sha256(data).hexdigest()

def relative_file(value):
    path = Path(value)
    assert not path.is_absolute() and '..' not in path.parts, 'Unsafe transfer path'
    assert value in ('index.html', 'source-build.json') or (len(path.parts) == 2 and path.parts[0] == 'assets' and path.suffix in ('.js', '.css')), 'Unexpected transfer target'
    return path

if TRANSFER.exists():
    manifest = json.loads(MANIFEST.read_text())
    encoded = ''.join(TRANSFER.read_text().split())
    assert digest(encoded.encode()) == manifest['encoded_sha256'], 'Encoded payload mismatch'
    raw = zlib.decompress(base64.b64decode(encoded, validate=True))
    assert digest(raw) == manifest['payload_sha256'], 'Decoded payload mismatch'
    payload = json.loads(raw)
    assert payload['source_commit'] == manifest['source_commit']
    baseline = json.loads((ROOT / 'source-build.json').read_text())
    assert baseline['source_commit'] == payload['base_source_commit'], 'Published baseline changed; review before applying'
    assert len(payload['files']) == 4
    pending = {}
    for entry in payload['files']:
        path = relative_file(entry['path'])
        oldpath = relative_file(entry['old_path'])
        old = (ROOT / oldpath).read_bytes()
        assert digest(old) == entry['old_sha256'], f'Baseline bytes changed: {oldpath}'
        new = bsdiff4.patch(old, base64.b64decode(entry['delta_b64'], validate=True))
        assert digest(new) == entry['new_sha256'], f'Output bytes mismatch: {path}'
        assert str(path) not in pending, 'Duplicate transfer target'
        pending[str(path)] = new
    assert set(manifest['changed_files']) == set(pending)
    deletes = [relative_file(value) for value in payload['delete_assets']]
    assert all(path.parts[0] == 'assets' and str(path) not in pending for path in deletes)
    code = payload['browser_script']
    compile(code, 'verify-lobby-cleanup.py', 'exec')
    assert 'isolated fixtures' in code and "page.route('**/api/**',fixture)" in code, 'Browser verification must isolate production writes'
    meta = json.loads(pending['source-build.json'])
    assert meta['lobby_revision'] == 'clean-20260919'
    assert meta['theme_art_updated'] is False
    assert meta['source_commit'] == payload['source_commit']
    # All validation completes before any existing build file is modified.
    for value, content in pending.items():
        path = ROOT / value
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    for path in deletes:
        (ROOT / path).unlink()
    Path('release-tools/verify-lobby-cleanup.py').write_text(code)
    print('Imported verified lobby-only source', payload['source_commit'])
else:
    meta = json.loads((ROOT / 'source-build.json').read_text())
    assert meta.get('lobby_revision') == 'clean-20260919', 'No prepared lobby release exists'
    assert Path('release-tools/verify-lobby-cleanup.py').is_file()
    print('Reusing previously verified lobby build', meta['source_commit'])
