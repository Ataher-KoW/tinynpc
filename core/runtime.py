"""Reusable NPC session: the host provides identity and visible world facts."""
from dataclasses import asdict, dataclass
import threading
import time
from inference import DialogueRequest
from .perception import PerceptionFrame
from .profile import character_traits


@dataclass(frozen=True)
class TurnResult:
    speech: str
    seconds: float
    example_id: int
    context: dict | None = None
    state: dict | None = None
    timings: dict | None = None


class NPCRuntime:
    def __init__(self, engine, memory):
        self.engine, self.memory = engine, memory
        self._lock = threading.RLock()
        self._topics={}

    def close(self):
        self.engine.close()
        with self._lock:
            self.memory.close()

    def talk_profile(self,profile,player_id,text,perception=None,on_sentence=None):
        """Apply a developer's JSON character definition, then run one dialogue turn."""
        with self._lock:
            prefix='profile fact '
            current={f['key']:f for f in self.memory.facts(profile.npc_id,player_id) if f['key'].startswith(prefix)}
            desired={prefix+str(i):fact for i,fact in enumerate(profile.known_facts)}
            for key in current.keys()-desired.keys():self.memory.forget(profile.npc_id,player_id,key)
            for key,value in desired.items():
                if key not in current or current[key]['value']!=value or current[key]['source']!='host':
                    self.memory.remember(profile.npc_id,player_id,key,value,importance=70)
            return self.talk_npc(profile.npc(),player_id,text,perception,on_sentence)

    def talk_npc(self, npc, player_id, text, perception=None, on_sentence=None):
        from .state import NPCState
        from .state_engine import apply_interaction
        from .interaction import classify
        from .mood import mood_for
        with self._lock:
            stored = self.memory.load_state(npc.npc_id, player_id)
            previous = npc.state
            npc.state = NPCState(**stored) if stored else NPCState()
            interaction = classify(text)
            apply_interaction(npc.state, npc.personality, interaction)
            try:
                result = self.talk(npc.npc_id, player_id, npc.name, npc.role, text, mood_for(npc), perception,character_traits(npc),on_sentence,npc.description,npc.principles)
            except Exception:
                npc.state = previous
                raise
            self.memory.save_state(npc.npc_id, player_id, asdict(npc.state))
            if interaction.kind != 'neutral':
                self.memory.remember(npc.npc_id, player_id, 'last interaction', interaction.kind, 'interaction',ttl=86400)
            return TurnResult(result.speech,result.seconds,result.example_id,result.context,asdict(npc.state),result.timings)

    def talk(self, npc_id, player_id, name, role, text, mood="calm", perception=None,traits=(),on_sentence=None,character_description='',principles=()):
        text = text.strip()
        if not text or len(text) > 400:
            raise ValueError("Use a message between 1 and 400 characters.")
        perception = perception or PerceptionFrame()
        with self._lock:
            started=time.perf_counter()
            observations = perception.observations(text)
            target,status=perception.resolve(text,self._topics.get((npc_id,player_id),''))
            self.memory.learn_claims(npc_id, player_id, text)
            request = DialogueRequest(name, role, mood, text, observations,
                self.memory.history(npc_id, player_id), self.memory.recall(npc_id, player_id, text),
                tuple(traits),target.describe() if target else '',status,character_description,tuple(principles),self.memory.character_context(npc_id,player_id))
            start = time.perf_counter()
            first_sentence=None
            def streamed(sentence):
                nonlocal first_sentence
                if first_sentence is None:first_sentence=time.perf_counter()-start
                if on_sentence is not None:on_sentence(sentence)
            if on_sentence is not None and hasattr(self.engine, 'respond_stream'):
                speech = self.engine.respond_stream(request, streamed)
            else:
                speech = self.engine.respond(request)
                if on_sentence is not None: on_sentence(speech)
            seconds = time.perf_counter()-start
            record = asdict(request)
            record['perception'] = asdict(perception)
            ident = self.memory.record(npc_id, player_id, record, speech, seconds)
            if target:self._topics[npc_id,player_id]=target.entity_id
            done=time.perf_counter()
            return TurnResult(speech, seconds, ident,record,timings={
                'context_seconds':start-started,'generation_seconds':seconds,
                'storage_seconds':done-start-seconds,'total_seconds':done-started,
                'first_sentence_seconds':first_sentence})
