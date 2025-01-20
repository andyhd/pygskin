# Pygskin

A collection of useful functions and classes for Pygame

## [`animate` function](pygskin/animation.py)
Animation generator function which takes a list of frames or mapping of
quotients (0.0 - 1.0) to keyframes and a function that returns a quotient, and
returns an generator that returns frames.
```python
anim = animate([image1, image2], timer.quotient)
screen.blit(next(anim))
```


## [`Assets` class](pygskin/assets.py)
Provides attribute access to asset files and batch loading
```python
assets = Assets()
screen.blit(assets.player)
assets.player_spawn_sfx.play()
```


## [`Timer` class](pygskin/timer.py)
A countdown timer dataclass. Can be used with the `animate` function.
```python
timer = Timer(3000)  # 3 seconds
timer.tick()
if timer.finished:
    timer.elapsed = 0  # loop
```


## [`iter_dialogue` function](pygskin/dialogue.py)
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


## [`Direction` enum](pygskin/direction.py)
Enum for up/down/left/right directions
```python
direction = Direction.UP
if direction in Direction.VERTICAL:
    rect.move_ip(direction.vector)
```


## [`easing` module](pygskin/easing.py)
A selection of easing functions for use with interpolation. Can be used with the
`animate` and `make_color_gradient` functions.


## [`get_ecs_update_fn` function](pygskin/ecs.py)
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


## [`bind` function](pygskin/func.py)
Partial function application with one or more argument placeholders at arbitrary
positions.
```python
foos = filter(bind(isinstance, ..., Foo), items)
```


## [`run_game` function](pygskin/game.py)
Pygbag compatible game loop.
```python
def main_loop(screen, events, exit):
    screen.fill(random.choice(pygame.color.THECOLORS.values()))

    for event in events:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            exit()


if __name__ == '__main__':
    run_game(Window("My Game", (WIDTH, HEIGHT)), main_loop)
```


## [`make_color_gradient` function](pygskin/gradient.py)
Generate a color gradient between two colors.
```python
sky_image = make_color_gradient(screen.size, "white", "blue")
screen.blit(sky_image)
```


## [`imgui` module](pygskin/imgui.py)
Immediate mode GUI.
```python
gui = imgui.IMGUI()

def main_loop(screen, events, exit):
    with imgui.render(gui, screen) as render:
        if render(imgui.button("Quit"), center=(100, 200)):
            exit()
```


## [`map_inputs_to_actions` function](pygskin/input.py)
Map input events to actions. Enables user-defined key bindings.
```python
keyboard_controls = {
    "jump": Event(pg.KEYDOWN, key=pg.K_UP),
    "duck": Event(pg.KEYDOWN, key=pg.K_DOWN),
    "quit": Event(pg.KEYDOWN, key=pg.K_ESCAPE),
}
for action in map_inputs_to_actions(
    keyboard_controls,
    pygame.event.get(),
):
    if action == "jump":
        player.jump()
    if action == "duck":
        player.duck()
    if action == "quit":
        exit()
```


## [`lazy` class](pygskin/lazy.py)
Lazy loading object proxy. Works like a partial function application for
objects.
```python
image = lazy(pygame.image.load, "foo.png"))
screen.blit(image)
```


## [`scroll_parallax_layers` function](pygskin/parallax.py)
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


## [`channel` function](pygskin/pubsub.py)
Simple pubsub implementation.
```python
foo = channel()
foo.subscribe(lambda x: print(f"subscriber 1: {x}"))
foo("bar")
```


## [`get_rect_attrs` function](pygskin/rect.py)
Filter rect attributes (eg `top`, `center`, `size`) from a dictionary. Useful
for passing kwargs to `pygame.Rect.move_to` or `pygame.Surface.get_rect`.
```python
def foo(image: Surface, **kwargs):
    image_rect = image.get_rect(**get_rect_attrs(kwargs))
```


## [`add_padding` function](pygskin/rect.py)
Add padding of varying amounts to a Rect.
```python
top, right, bottom, left = [100, 50, 10, 5]
padded, rect = add_padding(Rect(0, 0, 10, 10), [top, right, bottom, left])
assert padded.size == (120, 65)
assert rect.topleft == (5, 100)
```


## [`grid` function](pygskin/rect.py)
Divide a Rect into a specified number of rows and columns, and return a function
to access the cells by row/column index, or string aliases.
```python
get_cell = grid(
    Rect(0, 0, 100, 100),
    rows=2,
    cols=2,
    names={"nw": (0, 0), "ne": (1, 0), "sw": (0, 1), "se": (1, 1)},
)
assert get_cell("ne") == get_cell(1, 0) == Rect(50, 0, 50, 50)
```


## [`screen_manager` function](pygskin/screen.py)
Screen manager state machine.
```python
def main():
    return screen_manager(
        show_main_menu,
        play_level,
    )

def show_main_menu(surface, events, exit_screen):
    surface.blit(assets.main_menu)
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                exit_screen()
            if event.key == pygame.K_RETURN:
                exit_screen(to=play_level)

def play_level(surface, events, exit_screen):
    ...
```


## [`spritesheet` function](pygskin/spritesheet.py)
Provides grid cell access to a spritesheet image.
```python
get_sprite = spritesheet(pygame.image.load("foo.png"), rows=3, cols=4)
screen.blit(get_sprite(2, 1))
walk_frames = [get_sprite(0, i) for i in range(4)]
walk_anim = animate(walk_frames, timer.quotient)
```


## [`statemachine` function](pygskin/statemachine.py)
State machine as generator.


## [`get_styles` function](pygskin/stylesheet.py)
Simple cascading style sheet engine. Filters styles by object type, class and id
attributes. Can be used with imgui module.
```yaml
# styles.yaml
"*":
  color: black
  background_color: grey

"#error":
  background_color: red
```
```python
# cascading styles
stylesheet = partial(get_styles, assets.styles)
Foo = namedtuple("Foo", ["id"])
styles = stylesheet(Foo(id="error"))
assert styles["background_color"] == "red"

# use with imgui
with imgui.render(gui, surface, stylesheet) as render:
    render(imgui.button("Click me!"), center=(100, 100))
```


## [`make_sprite` function](pygskin/surface.py)
Create a sprite from an image.
```python
player = make_sprite(assets.player, center=player_pos)
```


## [`rotate_surface` function](pygskin/surface.py)
Rotate a surface in place or around a specified point.
```python
rotated_image = rotate_surface(image, angle, center=(0, 0))
```


## [`to_snakecase` and `snakecase_to_capwords` functions](pygskin/text.py)
Convert between snake_case and CapWords.


## [`speech_duration` function](pygskin/text.py)
Calculate rough speech duration in seconds.


## [`tile` function](pygskin/tile.py)
Generate a blit sequence to tile an image across a surface.
```python
screen.blits(tile(screen.get_rect(), assets.grass))
```


## [`angle_between` function](pygskin/vector.py)
Calculate the angle between two points.
