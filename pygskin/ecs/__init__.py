from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Type


class Entity:
    instances: list[Entity] = []

    def __init__(self) -> None:
        self.instances.append(self)

    def __getattr__(self, name: str) -> Any:
        for attr, value in self.__dict__.items():
            if value.__class__.__name__ == name:
                return value
        return self.__getattribute__(name)

    @classmethod
    def has(cls, *components: Type) -> Callable[[Entity], bool]:
        def check(entity):
            for component in components:
                try:
                    getattr(entity, component.__name__)
                except AttributeError:
                    return False
            return True

        return check


class System:
    query: Callable[[Entity], bool]

    def update(self, entities: list[Entity], **kwargs) -> None:
        for entity in self.filter(entities):
            self.update_entity(entity, **kwargs)

    def filter(self, entities: list[Entity]) -> list[Entity]:
        return filter(self.__class__.query, entities)

    def update_entity(self, entity: Entity, **kwargs) -> None:
        pass


class Container:
    @property
    def systems(self) -> list[System]:
        if not hasattr(self, "_systems"):
            setattr(self, "_systems", [])
        return self._systems

    def update(self, **kwargs) -> None:
        for system in self.systems:
            system.update(Entity.instances, **kwargs)
