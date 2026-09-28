from core.actions import ActionDefinition, ActionRegistry, actions_for_state
from core.personality import Personality
from core.state import NPCState


def test_actions_are_normalized() -> None:
    registry = ActionRegistry()
    registry.register(ActionDefinition("give_item", "Give an item", ("item_id",)))
    assert registry.get("GIVE_ITEM") is not None
    assert registry.available_names() == ["GIVE_ITEM"]


def test_attack_is_not_available_until_threshold_is_met() -> None:
    registry = ActionRegistry()
    registry.register(ActionDefinition("NONE", "None"))
    registry.register(ActionDefinition("ATTACK", "Attack"))
    assert "ATTACK" not in actions_for_state(registry, NPCState(attack_pressure=64), Personality(bravery=80))
    assert "ATTACK" in actions_for_state(registry, NPCState(attack_pressure=65), Personality(bravery=80))
