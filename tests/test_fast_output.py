import io
import json
from inference.gpu_service import GPUDialogueEngine

def test_native_output_requires_only_speech_and_streams_it():
    engine=object.__new__(GPUDialogueEngine);engine.settings={'seed':42};captured=[]
    def open_response(path,payload):
        if path=='/apply-template':return io.BytesIO(json.dumps({'prompt':'Hello'}).encode())
        if path=='/tokenize':return io.BytesIO(json.dumps({'tokens':[1]}).encode())
        captured.append(payload)
        event={'choices':[{'delta':{'content':'{"speech":"Hello there."}'}}]}
        return io.BytesIO(('data: '+json.dumps(event)+'\n').encode())
    engine.open=open_response
    assert engine._generate([{'role':'user','content':'Hello'}])=='Hello there.'
    schema=captured[0]['response_format']['schema']
    assert schema['required']==['speech'] and schema['additionalProperties'] is False
    assert captured[0]['seed']==42
