import pytest
from core.http_api import respond
from core.memory import MemoryStore
from core.runtime import NPCRuntime

class Engine:
    def respond(self,request):self.last=request;return 'Hello there.'

def test_api_visibility_memory_and_names(tmp_path):
    engine=Engine();store=MemoryStore(tmp_path/'memory.db');runtime=NPCRuntime(engine,store)
    try:
        payload={'text':'Call me Dev.','player_id':'p','visible_entities':[
            {'id':'door','description':'red door','distance':4},
            {'id':'secret','description':'hidden treasure','distance':1,'visible':False}]}
        assert respond(runtime,payload)['speech']=='Hello there.'
        payload['text']='What is my name?';respond(runtime,payload)
        assert any('Dev' in x for x in engine.last.memories)
        assert not any('treasure' in x for x in engine.last.observations)
        with pytest.raises(ValueError):respond(runtime,dict(payload,visible_entities=[{'id':'x','description':'box','visible':'false'}]))
        with pytest.raises(ValueError):respond(runtime,dict(payload,text='x'*401))
    finally:store.close()
