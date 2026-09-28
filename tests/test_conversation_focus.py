from dataclasses import replace
from core.memory import MemoryStore
from inference import DialogueRequest
from inference.conversation_policy import conversation_messages,repeats


def test_task_context_is_not_recalled_for_smalltalk_and_survives_reopen(tmp_path):
    path=tmp_path/'memory.db'
    with_memory=MemoryStore(path)
    with_memory.remember('guard','p','current delivery','You have a letter for Elena.','host',95,topic='task')
    with_memory.remember_event('guard','p','The player delivered bread.',90,topic='task')
    with_memory.remember('guard','p','player_name','Rowan','player_claim')
    with_memory.close()
    memory=MemoryStore(path)
    try:
        for text in ('yo how you doing','nope i dont','huh','tell me a joke','what is my name?',
                     'do you like Elena?','stop talking about the letter','no mission please'):
            facts=' '.join(memory.recall('guard','p',text))
            assert 'letter' not in facts and 'bread' not in facts
            assert 'Rowan' in facts
        assert 'letter' in ' '.join(memory.recall('guard','p','got any work?'))
        assert 'letter' in ' '.join(memory.recall('guard','p','who is the letter for?'))
        assert memory.facts('guard','p') # Filtering does not delete memories.
    finally:memory.close()


def test_old_loop_is_removed_from_prompt_without_modifying_history():
    history=(('no','You have a letter. Take it.'),('huh','You have a letter. Take it.'),('hi','You have a letter. Take it.'))
    request=DialogueRequest('Marcus','guard','calm','how are you?',history=history)
    messages=conversation_messages(request)
    assert len(messages)==2
    assert messages[-1]['content']=='how are you?'
    assert request.history==history
    assert repeats('You have a letter, take it!',history)
    assert not repeats('Long day. Could use a rest.',history)
    assert not repeats('Yes.',(('okay','Yes.'),))


def test_scene_context_is_not_inserted_into_player_speech():
    request=DialogueRequest('Marcus','guard','calm','hello',observations=('a fountain ahead',))
    messages=conversation_messages(request)
    assert 'fountain' in messages[0]['content']
    assert messages[-1]=={'role':'user','content':'hello'}


def test_background_ownership_is_explicit_and_player_claims_unchanged():
    request=DialogueRequest('Marcus','guard','calm','hello',memories=(
        'job: You guard your gate. (host)', 'opinion: I like you. (player_claim)'))
    prompt=conversation_messages(request)[0]['content']
    assert "Marcus guard Marcus's gate." in prompt
    assert 'I like you. (player_claim)' in prompt


def test_repeat_recovery_is_bounded_and_preserves_conversation_context():
    import threading
    from inference.gpu_service import GPUDialogueEngine
    engine=object.__new__(GPUDialogueEngine)
    engine.closed=False;engine.lock=threading.Lock()
    calls=[]
    def generate(messages,temperature=.65):
        calls.append(messages)
        return 'Take the letter to Elena.' if len(calls)==1 else 'I was distracted. How has your day been?'
    engine._generate=generate
    request=DialogueRequest('Marcus','guard','calm','I just want to chat',
        history=(('got work?','Take the letter to Elena.'),))
    assert engine.respond(request)=='I was distracted. How has your day been?'
    assert len(calls)==2
    assert any(message['content']=='got work?' for message in calls[1])
    assert calls[1][-1]['content']=='I just want to chat'
