"""Provides a Structure-of-Arrays (SoA) Entity-Component-System (ECS).

Components are stored in separate dicts, which can improve cache locality.
"""

from typing import Any
from typing import Generic
from typing import TypeVar

T = TypeVar("T")


class Component(Generic[T]):
    """A component for an entity.

    >>> class Position(Component[list[int]]): ...
    >>> class Velocity(Component[list[int]]): ...
    >>> class Mob:
    ...     position: Position = Position()
    ...     velocity: Velocity = Velocity()
    >>> mob = Mob()
    >>> mob.position = [0, 0]
    >>> mob.velocity = [1, 1]
    >>> def velocity_system() -> None:
    ...     for id, vel in Velocity.components.items():
    ...         pos = Position.components[id]
    ...         pos[0] += vel[0]
    ...         pos[1] += vel[1]
    >>> velocity_system()
    >>> mob.position
    [1, 1]
    """

    components: dict[int, T] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        cls.components = {}

    def __get__(self, instance: Any, owner=None) -> T:
        return self.components.get(id(instance))

    def __set__(self, instance: Any, value: T) -> None:
        self.components[id(instance)] = value
