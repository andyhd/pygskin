from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Protocol
from typing import get_type_hints


class UpdateEntityFunction(Protocol):
    def __call__(self, entity, *args, **kwargs) -> None:
        ...


class System:
    def __init__(self, fn: UpdateEntityFunction | None = None) -> None:
        self.fn = fn
        self.entity_class = object
        if callable(fn):
            hints = get_type_hints(fn)
            self.entity_class = next(iter(hints.values()))

    def filter(self, entity) -> bool:
        return isinstance(entity, self.entity_class)

    def update(self, _entities, *args, **kwargs) -> None:
        for entity in filter(self.filter, _entities):
            self.update_entity(entity, *args, **kwargs)

    def update_entity(self, entity, *args, **kwargs) -> None:
        if callable(self.fn):
            self.fn(entity, *args, **kwargs)


@dataclass
class Container:
    systems: list[System] = field(default_factory=list)
    entities: list = field(default_factory=list)

    def update(self, *args, **kwargs) -> None:
        for system in self.systems:
            system.update(self.entities, *args, **kwargs)
