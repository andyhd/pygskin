from __future__ import annotations

import random
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import pygame
from pygame.sprite import Sprite
from pygame.sprite import collide_rect

from pygskin import CachedSpritesheet
from pygskin import Direction
from pygskin import KeyDown
from pygskin import Sound
from pygskin import Spritesheet
from pygskin import message
from pygskin.ecs import Container
from pygskin.ecs import Entity
from pygskin.ecs import System
from pygskin.ecs.components import EventMap
from pygskin.ecs.systems import DisplaySystem
from pygskin.ecs.systems import EventSystem
from pygskin.ecs.systems import IntervalSystem


class Config:
    CELL_SIZE = (32, 32)
    WORLD_SIZE = (20, 15)
    FPS = 100


class SnakeSprites(CachedSpritesheet):
    filename = Path(__file__).parent / "images/snake.png"
    grid = (4, 4)
    names = {
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


@dataclass
class Segment(Sprite):
    rect: pygame.Rect
    direction: Direction
    spritesheet: Spritesheet
    turning_to: Direction | None = None
    is_head: bool = False
    is_tail: bool = False

    def __post_init__(self):
        super().__init__()
        if self.turning_to is None:
            self.turning_to = self.direction

    @property
    def image(self):
        key = f"{self.direction.name} {self.turning_to.name}"

        if self.is_tail:
            key = f"TAIL {self.turning_to.name}"

        if self.is_head:
            key = f"HEAD {self.direction.name}"

        return self.spritesheet[key]

    def __hash__(self):
        return hash(f"{id(self)}")


class Body(list[Segment]):
    pass


class Flags(dict[str, bool]):
    pass


class Snake(Entity):
    def __init__(self, pos, facing, length, spritesheet):
        rect = pygame.Rect(*pos, *Config.CELL_SIZE)
        self.body = Body(
            [
                Segment(
                    rect.move(*(facing.vector * -i)),
                    facing,
                    spritesheet,
                    is_head=i == 0,
                    is_tail=i == length - 1,
                )
                for i in range(length)
            ]
        )
        self.flags = Flags(
            alive=True,
            is_eating=False,
        )

    @property
    def head(self):
        return self.body[0]

    def grow(self):
        self.head.is_head = False
        self.body.insert(
            0,
            Segment(
                self.head.rect.move(
                    *(self.head.turning_to.vector.elementwise() * Config.CELL_SIZE)
                ),
                self.head.turning_to,
                self.head.spritesheet,
                is_head=True,
            ),
        )
        DisplaySystem.sprite_group.add(self.head)

    def shrink(self):
        if len(self.body) > 3:
            tail = self.body.pop()
            self.body[-1].is_tail = True
            tail.kill()

    def turn(self, direction):
        if direction.axis != self.head.direction.axis:
            self.head.turning_to = direction

    @message
    def die(self, *_):
        self.Flags["alive"] = False

    @message
    def eat(self, *_):
        self.Flags["is_eating"] = True


class Food(Sprite, Entity):
    def __init__(self, spritesheet):
        super().__init__()
        self.image = spritesheet[(2, 3)]
        self.rect = self.image.get_rect()
        DisplaySystem.sprite_group.add(self)

    def place(self, world):
        available_cells = list(
            world.cells.difference(
                *([s.rect.topleft for s in snake.body] for snake in world.snakes)
            )
        )
        self.rect.topleft = random.choice(available_cells)


class GrowShrinkSnakes(IntervalSystem):
    interval = 1000 / 7
    query = Entity.has(Body, Flags)

    def update_entity(self, snake, **kwargs):
        if snake.Flags["alive"]:
            snake.grow()

            if snake.Flags["is_eating"]:
                snake.Flags["is_eating"] = False
            else:
                snake.shrink()


class Eating(System):
    def query(x):
        return isinstance(x, Food)

    def update_entity(self, food, world):
        for snake in world.snakes:
            if snake.Flags["is_eating"]:
                continue
            if collide_rect(snake.head, food):
                snake.eat(food)
                food.place(world)


class Collisions(System):
    query = Entity.has(Body, Flags)

    def update_entity(self, snake, world):
        for other in world.snakes:
            if any(
                collide_rect(snake.head, segment)
                for segment in other.Body
                if segment != snake.head
            ):
                if snake.Flags["alive"]:
                    snake.die()


class World(dict):
    def __getattr__(self, name):
        return self.__getitem__(name)

    def __setattr__(self, name, value):
        self[name] = value


class Game(Entity):
    def __init__(self):
        super().__init__()

        self.running = True

        self.world = World(
            snakes=[],
            cells=set(
                (x * Config.CELL_SIZE[0], y * Config.CELL_SIZE[1])
                for x in range(Config.WORLD_SIZE[0])
                for y in range(Config.WORLD_SIZE[1])
            ),
        )

        self.container = Container()

        self.container.systems = [
            EventSystem(),
            GrowShrinkSnakes(fps=Config.FPS),
            Eating(),
            Collisions(),
            DisplaySystem(),
        ]

        self.event_map = EventMap(
            {
                KeyDown(pygame.K_ESCAPE): self.quit,
            }
        )

        spritesheet = SnakeSprites()

        player = Snake(Config.CELL_SIZE, Direction.RIGHT, 3, spritesheet)
        player.event_map = EventMap(
            {
                KeyDown(pygame.K_LEFT): partial(player.turn, Direction.LEFT),
                KeyDown(pygame.K_RIGHT): partial(player.turn, Direction.RIGHT),
                KeyDown(pygame.K_UP): partial(player.turn, Direction.UP),
                KeyDown(pygame.K_DOWN): partial(player.turn, Direction.DOWN),
            }
        )
        self.world.snakes.append(player)

        die_sound = Sound(Path(__file__).parent / "audio/die.wav")
        eat_sound = Sound(Path(__file__).parent / "audio/eat.wav")

        player.die.subscribe(die_sound.play)
        player.eat.subscribe(eat_sound.play)

        food = Food(spritesheet)
        food.place(self.world)

        self.container.entities = [
            self,
            food,
            player,
        ]

    def update(self):
        if self.running:
            self.container.update(world=self.world)

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            self.update()


if __name__ == "__main__":
    game = Game()
    game.run()
