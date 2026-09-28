"""Mutable per-NPC relationship and emotional state."""

from dataclasses import dataclass


@dataclass
class NPCState:
    anger: float = 0
    fear: float = 0
    stress: float = 0
    happiness: float = 50
    trust: float = 50
    respect: float = 50
    suspicion: float = 0
    shout_pressure: float = 0
    walk_away_pressure: float = 0
    attack_pressure: float = 0

    def clamp(self) -> "NPCState":
        for name, value in self.__dict__.items():
            setattr(self, name, max(0.0, min(100.0, value)))
        return self

    def summary(self) -> str:
        return f"anger={self.anger:.0f}, fear={self.fear:.0f}, trust={self.trust:.0f}, respect={self.respect:.0f}"

