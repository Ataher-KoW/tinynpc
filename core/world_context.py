"""Game-supplied facts; the model should not fabricate game truth."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorldContext:
    location: str = ""
    nearby_entities: tuple[str, ...] = ()
    facts: dict[str, str] = field(default_factory=dict)
    events: tuple[str, ...] = ()

