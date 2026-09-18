"""Restore the exact verified v1.5.1 build without expiring URLs or remote imports."""
from pathlib import Path
import base64, hashlib, json, re, zlib

root = Path('site').resolve()
sha = lambda value: hashlib.sha256(value).hexdigest()
packed = Path('deploy-assets/combo-v2.delta.b64').read_text().strip()
assert sha(packed.encode()) == 'c8c337f8a0cda783f0eff64e110af9c6f706c73e66a1f6207691a40a53c3e625', 'Transport checksum mismatch'
data = json.loads(zlib.decompress(base64.b64decode(packed, validate=True)))

def inside(name):
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Unsafe build path')
    return path

if all(inside(f['to']).is_file() and sha(inside(f['to']).read_bytes()) == f['new'] for f in data['files']):
    print('Exact verified recipe tier build already present')
    raise SystemExit(0)

outputs = []
for f in data['files']:
    source = inside(f['from'])
    old = source.read_bytes()
    assert sha(old) == f['old'], f'Concurrent build change: {f["from"]}'
    # This is only a lossless transport dictionary, not a runtime code rewrite.
    mapping = f.get('map', {})
    normalized = re.sub(r'[A-Za-z_$][\w$]*|.', lambda match: mapping.get(match[0], match[0]), old.decode(), flags=re.S).encode() if mapping else old
    chunks = []
    for piece in f['pieces']:
        if isinstance(piece, list):
            offset, length = piece
            assert 0 <= offset <= len(normalized) and 0 <= length <= len(normalized) - offset
            chunks.append(normalized[offset:offset + length])
        else:
            chunks.append(base64.b64decode(piece, validate=True))
    new = b''.join(chunks)
    assert sha(new) == f['new'], f'Build checksum mismatch: {f["to"]}'
    outputs.append((source, inside(f['to']), new))

# Write only after every source and reconstructed output has been verified.
for source, target, content in outputs:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
for source, target, _ in outputs:
    if source != target and source.exists():
        source.unlink()
artwork = 'aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
assert sha((root / 'giralab-loading-approved-aecda336.jpg').read_bytes()) == artwork
(root / 'loading-build.json').write_text(json.dumps({'sourceRun':35321477148, 'sourceCommit':data['source_commit'], 'artworkSHA256':artwork, 'dimensions':[864,1536], 'imageUnchanged':True, 'rulesVersion':2, 'gameVersion':'1.5.1'}, indent=2))
print('Exact tested recipe tier JS, CSS, HTML and metadata restored; original artwork unchanged')
