"""Game-facing action declarations."""

from dataclasses import dataclass, field

from .personality import Personality
from .state import NPCState


@dataclass(frozen=True)
class ActionDefinition:
    name: str
    description: str
    parameters: tuple[str, ...] = ()


@dataclass
class ActionRegistry:
    actions: dict[str, ActionDefinition] = field(default_factory=dict)

    def register(self, action: ActionDefinition) -> None:
        key = action.name.upper()
        if not key.replace("_", "").isalnum():
            raise ValueError("Action names can contain only letters, numbers, and underscores")
        self.actions[key] = ActionDefinition(key, action.description, action.parameters)

    def get(self, name: str) -> ActionDefinition | None:
        return self.actions.get(name.upper())

    def available_names(self) -> list[str]:
        return sorted(self.actions)


def actions_for_state(registry: ActionRegistry, state: NPCState, personality: Personality) -> list[str]:
    """Return only actions that are safe for the NPC's current state."""
    candidates = {"NONE", "LOOK_AT", "NOD", "SHAKE_HEAD"}
    if state.anger >= 10:
        candidates.add("WARN")
    if state.anger >= 35:
        candidates.update({"THREATEN", "SHOUT"})
    if state.walk_away_pressure >= 45:
        candidates.add("WALK_AWAY")
    if state.fear >= 45:
        candidates.add("FLEE")
    if state.attack_pressure >= 65 and personality.bravery >= 60:
        candidates.add("ATTACK")
    return [name for name in registry.available_names() if name in candidates]
