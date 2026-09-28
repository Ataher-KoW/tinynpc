"""Model-neutral, editable NPC definitions."""
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
from .npc import NPC
from .personality import Personality, SpeechStyle


@dataclass(frozen=True)
class NPCProfile:
    npc_id: str = 'marcus'
    name: str = 'Marcus'
    role: str = 'city guard'
    voice: str = 'steady'
    personality: Personality = field(default_factory=Personality)
    speech: SpeechStyle = field(default_factory=SpeechStyle)
    known_facts: tuple[str,...] = ()
    conversation_style: tuple[str,...] = ()
    description: str = ''

    def __post_init__(self):
        if not isinstance(self.description,str) or len(self.description)>1000:raise ValueError('Description: use at most 1000 characters.')
        for values in (self.known_facts,self.conversation_style):
            if not isinstance(values,(tuple,list)) or any(not isinstance(x,str) or not x.strip() for x in values):raise ValueError('Facts and style notes must be lists of nonempty strings.')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',self.npc_id):raise ValueError('ID: use 1–64 letters, numbers, underscores or hyphens.')
        if not self.name.strip() or len(self.name)>80:raise ValueError('Name: use 1–80 characters.')
        if not self.role.strip() or len(self.role)>160:raise ValueError('Role: use 1–160 characters.')
        if len(self.known_facts)>20 or any(len(x)>240 for x in self.known_facts):raise ValueError('Use up to 20 facts, each at most 240 characters.')
        if len(self.conversation_style)>4 or any(len(x)>200 for x in self.conversation_style):raise ValueError('Use up to 4 conversation style notes, each at most 200 characters.')

    def npc(self):return NPC(self.npc_id,self.name,self.role,self.personality,self.speech,conversation_style=self.conversation_style,description=self.description)

    @classmethod
    def from_dict(cls,data):
        if not isinstance(data,dict):raise ValueError('NPC definition must be an object.')
        for key in ('known_facts','conversation_style'):
            if not isinstance(data.get(key,[]),(list,tuple)):raise ValueError(key+' must be a list.')
        return cls(npc_id=data.get('npc_id',data.get('id','marcus')),name=data.get('name','Marcus'),
            role=data.get('role','city guard'),voice=data.get('voice','steady'),
            personality=Personality(**data.get('personality',{})),speech=SpeechStyle(**data.get('style',data.get('speech',{}))),
            known_facts=tuple(data.get('known_facts',())),conversation_style=tuple(data.get('conversation_style',())),description=data.get('description',''))

    def save(self,directory):
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
        path=directory/(self.npc_id+'.json')
        temp=path.with_suffix('.json.tmp')
        temp.write_text(json.dumps(asdict(self),indent=2),encoding='utf-8');temp.replace(path)
        return path


def character_traits(npc):
    result=[]
    for name,high,low in [('friendliness','friendly','reserved'),('patience','patient','impatient'),
                          ('humor','playful','serious'),('honesty','honest','evasive'),
                          ('curiosity','curious about people','keeps to familiar subjects'),
                          ('sociability','enjoys conversation','private and slow to open up')]:
        value=getattr(npc.personality,name)
        if value>=65:result.append(high)
        elif value<=35:result.append(low)
    if npc.speech.swearing>=65:result.append('occasional mild swearing')
    elif npc.speech.swearing<=10:result.append('avoid swearing')
    if npc.speech.sarcasm>=65:result.append('dry sarcasm')
    if npc.speech.verbosity>=65:result.append('longer replies when useful')
    elif npc.speech.verbosity<=35:result.append('brief replies')
    levels='Style levels (0=low, 50=moderate, 100=high): '+', '.join(
        f'{label}={getattr(npc.personality,key):g}' for key,label in
        [('humor','funny'),('bravery','bold'),('friendliness','friendly'),('patience','patient'),
         ('honesty','honest'),('curiosity','curious'),('sociability','sociable'),('aggressiveness','confrontational')])
    levels+=', '+', '.join(f'{key}={getattr(npc.speech,key):g}' for key in ('sarcasm','swearing','verbosity'))
    behavior=[]
    if npc.personality.bravery>=65:behavior.append('Speak up confidently; disagreement need not be hostile.')
    elif npc.personality.bravery<=35:behavior.append('Express uncertainty or caution without being helpless.')
    if npc.personality.aggressiveness>=65:behavior.append('Be firm when challenged; do not turn ordinary greetings into conflict.')
    if npc.personality.curiosity>=65:behavior.append('Ask a follow-up only when genuinely relevant, not after every reply.')
    if npc.personality.humor>=65:behavior.append('Use occasional situational wit; be sincere when the player is upset.')
    if npc.speech.sarcasm>=65:behavior.append('Aim sarcasm at the situation, not automatically at the player.')
    return (levels,)+tuple(result[:9])+tuple(npc.conversation_style[:4])+tuple(behavior)
