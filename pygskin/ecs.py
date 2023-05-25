from __future__ import annotations

from typing import Any
from typing import ClassVar
from typing import Protocol
from typing import Type


class Entity:
    instances: ClassVar[list[Entity]] = []

    def __init__(self) -> None:
        self.instances.append(self)

    def __getattr__(self, name: str) -> Any:
        for attr, value in self.__dict__.items():
            if value.__class__.__name__ == name:
                return value

        for attr, value in self.__class__.__dict__.items():
            if value.__class__.__name__ == name:
                return getattr(self, attr)

        return self.__getattribute__(name)

    def has(self, *components: Type) -> bool:
        for component in components:
            try:
                getattr(self, component.__name__)
            except AttributeError:
                return False
        return True


class System(Protocol):
    def update(self, entities: list[Entity], **kwargs) -> None:
        for entity in filter(self.filter, entities):
            self.update_entity(entity, **kwargs)

    def filter(self, entity: Entity) -> bool:
        return True

    def update_entity(self, entity: Entity, **kwargs) -> None:
        ...


class Container:
    @property
    def systems(self) -> list[System]:
        if not hasattr(self, "_systems"):
            setattr(self, "_systems", [])
        return self._systems

    def update(self, **kwargs) -> None:
        for system in self.systems:
            system.update(Entity.instances, **kwargs)
