"""
Asteroids

TODO:
    - title screen
    - high score table
    - level progression: more asteroids after clearing
    - large ufo: random firing and simple path across screen, 200pts
    - small ufo: aiming gets better as score increases, 1000pts, appears after 10,000pts
    - extra life per 10,000pts
    - homing fragments: big asteroid/hive splits into multiple homing ships
    - shield absorbs ufo bullets, bounces asteroids
    - shield brightness timer visualisation
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Protocol, runtime_checkable

import pygame
from pygame.math import Vector2

from pygskin import ecs
from pygskin.animation import Animation
from pygskin.assets import Assets
from pygskin.clock import Clock, Timer, on_tick
from pygskin.display import Display
from pygskin.events import Key
from pygskin.pubsub import message
from pygskin.text import Text
from pygskin.window import Window


assets = Assets(Path(__file__).parent / "assets")


class Size(IntEnum):
    BIG = 1
    MEDIUM = 2
    SMALL = 3


def translate(v: Vector2) -> Vector2:
    return round(v.elementwise() * Display.rect.size)


def random_position() -> Vector2:
    return Vector2(random.random(), random.random())


@runtime_checkable
class Drawable(Protocol):
    visible: bool = True

    def draw(self, surface: pygame.Surface) -> None:
        ...


class Mob(ecs.Entity, Drawable):
    colour: str = "white"
    radius: float = 0.1

    def __init__(
        self,
        pos: Vector2 | None = None,
        velocity: Vector2 | None = None,
        acceleration: Vector2 | None = None,
        angle: float = 0,
        spin: float = 0,
    ) -> None:
        super().__init__()

        self.pos = pos or random_position()
        self.velocity = velocity or Vector2(0, 0)
        self.acceleration = acceleration or Vector2(0, 0)
        self.angle = angle
        self.spin = spin

        self.center_offset = Vector2(self.radius, self.radius)
        self.rect = pygame.Rect(
            translate(self.pos - self.center_offset),
            translate(self.center_offset * 2),
        )

    def __hash__(self) -> str:
        return hash(id(self))

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(
            surface,
            self.colour,
            translate(self.pos),
            round(self.radius * Display.rect.width),
            width=1,
        )

    def kill(self) -> None:
        try:
            ecs.Entity.instances.remove(self)
        except ValueError:
            pass

    def collides_with(self, other: Mob) -> bool:
        return self.pos.distance_to(other.pos) < (self.radius + other.radius)


class Asteroid(Mob):
    def __init__(self, size: Size = Size.BIG, **kwargs) -> None:
        self.size = size
        self.radius, speed, self.score = {
            Size.BIG: (0.1, 0.02, 20),
            Size.MEDIUM: (0.05, 0.03, 50),
            Size.SMALL: (0.025, 0.04, 100),
        }[self.size]
        self.radii = [random.uniform(self.radius * 0.8, self.radius) for _ in range(20)]

        super().__init__(**kwargs)

        self.velocity = Vector2(
            random.uniform(-speed, speed),
            random.uniform(-speed, speed),
        )
        self.spin = random.uniform(-10, 10)

    def draw(self, surface: pygame.Surface) -> None:
        points = [
            translate(Vector2(0, radius).rotate(self.angle + i * 18) + self.pos)
            for i, radius in enumerate(self.radii)
        ]
        pygame.draw.polygon(surface, self.colour, points, width=2)

    @message
    def kill(self) -> None:
        super().kill()
        assets[f"bang_{self.size.name.lower()}"].play()

    def fragment(self) -> list[Asteroid]:
        return [
            Asteroid(size=Size(self.size + 1), pos=self.pos)
            for _ in range(2 if self.size != Size.SMALL else 0)
        ]


class Bullet(Mob):
    radius: float = 0.005
    colour: str = "orange"

    def __init__(self, ship: Ship, is_super: bool = False, **kwargs) -> None:
        self.ship = ship
        self.is_super = is_super
        self.lifetime = Timer(seconds=1, on_expire=self.kill)
        self.lifetime.start()
        super().__init__(**kwargs)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        if self.is_super:
            pygame.draw.circle(
                surface,
                "white",
                translate(self.pos),
                random.randrange(3),
            )

    def kill(self, *_) -> None:
        self.lifetime.cancel()
        super().kill()


class Explosion(Mob):
    radius: float = 0.75
    colour: str = "orange"

    def __init__(self, **kwargs) -> None:
        self.anim_radius = Animation(
            {0: 0.0, 200: self.radius},
        )
        self.anim_radius.end.subscribe(self.kill)
        self.anim_radius.start()

        super().__init__(**kwargs)

    def draw(self, surface: pygame.Surface) -> None:
        center = translate(self.pos)
        radius = round(self.anim_radius.current_frame() * Display.rect.width / 2)
        for i in range(2):
            pygame.draw.circle(
                surface,
                self.colour,
                center,
                radius + i * random.randrange(3),
                width=2,
            )


class Ship(Mob):
    radius: float = 0.025

    def __init__(self, **kwargs) -> None:
        self.alive = True
        self.respawn_timer = Timer(seconds=3, on_expire=self.respawn, delete=False)
        self.shield_timer = Timer(seconds=10, delete=False)
        self.thruster_on = False
        self.invulnerability_timer = Timer(seconds=2, delete=False)

        super().__init__(**kwargs)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.polygon(
            surface,
            "white",
            [
                translate(Vector2(0, radius).rotate(angle) + self.pos)
                for radius, angle in [
                    (self.radius, self.angle),  # nose
                    (self.radius, self.angle - 130),  # left
                    (self.radius / 2, self.angle + 180),  # tail
                    (self.radius, self.angle + 130),  # right
                ]
            ],
            width=2,
        )
        if self.shield_active():
            timer = self.shield_timer
            shield_remaining = timer.remaining / (timer.seconds * 1000)
            shield_color = pygame.Color(255, 255, 255, 64).lerp(
                pygame.Color(255, 255, 255, 255), shield_remaining
            )
            pygame.draw.circle(
                surface,
                shield_color,
                translate(self.pos),
                round(self.radius * Display.rect.width) + random.randrange(3),
                width=2,
            )

    @message
    def kill(self) -> None:
        assets.bang_big.play()
        self.thrust_stop()
        self.spin_stop()
        self.stop()
        self.alive = False
        self.visible = False

    def spin_left(self, *_) -> None:
        if self.alive:
            self.spin = -20

    def spin_right(self, *_) -> None:
        if self.alive:
            self.spin = 20

    def spin_stop(self, *_) -> None:
        if self.alive:
            self.spin = 0

    def thrust(self, *_) -> None:
        if self.alive:
            self.thruster_on = True
            assets.thrust.play(loops=-1, fade_ms=100)

    def thrust_stop(self, *_) -> None:
        if self.alive:
            self.thruster_on = False
            assets.thrust.fadeout(200)

    @property
    def acceleration(self) -> float:
        if self.alive and self.thruster_on:
            return Vector2(0, 0.0075).rotate(self.angle)
        return Vector2(0, 0)

    @acceleration.setter
    def acceleration(self, _) -> None:
        pass

    def stop(self, *_) -> None:
        if self.alive:
            self.velocity = Vector2(0, 0)

    def fire(self, *_) -> None:
        if self.alive:
            assets.fire.play()
            Bullet(
                ship=self,
                pos=self.pos,
                velocity=self.velocity + Vector2(0, 0.15).rotate(self.angle),
            )

    def shield_on(self, *_) -> None:
        timer = self.shield_timer
        if timer.started:
            timer.resume()
        else:
            timer.start()

    def shield_off(self, *_) -> None:
        self.shield_timer.pause()

    def shield_active(self) -> bool:
        timer = self.shield_timer
        return timer.started and not timer.ended and not timer.paused

    @property
    def invulnerable(self) -> bool:
        timer = self.invulnerability_timer
        return timer.started and not timer.ended

    def respawn(self) -> None:
        self.alive = True
        self.pos = Vector2(0.5, 0.5)
        self.velocity = Vector2(0, 0)
        self.acceleration = Vector2(0, 0)
        self.visible = True
        self.shield_timer.reset()
        self.invulnerability_timer.start()


@dataclass
class World(pygame.sprite.Sprite):
    ship: Ship
    level: int = 0
    num_asteroids: int = 0
    score: int = 0
    max_level: int = 0
    high_score: int = 0
    lives: int = 3
    paused: bool = False
    game_over: bool = False

    def __post_init__(self) -> None:
        pygame.sprite.Sprite.__init__(self, Display.sprites)

        self.heartbeat = HeartBeat(self)

        self.ship.kill.subscribe(self.remove_ship)

        self.surface = pygame.Surface(Display.rect.size).convert_alpha()
        self.rect = self.surface.get_rect()

        self.next_level_timer = Timer(seconds=3, delete=False)
        self.next_level_timer.end.subscribe(self.next_level)

        self.start_level()

    def start_level(self) -> None:
        self.asteroids = []
        for _ in range(self.num_asteroids):
            self.add_asteroid(Asteroid())

    @property
    def image(self) -> pygame.Surface:
        self.surface.blit(assets.background.data, (0, 0))
        for entity in ecs.Entity.instances:
            if isinstance(entity, Drawable) and entity.visible:
                entity.draw(self.surface)
        return self.surface

    def add_score(self, value: int) -> None:
        self.score += value

    def set_level(self, level: int) -> None:
        self.level = level

    def add_asteroid(self, asteroid: Asteroid) -> None:
        self.asteroids.append(asteroid)
        asteroid.kill.subscribe(lambda: self.remove_asteroid(asteroid))

    def remove_asteroid(self, asteroid: Asteroid) -> None:
        self.asteroids.remove(asteroid)
        self.add_score(asteroid.score)

        if self.score % 10000 <= asteroid.score:
            if self.lives < 10:
                self.lives += 1

        Explosion(pos=asteroid.pos)
        for fragment in asteroid.fragment():
            self.add_asteroid(fragment)

        if len(self.asteroids) == 0:
            self.next_level_timer.start()

    def remove_ship(self):
        self.lives -= 1
        Explosion(pos=self.ship.pos)

        if self.lives < 1:
            self.game_over = True

        else:
            self.ship.respawn_timer.start()

    def __hash__(self) -> str:
        return hash(id(self))

    def toggle_pause(self, *_) -> None:
        self.paused = not self.paused

    def next_level(self) -> None:
        self.set_level(self.level + 1)
        self.num_asteroids += 1
        self.start_level()


class UI(ecs.Entity, Drawable):
    def __init__(self, world: World) -> None:
        super().__init__()
        self.world = world

    def draw(self, surface: pygame.Surface) -> None:
        level = Text(f"Level {self.world.level}", color="green", padding=[10])
        surface.blit(level.image, level.rect)

        lives = Text(f"Lives {self.world.lives}", color="green", padding=[10])
        lives.rect.bottom = Display.rect.bottom
        surface.blit(lives.image, lives.rect)

        score = Text(f"Score {self.world.score}", color="green", padding=[10])
        score.rect.bottomright = Display.rect.size
        surface.blit(score.image, score.rect)

        if self.world.game_over:
            gameover = Text("GAME OVER", color="green")
            gameover.rect.center = Display.rect.center
            surface.blit(gameover.image, gameover.rect)

        elif self.world.paused:
            paused = Text("PAUSED", color="green")
            paused.rect.center = Display.rect.center
            surface.blit(paused.image, paused.rect)


@ecs.system
def physics(mob: Mob, world: World) -> None:
    if world.paused:
        return

    delta_time = Clock.delta_time / 100
    mob.velocity = mob.velocity.elementwise() + mob.acceleration * delta_time
    mob.pos += mob.velocity.elementwise() * delta_time
    mob.pos = mob.pos.elementwise() % 1.0
    mob.rect.center = translate(mob.pos)
    mob.angle += mob.spin * delta_time


@ecs.system
def bullets(bullet: Bullet, world: World) -> None:
    if world.paused:
        return

    for asteroid in world.asteroids:
        if bullet.collides_with(asteroid):
            asteroid.kill()
            bullet.kill()


@ecs.system
def collisions(ship: Ship, world: World) -> None:
    if world.paused or not ship.alive:
        return

    for asteroid in world.asteroids:
        if ship.collides_with(asteroid):
            if ship.shield_active():
                normal = asteroid.pos - ship.pos
                asteroid.velocity = asteroid.velocity.reflect(normal)
                asteroid.pos += asteroid.velocity
            elif not ship.invulnerable:
                ship.kill()


class HeartBeat(ecs.Entity):
    def __init__(self, world: World) -> None:
        super().__init__()
        self.world = world
        self._delay = 750
        assets.beat1.set_volume(0.3)

    @property
    def bpm(self) -> float:
        # increases from 80bpm to 180bpm with score
        return 100 * min(1.0, (1 + self.world.score) / 1000000) + 80

    @on_tick
    def beat(self, dt: int, **_) -> None:
        if self.world.paused:
            return
        self._delay -= dt
        if self._delay <= 0.0:
            assets.beat1.play()
            self._delay = 60000 / self.bpm


class Game(Window):
    def __init__(self) -> None:
        super().__init__(title="Asteroids", size=(800, 800))

        assets.load()
        assets.thrust.set_volume(0.5)

        self.systems.extend(
            [
                physics(),
                bullets(),
                collisions(),
            ]
        )

        ship = Ship(pos=Vector2(0.5, 0.5))
        self.world = World(ship, num_asteroids=4)
        UI(self.world)

        Key.escape.down.subscribe(self.quit)
        Key.left.down.subscribe(ship.spin_left)
        Key.left.up.subscribe(ship.spin_stop)
        Key.right.down.subscribe(ship.spin_right)
        Key.right.up.subscribe(ship.spin_stop)
        Key.up.down.subscribe(ship.thrust)
        Key.up.up.subscribe(ship.thrust_stop)
        Key.down.down.subscribe(ship.stop)
        Key.space.down.subscribe(ship.fire)
        Key.s.down.subscribe(ship.shield_on)
        Key.s.up.subscribe(ship.shield_off)
        Key.p.down.subscribe(self.world.toggle_pause)

    def update(self, **_) -> None:
        super().update(world=self.world)


if __name__ == "__main__":
    Game().run()
