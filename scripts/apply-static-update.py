"""Reconstruct the verified build locally; no temporary URLs or private source checkout."""
from pathlib import Path
import base64,hashlib,json,zlib
root=Path('site').resolve()
packed_path=Path('deploy-assets/combo-v2.delta.b64')
packed=packed_path.read_text()
# Normalize the one known staging transcription typo, then enforce the canonical transport checksum.
if 'uprwtMI' in packed: packed=packed.replace('uprwtMI','uprwtpMI',1)
assert hashlib.sha256(packed.encode()).hexdigest()=='93193e585d045e53d2dc1a8156e77ef00be44bcfbe4f9b954e50c6e0ac3e6593', 'Static transport checksum mismatch'
data=json.loads(zlib.decompress(base64.b64decode(packed,validate=True)))
packed_path.write_text(packed)
sha=lambda value:hashlib.sha256(value).hexdigest()
def inside(name):
 p=(root/name).resolve()
 if not p.is_relative_to(root):raise ValueError('Unsafe path')
 return p
if all(inside(f['to']).is_file() and sha(inside(f['to']).read_bytes())==f['new'] for f in data['files']):
 print('Verified combo build already present');raise SystemExit(0)
outputs=[]
for f in data['files']:
 source=inside(f['from']);old=source.read_bytes() if source.exists() else b''
 assert sha(old)==f['old'],f'Existing file changed concurrently: {f["from"]}'
 chunks=[]
 for part in f['pieces']:
  if isinstance(part,list):
   offset,length=part;assert 0<=offset<=len(old) and 0<=length<=len(old)-offset
   chunks.append(old[offset:offset+length])
  else:chunks.append(base64.b64decode(part,validate=True))
 new=b''.join(chunks);assert sha(new)==f['new'],f'Build checksum mismatch: {f["to"]}'
 outputs.append((source,inside(f['to']),new))
# Commit output only once every source and output checksum passed.
for source,target,new in outputs:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(new)
for source,target,_ in outputs:
 if source!=target and source.exists():source.unlink()
assert sha((root/'giralab-loading-approved-aecda336.jpg').read_bytes())=='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
(root/'loading-build.json').write_text(json.dumps({'sourceRun':35319043942,'sourceCommit':data['source_commit'],'artworkSHA256':'aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4','dimensions':[864,1536],'imageUnchanged':True,'rulesVersion':2,'gameVersion':'1.5.0'},indent=2))
print('Reconstructed tested JS, CSS, HTML and build metadata; approved artwork unchanged')
