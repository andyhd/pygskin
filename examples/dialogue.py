import pygame
import pygame.locals as pg

from pygskin import Assets
from pygskin import imgui
from pygskin import run_game
from pygskin.dialogue import iter_dialogue

assets = Assets()
gui = imgui.IMGUI()


def main():
    text = ["..."]
    choices = []

    def speak(actor, line):
        text[:] = f"{actor}: {line}"

    def stage_direction(params):
        text[:] = f"[{params}]"

    def prompt(options):
        choices[:] = options
        text[:] = "\n".join(
            ". ".join(map(str, pair))
            for pair in enumerate((option["text"] for option in options), 1)
        )

    context = {}
    dialogue = iter_dialogue(
        assets.ray_first_meeting,
        context=context,
        speak=speak,
        stage_direction=stage_direction,
        prompt=prompt,
    )

    def main_loop(surface, events, exit):
        surface.fill("black")

        for event in events:
            if event.type == pg.KEYDOWN:
                is_choice_key = event.key in range(pg.K_1, pg.K_1 + len(choices))

                if choices and is_choice_key:
                    if choice := choices[event.key - pg.K_1]:
                        context["choice"] = choice
                        choices[:] = []

                elif action := next(dialogue, None):
                    action()

        with imgui.render(gui, surface) as render:
            render(
                imgui.label("".join(text)),
                topleft=(20, 20),
                size=(760, 260),
                align="left",
                valign="top",
            )
            render(
                imgui.label("\n".join(str(_) for _ in context.items())),
                topleft=(20, 320),
                size=(760, 260),
                align="left",
                valign="top",
            )

    return main_loop


if __name__ == "__main__":
    run_game(pygame.Window("Dialogue Demo", (800, 600)), main())
