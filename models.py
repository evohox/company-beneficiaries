from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Entity:
    id: str
    type: str
    name: str


@dataclass(frozen=True, slots=True)
class Edge:
    owner_id: str
    owned_id: str
    share: float
