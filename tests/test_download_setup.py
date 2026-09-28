import hashlib
import io
import pytest
from inference.setup import download

class Response(io.BytesIO):
    status=206
    headers={'Content-Range':'bytes 3-5/6'}

def test_download_resumes_and_verifies(monkeypatch,tmp_path):
    target=tmp_path/'model.bin';target.with_suffix('.bin.part').write_bytes(b'abc')
    def open_request(request,timeout):
        assert request.headers['Range']=='bytes=3-'
        return Response(b'def')
    monkeypatch.setattr('urllib.request.urlopen',open_request)
    digest=hashlib.sha256(b'abcdef').hexdigest()
    assert download('https://example.invalid/model',target,6,digest).read_bytes()==b'abcdef'
    # Already complete files must not trigger another download.
    monkeypatch.setattr('urllib.request.urlopen',lambda *a,**k:pytest.fail('unexpected download'))
    assert download('https://example.invalid/model',target,6,digest)==target

def test_existing_bad_file_is_not_overwritten(tmp_path):
    target=tmp_path/'model.bin';target.write_bytes(b'bad')
    with pytest.raises(ValueError,match='Existing file'):
        download('https://example.invalid/model',target,3,hashlib.sha256(b'yes').hexdigest())
    assert target.read_bytes()==b'bad'

def test_model_parts_assemble_in_order_and_verify(monkeypatch,tmp_path):
    from inference.setup import install_model
    data={'first':b'abc','second':b'def'}
    def fake(url,path,size,digest):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data[url]);return path
    monkeypatch.setattr('inference.setup.download',fake)
    manifest=dict(filename='model.gguf',bytes=6,sha256=hashlib.sha256(b'abcdef').hexdigest(),parts=[
        dict(filename=k,url=k,bytes=3,sha256=hashlib.sha256(v).hexdigest()) for k,v in data.items()])
    result=install_model(manifest,tmp_path)
    assert result.read_bytes()==b'abcdef'
    assert not list((tmp_path/'parts').iterdir())
    assert install_model(manifest,tmp_path)==result
