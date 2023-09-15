from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

import pygame
from pygame.sprite import Sprite

from pygskin import ecs
from pygskin.assets import Assets
from pygskin.clock import Clock
from pygskin.clock import on_tick
from pygskin.direction import Direction
from pygskin.display import Display
from pygskin.events import KeyDown
from pygskin.events import Quit
from pygskin.events import event_listener
from pygskin.grid import Grid
from pygskin.pubsub import message
from pygskin.spritesheet import Spritesheet
from pygskin.text import Text
from pygskin.window import Window

assets = Assets(Path(__file__).parent / "assets")


SNAKE_SPRITE_MAP = {
    "APPLE": (2, 3),
    "HEAD UP": (0, 0),
    "HEAD DOWN": (1, 1),
    "HEAD LEFT": (0, 1),
    "HEAD RIGHT": (1, 0),
    "TAIL UP": (0, 2),
    "TAIL DOWN": (1, 3),
    "TAIL LEFT": (0, 3),
    "TAIL RIGHT": (1, 2),
    "UP LEFT": (3, 0),
    "UP RIGHT": (2, 0),
    "DOWN LEFT": (3, 1),
    "DOWN RIGHT": (2, 1),
    "LEFT UP": (2, 1),
    "LEFT DOWN": (2, 0),
    "RIGHT UP": (3, 1),
    "RIGHT DOWN": (3, 0),
    "UP UP": (2, 2),
    "DOWN DOWN": (2, 2),
    "LEFT LEFT": (3, 2),
    "RIGHT RIGHT": (3, 2),
}


class Cell(pygame.Vector2):
    SIZE = (32, 32)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.elementwise() * Cell.SIZE, Cell.SIZE)

    def __hash__(self) -> str:
        return hash((self.x, self.y, Cell.SIZE))


@dataclass
class Food(ecs.Entity, Sprite):
    spritesheet: Spritesheet
    cell: Cell = field(default_factory=lambda: Cell(0, 0))

    def __post_init__(self) -> None:
        ecs.Entity.__init__(self)
        Sprite.__init__(self, Display.sprites)
        self.cell = Cell(*self.cell)
        self.image = self.spritesheet["APPLE"]

    @property
    def rect(self) -> pygame.Rect:
        return self.cell.rect

    def __hash__(self) -> str:
        return hash(id(self))


@dataclass
class Segment(Sprite):
    cell: Cell
    direction: Direction
    spritesheet: Spritesheet
    prev: Segment | None = None
    next: Segment | None = None
    turning_to: Direction | None = None

    def __post_init__(self) -> None:
        Sprite.__init__(self, Display.sprites)
        self.cell = Cell(*self.cell)
        if self.turning_to is None:
            self.turning_to = self.direction

    @property
    def image(self) -> pygame.Surface:
        if self.next is None:
            return self.spritesheet[f"HEAD {self.direction.name}"]

        if self.prev is None:
            return self.spritesheet[f"TAIL {self.turning_to.name}"]

        return self.spritesheet[f"{self.direction.name} {self.turning_to.name}"]

    @property
    def rect(self) -> pygame.Rect:
        return self.cell.rect

    def __hash__(self):
        return hash(id(self))

    def __iter__(self):
        return iter(self.cell)

    def copy(self, cell: Cell) -> Segment:
        return Segment(cell, self.turning_to, self.spritesheet, self)


class Snake(deque, ecs.Entity):
    def __init__(
        self,
        cell: Cell,
        direction: Direction,
        length: int,
        spritesheet: Spritesheet,
    ) -> None:
        super().__init__()
        ecs.Entity.__init__(self)

        self.eat = message()
        self.interval = 1000 / 7
        self.spritesheet = spritesheet

        self.reset(cell, direction, length, spritesheet)

    def reset(
        self, cell: Cell, direction: Direction, length: int, spritesheet: Spritesheet
    ) -> None:
        self.alive = True
        self.timer = 0

        for segment in self:
            segment.kill()
            segment.prev = None
            segment.next = None
        self.clear()

        cell = cell - direction.vector * (length - 1)
        self.append(Segment(cell, direction, spritesheet))
        for _ in range(length - 1):
            self.grow()

    @property
    def head(self) -> Segment:
        return self[0]

    def grow(self, *_) -> None:
        new_segment = self.head.copy(self.head.cell + self.head.turning_to.vector)
        self.head.next = new_segment
        self.appendleft(new_segment)

    def shrink(self, *_) -> None:
        segment = self.pop()
        if segment.next:
            segment.next.prev = None
        segment.kill()

    @on_tick
    def update_timer(self, dt: int, **_) -> None:
        self.timer -= dt

    @property
    def should_update(self) -> bool:
        if self.timer <= 0:
            self.timer = self.interval
            return self.alive
        return False

    @event_listener
    def turn(
        self, event: KeyDown.LEFT | KeyDown.RIGHT | KeyDown.UP | KeyDown.DOWN
    ) -> None:
        try:
            if event.direction.axis != self.head.direction.axis:
                self.head.turning_to = event.direction
        except AttributeError:
            pass

    @message
    def die(self, *_):
        self.alive = False

    @property
    def cells(self) -> set[Cell]:
        return {segment.cell for segment in self}

    def hit_self(self) -> bool:
        return any(
            segment.cell == self.head.cell
            for segment in self
            if segment is not self.head
        )


class World(Grid):
    snake: Snake

    SIZE = (25, 18)

    def __init__(self, size: tuple[int, int] = SIZE) -> None:
        super().__init__(*size)
        self.food: list[Food] = []

    @property
    def available_cells(self) -> set[Cell]:
        return (
            {Cell(xy) for xy in self}
            - self.snake.cells
            - {food.cell for food in self.food}
        )

    def place(self, food: Food) -> None:
        if food not in self.food:
            self.food.append(food)
        food.cell = random.choice(list(self.available_cells))

    def food_at(self, cell: Cell) -> Food | None:
        for food in self.food:
            if food.cell == cell:
                return food


class Score(Text):
    def __init__(self) -> None:
        self.value = 0
        super().__init__(
            self.text,
            background=(0, 0, 0, 127),
            padding=[20],
        )
        self.add(Display.sprites)

    @property
    def text(self) -> str:
        return f"Score: {self.value}"

    @text.setter
    def text(self, val: str) -> None:
        pass

    def increment(self, *_) -> None:
        self.value += 1
        del self.image


@ecs.system
def move(snake: Snake, world: World, paused: bool, game_over: bool) -> None:
    if snake.should_update and not paused and not game_over:
        snake.grow()

        if snake.hit_self() or snake.head not in world:
            snake.die()

        elif food := world.food_at(snake.head.cell):
            snake.eat(food)
            world.place(food)

        else:
            snake.shrink()


class Game(Window):
    def __init__(self):
        self.world = World()
        self.world.cell_size = Cell.SIZE

        super().__init__(
            title="Snake",
            size=self.world.mapped_size,
            background=(0, 40, 0),
        )

        self.systems.append(move())

        spritesheet = Spritesheet(assets.snake, Grid(4, 4), SNAKE_SPRITE_MAP)

        self.world = World()
        self.world.snake = snake = Snake((0, 0), Direction.RIGHT, 3, spritesheet)
        self.world.place(Food(spritesheet))

        self.score = score = Score()
        self.score.rect.bottom = Display.rect.bottom

        snake.eat.subscribe(score.increment)
        snake.eat.subscribe(assets.eat_sound.play)
        snake.die.subscribe(assets.die_sound.play)
        snake.die.subscribe(self.game_over)

        self.state = {
            "world": self.world,
            "paused": True,
            "game_over": False,
        }

        self.pause_label = Text(
            ("PAUSED\n\nP   - Pause / Unpause\nR   - Restart\nEsc - Quit"),
            background=(0, 0, 255, 128),
            padding=[20],
        )
        self.pause_label.rect.center = Display.rect.center
        self.pause_label.add(Display.sprites)

        self.game_over_label = Text(
            "GAME OVER",
            background=(0, 0, 255, 128),
            padding=[20],
        )
        self.game_over_label.rect.center = Display.rect.center

    def update(self):
        super().update(**self.state)

    @event_listener
    def toggle_pause(self, _: KeyDown.P) -> None:
        if self.state["game_over"]:
            self.state["game_over"] = False
            self.game_over_label.kill()
            self.reset()
            return
        self.state["paused"] = not self.state["paused"]
        if self.state["paused"]:
            self.pause_label.add(Display.sprites)
            self.pause_label.rect.center = Display.rect.center
        else:
            self.pause_label.kill()

    @event_listener
    def reset(self, _: KeyDown.R) -> None:
        self.score.value = -1
        self.score.increment()
        self.world.snake.reset((0, 0), Direction.RIGHT, 3, self.world.snake.spritesheet)

    @event_listener
    def quit(self, _: KeyDown.ESCAPE | Quit) -> None:
        self.running = False

    def game_over(self) -> None:
        self.state["game_over"] = True
        self.game_over_label.add(Display.sprites)


if __name__ == "__main__":
    Game().run()
