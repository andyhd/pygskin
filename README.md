# Pygskin

A collection of useful functions and classes for Pygame

## `animate` function
Animation generator function which takes a list of frames or mapping of
quotients (0.0 - 1.0) to keyframes and a function that returns a quotient, and
returns an generator that returns frames.
```python
anim = animate([image1, image2], timer.quotient)
screen.blit(next(anim), (0, 0))
```
TODO
* [ ] Support `duration` and `loop_count` arguments
* [ ] `send` delta time to the generator?


## `Assets` class
Provides attribute access to asset files and batch loading
```python
assets = Assets()
screen.blit(assets.player, (0, 0))
assets.player_spawn_sfx.play()
```
TODO
* [ ] Wrap all assets with `LazyObject` to avoid loading assets at import time


## `Timer` class
A countdown timer dataclass. Can be used with the `animate` function.
```python
timer = Timer(3000)  # 3 seconds
timer.tick()
if timer.finished:
    timer.elapsed = 0  # loop
```


## `iter_dialogue` function
Generator function for stepping through a dialogue script parsed from a JSON or
YAML file.
```python
context = {}
dialogue = iter_dialogue(
    assets.act1_scene1,
    context,
    speak=speak,
)

def main_loop(screen, events, quit):
    if action := next(dialogue, None):
        action()
```


## `Direction` enum
Enum for up/down/left/right directions
```python
direction = Direction.UP
if direction in Direction.VERTICAL:
    rect.move_ip(direction.vector)
```


## `easing` module
A selection of easing functions for use with interpolation. Can be used with the
`animate` function.


## `get_ecs_update_fn` function
An extremely simple ECS implementation.
```python
@filter_entities(has_velocity)
def apply_velocity(entity):
    entity.pos += entity.velocity

ecs_update = get_ecs_update_fn([apply_velocity])

@dataclass
class Entity:
    pos: Vector2
    velocity: Vector2

ecs_update([Entity(pos=Vector2(0, 0), velocity=Vector2(1, 1)])
```


## `run_game` function
Pygbag compatible game loop.
```python
def main_loop(screen, events, quit):
    screen.fill(random.choice(pygame.color.THECOLORS.values()))

    for event in events:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            quit()


if __name__ == '__main__':
    run_game(Window("My Game", (WIDTH, HEIGHT)), main_loop)
```


## `imgui` module
Immediate mode GUI.
```python
gui = imgui.IMGUI()

def main_loop(screen, events, quit):
    with imgui.render(gui, screen) as render:
        if render(imgui.button("Quit"), center=(100, 200)):
            break
```
TODO
* [ ] More widgets
* [ ] Layouts


## `channel` function
Simple pubsub implementation.
```python
foo = channel()
foo.subscribe(lambda x: print(f"subscriber 1: {x}"))
foo("bar")
```


## `screen_manager` function
Screen manager state machine.
```python
def main():
    return screen_manager(
        {
            show_title: [start_level, enter_level_code],
            show_code_prompt: [start_level, return_to_titles],
            play_level: [end_level],
            show_game_over: [return_to_titles],
        }
    )

def show_main_menu(surface, events, screen_manager):
    surface.blit(assets.main_menu, (0, 0))
    for event in events:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            screen_manager.send("start_level")
        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            screen_manager.send("enter_code")

def start_level(input):
    return play_level if input == "start_level" else None

def enter_level_code(input):
    return show_code_prompt if input == "enter_code" else None
```
TODO
* [ ] Transition animations (fade in/out, slide, wipe, etc)
* [ ] Less clunky transition functions


## `statemachine` function
State machine as generator.


## `utils` module
* `angle_between` function
* `make_sprite` function
* `make_color_gradient` function
* `tile` function
* `scroll_parallax_layers` function


## Other TODO

* [ ] Configurable controls
* [ ] Save / Load
* [ ] Network
