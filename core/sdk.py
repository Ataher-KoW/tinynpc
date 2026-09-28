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
        return self.runtime.talk_profile(profile,player_id,text,perception or PerceptionFrame())

    def close(self):
        if not self.closed:self.closed=True;self.runtime.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
