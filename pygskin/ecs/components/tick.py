from dataclasses import dataclass
from typing import Callable


@dataclass
class TickHandler:
    on_tick: Callable[[int], None]
