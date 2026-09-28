"""Transparent, deterministic NPC state changes."""

from .personality import Personality
from .response import Interaction
from .state import NPCState


def apply_interaction(state: NPCState, personality: Personality, interaction: Interaction) -> NPCState:
    severity = interaction.severity
    sensitivity = 0.5 + personality.aggressiveness / 100
    if interaction.kind == "insult":
        state.anger += severity * 20 * sensitivity
        state.respect -= severity * 12
        state.trust -= severity * 5
        state.shout_pressure += severity * 18 * sensitivity
        state.walk_away_pressure += severity * (12 - personality.patience / 20)
        state.attack_pressure += severity * 10 * personality.aggressiveness / 100
    elif interaction.kind == "threat":
        state.fear += severity * 18 * (1.5 - personality.bravery / 100)
        state.anger += severity * 12 * sensitivity
        state.suspicion += severity * 15
        state.attack_pressure += severity * 15 * personality.bravery / 100
    elif interaction.kind == "kindness":
        state.happiness += severity * 14 * (0.5 + personality.friendliness / 100)
        state.trust += severity * 12
        state.respect += severity * 6
        state.anger -= severity * 8
    elif interaction.kind == "help":
        state.trust += severity * 16
        state.respect += severity * 10
        state.stress -= severity * 8
    return state.clamp()


def decay(state: NPCState, seconds: float) -> NPCState:
    if seconds < 0:
        raise ValueError("seconds cannot be negative")
    for name, rate in (("anger", .35), ("fear", .25), ("stress", .30), ("shout_pressure", .50), ("walk_away_pressure", .25), ("attack_pressure", .35)):
        setattr(state, name, getattr(state, name) - seconds * rate)
    return state.clamp()

