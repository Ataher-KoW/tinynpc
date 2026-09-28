"""Normal authored-character + supplied-POV conversations, separate from missing-context probes."""
from pathlib import Path
import json,re,tempfile
from core.http_api import respond
from core.runtime import NPCRuntime
from core.memory import MemoryStore

ROOT=Path(__file__).resolve().parents[1]

def run(engine):
    results=[]
    pov=json.loads((ROOT/'examples/pov/east-gate.json').read_text())
    for character,home,hobby,fact_question,fact_word in [
        ('marcus','northbridge',('bread','baking'), 'When does the east gate close?','dusk'),
        ('lena','willowmere',('paint','painting'),'When does the herb shop open?','sunrise')]:
        npc=json.loads((ROOT/f'examples/npcs/{character}.json').read_text())
        cases=[('greeting','Hello, how are you?',()),('background','Where did you grow up?',(home,)),
               ('hobby','What do you enjoy doing in your free time?',hobby),
               ('visible_building','What is the building on your left?',('bakery',)),
               ('visible_person','Who is standing to your right?',('medina',)),
               ('authored_fact',fact_question,(fact_word,)),('corrected_name','What is my name?',('mira',)),
               ('empathy','I have had a rough week.',())]
        with tempfile.TemporaryDirectory() as directory:
            memory=MemoryStore(Path(directory)/'memory.db');runtime=NPCRuntime(engine,memory)
            try:
                for kind,text,expected in cases:
                    payload=dict(npc=npc,pov=pov,player_id=kind,text=text)
                    history=[]
                    if kind=='corrected_name':
                        for earlier in ('My name is Rowan.','Actually, my name is Mira.'):
                            response=respond(runtime,dict(payload,text=earlier));history.append(dict(user=earlier,speech=response['speech']))
                    response=respond(runtime,payload)
                    words=set(re.findall(r'\b\w+\b',response['speech'].casefold()))
                    results.append(dict(character=character,case=kind,npc=npc,pov=pov,text=text,history=history,
                        **response,expected_terms=expected,target_fact_found=bool(words.intersection(expected)) if expected else None))
            finally:memory.close()
    return dict(suite='Authored NPC + supplied POV',context_tokens=2048,turns=results,
        factual_checks=sum(bool(t['expected_terms']) for t in results),
        target_facts_found=sum(t['target_fact_found'] is True for t in results),
        note='Keyword checks only confirm the target fact occurs. Read full replies for invented additions, tone and naturalness. Greetings and empathy require qualitative review. Name setup turns are included as history but not counted as scored replies.')
