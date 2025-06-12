import pygame

from pygskin import Assets
from pygskin import animate
from pygskin import run_game
from pygskin import spritesheet


def main():
    assets = Assets()
    sheet = spritesheet(assets.cat, scale_by=4, rows=3, columns=8)
    walk_left = [sheet(x, 0) for x in range(8)]
    anim = animate(walk_left, lambda: (pygame.time.get_ticks() % 300) / 300)

    def main_loop(surface, events, exit):
        surface.fill((0, 0, 0))
        surface.blit(next(anim), (160, 160))

    return main_loop


if __name__ == "__main__":
    run_game(pygame.Window("Spritesheet Animation", (400, 400)), main())
