"""Structured output returned to the game."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Interaction:
    kind: str
    severity: float = 0.0

    def __post_init__(self) -> None:
        if not 0 <= self.severity <= 1:
            raise ValueError("Interaction severity must be between 0 and 1")


@dataclass(frozen=True)
class NPCResponse:
    speech: str
    emotion: str
    action: str = "NONE"
    target_id: str | None = None
    parameters: dict[str, str] = field(default_factory=dict)
    interaction: Interaction | None = None

