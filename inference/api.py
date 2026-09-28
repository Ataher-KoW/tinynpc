"""Model-independent dialogue contract shared with games."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DialogueRequest:
    npc_name: str
    npc_role: str
    mood: str
    player_text: str
    observations: tuple[str, ...] = ()
    history: tuple[tuple[str, str], ...] = ()
    memories: tuple[str, ...] = ()
    character_traits: tuple[str, ...] = ()
    reference: str = ""
    reference_status: str = "none"


class DialogueEngine(Protocol):
    def respond(self, request: DialogueRequest) -> str:
        """Return spoken dialogue or raise an error; never execute a game action."""
        ...

    def close(self) -> None:
        """Release owned worker resources."""
        ...
