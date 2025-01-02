"""Entity-Component-System (ECS) implementation."""

from collections.abc import Callable
from collections.abc import Iterable
from functools import wraps
from typing import Any
from typing import Concatenate
from typing import get_type_hints

FilterFn = Callable[[Any], bool]
SystemFn = Callable[Concatenate[Any, ...], None]


def filter_entities(filter_fn: FilterFn) -> Callable[[SystemFn], SystemFn]:
    """Decorator to set filter function for system.

    >>> def has_velocity(entity):
    ...     return hasattr(entity, "velocity")
    >>> @filter_entities(has_velocity)
    ... def apply_velocity(entity):
    ...     entity.position += entity.velocity
    """

    def _filtered_system(system_fn: SystemFn) -> SystemFn:

        @wraps(system_fn)
        def _system_fn(entity: Any, **kwargs) -> None:
            if filter_fn(entity):
                system_fn(entity, **kwargs)

        _system_fn.filtered = True  # type: ignore[attr-defined]
        return _system_fn

    return _filtered_system


def get_ecs_update_fn(systems: list[SystemFn]) -> Callable:
    """Return an update function for ECS."""
    filter_cache: dict[SystemFn, SystemFn] = {}

    def get_filtered_system_fn(system: SystemFn) -> SystemFn:
        if getattr(system, "filtered", False):
            return system

        if callable(filter := getattr(system, "filter_entities", None)):
            return filter_entities(filter)(system)

        entity_type = next(iter(get_type_hints(system).values()))
        return filter_entities(lambda _: isinstance(_, entity_type))(system)

    def ecs_update(entities: Iterable[Any], **kwargs) -> None:
        """Update entities with systems."""
        for system in systems:
            if not (system_fn := filter_cache.get(system)):
                system_fn = filter_cache[system] = get_filtered_system_fn(system)
            for entity in entities:
                system_fn(entity, entities=entities, **kwargs)

    return ecs_update

