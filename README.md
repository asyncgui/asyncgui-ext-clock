# Clock

An event scheduler.

```python
from asyncgui_ext.clock import Clock

clock = Clock()

# Schedules a function to be called after a delay of 20 time units.
clock.schedule_once(lambda dt: print("Hello"), 20)

# Advances the clock by 10 time units.
clock.tick(10)

# The clock advanced by a total of 20 time units, and the callback function will be called.
clock.tick(10)  # => Hello
```

It also supports async-style APIs. The code below does the same thing as the previous one but in an async-style.

```python
import asyncgui
from asyncgui_ext.clock import Clock

clock = Clock()

async def main():
    await clock.sleep(20)
    print("Hello")

asyncgui.start(main())
clock.tick(10)
clock.tick(10)  # => Hello
```

The two examples above effectively illustrate how this module works, but they are not practical.
In a real-world program, you probably want to call ``clock.tick()`` in a loop or schedule it to be called repeatedly using another scheduling API.
For example, if you are using `PyGame`, you want to do:

```python
clock = pygame.time.Clock()
vclock = asyncui_ext.clock.Clock()

# main loop
while running:
    ...

    dt = clock.tick(fps)
    vclock.tick(dt)
```

And if you are using `Kivy`, you want to do:

```python
from kivy.clock import Clock
vclock = asyncui_ext.clock.Clock()

Clock.schedule_interval(vclock.tick, 0)
```

## Installation

```
poetry add asyncgui-ext-clock@~0.1
pip install "asyncgui-ext-clock>=0.1,<0.2"
```

## Tested on

- CPython 3.10
- CPython 3.11
