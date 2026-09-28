from dataclasses import asdict
import pytest
from core.profile import NPCProfile
from core.http_api import respond
from core.memory import MemoryStore
from core.runtime import NPCRuntime
from inference.conversation_policy import conversation_messages

class Engine:
    def respond(self,request):self.request=request;return 'Hello.'

def test_description_scene_and_player_text_remain_distinct(tmp_path):
    engine=Engine();memory=MemoryStore(tmp_path/'m.db');runtime=NPCRuntime(engine,memory)
    payload={'npc':{'id':'guard','name':'Marcus','description':'Marcus grew up in Northbridge.',
                    'known_facts':['The gate closes at dusk.']},'text':'Hello, how are you?',
             'pov':{'location':'East gate','entities':[{'id':'player','kind':'person','description':'the player','distance':2,'activity':'speaking'}]}}
    try:
        respond(runtime,payload)
        messages=conversation_messages(engine.request)
        assert 'Northbridge' in messages[0]['content']
        assert 'East gate' in messages[0]['content'] and 'speaking' in messages[0]['content']
        assert messages[-1]=={'role':'user','content':'Hello, how are you?'}
        # Editing a profile replaces or removes its authored facts without erasing other memory.
        payload['npc']['known_facts']=[];payload['npc']['description']='Marcus grew up in Lakeside.'
        respond(runtime,payload)
        assert engine.request.character_description.endswith('Lakeside.')
        assert not any(f['key'].startswith('profile fact ') for f in memory.facts('guard','local-player'))
    finally:memory.close()

def test_profile_json_roundtrip_and_bad_types():
    p=NPCProfile.from_dict({'id':'lena','description':'A patient herbalist.','style':{'verbosity':25}})
    assert NPCProfile.from_dict(asdict(p))==p
    with pytest.raises(ValueError):NPCProfile.from_dict({'description':'x'*1001})
    with pytest.raises(ValueError):NPCProfile.from_dict({'known_facts':'not a list'})

def test_named_entity_keeps_its_description():
    from core.perception import PerceivedEntity
    text=PerceivedEntity('courier','person','courier in a blue coat',5,'right',known_name='Medina').describe()
    assert 'Medina' in text and 'blue coat' in text
