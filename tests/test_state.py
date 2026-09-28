from core.personality import Personality
from core.response import Interaction
from core.state import NPCState
from core.state_engine import apply_interaction, decay


def test_insult_raises_anger_and_lowers_respect() -> None:
    state = NPCState(anger=10, respect=70)
    apply_interaction(state, Personality(aggressiveness=60), Interaction("insult", .8))
    assert state.anger > 10
    assert state.respect < 70


def test_decay_cools_without_going_below_zero() -> None:
    state = NPCState(anger=3, shout_pressure=4)
    decay(state, 100)
    assert state.anger == 0
    assert state.shout_pressure == 0
