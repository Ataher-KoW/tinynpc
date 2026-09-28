"""Download verified model and optional native runtime. Standard library only."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parent

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def download(url,path,size,digest):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.stat().st_size==size and sha256(path)==digest:return path
        raise ValueError(f'Existing file does not match manifest: {path}. Rename it before retrying.')
    partial=path.with_suffix(path.suffix+'.part')
    offset=partial.stat().st_size if partial.exists() else 0
    if offset>size:raise ValueError('Partial download exceeds expected size; rename it before retrying.')
    if offset<size:
        request=urllib.request.Request(url,headers={'User-Agent':'TinyNPC/0.1','Range':f'bytes={offset}-'})
        with urllib.request.urlopen(request,timeout=120) as response:
            if response.status==206:
                if not response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
                    raise ValueError('Server returned the wrong resume range.')
            elif response.status==200:offset=0
            else:raise ValueError(f'Unexpected HTTP status: {response.status}')
            with partial.open('ab' if offset else 'wb') as output:
                while block:=response.read(4*1024*1024):
                    offset+=len(block)
                    if offset>size:raise ValueError('Download exceeds manifest size.')
                    output.write(block)
                    print(f'\r{path.name}: {offset/size:.0%}',end='',flush=True)
        print()
    if partial.stat().st_size!=size or sha256(partial)!=digest:
        raise ValueError(f'Checksum failed: {partial}. Rename the partial file before retrying.')
    partial.replace(path)
    return path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',choices=['manual','windows-cuda','windows-cpu'],default='manual')
    args=parser.parse_args()
    if args.runtime!='manual' and platform.system()!='Windows':parser.error('Automatic native setup is Windows only. Use --runtime manual and see docs/integration.md.')
    manifest=json.loads((ROOT/'model-manifest.json').read_text())
    download(manifest['url'],ROOT/'models'/manifest['filename'],manifest['bytes'],manifest['sha256'])
    if args.runtime=='manual':
        print('Model ready. Set server_path in inference/config.json to your llama-server executable.');return
    metadata=json.loads((ROOT/'runtime-release.json').read_text())
    wanted=['llama-b11060-bin-win-cuda-12.4-x64.zip','cudart-llama-bin-win-cuda-12.4-x64.zip'] if args.runtime=='windows-cuda' else ['llama-b11060-bin-win-cpu-x64.zip']
    for name in wanted:
        item=next(a for a in metadata['assets'] if a['name']==name)
        archive=download(item['url'],ROOT/'runtime/downloads'/name,item['bytes'],item['digest'].removeprefix('sha256:'))
        destination=ROOT/'runtime/bin';destination.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist():
                filename=Path(info.filename).name
                if info.is_dir() or not (filename=='llama-server.exe' or filename.endswith('.dll') or filename.lower().startswith(('license','copying'))):continue
                with z.open(info) as source,(destination/filename).open('wb') as target:
                    import shutil
                    shutil.copyfileobj(source,target)
    settings=json.loads((ROOT/'config.json').read_text())
    settings.update(server_path='runtime/bin/llama-server.exe',gpu_layers=99 if args.runtime=='windows-cuda' else 0)
    (ROOT/'config.json').write_text(json.dumps(settings,indent=2)+'\n')
    print('Ready. Run: python -m examples.chat')

if __name__=='__main__':main()
