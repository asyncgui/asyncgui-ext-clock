# Clock

*Event scheduler designed for asyncgui programs.*

```python
import asyncgui
from asyncgui_ext.clock import Clock

clock = Clock()

async def async_fn():
    await clock.sleep(20)  # Waits for 20 time units
    print("Hello")

asyncgui.start(async_fn())
clock.tick(10)  # Advances the clock by 10 time units.
clock.tick(10)  # Total of 20 time units. The task above will wake up, and prints 'Hello'.
```

The example above effectively illustrate how this module works but it's not practical.
In a real-world program, you probably want to call ``clock.tick()`` in a loop or schedule it to be called repeatedly using another scheduling API.
For example, if you are using `PyGame`, you may want to do:

```python
pygame_clock = pygame.time.Clock()
clock = asyncgui_ext.clock.Clock()

# main loop
while running:
    ...

    dt = pygame_clock.tick(fps)
    clock.tick(dt)
```

And if you are using `Kivy`, you may want to do:

```python
from kivy.clock import Clock

clock = asyncui_ext.clock.Clock()
Clock.schedule_interval(clock.tick, 0)
```

## Installation

Pin the minor version.

```
poetry add asyncgui-ext-clock@~0.5
pip install "asyncgui-ext-clock>=0.5,<0.6"
```

## Tested on

- CPython 3.10
- CPython 3.11
- CPython 3.12

## Misc

- [YouTube Demo](https://youtu.be/kPVzO8fF0yg) (with Kivy)
