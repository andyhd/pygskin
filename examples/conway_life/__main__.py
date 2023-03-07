from __future__ import annotations

import random

import pygame

from pygskin import ecs
from pygskin.ecs.components import EventMap
from pygskin.ecs.systems import DisplaySystem
from pygskin.ecs.systems import EventSystem
from pygskin.ecs.systems import IntervalSystem
from pygskin.events import KeyDown
from pygskin.events import MouseButtonDown
from pygskin.events import MouseButtonUp
from pygskin.events import MouseMotion
from pygskin.text import Text


class World(ecs.Entity, pygame.sprite.Sprite):
    def __init__(self, size: tuple[int, int], cell_size: tuple[int, int]) -> None:
        super().__init__()
        (self.width, self.height) = (w, h) = size
        (self.cell_width, self.cell_height) = (cw, ch) = cell_size
        self.rect = pygame.Rect((0, 0), (w * cw, h * ch))
        self.cells = self.empty()
        self.surface = pygame.Surface(self.rect.size)

    def empty(self) -> None:
        return [[False for _ in range(self.width)] for _ in range(self.height)]

    def next_generation(self) -> None:
        next_gen = self.empty()
        for y, row in enumerate(self.cells):
            for x, alive in enumerate(row):
                num_neighbours = self.count_neighbours(x, y)
                next_gen[y][x] = (alive and 2 <= num_neighbours <= 3) or (
                    not alive and num_neighbours == 3
                )
        self.cells = next_gen

    def count_neighbours(self, x: int, y: int) -> int:
        count = 0
        for j in (-1, 0, 1):
            for i in (-1, 0, 1):
                (nx, ny) = (x + i, y + j)
                if (
                    (nx, ny) != (x, y)
                    and 0 <= nx < self.width
                    and 0 <= ny < self.height
                    and self.cells[ny][nx]
                ):
                    count += 1
        return count

    @property
    def image(self) -> pygame.Surface:
        self.surface.fill("black")
        rect = pygame.Rect((0, 0), (self.cell_width, self.cell_height))
        for y, row in enumerate(self.cells):
            for x, alive in enumerate(row):
                if alive:
                    rect.topleft = (x * self.cell_width, y * self.cell_height)
                    pygame.draw.rect(self.surface, "white", rect)
        return self.surface


class GenerationSystem(IntervalSystem):
    def query(x):
        return isinstance(x, World)

    def should_update(self, **state) -> bool:
        if state["paused"]:
            return False
        return super().should_update()

    def update_entity(self, entity: ecs.Entity, **state) -> None:
        entity.next_generation()


class Game(ecs.Entity, ecs.Container):
    def __init__(self) -> None:
        super().__init__()
        self.world = World((160, 160), cell_size=(5, 5))
        self.world.add(DisplaySystem.sprite_group)

        self.state = {
            "running": True,
            "paused": True,
            "painting": False,
            "world": self.world,
        }

        self.systems.extend(
            [
                DisplaySystem(
                    size=self.world.rect.size,
                    title="Conway's Life",
                ),
                EventSystem(),
                GenerationSystem(fps=100),
            ]
        )

        self.pause_label = Text(
            (
                "PAUSED\n"
                "\n"
                "P   - Toggle pause\n"
                "R   - Randomise world\n"
                "G   - Add a Gosper Gun\n"
                "C   - Clear world\n"
                "Esc - Quit\n"
                "\n"
                "While paused, you can draw\n"
                "with the mouse"
            ),
            background="blue",
            padding=(20, 20),
        )
        self.pause_label.image.set_alpha(127)
        self.pause_label.rect.center = self.world.rect.center
        self.pause_label.add(DisplaySystem.sprite_group)

        self.entities = [
            self,
            self.world,
            self.pause_label,
        ]

        self.event_map = EventMap(
            {
                KeyDown(pygame.K_ESCAPE): self.quit,
                KeyDown(pygame.K_c): self.clear,
                KeyDown(pygame.K_g): self.gosper_gun,
                KeyDown(pygame.K_p): self.toggle_pause,
                KeyDown(pygame.K_r): self.randomize,
                MouseButtonDown(1): self.toggle_painting,
                MouseButtonUp(1): self.toggle_painting,
                MouseMotion((1, 0, 0)): self.paint,
            }
        )

    def run(self) -> None:
        while self.state["running"]:
            self.update(**self.state)

    def quit(self, *args) -> None:
        self.state["running"] = False

    def randomize(self, *args) -> None:
        self.world.cells = [
            random.choices([True, False], k=self.world.width)
            for _ in range(self.world.height)
        ]

    def clear(self, *args) -> None:
        self.world.cells = self.world.empty()

    def toggle_pause(self, *args) -> None:
        self.state["paused"] = not self.state["paused"]
        if self.state["paused"]:
            self.pause_label.add(DisplaySystem.sprite_group)
        else:
            self.pause_label.kill()

    def toggle_painting(self, event) -> None:
        if self.state["paused"]:
            self.state["painting"] = not self.state["painting"]

    def paint(self, event) -> None:
        if self.state["painting"]:
            x = event.pos[0] // self.world.cell_width
            y = event.pos[1] // self.world.cell_height
            self.world.cells[y][x] = True

    def gosper_gun(self, *args) -> None:
        cells = (
            "......................................",
            ".........................O............",
            ".......................O.O............",
            ".............OO......OO............OO.",
            "............O...O....OO............OO.",
            ".OO........O.....O...OO...............",
            ".OO........O...O.OO....O.O............",
            "...........O.....O.......O............",
            "............O...O.....................",
            ".............OO.......................",
            "......................................",
        )
        for y, row in enumerate(cells):
            for x, cell in enumerate(row):
                self.world.cells[y + 40][x + 40] = cell == "O"


if __name__ == "__main__":
    Game().run()
