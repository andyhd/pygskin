from __future__ import annotations

import contextlib
from collections.abc import Callable
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field

import pygame
from pygame.math import Vector2

from pygskin import ecs
from pygskin.clock import on_tick
from pygskin.pubsub import message

Vector = Iterable[float]
Force = Callable[["Particle", int], None]
ParticleStream = Iterable[Iterable["Particle"]]


@dataclass
class Particle(pygame.sprite.Sprite, ecs.Entity):
    pos: Vector = field(default_factory=lambda: Vector2(0, 0))
    size: Vector = field(default_factory=lambda: Vector2(1, 1))
    velocity: Vector = field(default_factory=lambda: Vector2(0, 0))
    spin: float = 0
    angle: float = 0
    scale: float = 1
    colour: pygame.Color | None = None
    alpha: int = 255
    surface: pygame.Surface | None = None
    mass: float = 0
    drag_coefficient: float = 0
    forces: Iterable[Force] = field(default_factory=list)

    def __post_init__(self) -> None:
        pygame.sprite.Sprite.__init__(self)
        ecs.Entity.__init__(self)
        self.acceleration = Vector2(0, 0)
        self.age = 0
        self._image = None
        self._original_surface = self.surface
        if self.surface:
            self.size = self.surface.get_size()
        elif not self.colour:
            self.colour = pygame.Color(255, 255, 255, 255)

    def __hash__(self):
        return id(self)

    @property
    def image(self):
        if not self._image:
            if self._original_surface:
                self._image = pygame.transform.rotozoom(
                    self._original_surface,
                    self.angle,
                    self.scale,
                )
            else:
                self.size = Vector2(self.size)
                self._image = pygame.Surface(self.size * self.scale).convert_alpha()
                pygame.draw.circle(
                    self._image,
                    self.colour,
                    center=(self.size / 2) * self.scale,
                    radius=(max(*self.size) / 2) * self.scale,
                )
        return self._image

    def redraw(self) -> None:
        self._image = None

    @property
    def rect(self):
        return self.image.get_rect(center=self.pos)

    @on_tick
    def update(self, dt: int, **_) -> None:
        self.acceleration = Vector2(0, 0)
        for force in self.forces:
            force(self, dt)
        mass = max(self.mass, 0.00001)
        self.velocity += (self.acceleration / mass) * dt * 0.001
        self.pos += self.velocity
        if self.spin:
            self.angle += self.spin * dt * 0.001
            self.redraw()

    def kill(self, callback: Callable[[Particle], None] | None = None) -> None:
        if callable(callback):
            callback(self)
        with contextlib.suppress(ValueError):
            ecs.Entity.instances.remove(self)

        super().kill()


@dataclass
class Emitter(ecs.Entity):
    pos: Vector = field(default_factory=lambda: Vector2(0, 0))
    streams: Iterable[ParticleStream] = field(default_factory=list)
    max_particles: int = 0
    groups: Iterable[pygame.sprite.Group] = field(default_factory=list)
    running: bool = True

    def __post_init__(self) -> None:
        ecs.Entity.__init__(self)
        self.particles = pygame.sprite.Group()
        self.streams = list(self.streams)
        self.emitted = 0

    def __repr__(self) -> str:
        return f"<Emitter id={id(self)} streams={self.streams}>"

    def add_stream(self, stream: ParticleStream, pre_fill: int = 0) -> None:
        self.streams.append(stream)
        # TODO pre-fill

    @on_tick
    def update(self, _, **__) -> None:
        # TODO use delta time to control rate of particle emission (eg 3/sec)
        for stream in self.streams:
            for particle in next(stream):
                if not self.max_particles or len(self.particles) < self.max_particles:
                    particle.pos += self.pos
                    particle.add(self.particles, *self.groups)


@dataclass
class Age:
    rate: float
    max_age: float = 0
    callback: Callable[[Particle], None] | None = None

    def __call__(self, particle: Particle, dt: int) -> None:
        particle.age += self.rate * dt
        if 0 < self.max_age <= particle.age:
            particle.kill(self.callback)


@dataclass
class Gravity:
    gravity: Vector = field(default_factory=lambda: Vector2(0, 9.8))

    def __post_init__(self) -> None:
        self.gravity = Vector2(*self.gravity)

    def __call__(self, particle: Particle, dt: int) -> None:
        particle.acceleration += self.gravity


@dataclass
class Drag:
    fluid_velocity: Vector = field(default_factory=lambda: Vector2(0, 0))
    domain: pygame.Rect | None = None

    def __call__(self, particle: Particle, dt: int) -> None:
        if self.domain and not self.domain.contains(particle.pos):
            return
        epsilon = 0.00001
        rvel = particle.velocity * dt * 0.001 - self.fluid_velocity * dt * 0.001
        rmag = rvel.length_squared()
        if rmag > epsilon:
            linear_coefficient = particle.drag_coefficient
            squared_coefficient = linear_coefficient * linear_coefficient
            drag = linear_coefficient * rmag + squared_coefficient * rmag * rmag
            particle.acceleration += (rvel / rmag) * drag


@dataclass
class Spin:
    degrees_per_second: float

    def __call__(self, particle: Particle, dt: int) -> None:
        particle.angle += self.degrees_per_second * dt * 0.001
        particle.redraw()


class CollisionCheck:
    @message
    def collision(self, particle: Particle) -> None:
        particle.kill()


@dataclass
class Boundary(CollisionCheck):
    rect: pygame.Rect
    inside: bool = True

    def __call__(self, particle: Particle, _) -> None:
        particle_in_rect = self.rect.collidepoint(*particle.pos)

        if (self.inside and not particle_in_rect) or (
            not self.inside and particle_in_rect
        ):
            self.collision(particle)


@dataclass
class Mask(CollisionCheck):
    other: pygame.sprite.Sprite

    def __call__(self, particle: Particle, _) -> None:
        if not self.other.rect.colliderect(particle.rect):
            return

        pmask = pygame.mask.from_surface(particle.image)
        px, py = particle.rect.topleft
        ox, oy = self.other.rect.topleft

        if self.other.mask.overlap(pmask, (px - ox, py - oy)):
            self.collision(particle)
