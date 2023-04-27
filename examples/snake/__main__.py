from __future__ import annotations

import random
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import pygame
from pygame.sprite import Sprite
from pygame.sprite import collide_rect

from pygskin import ecs
from pygskin.assets import Sound
from pygskin.direction import Direction
from pygskin.events import EventMap
from pygskin.display import Display
from pygskin.clock import Clock
from pygskin.events import KeyDown
from pygskin.grid import Grid
from pygskin.pubsub import message
from pygskin.spritesheet import Spritesheet
from pygskin.window import Window


class Config:
    CELL_SIZE = (32, 32)
    WORLD_SIZE = (20, 15)
    FPS = 100


SNAKE_SPRITE_MAP = {
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

    def __repr__(self):
        return f"<Segment {self.rect} {self.is_head=} {self.is_tail=}>"


class Body(list[Segment]):
    pass


class Flags(dict[str, bool]):
    pass


class Snake(ecs.Entity):
    def __init__(self, pos, facing, length, spritesheet):
        super().__init__()
        rect = pygame.Rect(*pos, *Config.CELL_SIZE)
        self.body = Body(
            [
                Segment(
                    rect.move(
                        *(
                            pygame.math.Vector2(
                                facing.vector.elementwise() * Config.CELL_SIZE,
                            ).elementwise()
                            * -i,
                        ),
                    ),
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
        Display.sprites.add(self.head)

    def shrink(self):
        if len(self.body) > 3:
            tail = self.body.pop()
            self.body[-1].is_tail = True
            tail.kill()

    def turn(self, direction, *args):
        if direction.axis != self.head.direction.axis:
            self.head.turning_to = direction

    @message
    def die(self, *_):
        self.Flags["alive"] = False

    @message
    def eat(self, *_):
        self.Flags["is_eating"] = True

    def __repr__(self):
        return f"<Snake {self.flags} {self.body}>"


class Food(Sprite, ecs.Entity):
    def __init__(self, spritesheet):
        ecs.Entity.__init__(self)
        Sprite.__init__(self)
        self.image = spritesheet[(2, 3)]
        self.rect = self.image.get_rect()
        Display.sprites.add(self)

    def place(self, world):
        available_cells = list(
            world["cells"].difference(*(s.rect.topleft for s in world["player"].Body))
        )
        self.rect.topleft = random.choice(available_cells)


class GrowShrinkSnakes(IntervalSystem):
    # TODO refactor IntervalSystem as a callback that can be added to Clock
    # eg Clock.every(msec=1000 / 7).subscribe(GrowShrinkSnakes())
    interval = 1000 / 7
    query = ecs.Entity.has(Body, Flags)

    def update_entity(self, snake, **kwargs):
        if snake.Flags["alive"]:
            snake.grow()

            if snake.Flags["is_eating"]:
                snake.Flags["is_eating"] = False
            else:
                snake.shrink()


class Eating(ecs.System):
    def query(x):
        return isinstance(x, Food)

    def update_entity(self, food, **world):
        snake = world["player"]
        if snake.Flags["is_eating"]:
            return
        if collide_rect(snake.head, food):
            snake.eat(food)
            food.place(world)


class Collisions(ecs.System):
    query = ecs.Entity.has(Body, Flags)

    def update_entity(self, snake, **world):
        for segment in snake.Body:
            if (
                snake.Flags["alive"]
                and segment != snake.head
                and collide_rect(snake.head, segment)
            ):
                snake.die()
                break


class Game(Window):
    def __init__(self):
        super().__init__(title="Snake")

        self.world = {
            "cells": set(
                (x * Config.CELL_SIZE[0], y * Config.CELL_SIZE[1])
                for x in range(Config.WORLD_SIZE[0])
                for y in range(Config.WORLD_SIZE[1])
            ),
        }

        self.systems.extend(
            [
                GrowShrinkSnakes(fps=Config.FPS),
                Eating(),
                Collisions(),
            ]
        )

        self.event_map.update({KeyDown(pygame.K_ESCAPE): self.quit})

        sprites = pygame.image.load(Path(__file__).parent / "images/snake.png")
        spritesheet = Spritesheet(sprites, Grid(4, 4), SNAKE_SPRITE_MAP)

        player = Snake(Config.CELL_SIZE, Direction.RIGHT, 3, spritesheet)
        player.event_map = EventMap(
            {
                KeyDown(pygame.K_LEFT): partial(player.turn, Direction.LEFT),
                KeyDown(pygame.K_RIGHT): partial(player.turn, Direction.RIGHT),
                KeyDown(pygame.K_UP): partial(player.turn, Direction.UP),
                KeyDown(pygame.K_DOWN): partial(player.turn, Direction.DOWN),
            }
        )

        die_sound = Sound(Path(__file__).parent / "audio/die.wav")
        eat_sound = Sound(Path(__file__).parent / "audio/eat.wav")

        player.die.subscribe(die_sound.play)
        player.eat.subscribe(eat_sound.play)
        self.world["player"] = player

        food = Food(spritesheet)
        food.place(self.world)

    def update(self):
        super().update(**self.world)


if __name__ == "__main__":
    Game().run()
