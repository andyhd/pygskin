from __future__ import annotations

import pygame

from pygskin.pubsub import message


KEYCODE_MAP = {
    f'{"_" if name[2:].isdigit() else ""}{name[2:].lower()}': value
    for name, value in pygame.__dict__.items()
    if name.startswith("K_") and name not in ["K_LAST"]
}


class KeyMeta(type):
    """Metaclass for Key

    Keeps references to singleton Key instances for each keycode, so that only one
    pubsub message exists for each key event.
    """

    def __getattr__(self, name: str) -> Key:
        """Get Key instance by name"""
        keycode = KEYCODE_MAP.get(name)
        if keycode is not None:
            key = Key(keycode)
            setattr(self, name, key)
            return key

    def __getitem__(self, keycode: int) -> Key:
        """Get Key instance by keycode"""
        for name, value in KEYCODE_MAP.items():
            if keycode == value:
                return getattr(self, name)
        raise KeyError(keycode)


class Key(metaclass=KeyMeta):
    def __init__(self, keycode: int) -> None:
        self.keycode = keycode
        self.down = message()
        self.up = message()

    @classmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        key = Key[event.key]
        if event.type == pygame.KEYDOWN:
            key.down(event)
        else:
            key.up(event)


class Mouse:
    class Button:
        def __init__(self, button_num: int) -> None:
            self.num = button_num
            self.down = message()
            self.up = message()

        @classmethod
        def handle_event(self, event: pygame.event.Event) -> None:
            button = Mouse.button[event.button]
            if event.type == pygame.MOUSEBUTTONDOWN:
                button.down(event)
            else:
                button.up(event)

    motion = message()
    button = {
        1: Button(1),
        2: Button(2),
        3: Button(3),
    }

    @classmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        Mouse.motion(event)


class Quit:
    msg = message()

    @classmethod
    def handle_event(cls, event: pygame.event.Event) -> None:
        cls.msg(event)

    @classmethod
    def subscribe(cls, callback: Callable[[pygame.event.Event], None]) -> None:
        cls.msg.subscribe(callback)


class EventSystem:
    """
    >>> Key.space.down.subscribe(lambda ev: print(ev))
    >>> _ = pygame.init()
    >>> _ = pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    >>> EventSystem().update([])
    <Event(768-KeyDown {'key': 32})>
    """

    event_map = {
        pygame.QUIT: Quit,
        pygame.KEYDOWN: Key,
        pygame.KEYUP: Key,
        pygame.MOUSEBUTTONDOWN: Mouse.Button,
        pygame.MOUSEBUTTONUP: Mouse.Button,
        pygame.MOUSEMOTION: Mouse,
    }

    def update(self, *args, **kwargs) -> None:
        for event in pygame.event.get():
            handler = self.event_map.get(event.type)
            if handler:
                handler.handle_event(event)


class EventGroup(list[message]):
    """
    Call a function if any of the listed Events is fired.

    >>> fire = EventGroup([Mouse.button[1].down])
    >>> fire.subscribe(lambda *_: print("BANG!"))
    >>> _ = pygame.init()
    >>> _ = pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1))
    >>> EventSystem().update([])
    BANG!
    """

    def __init__(self, events: list[message]) -> None:
        super().__init__()
        for event in events:
            self.append(event)
        self.callback: Callable | None = None

    def subscribe(self, callback: Callable) -> None:
        self.callback = callback

    def append(self, event: message) -> None:
        super().append(event)
        event.subscribe(self.trigger)

    def remove(self, event: message) -> None:
        super().remove(event)
        event.subscribers.remove(self.trigger)

    def trigger(self, *args) -> None:
        if callable(self.callback):
            self.callback(*args)
