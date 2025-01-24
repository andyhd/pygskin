import random
from itertools import repeat

import pygame
import pygame.locals as pg
from pygame import Rect
from pygame import Surface
from pygame import Window
from pygame.color import THECOLORS
from pygame.sprite import Group

from pygskin import Assets
from pygskin import Direction
from pygskin import Timer
from pygskin import animate
from pygskin import imgui
from pygskin import make_sprite
from pygskin import run_game
from pygskin import shake
from pygskin import tile
from pygskin.camera import Camera

assets = Assets()
gui = imgui.IMGUI()


def test_camera() -> None:
    """Test the Camera class."""
    camera = Camera()

    world = Surface((1600, 1200), pygame.SRCALPHA)
    for x in range(16):
        for y in range(12):
            pygame.draw.rect(
                world,
                random.choice(list(THECOLORS.values())),
                Rect(x * 100, y * 100, 100, 100),
            )

    direction: Direction | None = None
    zooming: str | None = None
    timer = Timer(3000)
    shake_anim = iter(repeat((0, 0)))
    assets.cat.set_colorkey("black")
    cat = pygame.transform.scale_by(assets.cat.subsurface((0, 0, 16, 16)), 3)
    sprites = Group(
        [
            make_sprite(cat, center=(x * 100, y * 100))
            for x in range(16)
            for y in range(12)
        ]
    )

    def main_loop(screen, events, exit):
        nonlocal direction, shake_anim, zooming

        before_shake = camera.rect.topleft
        camera.view.fill("black")
        camera.rect.move_ip(next(shake_anim))
        camera.blits(tile(camera.rect, world))
        sprites.draw(camera)
        camera.draw(screen)
        camera.rect.topleft = before_shake

        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    direction = Direction.UP
                if event.key == pg.K_DOWN:
                    direction = Direction.DOWN
                if event.key == pg.K_LEFT:
                    direction = Direction.LEFT
                if event.key == pg.K_RIGHT:
                    direction = Direction.RIGHT

                if event.key == pg.K_q:
                    zooming = "in"
                if event.key == pg.K_a:
                    zooming = "out"

                if event.key == pg.K_SPACE:
                    timer.elapsed = 0
                    shake_anim = animate(shake(), timer.quotient)

            if event.type == pg.KEYUP:
                direction = None
                zooming = None

        if zooming == "in":
            camera.zoom += 0.1
        if zooming == "out":
            camera.zoom -= 0.1
        if direction:
            camera.rect.move_ip(direction.vector * (10 / camera.zoom))

        with imgui.render(gui, screen) as render:
            render(
                imgui.label(
                    f"Camera test\n"
                    f"Zoom: {camera.zoom:.2f}\n"
                    f"Position: {camera.rect.topleft}",
                ),
                align="left",
                valign="top",
                topleft=(10, 10),
            )
            render(
                imgui.label(
                    "Arrow keys: move camera, "
                    "Q: zoom in, "
                    "A: zoom out, SPACE: shake",
                ),
                align="left",
                bottomleft=(10, 590),
            )

    return main_loop


if __name__ == "__main__":
    run_game(Window("Camera test", (800, 600)), test_camera())
