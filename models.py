from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Entity:
    id: str
    type: str
    name: str
