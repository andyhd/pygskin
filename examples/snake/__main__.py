from __future__ import annotations

import random
from functools import partial
from pathlib import Path

import pygame
from pygame.sprite import Sprite
from pygame.sprite import collide_rect

from pygskin import ecs
from pygskin.assets import Assets
from pygskin.direction import Direction
from pygskin.events import Key
from pygskin.display import Display
from pygskin.clock import Clock
from pygskin.clock import on_tick
from pygskin.grid import Grid
from pygskin.pubsub import message
from pygskin.spritesheet import Spritesheet
from pygskin.window import Window


assets = Assets(Path(__file__).parent / "assets")


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


class Segment(Sprite):
    def __init__(
        self,
        rect: pygame.Rect,
        direction: Direction,
        spritesheet: Spritesheet,
        turning_to: Direction | None = None,
        is_head: bool = False,
        is_tail: bool = False,
    ) -> None:
        super().__init__()
        self.rect = rect
        self.direction = direction
        self.spritesheet = spritesheet
        self.turning_to = turning_to
        self.is_head = is_head
        self.is_tail = is_tail
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


class Snake(ecs.Entity):
    def __init__(self, pos, facing, length, spritesheet):
        super().__init__()
        rect = pygame.Rect(*pos, *Config.CELL_SIZE)
        self.body = [
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
        self.alive = True
        self.is_eating = False,
        self.interval = 1000 / 7
        self.timer = self.interval

    @on_tick
    def update_entity(self, dt: int, **_) -> None:
        if self.alive:
            self.timer -= dt
            if self.timer <= 0:
                self.timer = self.interval

                self.grow()

                if self.is_eating:
                    self.is_eating = False
                else:
                    self.shrink()

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
        self.alive = False

    @message
    def eat(self, *_):
        self.is_eating = True


class Food(Sprite, ecs.Entity):
    def __init__(self, spritesheet):
        ecs.Entity.__init__(self)
        Sprite.__init__(self)
        self.image = spritesheet[(2, 3)]
        self.rect = self.image.get_rect()
        Display.sprites.add(self)

    def place(self, world):
        available_cells = list(
            world["cells"].difference(*(s.rect.topleft for s in world["player"].body))
        )
        self.rect.topleft = random.choice(available_cells)


class Eating(ecs.System):
    def filter(self, entity: ecs.Entity) -> bool:
        return isinstance(entity, Food)

    def update_entity(self, food, **world):
        snake = world["player"]
        if snake.is_eating:
            return
        if collide_rect(snake.head, food):
            snake.eat(food)
            food.place(world)


class Collisions(ecs.System):
    def filter(self, entity: ecs.Entity) -> bool:
        return isinstance(entity, Snake)

    def update_entity(self, snake, **world):
        for segment in snake.body:
            if (
                snake.alive
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
                Clock(fps=Config.FPS),
                Eating(),
                Collisions(),
            ]
        )

        spritesheet = Spritesheet(assets.snake, Grid(4, 4), SNAKE_SPRITE_MAP)

        player = Snake(Config.CELL_SIZE, Direction.RIGHT, 3, spritesheet)

        # controls
        Key.escape.down.subscribe(self.quit)
        Key.left.down.subscribe(partial(player.turn, Direction.LEFT))
        Key.right.down.subscribe(partial(player.turn, Direction.RIGHT))
        Key.up.down.subscribe(partial(player.turn, Direction.UP))
        Key.down.down.subscribe(partial(player.turn, Direction.DOWN))

        player.die.subscribe(assets.die_sound.play)
        player.eat.subscribe(assets.eat_sound.play)

        self.world["player"] = player

        food = Food(spritesheet)
        food.place(self.world)

    def update(self):
        super().update(**self.world)


if __name__ == "__main__":
    Game().run()
