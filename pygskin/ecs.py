"""
Provides an Entity-Component-System (ECS) with automatic component generation from class
attributes.

>>> from pygame import Vector2

>>> class Ball(Entity):
...    pos: Vector2 = lambda: Vector2(1, 1)
...    velocity: Vector2 = lambda: Vector2(0, 0)

>>> ball1 = Ball(velocity=Vector2(2, 3))
>>> ball2 = Ball(velocity=Vector2(5, 4))

>>> @system
... def apply_velocity(pos: Vector2, velocity: Vector2):
...     pos += velocity

>>> apply_velocity()

>>> print(f"{ball1.pos=} {ball2.pos=}")
ball1.pos=Vector2(3, 4) ball2.pos=Vector2(6, 5)
""" 

from abc import ABCMeta
from collections.abc import Callable
from collections.abc import Iterator
from functools import cache
from functools import reduce
from functools import wraps
from inspect import signature
from typing import Any
from typing import ClassVar
from typing import Protocol
from typing import TypeVar
from typing import runtime_checkable

from .sparse_array import SparseArray

NO_DEFAULT = object()
T = TypeVar("T")
EntityT = TypeVar("EntityT", bound="Entity")


@runtime_checkable
class DefaultFactory[T](Protocol):
    def __call__(self) -> T: ...


class Component[T]:
    """A component in the ECS.
    
    Components are used to store data for entities.
    """

    def __init__(self, default: T | DefaultFactory[T] | NO_DEFAULT = NO_DEFAULT):
        self.default = default

    def __set_name__(self, owner: type[EntityT], name: str) -> None:
        if name in ("entity", "eid"):
            raise ValueError(f"Component name '{name}' is reserved")
        self.name = name

    def __set__(self, instance: EntityT, value: T) -> None:
        EntityMeta._components.setdefault(self.name, SparseArray())[instance.eid] = value
        get_component_arrays.cache_clear()

    def __get__(self, instance: EntityT | None, owner: type[EntityT]) -> T:
        if instance is None:
            return self
        return EntityMeta._components[self.name].get(instance.eid)


class EntityMeta(ABCMeta):
    """Metaclass for entities.
    
    This metaclass automatically generates components for entities based on their
    type annotations.
    """

    _components: ClassVar[dict[str, SparseArray]] = {}
    _next_entity_id: ClassVar[int] = 0
    _free_entity_ids: ClassVar[list[int]] = []

    def __new__(
        cls,
        name: str,
        bases: tuple[type, ...],
        ns: dict[str, Any],
    ) -> type[EntityT]:
        """Create a new entity class."""
        for attr, attr_type in ns.get('__annotations__', {}).items():
            if attr in ns and isinstance(ns[attr], type(property())):
                continue
            ns[attr] = Component[attr_type](ns.get(attr, NO_DEFAULT))

        original_init = ns.get("__init__")

        def __init__(self: EntityT, *args: Any, **kwargs: Any) -> None:
            if original_init:
                original_init(self, *args, **kwargs)

            try:
                self.eid = cls._free_entity_ids.pop()
            except IndexError:
                self.eid = cls._next_entity_id
                cls._next_entity_id += 1

            for name, component in ns.items():
                if not isinstance(component, Component):
                    continue
                if name in kwargs:
                    component.__set__(self, kwargs[name])
                elif isinstance(component.default, DefaultFactory):
                    component.__set__(self, component.default())
                elif component.default is not NO_DEFAULT:
                    component.__set__(self, component.default)
                else:
                    raise TypeError(f"Missing required component '{name}'")

        ns["__init__"] = __init__
        return super().__new__(cls, name, bases, ns)


@cache
def get_component_arrays(*names: str) -> tuple[list[SparseArray], set[int]]:
    """Get component arrays and matching entity IDs for the given component names."""
    entity_ids = set()
    if arrays := [EntityMeta._components.get(name, SparseArray()) for name in names]:
        entity_ids = reduce(set.intersection, (a._active for a in arrays))
    return arrays, entity_ids


def get_components(*names: str) -> Iterator[tuple[Any, ...]]:
    """Get component value tuples for entities with all requested components."""
    arrays, entity_ids = get_component_arrays(*names)
    if arrays:
        yield from (tuple(array.get(eid) for array in arrays) for eid in entity_ids)


def map_components(func: Callable[..., None], **context) -> None:
    """Map a function over all entities with the given components.
    
    The function will be called with the components of all entities that have all the
    requested components.
    """
    component_names = [p.name for p in signature(func).parameters.values()]
    for components in get_components(*component_names):
        func(*components, **context)


def system(func: Callable[..., None]) -> Callable[[], None]:
    """Decorate a function to run as a system.
    
    The function will be called with the components of all entities that have all the
    requested components.
    """
    @wraps(func)
    def wrapper(**context):
        map_components(func, **context)
    
    wrapper.is_system = True
    return wrapper


class Entity(metaclass=EntityMeta):
    """An abstract base class for entities in the ECS.
    
    All game entities should inherit from this class and define their components
    as type-annotated class attributes.
    """
    def kill(self) -> None:
        """Remove this entity and all its components."""
        kill_entity(self)


def kill_entity(entity_or_id: int | EntityT) -> None:
    """Remove an entity and all its components."""
    eid = entity_or_id.eid if isinstance(entity_or_id, Entity) else entity_or_id
    
    for component_array in EntityMeta._components.values():
        if eid in component_array:
            del component_array[eid]
    
    EntityMeta._free_entity_ids.append(eid)
    get_component_arrays.cache_clear()


__all__ = [
    "Entity",
    "kill_entity",
    "map_components",
    "system",
]
