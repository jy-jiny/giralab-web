"""Lossless UTF-8 copy/insert transport; never accept an unverified generated bundle."""
from pathlib import Path
import hashlib,json
root=Path('site');sha=lambda b:hashlib.sha256(b).hexdigest()
trans=Path('deploy-assets/board-regeneration.text.json')
source='fc92a788e5274f03461f6054e36cd43148942bd0'
if not trans.exists():
    assert json.loads((root/'source-build.json').read_text())['game_version']=='1.5.5'
    raise SystemExit(0)
ops=json.loads(trans.read_text())
pairs=[
 ('js','assets/index-DiuLQ_BD.js','assets/index-D4ou0c9Y.js','4d8ff4e7325f1d88e0833ecabb9bbd8ff4cb5a63ae17b8b0a2fe913b1d900196','7caf789100b1c108e3729828f7a2a67e35762b6efe10222269f37ec6f5be5b39'),
 ('css','assets/index-CQNxQXdQ.css','assets/index-CaYzGNQK.css','6d92c7e2c6e59efada4d3671624457ce147cbd5a527d30b33d10d6a2d2403513','9c95c80b8d137af72fd9cef0930a92d67470fb21a9458cbc1d92fb08e7c19ceb'),
]
outputs=[]
for kind,oldname,newname,oldhash,newhash in pairs:
    raw=(root/oldname).read_bytes();assert sha(raw)==oldhash,oldname
    old=raw.decode('utf-8');pieces=[]
    for item in ops[kind]:
        if isinstance(item,list):
            offset,length=item;assert 0<=offset<=len(old) and 0<=length<=len(old)-offset
            pieces.append(old[offset:offset+length])
        else:
            assert isinstance(item,str);pieces.append(item)
    content=''.join(pieces).encode('utf-8');assert sha(content)==newhash,newname
    outputs.append((oldname,newname,content))
html=(root/'index.html').read_bytes();assert sha(html)=='76627d98d78bc88b902c592f7ff394516d3f168d52dc59fdf322fdc6e768ee14'
for _,old,new,_,_ in pairs:html=html.replace(old.encode(),new.encode())
assert sha(html)=='0b0566524ea51b019800abf8faa50f34833093c1011d0ebc6eec488e6c6ff136'
outputs.append(('index.html','index.html',html))
raw=(root/'source-build.json').read_bytes();assert sha(raw)=='2a24ad54ce038800a1d6586eae8b78f75e2e8b7c8d06707d3aee382a1c37ea75'
meta=json.loads(raw);meta.update(source_commit=source,game_version='1.5.5',board_regeneration_mode='full-new',regeneration_animation='preserved',recipe_count=18)
raw=json.dumps(meta,ensure_ascii=False,indent=2).encode();assert sha(raw)=='ffe0644b03a8f9617a7776c183f5a5e72e6e56c2efffa8bc6a01d9a68e2f21a2'
outputs.append(('source-build.json','source-build.json',raw))
assert sha((root/'giralab-loading-approved-aecda336.jpg').read_bytes())=='aecda336dbd02b209b88e906e731e50f78bd882a45a04ea56193b10755501cc4'
# Only commit output bytes after every source and destination hash has matched.
for old,new,content in outputs:
    (root/new).write_bytes(content)
    if old!=new:(root/old).unlink()
(root/'loading-build.json').write_text(json.dumps({'sourceRun':35334546811,'sourceCommit':source,'artworkSHA256':meta['approved_image_sha256'],'dimensions':[864,1536],'imageUnchanged':True,'gameVersion':'1.5.5','rulesVersion':2,'boardRegenerationMode':'full-new'},indent=2))
Path('deploy-assets/board-regeneration-import.json').unlink(missing_ok=True)
print('Restored exact tested 1.5.5 HTML/JS/CSS/metadata; all checksums match source CI build.')
