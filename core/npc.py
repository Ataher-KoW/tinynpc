"""NPC definition joined to its live state."""

from dataclasses import dataclass, field
from .personality import Personality, SpeechStyle
from .state import NPCState


@dataclass
class NPC:
    npc_id: str
    name: str
    role: str
    personality: Personality = field(default_factory=Personality)
    speech: SpeechStyle = field(default_factory=SpeechStyle)
    state: NPCState = field(default_factory=NPCState)
    conversation_style: tuple[str, ...] = ()
    description: str = ''
