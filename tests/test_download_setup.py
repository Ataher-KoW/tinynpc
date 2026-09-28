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
