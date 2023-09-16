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

import contextlib
import random
from enum import IntEnum
from pathlib import Path

import pygame
from pygame.math import Vector2

from pygskin import ecs
from pygskin.animation import Animation
from pygskin.assets import Assets
from pygskin.clock import Clock
from pygskin.clock import Timer
from pygskin.display import Display
from pygskin.events import KeyDown
from pygskin.events import KeyUp
from pygskin.events import Quit
from pygskin.events import event_listener
from pygskin.pubsub import message
from pygskin.text import Text
from pygskin.text import DynamicText
from pygskin.window import Window

assets = Assets(Path(__file__).parent / "assets")


def translate(v: Vector2) -> Vector2:
    return round(v.elementwise() * Display.rect.size)


def random_position() -> Vector2:
    return Vector2(random.random(), random.random())


class Mob(ecs.Entity):
    colour: str = "white"
    radius: float = 0.1

    def __init__(self, **kwargs) -> None:
        super().__init__()

        self.pos = Vector2(kwargs.get("pos", 0.5))
        self.velocity = Vector2(kwargs.get("velocity", 0))
        self.acceleration = Vector2(0)
        self.angle: float = kwargs.get("angle", 0.0)
        self.spin: float = kwargs.get("spin", 0.0)

        offset = Vector2(self.radius)
        self.rect = pygame.Rect(translate(self.pos - offset), translate(offset * 2))

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(
            surface,
            self.colour,
            translate(self.pos),
            round(self.radius * Display.rect.width),
            width=1,
        )

    def kill(self) -> None:
        with contextlib.suppress(ValueError):
            ecs.Entity.instances.remove(self)

    def collides_with(self, other: Mob) -> bool:
        return self.pos.distance_to(other.pos) < (self.radius + other.radius)


class Ship(Mob):
    radius: float = 0.025

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.alive = True
        self.thruster_on = False
        self.lives = 3
        self.respawn_timer = Timer(seconds=3, on_expire=self.respawn)
        self.shield_timer = Timer(seconds=10)
        self.invulnerability_timer = Timer(seconds=2)

    @property
    def acceleration(self) -> float:
        if self.alive and self.thruster_on:
            return Vector2(0, 0.0075).rotate(self.angle)
        return Vector2(0, 0)

    @acceleration.setter
    def acceleration(self, _) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return

        pygame.draw.polygon(
            surface,
            self.colour,
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
        if self.shield_on:
            timer = self.shield_timer
            shield_percentage = timer.remaining / (timer.seconds * 1000)
            shield_colour = pygame.Color(255, 255, 255, 64).lerp(
                pygame.Color(255, 255, 255, 255),
                shield_percentage,
            )
            pygame.draw.circle(
                surface,
                shield_colour,
                translate(self.pos),
                round(self.radius * Display.rect.width) + random.randrange(3),
                width=2,
            )

    @message
    def kill(self) -> None:
        assets.bang_big.play()
        self.thrust_stop()
        self.spin = 0.0
        self.velocity = Vector2(0)
        self.alive = False

    @event_listener
    def thrust(self, _: KeyDown.UP) -> None:
        if self.alive:
            self.thruster_on = True
            assets.thrust.play(loops=-1, fade_ms=100)

    @event_listener
    def thrust_stop(self, _: KeyUp.UP | None = None) -> None:
        if self.alive:
            self.thruster_on = False
            assets.thrust.fadeout(200)

    @event_listener
    def spin_left(self, _: KeyDown.LEFT) -> None:
        if self.alive:
            self.spin = -20

    @event_listener
    def spin_right(self, _: KeyDown.RIGHT) -> None:
        if self.alive:
            self.spin = 20

    @event_listener
    def spin_stop(self, _: KeyUp.LEFT | KeyUp.RIGHT | None = None) -> None:
        if self.alive:
            self.spin = 0

    @event_listener
    def fire(self, _: KeyDown.SPACE) -> None:
        if self.alive:
            assets.fire.play()
            Bullet(
                ship=self,
                pos=self.pos,
                velocity=self.velocity + Vector2(0, 0.15).rotate(self.angle),
            )

    @event_listener
    def shield(self, _: KeyDown.S) -> None:
        timer = self.shield_timer
        if timer.started:
            timer.resume()
        else:
            timer.start()

    @event_listener
    def shield_off(self, _: KeyUp.S) -> None:
        self.shield_timer.pause()

    @property
    def shield_on(self) -> bool:
        timer = self.shield_timer
        return timer.started and not (timer.ended or timer.paused)

    @property
    def invulnerable(self) -> bool:
        timer = self.invulnerability_timer
        return timer.started and not timer.ended

    def respawn(self) -> None:
        self.alive = True
        self.pos = Vector2(0.5)
        self.velocity = Vector2(0)
        self.shield_timer.reset()
        self.invulnerability_timer.start()


class Bullet(Mob):
    radius: float = 0.005
    colour: str = "orange"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.lifetime = Timer(seconds=1, on_expire=self.kill, delete=True)
        self.lifetime.start()

    def kill(self) -> None:
        self.lifetime.cancel()
        super().kill()


class Explosion(Mob):
    radius: float = 0.375
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
        radius = round(self.anim_radius.current_frame() * Display.rect.width)
        for i in range(2):
            pygame.draw.circle(
                surface,
                self.colour,
                center,
                radius + i * random.randrange(3),
                width=2,
            )


class Size(IntEnum):
    BIG = 1
    MEDIUM = 2
    SMALL = 3


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
        pygame.draw.polygon(
            surface,
            self.colour,
            [
                translate(Vector2(0, radius).rotate(self.angle + i * 18) + self.pos)
                for i, radius in enumerate(self.radii)
            ],
            width=2,
        )

    @message
    def kill(self) -> None:
        super().kill()
        assets[f"bang_{self.size.name.lower()}"].play()

    def fragment(self) -> list[Asteroid]:
        return [
            Asteroid(size=Size(self.size + 1), pos=self.pos)
            for _ in range(2 if self.size != Size.SMALL else 0)
        ]


class World(pygame.sprite.Sprite):
    def __init__(self) -> None:
        super().__init__(Display.sprites)
        self.paused = False
        self.score = 0
        self.level = 0
        self.asteroids = []

    def load(self) -> None:
        self.surface = pygame.Surface(Display.rect.size).convert_alpha()
        self.rect = self.surface.get_rect()

        # self.heartbeat = HeartBeat(self)

        self.ship = Ship(pos=Vector2(0.5))
        self.ship.kill.subscribe(self.remove_ship)

        kw = {"color": "green", "padding": [10]}
        self.game_over_label = Text("GAME OVER", center=Display.rect.center, **kw)
        self.pause_label = Text("PAUSED", center=Display.rect.center, **kw)
        self.ui = pygame.sprite.Group(
            DynamicText(lambda: f"Level {self.level}", **kw),
            DynamicText(
                lambda: f"Lives {self.ship.lives}", bottom=Display.rect.bottom, **kw
            ),
            DynamicText(
                lambda: f"Score {self.score}", bottomright=Display.rect.size, **kw
            ),
        )

        self.next_level_timer = Timer(seconds=3, on_expire=self.next_level)
        self.heartbeat_timer = Timer(seconds=1, on_expire=self.heartbeat)

        self.start_level()

    @property
    def image(self) -> pygame.Surface:
        self.surface.blit(assets.background.data, (0, 0))
        for entity in ecs.Entity.instances:
            if isinstance(entity, Mob):
                entity.draw(self.surface)
        self.ui.draw(self.surface)
        return self.surface

    def start_level(self) -> None:
        self.asteroids = []
        for _ in range(self.level + 3):
            self.add_asteroid(Asteroid())
        self.ship.invulnerability_timer.start()

    def add_asteroid(self, asteroid: Asteroid) -> None:
        self.asteroids.append(asteroid)
        asteroid.kill.subscribe(lambda: self.remove_asteroid(asteroid))

    def remove_asteroid(self, asteroid: Asteroid) -> None:
        self.asteroids.remove(asteroid)
        self.score += asteroid.score

        if self.score % 10000 <= asteroid.score and self.ship.lives < 10:
            self.ship.lives += 1

        Explosion(pos=asteroid.pos)
        for fragment in asteroid.fragment():
            self.add_asteroid(fragment)

        if len(self.asteroids) == 0:
            self.next_level_timer.start()

    def remove_ship(self):
        self.ship.lives -= 1
        Explosion(pos=self.ship.pos)

        if self.ship.lives < 1:
            self.game_over = True
            self.ui.add(self.game_over_label)

        else:
            self.ship.respawn_timer.start()

    def __hash__(self) -> str:
        return hash(id(self))

    @event_listener
    def toggle_pause(self, _: KeyDown.P) -> None:
        self.paused = not self.paused
        if self.paused:
            self.ui.add(self.pause_label)
        else:
            self.ui.remove(self.pause_label)

    def next_level(self) -> None:
        self.level += 1
        self.start_level()

    def heartbeat(self) -> None:
        assets.beat1.play()
        timer = self.heartbeat_timer
        start = 60 / 180
        end = 60 / 80
        quotient = min(1.0, self.score / 1000000)
        timer.seconds = start + quotient * (end - start)
        timer.start()


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
            if ship.shield_on:
                normal = asteroid.pos - ship.pos
                asteroid.velocity = asteroid.velocity.reflect(normal)
                asteroid.pos += asteroid.velocity
            elif not ship.invulnerable:
                ship.kill()


# class HeartBeat(ecs.Entity):
#     def __init__(self, world: World) -> None:
#         super().__init__()
#         self.world = world
#         self._delay = 750
#         assets.beat1.set_volume(0.3)

#     @property
#     def bpm(self) -> float:
#         # increases from 80bpm to 180bpm with score
#         return 100 * min(1.0, (1 + self.world.score) / 1000000) + 80

#     @on_tick
#     def beat(self, dt: int, **_) -> None:
#         if self.world.paused:
#             return
#         self._delay -= dt
#         if self._delay <= 0.0:
#             assets.beat1.play()
#             self._delay = 60000 / self.bpm


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

        self.world = World()
        self.world.load()

    def update(self, **_) -> None:
        super().update(world=self.world)

    @event_listener
    def quit(self, _: Quit | KeyDown.ESCAPE) -> None:
        self.running = False


if __name__ == "__main__":
    Game().run()
