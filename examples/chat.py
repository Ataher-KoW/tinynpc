"""Minimal playable text conversation using the same game-facing API."""
from inference import create_dialogue_service
from core.memory import MemoryStore
from core.runtime import NPCRuntime
from core.profile import NPCProfile
from core.perception import PerceptionFrame,PerceivedEntity

def main():
    print('Loading local dialogue. The first start can take a moment.')
    runtime=NPCRuntime(create_dialogue_service(),MemoryStore('data/example-memory.db'))
    npc=NPCProfile(name='Marcus',role='city guard').npc()
    view=PerceptionFrame(entities=(PerceivedEntity('bakery','building','small stone bakery',12,'left'),))
    print('Marcus is by the town gate. Type /quit to leave.')
    try:
        while True:
            text=input('You: ').strip()
            if text=='/quit':break
            if not text:continue
            result=runtime.talk_npc(npc,'demo-player',text,view)
            print(f'Marcus: {result.speech}\n[{result.seconds:.3f}s generation]')
    except (KeyboardInterrupt,EOFError):pass
    finally:runtime.close()

if __name__=='__main__':main()
