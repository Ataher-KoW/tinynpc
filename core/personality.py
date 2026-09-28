"""Stable character traits."""

from dataclasses import dataclass


def _validate(value: float, name: str) -> None:
    if not 0 <= value <= 100:
        raise ValueError(f"{name} must be between 0 and 100")


@dataclass(frozen=True)
class Personality:
    friendliness: float = 50
    patience: float = 50
    bravery: float = 50
    aggressiveness: float = 50
    humor: float = 50
    honesty: float = 50
    curiosity: float = 50
    sociability: float = 50

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            _validate(value, name)


@dataclass(frozen=True)
class SpeechStyle:
    swearing: float = 0
    sarcasm: float = 0
    verbosity: float = 50

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            _validate(value, name)

