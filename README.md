# Clock

*An event scheduler designed for asyncgui programs.*

First, take a look at the callback-style code below that has nothing to do with `asyncgui`.
If you've ever used `Kivy` or `Pyglet`, you may find it familiar.

```python
from asyncgui_ext.clock import Clock

clock = Clock()

# Schedules a function to be called after a delay of 20 time units.
clock.schedule_once(lambda dt: print("Hello"), 20)

# Advances the clock by 10 time units.
clock.tick(10)

# The clock advanced by a total of 20 time units.
# The callback function will be called.
clock.tick(10)  # => Hello
```

Next one is async/await-style code that involves `asyncgui`, and does the same thing as the previous.

```python
import asyncgui
from asyncgui_ext.clock import Clock

clock = Clock()

async def async_fn():
    await clock.sleep(20)
    print("Hello")

asyncgui.start(async_fn())
clock.tick(10)
clock.tick(10)  # => Hello
```

These two examples effectively illustrate how this module works but they are not practical.
In a real-world program, you probably want to call ``clock.tick()`` in a loop or schedule it to be called repeatedly using another scheduling API.
For example, if you are using `PyGame`, you may want to do:

```python
clock = pygame.time.Clock()
vclock = asyncgui_ext.clock.Clock()

# main loop
while running:
    ...

    dt = clock.tick(fps)
    vclock.tick(dt)
```

And if you are using `Kivy`, you may want to do:

```python
from kivy.clock import Clock

vclock = asyncui_ext.clock.Clock()
Clock.schedule_interval(vclock.tick, 0)
```

## Installation

Pin the minor version.

```
poetry add asyncgui-ext-clock@~0.3
pip install "asyncgui-ext-clock>=0.3,<0.4"
```

## Tested on

- CPython 3.10
- CPython 3.11
- CPython 3.12

## Misc

- [YouTube Demo](https://youtu.be/kPVzO8fF0yg) (with Kivy)
