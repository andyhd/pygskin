from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any
from typing import ClassVar
from typing import get_type_hints

from pygskin.utils import Decorator


class Entity:
    instances: ClassVar[list[Entity]] = []

    def __init__(self) -> None:
        self.instances.append(self)

    def __getattr__(self, name: str) -> Any:
        for _, value in self.__dict__.items():
            if value.__class__.__name__ == name:
                return value

        for attr, value in self.__class__.__dict__.items():
            if value.__class__.__name__ == name:
                return getattr(self, attr)

        return self.__getattribute__(name)

    def has(self, *components: type) -> bool:
        return any(isinstance(attr, components) for _, attr in inspect.getmembers(self))


class System(Decorator):
    def update(self, entities: list[Entity], *args, **kwargs) -> None:
        for entity in filter(self.filter, entities):
            self.update_entity(entity, *args, **kwargs)

    def filter(self, entity: Entity) -> bool:
        return isinstance(entity, self.entity_class)

    def update_entity(self, entity: Entity, *args, **kwargs) -> None:
        self.call_function(entity, *args, **kwargs)

    def set_args(self, *args, **kwargs) -> None:
        super().set_args()
        self.filter = kwargs.get("filter", self.filter)

    def set_function(self, fn: Callable) -> None:
        super().set_function(fn)

        hints = get_type_hints(fn)
        self.entity_class = next(iter(hints.values()))


class Container:
    @property
    def systems(self) -> list[System]:
        if not hasattr(self, "_systems"):
            self._systems = []
        return self._systems

    def update(self, **kwargs) -> None:
        for system in self.systems:
            system.update(Entity.instances, **kwargs)
