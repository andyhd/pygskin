"""Provides a sparse array implementation for ECS component storage."""

from collections.abc import Iterator
from typing import Generic
from typing import TypeVar

T = TypeVar("T")


class SparseArray(Generic[T]):
    """A sparse array optimized for ECS component storage.
    
    >>> arr = SparseArray[int](initial_capacity=4)
    >>> arr[0] = 1
    >>> arr[3] = 4
    >>> list(arr)  # Only iterates over active elements
    [1, 4]
    >>> arr[0]  # Direct access
    1
    >>> 0 in arr  # Check if index is active
    True
    """
    
    def __init__(self, *, initial_capacity: int = 1024) -> None:
        """Initialize a new sparse array.
        
        Args:
            initial_capacity: Initial size of the internal array
        """
        self._values = [None] * initial_capacity
        self._active: set[int] = set()
        self._capacity = initial_capacity
    
    def __getitem__(self, index: int) -> T:
        """Get value at index. Raises KeyError if index not active."""
        if index not in self._active:
            raise KeyError(f"No value at index {index}")
        return self._values[index]
    
    def __setitem__(self, index: int, value: T) -> None:
        """Set value at index, expanding array if needed."""
        if index >= self._capacity:
            self._expand(new_size=max(index + 1, self._capacity * 2))
        self._values[index] = value
        self._active.add(index)
    
    def __delitem__(self, index: int) -> None:
        """Remove value at index."""
        if index not in self._active:
            raise KeyError(f"No value at index {index}")
        self._values[index] = None
        self._active.remove(index)
    
    def __contains__(self, index: int) -> bool:
        """Check if index has a value."""
        return index in self._active
    
    def __iter__(self) -> Iterator[T]:
        """Iterate over active values in insertion order."""
        return (self._values[i] for i in sorted(self._active))
    
    def __len__(self) -> int:
        """Get number of active elements."""
        return len(self._active)
    
    @property
    def active_indices(self) -> list[int]:
        """Get list of active indices in sorted order."""
        return sorted(self._active)
    
    @property
    def capacity(self) -> int:
        """Get current capacity of array."""
        return self._capacity
    
    def clear(self) -> None:
        """Remove all values."""
        for index in self._active:
            self._values[index] = None
        self._active.clear()
    
    def get(self, index: int, default: T | None = None) -> T | None:
        """Get value at index, returning default if not active."""
        return self._values[index] if index in self._active else default
    
    def _expand(self, new_size: int) -> None:
        """Expand internal array to new size."""
        self._values.extend([None] * (new_size - self._capacity))
        self._capacity = new_size
