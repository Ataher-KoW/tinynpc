import json
import pytest
from core.memory import MemoryStore
from core.runtime import NPCRuntime
from core.npc import NPC
from core.perception import PerceptionFrame, PerceivedEntity


class Engine:
    def respond(self, request):
        self.request=request
        return 'Good to see you.'


def test_memory_persists_and_isolates_players_and_npcs(tmp_path):
    path=tmp_path/'memory.db'
    store=MemoryStore(path)
    engine=Engine();runtime=NPCRuntime(engine,store)
    runtime.talk('guard','sam','Marcus','guard','My name is Sam')
    store.close()
    store=MemoryStore(path)
    try:
        assert 'Sam' in store.recall('guard','sam','name')[0]
        assert store.history('guard','sam')[0][0]=='My name is Sam'
        assert not store.recall('guard','other')
        assert not store.history('bartender','sam')
        runtime=NPCRuntime(engine,store)
        runtime.talk('guard','sam','Marcus','guard','what is my name?')
        assert 'Sam' in engine.request.memories[0]
    finally:store.close()


def test_state_persists_without_leaking_to_other_player(tmp_path):
    store=MemoryStore(tmp_path/'memory.db')
    try:
        runtime=NPCRuntime(Engine(),store);npc=NPC('guard','Marcus','guard')
        runtime.talk_npc(npc,'one','fuck you')
        anger=npc.state.anger
        assert anger>0
        runtime.talk_npc(npc,'two','hello')
        assert npc.state.anger==0
        runtime.talk_npc(npc,'one','hello')
        assert npc.state.anger==anger
    finally:store.close()


def test_visibility_and_image_capability_are_explicit(tmp_path):
    frame=PerceptionFrame((PerceivedEntity('secret','building','secret lab',1,visible=False),
        PerceivedEntity('cart','prop','wooden cart',3)))
    assert all('secret' not in text for text in frame.observations())
    assert 'wooden cart' in frame.observations()[0]
    with pytest.raises(ValueError,match='pixel understanding'):
        PerceptionFrame(image_path='photo.png').observations()
    with pytest.raises(ValueError,match='does not exist'):
        PerceptionFrame(image_path='missing.png',caption='a cart').observations()


def test_only_approved_corrected_examples_export(tmp_path):
    store=MemoryStore(tmp_path/'memory.db')
    try:
        for text in ['one','two','three']:
            store.record('npc','player',{'player_text':text},'bad answer',.1)
        store.review(1,'accepted','Corrected answer.')
        store.review(2,'rejected')
        path=tmp_path/'accepted.jsonl'
        assert store.export(path)==1
        assert json.loads(path.read_text())['speech']=='Corrected answer.'
        with pytest.raises(ValueError):store.review(999,'accepted')
    finally:store.close()


def test_failed_generation_does_not_record_a_training_answer(tmp_path):
    class Failing:
        def respond(self,request):raise RuntimeError('failed')
    store=MemoryStore(tmp_path/'memory.db')
    try:
        npc=NPC('guard','Marcus','guard')
        with pytest.raises(RuntimeError):NPCRuntime(Failing(),store).talk_npc(npc,'one','fuck you')
        assert npc.state.anger==0
        assert not store.examples()
        assert store.load_state('guard','one') is None
    finally:store.close()
