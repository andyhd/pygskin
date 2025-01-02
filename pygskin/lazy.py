from collections.abc import Callable
from functools import cache
from typing import Generic
from typing import TypeVar

T = TypeVar("T")


class LazyObject(Generic[T]):
    """A lazy object.

    This class is used to defer loading of an object until it is accessed.

    >>> class Foo:
    ...     def __init__(self):
    ...         print("Foo.__init__ called")
    ...         self.bar = 42
    ...
    >>> lazy_foo = LazyObject(Foo)
    >>> lazy_foo.bar
    Foo.__init__ called
    42
    >>> lazy_foo.bar
    42
    >>> isinstance(lazy_foo, Foo)
    True
    """

    def __init__(self, loader: Callable[[], T]) -> None:
        self._loader = loader

    @cache  # noqa: B019
    def _load(self) -> T:
        return self._loader()

    def __getattr__(self, name: str) -> T:
        return getattr(self._load(), name)

    def __setattr__(self, name: str, value: T) -> None:
        if name.startswith("_load"):
            return super().__setattr__(name, value)
        setattr(self._load(), name, value)

    def __delattr__(self, name: str) -> None:
        if name.startswith("_load"):
            raise AttributeError(f"cannot delete attribute '{name}'")
        delattr(self._load(), name)

    __members__ = property(lambda self: self.__dir__())

    def __dir__(self) -> list[str]:
        return dir(self._load())

    @property
    def __class__(self) -> type:
        return self._load().__class__

    @__class__.setter
    def __class__(self, cls: type) -> None:
        pass


def lazy(loader: Callable[[], T]) -> LazyObject[T]:
    """Return a lazy object."""
    return LazyObject(loader)
