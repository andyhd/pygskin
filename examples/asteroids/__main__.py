"""
Asteroids

TODO:
    - title screen
    - high score table
    - small ufo: aiming gets better as score increases, 1000pts, appears after 10,000pts
    - bug: unpausing activates shield
"""

from __future__ import annotations

import contextlib
import math
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
from pygskin.text import DynamicText
from pygskin.text import Text
from pygskin.utils import angle_between
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

    def draw_poly(
        self, surface: pygame.Surface, radial_points: list[Vector2], **kwargs
    ) -> None:
        angle = kwargs.get("angle", self.angle)
        pos = kwargs.get("pos", self.pos)
        radius = kwargs.get("radius", self.radius)
        pygame.draw.polygon(
            surface,
            kwargs.get("colour", "white"),
            [
                translate(Vector2(0, radius * r_mul).rotate(angle + a_add) + pos)
                for r_mul, a_add in radial_points
            ],
            width=kwargs.get("width", 1),
        )

    def draw_circle(self, surface: pygame.Surface, **kwargs) -> None:
        pygame.draw.circle(
            surface,
            kwargs.get("colour", self.colour),
            translate(kwargs.get("pos", self.pos)),
            round(kwargs.get("radius", self.radius) * Display.rect.width),
            width=kwargs.get("width", 1),
        )

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_circle(surface)

    def kill(self) -> None:
        with contextlib.suppress(ValueError):
            ecs.Entity.instances.remove(self)

    def collides_with(self, other: Mob) -> bool:
        return self.pos.distance_to(other.pos) < (self.radius + other.radius)


class Ship(Mob):
    radius: float = 0.02

    fuselage = [(1, 0), (1, -150), (1, 150)]
    wings = [(0, 0), (1.2, -120), (1, -150), (1, 150), (1.2, 120)]
    exhaust = [(1, -150), (1.2, -180), (1, 150)]

    thrust_vector = Vector2(0, 0.005)

    full_shield_colour = pygame.Color(255, 255, 255, 255)
    low_shield_colour = pygame.Color(255, 255, 255, 64)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.alive = True
        self.paused = False
        self.thruster_on = False
        self.lives = 3
        self.respawn_timer = Timer(seconds=3, on_expire=self.respawn)
        self.shield_timer = Timer(seconds=10)
        self.invulnerability_timer = Timer(seconds=2)

    @property
    def acceleration(self) -> float:
        if self.alive and self.thruster_on:
            return Ship.thrust_vector.rotate(self.angle)
        return Vector2(0)

    @acceleration.setter
    def acceleration(self, _) -> None:
        pass

    def draw(self, surface: pygame.Surface, **kwargs) -> None:
        for_lives_meter = "pos" in kwargs

        if not self.alive and not for_lives_meter:
            return

        r = self.radius

        self.draw_poly(surface, Ship.fuselage, **kwargs)
        self.draw_poly(surface, Ship.wings, **kwargs)

        if for_lives_meter:
            return

        if self.shield_on:
            timer = self.shield_timer
            shield_percentage = timer.remaining / (timer.seconds * 1000)
            shield_colour = Ship.low_shield_colour.lerp(
                Ship.full_shield_colour,
                shield_percentage,
            )
            if not self.paused:
                self.draw_circle(
                    surface,
                    colour=shield_colour,
                    radius=r + random.uniform(0, 0.00375),
                )

        if self.thruster_on:
            self.draw_poly(surface, Ship.exhaust)

    @message
    def add_life(self) -> None:
        if self.lives < 10:
            self.lives += 1
            assets.life.play()

    @message
    def kill(self) -> None:
        assets.bang_big.play()
        self.thrust_stop()
        self.spin = 0.0
        self.velocity = Vector2(0)
        self.alive = False
        self.lives -= 1

    @event_listener
    def thrust(self, _: KeyDown.UP) -> None:
        if self.alive and not self.paused:
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
        if self.alive and not self.paused:
            assets.fire.play()
            Bullet(
                ship=self,
                pos=self.pos,
                velocity=self.velocity + Vector2(0, 0.15).rotate(self.angle),
            )

    @event_listener
    def shield(self, _: KeyDown.S) -> None:
        if self.alive and not self.paused:
            timer = self.shield_timer
            if timer.started:
                timer.resume()
            else:
                timer.start()

    @event_listener
    def shield_off(self, _: KeyUp.S) -> None:
        if self.alive:
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

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if self.paused:
            self.respawn_timer.pause()
            self.shield_timer.pause()
            self.invulnerability_timer.pause()
        else:
            self.respawn_timer.resume()
            self.invulnerability_timer.resume()


class Bullet(Mob):
    radius: float = 0.005
    colour: str = "orange"

    def __init__(self, **kwargs) -> None:
        self.from_ship = bool(kwargs.pop("ship", False))
        if not self.from_ship:
            self.colour = "greenyellow"
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
        self.anim_radius = Animation({0: 0.0, 200: 1.0})
        self.anim_radius.end.subscribe(self.kill)
        self.anim_radius.start()
        super().__init__(**kwargs)

    def draw(self, surface: pygame.Surface) -> None:
        radius = self.anim_radius.current_frame() * self.radius
        for i in range(2):
            self.draw_circle(surface, radius=radius + i * random.uniform(0.0, 0.00375))


class Size(IntEnum):
    BIG = 1
    MEDIUM = 2
    SMALL = 3


class Asteroid(Mob):
    def __init__(self, size: Size = Size.BIG, **kwargs) -> None:
        self.size = size
        self.radius, speed, self.score = {
            Size.BIG: (0.08, 0.01, 20),
            Size.MEDIUM: (0.04, 0.02, 50),
            Size.SMALL: (0.02, 0.03, 100),
        }[self.size]

        self.points = [Vector2(random.uniform(0.8, 1), i * 18) for i in range(20)]

        super().__init__(**kwargs)

        self.velocity = Vector2(
            random.uniform(-speed, speed),
            random.uniform(-speed, speed),
        )
        self.spin = random.uniform(-10, 10)

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_poly(surface, self.points)

    @message
    def kill(self) -> None:
        super().kill()
        assets[f"bang_{self.size.name.lower()}"].play()

    def fragment(self) -> list[Asteroid]:
        return [
            Asteroid(size=Size(self.size + 1), pos=self.pos)
            for _ in range(2 if self.size != Size.SMALL else 0)
        ]


class Saucer(Mob):
    sections = [
        [(1, 90), (0.5, 45), (0.5, -45), (1, -90)],
        [(1, 90), (0.5, 135), (0.5, -135), (1, -90)],
        [(0.5, 135), (0.75, 160), (0.75, -160), (0.5, -135)],
    ]

    def __init__(self, size: Size = Size.BIG, **kwargs) -> None:
        self.size = size
        self.radius, speed, self.score = {
            Size.BIG: (0.04, 0.015, 200),
            Size.SMALL: (0.025, 0.01, 1000),
        }[self.size]

        self.ship = kwargs.pop("ship")

        super().__init__(**kwargs)

        self.starting_velocity = Vector2((speed if self.pos.x <= 0 else -speed), 0)

        self.firing_timer = Timer(seconds=3, on_expire=self.fire)
        self.firing_timer.start()

    @property
    def velocity(self) -> Vector2:
        return Vector2(
            self.starting_velocity.x,
            math.sin(math.radians(self.pos.x * 360 * 3)) * 0.015,
        )

    @velocity.setter
    def velocity(self, _) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        for section in Saucer.sections:
            self.draw_poly(surface, section)

    @message
    def kill(self) -> None:
        self.firing_timer.cancel()
        assets[f"bang_{self.size.name.lower()}"].play()
        super().kill()

    def fire(self) -> object:
        assets.saucer_fire.play()
        if self.size == Size.BIG:
            velocity = self.velocity + Vector2(0, 0.15).rotate(random.random() * 360)
        else:
            velocity = ((self.ship.pos - self.pos).normalize() * 0.15).rotate(
                random.uniform(-10, 10)
            )
        Bullet(
            pos=self.pos,
            velocity=velocity,
        )

        self.firing_timer.seconds = random.uniform(1, 2)
        self.firing_timer.start()

        return message.CANCEL

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if self.paused:
            self.firing_timer.pause()
        else:
            self.firing_timer.resume()


class Drone(Asteroid):
    colour: str = "lightblue"
    segment = [(1, 0), (1, -120), (0.1, 180), (1, 120)]

    def __init__(self, size: Size = Size.BIG, **kwargs) -> None:
        self.ship = kwargs.pop("ship", None)
        self.size = size
        self.radius, self.speed, self.score, self.num_fragments = {
            Size.BIG: (0.05, 0.01, 0, 3),
            Size.MEDIUM: (0.04, 0.0125, 0, 2),
            Size.SMALL: (0.025, 0.0175, 200, 0),
        }[self.size]

        self._speed_squared = self.speed_squared = self.speed**2
        self._velocity = Vector2(0, self.speed).rotate(random.random() * 360)

        Mob.__init__(self, **kwargs)

    @property
    def velocity(self) -> Vector2:
        if self._speed_squared > self.speed_squared:
            self._velocity.scale_to_length(self.speed)
            self._speed_squared = self.speed_squared
        return self._velocity

    @velocity.setter
    def velocity(self, value: Vector2) -> None:
        self._velocity = value
        self._speed_squared = value.length_squared()

    @property
    def acceleration(self) -> Vector2:
        if self.size == Size.BIG:
            return Vector2(1)
        return Vector2(0, 0.0075).rotate(self.angle)
        return (self.ship.pos - self.pos).normalize() * 0.0075

    @acceleration.setter
    def acceleration(self, _) -> None:
        pass

    @property
    def spin(self) -> float:
        angle_to_ship = 180 - angle_between(self.pos, self.ship.pos)
        return -10 if (angle_to_ship - self.angle) % 360 < 180 else 10

    @spin.setter
    def spin(self, value: float) -> None:
        self._spin = max(-20, min(20, value))

    def draw(self, surface: pygame.Surface) -> None:
        angle = self.angle
        pos = self.pos

        if self.size == Size.SMALL:
            self.draw_poly(surface, Drone.segment)

        elif self.size == Size.MEDIUM:
            offset = math.tan(math.radians(50)) * 0.01
            for a_add in (0, 180):
                self.draw_poly(
                    surface,
                    Drone.segment,
                    angle=angle + a_add,
                    pos=pos + Vector2(0, offset).rotate(angle + a_add),
                    radius=0.025,
                )

        elif self.size == Size.BIG:
            for angle in range(0, 360, 60):
                self.draw_poly(
                    surface,
                    Drone.segment,
                    pos=pos + Vector2(0, 0.025).rotate(angle),
                    angle=angle - (60 if angle % 120 == 0 else -60),
                    radius=0.025,
                )

    def fragment(self) -> list[Drone]:
        fragments = []
        if self.size == Size.SMALL:
            return fragments

        size = Size(self.size + 1)
        pos = self.pos
        for _ in range(self.num_fragments):
            angle = random.random() * 360
            fragments.append(Drone(size=size, pos=pos, angle=angle, ship=self.ship))
        return fragments


class LifeMeter(pygame.sprite.Sprite):
    def __init__(self, ship: Ship) -> None:
        super().__init__()
        self.ship = ship
        self.image = pygame.Surface(
            translate(Vector2(1.0, ship.radius * 2.4))
        ).convert_alpha()
        self.rect = self.image.get_rect(topleft=translate(Vector2(0.025, 0.075)))
        self.ship.add_life.subscribe(self.redraw)
        self.ship.kill.subscribe(self.redraw)
        self.redraw()

    # @event_listener
    # def redraw(self, event: Ship.RemoveLife | Ship.AddLife) -> None:
    def redraw(self) -> None:
        self.image.fill((0, 0, 0, 0))
        for i in range(self.ship.lives):
            self.ship.draw(
                self.image,
                angle=180,
                pos=Vector2(
                    self.ship.radius * 2.2 + (i * self.ship.radius * 2.5),
                    self.ship.radius,
                ),
            )


class World(ecs.Entity, pygame.sprite.Sprite):
    def __init__(self) -> None:
        ecs.Entity.__init__(self)
        pygame.sprite.Sprite.__init__(self, Display.sprites)

    def load(self) -> None:
        self.surface = pygame.Surface(Display.rect.size).convert_alpha()
        self.rect = self.surface.get_rect()

        self.paused = False
        self.score = 0
        self.level = 0
        self.asteroids = []
        self.saucer = None

        self.ship = Ship(pos=Vector2(0.5))
        self.ship.kill.subscribe(self.remove_ship)

        kw = {
            "color": "white",
            "padding": [10],
            "font": assets.Hyperspace.size(40),
        }
        self.game_over_label = Text(
            "GAME OVER", center=translate(Vector2(0.5, 0.4)), **kw
        )
        self.pause_label = Text("PAUSED", center=translate(Vector2(0.5, 0.6)), **kw)
        self.ui = pygame.sprite.Group(
            DynamicText(
                lambda: f"{self.score}", topleft=translate(Vector2(0.025, 0)), **kw
            ),
            LifeMeter(self.ship),
        )

        self.next_level_timer = Timer(seconds=3, on_expire=self.next_level)

        self.heartbeat_timer = Timer(seconds=1, on_expire=self.heartbeat)
        self.heartbeat_timer.start()

        self.saucer_timer = Timer(seconds=60, on_expire=self.add_saucer)
        self.saucer_timer.start()

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
        for _ in range(min(6, self.level + 3)):
            self.add_asteroid(
                Asteroid(
                    pos=Vector2(
                        0, random.uniform(0.7, 0.9) * Display.rect.width
                    ).rotate(random.random() * 360)
                    + self.ship.pos
                )
            )

        if self.level > 3:
            self.add_asteroid(
                Drone(
                    size=Size.BIG,
                    pos=Vector2(
                        0, random.uniform(0.7, 0.9) * Display.rect.width
                    ).rotate(random.random() * 360)
                    + self.ship.pos,
                    ship=self.ship,
                )
            )

        self.ship.invulnerability_timer.start()

    def add_saucer(self) -> None:
        if not self.saucer:
            size = Size.SMALL if random.random() * self.level > 1 else Size.BIG
            start = Vector2(random.choice((0, 1)), random.uniform(0.1, 0.9))
            self.saucer = Saucer(size=size, pos=start, ship=self.ship)
            assets[f"saucer_{size.name.lower()}"].play(loops=-1, fade_ms=100)
            self.saucer.kill.subscribe(lambda: self.remove_saucer())

    def remove_saucer(self) -> None:
        saucer = self.saucer
        if saucer:
            self.saucer = None
            assets[f"saucer_{saucer.size.name.lower()}"].fadeout(200)

            Explosion(pos=saucer.pos)

            self.saucer_timer.start()

    def add_asteroid(self, asteroid: Asteroid) -> None:
        self.asteroids.append(asteroid)
        asteroid.kill.subscribe(lambda: self.remove_asteroid(asteroid))

    def remove_asteroid(self, asteroid: Asteroid) -> None:
        self.asteroids.remove(asteroid)

        Explosion(pos=asteroid.pos)
        for fragment in asteroid.fragment():
            self.add_asteroid(fragment)

        if len(self.asteroids) == 0:
            self.next_level_timer.start()

    def add_score(self, score: int) -> None:
        self.score += score
        if self.score >= 10000 and self.score % 10000 <= score:
            self.ship.add_life()

    def remove_ship(self):
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
            for entity in ecs.Entity.instances:
                if isinstance(entity, Timer):
                    entity.pause()
        else:
            self.ui.remove(self.pause_label)
            for entity in ecs.Entity.instances:
                if isinstance(entity, Timer):
                    entity.resume()
        self.ship.toggle_pause()
        if self.saucer:
            self.saucer.toggle_pause()

    def next_level(self) -> None:
        self.level += 1
        self.start_level()

    def heartbeat(self, **kwargs) -> object:
        assets.beat1.play()
        timer = self.heartbeat_timer
        start = 60 / 60
        end = 60 / 240
        quotient = min(1.0, self.score / 1000000)
        timer.seconds = start + quotient * (end - start)
        timer.start()
        return message.CANCEL


@ecs.system
def physics(mob: Mob, world: World) -> None:
    if world.paused:
        return

    delta_time = Clock.delta_time / 100
    mob.velocity = mob.velocity.elementwise() + mob.acceleration * delta_time
    mob.pos += mob.velocity.elementwise() * delta_time
    mob.pos = mob.pos.elementwise() % 1.0
    mob.rect.center = translate(mob.pos)
    mob.angle = (mob.angle + mob.spin * delta_time) % 360


@ecs.system
def bullets(bullet: Bullet, world: World) -> None:
    if world.paused:
        return

    for asteroid in world.asteroids:
        if bullet.collides_with(asteroid):
            if bullet.from_ship:
                world.add_score(asteroid.score)
            asteroid.kill()
            bullet.kill()

    saucer = world.saucer
    if saucer and bullet.collides_with(saucer) and bullet.from_ship:
        world.add_score(saucer.score)
        saucer.kill()
        bullet.kill()

    ship = world.ship
    if (
        ship.alive
        and not ship.invulnerable
        and not bullet.from_ship
        and bullet.collides_with(ship)
    ):
        bullet.kill()
        if not ship.shield_on:
            ship.kill()


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

    saucer = world.saucer
    if saucer and ship.collides_with(saucer):
        if ship.shield_on:
            saucer.kill()
        else:
            ship.kill()


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
