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


## `bind` function
Partial function application with one or more argument placeholders at arbitrary
positions.
```python
foos = filter(bind(isinstance, ..., Foo), items)
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


## `make_color_gradient` function
Generate a color gradient between two colors.
```python
sky_image = make_color_gradient(screen.size, "white", "blue")
screen.blit(sky_image, (0, 0))
```


## `rhash`/`unrhash` functions
Simple reversible hash function for generating unique IDs.
```python
id = rhash("foo")
assert unrhash(id) == "foo"
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


## `LazyObject` class
Lazy loading object proxy.
```python
image = LazyObject(lambda: pygame.image.load("foo.png"))
screen.blit(image, (0, 0))
```


## `scroll_parallax_layers` function
Scroll parallax layers at different rates.
```python
background = LayeredUpdates()
background.add(assets.sky, layer=0)
background.add(assets.mountains, layer=1)
background.add(assets.trees, layer=2)

scroll_parallax_layers(
    (vx, vy),
    background.layers,
    background.get_sprites_from_layer,
    {0: 0, 1: 1.5, 2: 2.0},
)
```


## `channel` function
Simple pubsub implementation.
```python
foo = channel()
foo.subscribe(lambda x: print(f"subscriber 1: {x}"))
foo("bar")
```


## `get_rect_attrs` function
Filter rect attributes (eg `top`, `center`, `size`) from a dictionary. Useful
for passing kwargs to `pygame.Rect.move_to` or `pygame.Surface.get_rect`.
```python
def foo(image: Surface, **kwargs):
    image_rect = image.get_rect(**get_rect_attrs(kwargs))
```


## `add_padding` function
Add padding of varying amounts to a Rect.
```python
rect = add_padding(Rect(0, 0, 10, 10), [100, 50, 10, 5])
assert rect.size == (120, 65)
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


## `Spritesheet` class
Provides item access to a spritesheet image where sprites are arranged in a grid.
```python
spritesheet = Spritesheet("foo.png", rows=3, cols=4))
screen.blit(spritesheet[(2, 1], (0, 0))
walk_frames = [spritesheet[(0, i)] for i in range(4)]
walk_anim = animate(walk_frames, timer.quotient)
```
TODO
* [ ] Slice support for ranges


## `statemachine` function
State machine as generator.


## `get_styles` function
Simple cascading style sheet engine. Filters styles by object type, class and id
attributes.
```python
stylesheet = {
    "Button": {
        "color": "black",
        "background-color": "grey",
    },
    "Button#quit": {
        "background-color": "red",
    },
}
Button = namedtuple("Button", ["id"])
styles = get_styles(stylesheet, Button(id="quit"))
assert styles == {"color": "black", "background-color": "red"}
```


## `make_sprite` function
Create a sprite from an image.
```python
player = make_sprite(assets.player, center=player_pos)
```


## `rotate_surface` function
Rotate a surface in place or around a specified point.
```python
rotated_image = rotate_surface(image, angle, center=(0, 0))
```


## `to_snakecase` and `snakecase_to_capwords` functions
Convert between snake_case and CapWords.


## `speech_duration` function
Calculate rough speech duration in seconds.


## `tile` function
Generate a blit sequence to tile an image across a surface.
```python
screen.blits(tile(screen.get_rect(), assets.grass))
```


## `angle_between` function
Calculate the angle between two points.


## Other TODO

* [ ] Configurable controls
* [ ] Save / Load
* [ ] Network
