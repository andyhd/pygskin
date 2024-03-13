"""Tetris."""

from __future__ import annotations

import random
from collections import deque
from contextlib import suppress
from dataclasses import InitVar
from dataclasses import dataclass
from dataclasses import field
from functools import cache
from typing import Callable
from typing import ClassVar
from typing import Iterator

import pygame

from pygskin import ecs
from pygskin import gui
from pygskin import layout
from pygskin.clock import Timer
from pygskin.direction import Direction
from pygskin.display import Display
from pygskin.events import KeyDown
from pygskin.events import KeyUp
from pygskin.events import Quit
from pygskin.events import event_listener
from pygskin.pubsub import message
from pygskin.screen import Screen
from pygskin.screen import ScreenManager
from pygskin.window import Window

TETROMINOES_DATA = [
    (184, "magenta"),  # T
    (432, "yellow"),  # O
    (147, "blue"),  # J
    (150, "orange"),  # L
    (1170, "cyan"),  # I
    (408, "green"),  # S
    (240, "red"),  # Z
]


class Square:
    """
    A single square of a tetromino.
    """

    SIZE: ClassVar[int] = 40

    @classmethod
    @cache
    def draw(cls, color_name: str) -> pygame.Surface:
        """Draw a square."""
        w = h = Square.SIZE
        color = pygame.Color(color_name)
        hilite = color.lerp("white", 0.3)
        shadow = color.lerp("black", 0.3)

        image = pygame.Surface((w, h)).convert()
        pygame.draw.polygon(image, hilite, ((0, 0), (w, 0), (0, h)))
        pygame.draw.polygon(image, shadow, ((w, 0), (w, h), (0, h)))
        ox = oy = Square.SIZE * 0.1
        w -= int(ox * 2)
        h -= int(oy * 2)
        pygame.draw.rect(image, color, pygame.Rect(ox, oy, w, h))
        return image


@dataclass
class Tetromino:
    """
    Base class for a shape made of 4 squares.
    """

    bitmask: InitVar[int]
    color: str
    position: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0))
    offsets: list[pygame.Vector2] = field(init=False)

    queue: ClassVar[deque[Tetromino]] = deque(maxlen=3)

    def __post_init__(self, bitmask: int) -> None:
        """
        Initialize non-parameter attributes.
        """
        self.offsets = [
            pygame.Vector2(x - 1, 1 - y)
            for y in range(4)
            for x in range(3)
            if (bitmask >> y * 3) & (2**x)
        ]

    def __iter__(self) -> Iterator[tuple[int, int]]:
        """
        Iterate component square positions.
        """
        for x, y in self.offsets:
            yield int(x + self.position.x), int(y + self.position.y)

    @classmethod
    def random(cls) -> Tetromino:
        """
        Get a random Tetromino.
        """
        return Tetromino(*random.choice(TETROMINOES_DATA))

    @classmethod
    def pop(cls, position: pygame.Vector2) -> Tetromino:
        """
        Pop the next Tetromino off the queue.
        """
        if not cls.queue:
            cls.queue.extend(Tetromino.random() for _ in range(3))
        tetromino = cls.queue.popleft()
        tetromino.move(position - tetromino.position)
        cls.queue.append(Tetromino.random())
        return tetromino

    def rotate(self) -> None:
        """
        Rotate the Tetromino by 90 degrees.
        """
        for offset in self.offsets:
            offset.rotate_ip(90)

    def move(self, vector: pygame.Vector2) -> None:
        """
        Move the Tetromino.
        """
        self.position += vector


class Collision(Exception):
    """Tetromino collision."""


@dataclass
class PlayField(ecs.Entity, pygame.sprite.Sprite):
    """
    Field of play, where Tetrominos fall down and stack up.
    """

    size: InitVar[pygame.Vector2] = field(default=pygame.Vector2(10, 20))
    rows: list[list[str | None]] = field(init=False)

    def __post_init__(self, size: pygame.Vector2) -> None:
        """
        Initialize non-parameter attributes.
        """
        ecs.Entity.__init__(self)
        pygame.sprite.Sprite.__init__(self)

        self.num_cols, self.num_rows = map(int, size)
        self.rows = [[None for _ in range(self.num_cols)] for _ in range(self.num_rows)]
        self.rect = pygame.Rect((0, 0), size * Square.SIZE)
        self._image = pygame.Surface(self.rect.size).convert_alpha()

        self.tetromino = Tetromino.pop(position=pygame.Vector2(4, 0))

        self.rows_removed = message()

    def __hash__(self) -> int:
        return id(self)

    @property
    def image(self) -> pygame.Surface:
        """Get playfield image."""
        image = self._image
        image.fill((0, 0, 0, 0))
        pygame.draw.rect(image, "darkgrey", image.get_rect(), width=1)
        tetromino_squares = list(self.tetromino)
        for y, row in enumerate(self.rows):
            for x, color in enumerate(row):
                if color or (x, y) in tetromino_squares:
                    color = color or self.tetromino.color
                    image.blit(Square.draw(color), pygame.Vector2(x, y) * Square.SIZE)
        return image

    def tetromino_collides(self) -> bool:
        """Check if tetromino collides with squares in the field."""
        for x, y in self.tetromino:
            if y < 0:
                continue
            if y >= self.num_rows or x < 0 or x >= self.num_cols:
                return True
            if self.rows[y][x] is not None:
                return True
        return False

    def move_tetromino(self, vector: pygame.Vector2) -> None:
        """Move tetromino if possible."""
        old_pos = self.tetromino.position.copy()
        self.tetromino.move(vector)
        if self.tetromino_collides():
            self.tetromino.position = old_pos
            raise Collision()

    def rotate_tetromino(self) -> None:
        """Rotate tetromino if possible."""
        old_offsets = list(self.tetromino.offsets)
        self.tetromino.rotate()
        if self.tetromino_collides():
            self.tetromino.offsets = old_offsets
            raise Collision()

    def delete_filled_rows(self) -> int:
        """Remove filled rows and shift upper rows down."""
        removed_rows = []
        for i, row in enumerate(self.rows):
            if all(row):  # filled row
                # shift row data down
                self.rows[1 : i + 1] = self.rows[:i]
                self.rows[0] = [None for _ in range(self.num_cols)]
                removed_rows.append(i)
        if removed_rows:
            self.rows_removed(removed_rows)
        return len(removed_rows)

    def lock_tetromino(self) -> None:
        """Lock tetromino in place."""
        for x, y in self.tetromino:
            self.rows[y][x] = self.tetromino.color


class Preview(ecs.Entity, pygame.sprite.Sprite):
    """Preview the next few tetrominoes."""

    def __init__(self) -> None:
        """Initialize the object."""
        ecs.Entity.__init__(self)
        pygame.sprite.Sprite.__init__(self)

        self.rect = pygame.Rect(0, 0, 200, 560)
        self._image = pygame.Surface(self.rect.size).convert_alpha()

    def __hash__(self) -> int:
        return id(self)

    @property
    def image(self) -> pygame.Surface:
        """Draw the upcoming tetrominoes."""
        image = self._image
        image.fill((0, 0, 0, 0))
        length = len(Tetromino.queue)
        for i, tetromino in enumerate(Tetromino.queue):
            for x, y in tetromino:
                dest = pygame.Vector2(1 + x, 1 + y) * Square.SIZE + (
                    20,
                    20 + (length - 1 - i) * 200,
                )
                image.blit(Square.draw(tetromino.color), dest)
        pygame.draw.rect(image, "darkgrey", image.get_rect(), width=1)
        return image


class ScoreBoard(gui.Container):
    def __init__(self, **kwargs) -> None:
        """Initialize the scoreboard."""
        super().__init__(
            style={
                "background": (0, 0, 0, 0.5),
                "padding": [0, 20],
            }
        )
        self.layout = layout.Fill(direction=Direction.HORIZONTAL)

        self.fields = {
            "score": 0,
            "rows": 0,
            "level": 1,
        }
        self.widgets = {}
        columns = [gui.Container(), gui.Container()]
        ralign = {"style": {"align": "RIGHT"}}

        for name in self.fields.keys():
            columns[0].add_child(gui.Label(name.title()))
            self.widgets[name] = gui.Label(str(self.fields[name]), **ralign)
            columns[1].add_child(self.widgets[name])

            if not hasattr(ScoreBoard, name):
                setattr(
                    ScoreBoard,
                    name,
                    property(
                        # fget=ScoreBoard.get_field(name),
                        fset=ScoreBoard.set_field(name),
                    ),
                )

        self.add_child(columns[0])
        self.add_child(columns[1])

    @classmethod
    def set_field(cls, name: str) -> Callable:
        """Make field and widget setter function."""

        def setter(self, value: int) -> None:
            self.fields[name] = value
            self.widgets[name].set_text(str(value))

        return setter

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the scoreboard."""
        super().draw(surface)
        pygame.draw.rect(
            surface, "darkgrey", pygame.Rect((0, 0), self.rect.size), width=1
        )


class Gameplay(Screen):
    """Gameplay screen."""

    def load(self, *args, **kwargs) -> None:
        """Initialize the screen on load."""
        self.paused = False
        self.drop_timer = Timer(seconds=0.3, delete=False)
        self.score = 0
        self.total_rows = 0
        self.level = 1

        self.systems.append(move_tetromino_down)

        self.field = PlayField()
        self.field.rect.topleft = (20, 20)
        self.field.rows_removed.subscribe(self.add_score)
        self.field.rows_removed.subscribe(self.add_rows)

        self.preview = Preview()
        self.preview.rect.topright = (640, 20)

        self.scoreboard = ScoreBoard()
        self.scoreboard.rect = pygame.Rect(440, 600, 200, 220)

        Display.sprites.add(self.field, self.preview, self.scoreboard)

    def update(self) -> None:
        """Update the screen."""
        super().update(game=self)

    @property
    def ready_to_update(self) -> bool:
        """Update at specific interval."""
        ready = not self.drop_timer.started or self.drop_timer.ended

        if ready:
            self.drop_timer.start()

        return ready

    def add_score(self, rows: list[int]) -> None:
        """Increment score based on number of rows filled at once."""
        self.score += [40, 100, 300, 1200][len(rows) - 1] * self.level
        self.scoreboard.score = self.score

        # TODO hard-drop bonus

    def add_rows(self, rows: list[int]) -> None:
        """Increment count of filled rows."""
        self.total_rows += len(rows)
        self.scoreboard.rows = self.total_rows
        if self.total_rows / 10 > self.level:
            self.level += 1
            self.scoreboard.level = self.level
            self.drop_timer.seconds *= 0.75

    @event_listener
    def move_tetromino(self, event: KeyDown.LEFT | KeyDown.RIGHT) -> None:
        """Move tetromino left or right."""
        with suppress(Collision):
            self.field.move_tetromino(event.direction.vector)

    @event_listener
    def rotate_tetromino(self, _: KeyDown.UP) -> None:
        """Rotate tetromino."""
        with suppress(Collision):
            self.field.rotate_tetromino()

    @event_listener
    def soft_drop(self, _: KeyDown.DOWN) -> None:
        """Speed up tetromino drop speed."""
        self.drop_timer.seconds *= 0.2

    @event_listener
    def end_soft_drop(self, _: KeyUp.DOWN) -> None:
        """Resume previous drop speed."""
        self.drop_timer.seconds *= 5


@ecs.System
def move_tetromino_down(field: PlayField, game: Gameplay, **_) -> None:
    """Move tetromino under gravity."""
    if game.paused or not game.ready_to_update:
        return

    try:
        field.move_tetromino(Direction.DOWN.vector)
    except Collision:
        field.lock_tetromino()
        field.delete_filled_rows()
        field.tetromino = Tetromino.pop(position=pygame.Vector2(4, 0))


class GameOver(Screen):
    """Placeholder."""


class Game(Window, ecs.Entity, ScreenManager):
    """Game window."""

    def __init__(self) -> None:
        """Initialize object."""
        Window.__init__(self, size=(660, 840), title="Tetris")

        self.screen = Gameplay()

    def update(self, **_) -> None:
        """Update current screen."""
        Window.update(self)
        ScreenManager.update(self)

    @event_listener
    def quit(self, _: Quit | KeyDown.ESCAPE) -> None:
        """Quit game."""
        self.running = False

    @Gameplay.transition
    def game_over(self) -> Screen:
        """Transition to game over state."""
        return GameOver()


if __name__ == "__main__":
    Game().run()