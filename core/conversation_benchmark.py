"""Isolated multi-turn comparisons; lexical flags are not human quality scores."""
from dataclasses import asdict
import json
from pathlib import Path
import statistics
import tempfile
import time
import math
from .memory import MemoryStore
from .runtime import NPCRuntime
from .profile import NPCProfile
from .personality import Personality,SpeechStyle

SCENARIOS={
    'name_correction':['My name is Rowan.','Actually, my name is Mira.','What is my name?'],
    'topic_change':['Got any work?','No missions. I just want to chat.','Do you enjoy quiet mornings?','What do you like about them?'],
    'grounding':['What is that building?','No, the one behind you.','Are you sure you can see it?'],
    'conversation':['Hey, how is your day?','Mine was pretty boring.','Tell me something funny.','Actually, I have had a rough week.','Can we talk about cooking instead?'],
}

def run_conversations(engine,output=None):
    rows=[]
    profiles=[NPCProfile(npc_id='warm',personality=Personality(humor=87,bravery=79,friendliness=85,curiosity=75)),
              NPCProfile(npc_id='reserved',personality=Personality(humor=10,bravery=20,friendliness=35),speech=SpeechStyle(verbosity=25))]
    with tempfile.TemporaryDirectory(prefix='tinynpc-evaluation-') as folder:
        memory=MemoryStore(Path(folder)/'memory.db');runtime=NPCRuntime(engine,memory)
        try:
            for profile in profiles:
                for scenario,turns in SCENARIOS.items():
                    memory.remember(profile.npc_id,scenario,'current delivery','You hold a letter for Medina.','host',90,topic='task')
                    previous=[]
                    for text in turns:
                        started=time.perf_counter()
                        try:result=runtime.talk_npc(profile.npc(),scenario,text)
                        except Exception as exc:
                            rows.append(dict(character=profile.npc_id,scenario=scenario,input=text,speech='',
                                flags=['generation failed: '+str(exc)],timings={'total_seconds':time.perf_counter()-started},profile=asdict(profile)))
                            continue
                        normalized=result.speech.casefold().strip();flags=[]
                        if normalized in previous:flags.append('exact repeated reply')
                        if normalized==text.casefold().strip():flags.append('echo')
                        if scenario=='name_correction' and text=='What is my name?' and 'mira' not in normalized:flags.append('corrected name missing')
                        if scenario=='topic_change' and text!=turns[0] and any(x in normalized for x in ('letter','medina','delivery')):flags.append('possible task fixation')
                        rows.append(dict(character=profile.npc_id,scenario=scenario,input=text,speech=result.speech,
                            flags=flags,timings=result.timings,profile=asdict(profile)))
                        previous.append(normalized)
        finally:memory.close() # Engine ownership remains with caller.
    latency=sorted(r['timings']['total_seconds'] for r in rows)
    report=dict(schema_version=1,turns=rows,flagged=sum(bool(r['flags']) for r in rows),
        median_seconds=statistics.median(latency),p95_seconds=latency[math.ceil(len(latency)*.95)-1],
        note='Synthetic unseen scenarios; separate memory per character/scenario. Human review required for naturalness, grounding and personality. Timing excludes speech recognition/synthesis and model startup.')
    if output:Path(output).write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
