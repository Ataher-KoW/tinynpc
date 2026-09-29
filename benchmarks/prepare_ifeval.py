"""Download pinned official IFEval files into ignored local evaluation storage."""
import hashlib
import json
from pathlib import Path
import urllib.request

def main():
    root=Path(__file__).resolve().parents[1]
    source=json.loads((Path(__file__).parent/'ifeval-source.json').read_text())
    target=root/'data/ifeval';package=target/'upstream/instruction_following_eval'
    for name,digest in source['sha256'].items():
        url=f"https://raw.githubusercontent.com/google-research/google-research/{source['revision']}/instruction_following_eval/{name}"
        with urllib.request.urlopen(url,timeout=120) as response:data=response.read()
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Upstream checksum mismatch: '+name)
        path=package/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    (target/'source.json').write_text(json.dumps(source,indent=2))
    import nltk
    nltk.download('punkt_tab',download_dir=str(target/'nltk'),raise_on_error=True)
    print('Pinned IFEval inputs and scorer ready.')

if __name__=='__main__':main()
