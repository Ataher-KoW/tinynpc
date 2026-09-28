import json
from core.memory import MemoryStore
from core.profile import NPCProfile,character_traits
from core.personality import Personality,SpeechStyle
from core.sdk import NPCSession
from core.conversation_benchmark import run_conversations

class Engine:
    def respond(self,request):return 'That sounds interesting.'
    def close(self):pass

def test_unverified_claim_cannot_overwrite_confirmed_fact(tmp_path):
    m=MemoryStore(tmp_path/'m.db')
    m.remember('n','p','location','gate','host')
    m.remember('n','p','location','market','player_claim')
    facts={r['key']:r for r in m.facts('n','p')}
    assert facts['location']['value']=='gate'
    assert facts['claim:location']['source']=='player_claim'
    m.close()

def test_corrections_and_negated_names(tmp_path):
    m=MemoryStore(tmp_path/'m.db')
    m.learn_claims('n','p','My name is Rowan.')
    m.learn_claims('n','p','Actually, my name is Mira.')
    for text in ("Don't call me Bob.",'My name is not Rowan.','He said call me Fred.','Call me whatever.'):
        m.learn_claims('n','p',text)
    assert m.facts('n','p')[0]['value']=='Mira'
    assert not m.facts('other','p')
    m.close()

def test_retention_dedup_and_review_protection(tmp_path):
    m=MemoryStore(tmp_path/'m.db',max_facts=2,max_turns=3)
    m.remember('n','p','world','confirmed','host')
    first=m.remember_event('n','p','The player waved.')
    assert first==m.remember_event('n','p','The player waved.')
    for i in range(6):m.remember('n','p',f'claim{i}',str(i),'player_claim')
    assert len(m.facts('n','p'))==3
    ident=m.record('n','p',dict(player_text='hi'),'bad reply',0)
    m.review(ident,'accepted','Good reply.')
    bad=m.record('n','p',dict(player_text='hello'),'Wrong.',0);m.review(bad,'rejected')
    assert m.history('n','p')==( ('hi','Good reply.'), )
    for i in range(7):m.record('n','p',dict(player_text=str(i)),'ok',0)
    assert len(m.examples('unreviewed'))==3
    assert len(m.examples('accepted'))==1 and len(m.examples('rejected'))==1
    m.close()

def test_unchanged_profile_facts_are_not_rewritten(tmp_path):
    with NPCSession(tmp_path/'m.db',Engine(),enable_speech=False) as s:
        p=NPCProfile(known_facts=('Gate closes at dusk.',))
        s.reply(p,'hello')
        original=s.memory.remember;calls=[]
        def remember(*a,**kw):calls.append(a);return original(*a,**kw)
        s.memory.remember=remember
        result=s.reply(p,'How is your day?')
        assert not calls
        assert result.timings['total_seconds']>=result.timings['generation_seconds']

def test_style_avoids_automatic_hostility():
    p=NPCProfile(personality=Personality(bravery=90,humor=90),speech=SpeechStyle(sarcasm=90))
    traits=' '.join(character_traits(p.npc()))
    assert 'disagreement need not be hostile' in traits and 'sincere' in traits

def test_benchmark_detects_repetition_without_live_memory():
    result=run_conversations(Engine())
    assert len(result['turns'])==30
    assert result['flagged']>0

def test_smalltalk_word_overlap_does_not_reopen_quest(tmp_path):
    m=MemoryStore(tmp_path/'m.db')
    m.remember('n','p','current delivery','Carry this letter for Medina.','host',90,topic='task')
    for query in ('I need help cooking.','I like writing letters.','I just want to chat about that letter.'):
        assert not m.recall('n','p',query)
    assert m.recall('n','p','Who is the letter for?')
    m.close()
