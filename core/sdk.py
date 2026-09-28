"""Convenient text-only session with authored profile facts."""
from inference import create_dialogue_service
from .memory import MemoryStore
from .runtime import NPCRuntime
from .perception import PerceptionFrame

class NPCSession:
    def __init__(self,database,engine=None,enable_speech=False):
        if enable_speech:raise ValueError('This release is text only.')
        self.memory=MemoryStore(database)
        try:self.engine=engine or create_dialogue_service()
        except Exception:self.memory.close();raise
        self.runtime=NPCRuntime(self.engine,self.memory)
        self.closed=False

    def reply(self,profile,text,player_id='local-player',perception=None):
        if self.closed:raise RuntimeError('Session is closed.')
        prefix='profile fact '
        with self.runtime._lock:
            current={f['key']:f for f in self.memory.facts(profile.npc_id,player_id) if f['key'].startswith(prefix)}
            desired={prefix+str(i):fact for i,fact in enumerate(profile.known_facts)}
            for key in current.keys()-desired.keys():self.memory.forget(profile.npc_id,player_id,key)
            for key,value in desired.items():
                if key not in current or current[key]['value']!=value or current[key]['source']!='host':
                    self.memory.remember(profile.npc_id,player_id,key,value,importance=70)
            return self.runtime.talk_npc(profile.npc(),player_id,text,perception or PerceptionFrame())

    def close(self):
        if not self.closed:self.closed=True;self.runtime.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
