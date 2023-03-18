from __future__ import annotations

import random

import pygame

from pygskin import ecs
from pygskin.ecs.components import EventMap
from pygskin.ecs.systems import DisplaySystem
from pygskin.ecs.systems import IntervalSystem
from pygskin.events import KeyDown
from pygskin.events import MouseButtonDown
from pygskin.events import MouseButtonUp
from pygskin.events import MouseMotion
from pygskin.grid import Grid
from pygskin.text import Text
from pygskin.window import Window


class World(ecs.Entity, pygame.sprite.Sprite):
    def __init__(self, grid: Grid, cell_size: tuple[int, int]) -> None:
        ecs.Entity.__init__(self)
        pygame.sprite.Sprite.__init__(self)
        self.grid = grid
        self.grid.cell_size = cell_size
        self.rect = pygame.Rect((0, 0), grid.mapped_size)
        self.cells = self.empty()
        self.surface = pygame.Surface(self.rect.size)

    def empty(self) -> None:
        return [[False for _ in range(self.grid.cols)] for _ in range(self.grid.rows)]

    def next_generation(self) -> None:
        next_gen = self.empty()
        for (x, y) in self.grid:
            alive = self.cells[y][x]
            num_neighbours = self.count_neighbours(x, y)
            next_gen[y][x] = (alive and 2 <= num_neighbours <= 3) or (
                not alive and num_neighbours == 3
            )
        self.cells = next_gen

    def count_neighbours(self, x: int, y: int) -> int:
        return sum(
            int(self.cells[ny][nx])
            for (nx, ny) in self.grid.neighbours(x, y)
            if (nx, ny) in self.grid
        )

    @property
    def image(self) -> pygame.Surface:
        self.surface.fill("black")
        for (x, y) in self.grid:
            if self.cells[y][x]:
                pygame.draw.rect(self.surface, "white", self.grid.rect((x, y)))
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


class Game(Window):
    def __init__(self) -> None:
        self.world = World(Grid(160, 160), cell_size=(5, 5))
        self.world.add(DisplaySystem.sprite_group)

        super().__init__(size=self.world.rect.size, title="Conway's Life")

        self.state = {
            "paused": True,
            "painting": False,
            "world": self.world,
        }

        self.systems.append(GenerationSystem(fps=100))

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

    def update(self):
        super().update(**self.state)

    def randomize(self, *args) -> None:
        self.world.cells = [
            random.choices([True, False], k=self.world.grid.cols)
            for _ in range(self.world.grid.rows)
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
            x = event.pos[0] // self.world.grid.cell_width
            y = event.pos[1] // self.world.grid.cell_height
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
