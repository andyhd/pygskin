import pygame

from pygskin import Assets
from pygskin import Timer
from pygskin import animate
from pygskin import run_game
from pygskin import spritesheet


def main():
    assets = Assets()
    sheet = spritesheet(pygame.transform.scale_by(assets.cat, 4), rows=3, columns=8)
    walk_left = [sheet(x, 0) for x in range(8)]
    timer = Timer(300, loop=-1)
    anim = animate(walk_left, timer.quotient)

    def main_loop(surface, events, exit):
        timer.tick()
        surface.fill((0, 0, 0))
        surface.blit(next(anim), (160, 160))

    return main_loop


if __name__ == "__main__":
    run_game(pygame.Window("Spritesheet Animation", (400, 400)), main())
