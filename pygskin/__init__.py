import sys
from contextlib import redirect_stdout

with redirect_stdout(None):
    import pygame  # noqa

from pygskin.assets import Image, Sound, Music  # noqa

from pygskin.events import Event  # noqa

for class_ in Event.CLASSES.values():
    setattr(sys.modules[__name__], class_.__name__, class_)

from pygskin.input import Input, InputHandler  # noqa

from pygskin.interfaces import Drawable, Updatable  # noqa

from pygskin.pubsub import Message  # noqa

from pygskin.screen import Screen  # noqa

from pygskin.spritesheet import Spritesheet, CachedSpritesheet  # noqa

from pygskin.state_machine import StateMachine  # noqa

from pygskin.text import Text  # noqa

from pygskin.timer import Timer  # noqa

from pygskin.window import Window  # noqa
