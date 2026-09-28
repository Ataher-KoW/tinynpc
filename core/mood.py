"""Deterministic mood labels; independent of inference implementation."""
def mood_for(npc):
    if npc.state.fear >= 45: return "frightened"
    if npc.state.anger >= 35: return "angry"
    if npc.state.anger >= 10: return "irritated"
    return "calm"
