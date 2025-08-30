# Clock

```python
import asyncgui
from asyncgui_ext.clock import Clock

clock = Clock()

async def async_fn():
    await clock.sleep(20)  # Waits for 20 time units
    print("Hello")

asyncgui.start(async_fn())
clock.advance(10)  # Advances the clock by 10 time units.
clock.advance(10)  # Total of 20 time units. The async_fn will wake up, and prints 'Hello'.
```

The example above effectively illustrate how this module works but it's not practical.
In a real-world program, you probably want to call ``clock.advance()`` in a main loop.
For example, if you are using `PyGame`, you may want to do:

```python
pygame_clock = pygame.time.Clock()
clock = asyncgui_ext.clock.Clock()

# main loop
while running:
    ...

    dt = pygame_clock.tick(fps)
    clock.advance(dt)
```

## Installation

Pin the minor version.

```
poetry add asyncgui-ext-clock@~0.6
pip install "asyncgui-ext-clock>=0.6,<0.7"
```

## Tested on

- CPython 3.10
- CPython 3.11
- CPython 3.12
- CPython 3.13
- PyPy 3.10
