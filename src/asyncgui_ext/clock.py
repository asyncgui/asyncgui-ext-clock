__all__ = (
    'ClockEvent', 'Clock',
    'sleep', 'move_on_after', 'n_frames',
    'anim_attrs', 'anim_attrs_abbr',
    'anim_with_dt', 'anim_with_et', 'anim_with_dt_et', 'anim_with_ratio', 'anim_with_dt_et_ratio',
    'interpolate_scalar', 'interpolate_sequence',
    'run_in_thread', 'run_in_executor',
)

import types
from typing import TypeAlias, TypeVar
from collections.abc import Callable, Awaitable, AsyncIterator
from functools import partial
from dataclasses import dataclass
from contextlib import AbstractAsyncContextManager
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

from asyncgui import ISignal, Cancelled, Task, wait_any_cm, _sleep_forever, _current_task

TimeUnit = TypeVar("TimeUnit")
ClockCallback: TypeAlias = Callable[[TimeUnit], None]


@dataclass(slots=True)
class ClockEvent:
    _deadline: TimeUnit
    _last_tick: TimeUnit
    callback: ClockCallback
    '''
    The callback function registered using the ``Clock.schedule_xxx()`` call that returned this instance.
    You can replace it with another one by simply assigning to this attribute.

    .. code-block::

        event = clock.schedule_xxx(...)
        event.callback = another_function
    '''

    _interval: TimeUnit | None
    _cancelled: bool = False

    def cancel(self):
        self._cancelled = True


class Clock:
    __slots__ = ('_cur_time', '_events', '_events_to_be_added', '__weakref__', )

    def __init__(self, initial_time=0):
        self._cur_time = initial_time
        self._events: list[ClockEvent] = []
        self._events_to_be_added: list[ClockEvent] = []  # double buffering

    @property
    def current_time(self) -> TimeUnit:
        return self._cur_time

    def tick(self, delta_time):
        '''
        Advances the clock time and triggers scheduled events accordingly.
        The ``delta_time`` must be 0 or greater.
        '''
        self._cur_time += delta_time
        cur_time = self._cur_time

        events = self._events
        events_tba = self._events_to_be_added
        tba_append = events_tba.append
        if events_tba:
            events.extend(events_tba)
            events_tba.clear()
        for e in events:
            if e._cancelled:
                continue
            if e._deadline > cur_time:
                tba_append(e)
                continue
            if e.callback(cur_time - e._last_tick) is False or e._interval is None:
                continue
            e._deadline += e._interval
            e._last_tick = cur_time
            tba_append(e)
        events.clear()
        # swap
        self._events = events_tba
        self._events_to_be_added = events

    def schedule_once(self, func, delay) -> ClockEvent:
        '''
        Schedules the ``func`` to be called after the ``delay``.

        To unschedule:

        .. code-block::

            event = clock.schedule_once(func, 10)
            event.cancel()
        '''
        cur_time = self._cur_time
        event = ClockEvent(cur_time + delay, cur_time, func, None)
        self._events_to_be_added.append(event)
        return event

    def schedule_interval(self, func, interval) -> ClockEvent:
        '''
        Schedules the ``func`` to be called repeatedly at a specified interval.

        There are two ways to unschedule the event. One is the same as :meth:`schedule_once`.

        .. code-block::

            event = clock.schedule_once(func, 10)
            event.cancel()

        The other one is to return ``False`` from the callback function.

        .. code-block::

            def func(dt):
                if some_condition:
                    return False
        '''
        cur_time = self._cur_time
        event = ClockEvent(cur_time + interval, cur_time, func, interval)
        self._events_to_be_added.append(event)
        return event


async def sleep(clock: Clock, duration) -> Awaitable:
    '''
    Waits for a specified period of time.

    .. code-block::

        await sleep(clock, 10)
    '''
    sig = ISignal()
    event = clock.schedule_once(sig.set, duration)

    try:
        await sig.wait()
    except Cancelled:
        event.cancel()
        raise


def move_on_after(clock: Clock, timeout) -> AbstractAsyncContextManager[Task]:
    '''
    Returns an async context manager that applies a time limit to its code block,
    like :func:`trio.move_on_after` does.

    .. code-block::

        async with move_on_after(clock, 10) as bg_task:
            ...

        if bg_task.finished:
            print("The code block was interrupted due to a timeout")
        else:
            print("The code block exited gracefully.")
    '''
    return wait_any_cm(sleep(clock, timeout))


@types.coroutine
def n_frames(clock: Clock, n: int) -> Awaitable:
    '''
    Waits for a specified number of times the :meth:`Clock.tick` to be called.

    .. code-block::

        await n_frames(clock, 2)

    If you want to wait for one time, :func:`sleep` is preferable for a performance reason.

    .. code-block::

        await sleep(clock, 0)
    '''
    if n < 0:
        raise ValueError(f"Waiting for {n} frames doesn't make sense.")
    if not n:
        return

    task = (yield _current_task)[0][0]

    def callback(dt):
        nonlocal n
        n -= 1
        if not n:
            task._step()
            return False

    event = clock.schedule_interval(callback, 0)

    try:
        yield _sleep_forever
    finally:
        event.cancel()


async def anim_with_dt(clock: Clock, *, step=0) -> AsyncIterator[TimeUnit]:
    '''
    An async form of :meth:`Clock.schedule_interval`.

    .. code-block::

        async for dt in anim_with_dt(clock, step=10):
            print(dt)
            if some_condition:
                break

    The code above is quivalent to the below.

    .. code-block::

        def callback(dt):
            print(dt)
            if some_condition:
                return False

        clock.schedule_interval(callback, 10)

    **Restriction**

    You are not allowed to perform any kind of async operations during the loop.

    .. code-block::

        async for dt in anim_with_dt(clock):
            await awaitable  # NOT ALLOWED
            async with async_context_manager:  # NOT ALLOWED
                ...
            async for __ in async_iterator:  # NOT ALLOWED
                ...

    This is also true of other ``anim_with_xxx`` APIs.
    '''
    async with _repeat_sleeping(clock, step) as sleep:
        while True:
            yield await sleep()


async def anim_with_et(clock: Clock, *, step=0) -> AsyncIterator[TimeUnit]:
    '''
    Same as :func:`anim_with_dt` except this one generates the total elapsed time of the loop instead of the elapsed
    time between frames.

    .. code-block::

        timeout = ...
        async for et in anim_with_et(clock):
            ...
            if et > timeout:
                break
    '''
    et = 0
    async with _repeat_sleeping(clock, step) as sleep:
        while True:
            et += await sleep()
            yield et


async def anim_with_dt_et(clock: Clock, *, step=0) -> AsyncIterator[tuple[TimeUnit, TimeUnit]]:
    '''
    :func:`anim_with_dt` and :func:`anim_with_et` combined.

    .. code-block::

        async for dt, et in anim_with_dt_et(clock):
            ...
    '''
    et = 0
    async with _repeat_sleeping(clock, step) as sleep:
        while True:
            dt = await sleep()
            et += dt
            yield dt, et


async def anim_with_ratio(clock: Clock, *, duration, step=0) -> AsyncIterator[float]:
    '''
    Same as :func:`anim_with_et` except this one generates the total progression ratio of the loop.

    .. code-block::

        async for p in anim_with_ratio(clock, duration=...):
            print(p * 100, "%")

    If you want to progress at a non-consistant rate, you may find the
    `source code <https://github.com/kivy/kivy/blob/master/kivy/animation.py>`__
    of the :class:`kivy.animation.AnimationTransition` helpful.

    .. code-block::

        async for p in anim_with_ratio(clock, duration=...):
            p = p * p  # quadratic
            print(p * 100, "%")
    '''
    if not duration:
        await sleep(clock, step)
        yield 1.0
        return
    et = 0
    async with _repeat_sleeping(clock, step) as sleep_:
        while et < duration:
            et += await sleep_()
            yield et / duration


async def anim_with_dt_et_ratio(clock: Clock, *, duration, step=0) -> AsyncIterator[tuple[TimeUnit, TimeUnit, float]]:
    '''
    :func:`anim_with_dt`, :func:`anim_with_et` and :func:`anim_with_ratio` combined.

    .. code-block::

        async for dt, et, p in anim_with_dt_et_ratio(clock):
            ...
    '''
    async with _repeat_sleeping(clock, step) as sleep:
        if not duration:
            dt = await sleep()
            yield dt, dt, 1.0
            return
        et = 0.
        while et < duration:
            dt = await sleep()
            et += dt
            yield dt, et, et / duration


def _linear(p):
    return p


async def interpolate_scalar(clock, start, end, *, duration, step=0, transition=_linear) -> AsyncIterator:
    '''
    Interpolates between the values ``start`` and ``end`` in an async-manner.

    .. code-block::

        async for v in interpolate(clock, 0, 100, duration=100, step=30):
            print(int(v))

    ============ ======
    elapsed time output
    ============ ======
    0            0
    30           30
    60           60
    90           90
    **120**      100
    ============ ======
    '''
    slope = end - start
    yield transition(0.) * slope + start
    async for p in anim_with_ratio(clock, step=step, duration=duration):
        if p >= 1.0:
            break
        yield transition(p) * slope + start
    yield transition(1.) * slope + start


async def interpolate_sequence(clock, start, end, *, duration, step=0, transition=_linear, output_type=tuple) -> AsyncIterator:
    '''
    Same as :func:`interpolate_scalar` except this one is for sequence type.

    .. code-block::

        async for v in interpolate_sequence(clock, [0, 50], [100, 100], duration=100, step=30):
            print(v)

    ============ ==========
    elapsed time output
    ============ ==========
    0            (0, 50)
    30           (30, 65)
    60           (60, 80)
    90           (90, 95)
    **120**      (100, 100)
    ============ ==========
    '''
    zip_ = zip
    slope = tuple(end_elem - start_elem for end_elem, start_elem in zip_(end, start))

    p = transition(0.)
    yield output_type(p * slope_elem + start_elem for slope_elem, start_elem in zip_(slope, start))

    async for p in anim_with_ratio(clock, step=step, duration=duration):
        if p >= 1.0:
            break
        p = transition(p)
        yield output_type(p * slope_elem + start_elem for slope_elem, start_elem in zip_(slope, start))

    p = transition(1.)
    yield output_type(p * slope_elem + start_elem for slope_elem, start_elem in zip_(slope, start))


async def run_in_thread(clock: Clock, func, *, daemon=None, polling_interval) -> Awaitable:
    '''
    Creates a new thread, runs a function within it, then waits for the completion of that function.

    .. code-block::

        return_value = await run_in_thread(clock, func, polling_interval=...)
    '''
    return_value = None
    exception = None
    done = False

    def wrapper():
        nonlocal return_value, done, exception
        try:
            return_value = func()
        except Exception as e:
            exception = e
        finally:
            done = True

    Thread(target=wrapper, daemon=daemon).start()
    async with _repeat_sleeping(clock, polling_interval) as sleep:
        while not done:
            await sleep()
    if exception is not None:
        raise exception
    return return_value


async def run_in_executor(clock: Clock, executer: ThreadPoolExecutor, func, *, polling_interval) -> Awaitable:
    '''
    Runs a function within a :class:`concurrent.futures.ThreadPoolExecutor`, and waits for the completion of the
    function.

    .. code-block::

        executor = ThreadPoolExecutor()
        return_value = await run_in_executor(clock, executor, func, polling_interval=...)
    '''
    return_value = None
    exception = None
    done = False

    def wrapper():
        nonlocal return_value, done, exception
        try:
            return_value = func()
        except Exception as e:
            exception = e
        finally:
            done = True

    future = executer.submit(wrapper)
    try:
        async with _repeat_sleeping(clock, polling_interval) as sleep:
            while not done:
                await sleep()
    except Cancelled:
        future.cancel()
        raise
    if exception is not None:
        raise exception
    return return_value


def _update(setattr, zip, min, obj, duration, transition, output_seq_type, anim_params, task, p_time, dt):
    time = p_time[0] + dt
    p_time[0] = time

    # calculate progression
    progress = min(1., time / duration)
    t = transition(progress)

    # apply progression on obj
    for attr_name, org_value, slope, is_seq in anim_params:
        if is_seq:
            new_value = output_seq_type(
                slope_elem * t + org_elem
                for org_elem, slope_elem in zip(org_value, slope)
            )
            setattr(obj, attr_name, new_value)
        else:
            setattr(obj, attr_name, slope * t + org_value)

    # time to stop ?
    if progress >= 1.:
        task._step()
        return False


_update = partial(_update, setattr, zip, min)


@types.coroutine
def _anim_attrs(
        clock: Clock, obj, duration, step, transition, output_seq_type, animated_properties,
        getattr=getattr, isinstance=isinstance, tuple=tuple, partial=partial, native_seq_types=(tuple, list),
        zip=zip, _update=_update,
        _current_task=_current_task, _sleep_forever=_sleep_forever, /):

    # get current values & calculate slopes
    anim_params = tuple(
        (
            org_value := getattr(obj, attr_name),
            is_seq := isinstance(org_value, native_seq_types),
            (
                org_value := tuple(org_value),
                slope := tuple(goal_elem - org_elem for goal_elem, org_elem in zip(goal_value, org_value)),
            ) if is_seq else (slope := goal_value - org_value),
        ) and (attr_name, org_value, slope, is_seq, )
        for attr_name, goal_value in animated_properties.items()
    )

    try:
        event = clock.schedule_interval(
            partial(_update, obj, duration, transition, output_seq_type, anim_params, (yield _current_task)[0][0], [0, ]),
            step,
        )
        yield _sleep_forever
    finally:
        event.cancel()


del _update


def anim_attrs(clock, obj, *, duration, step=0, transition=_linear, output_seq_type=tuple,
               **animated_properties) -> Awaitable:
    '''
    Animates attibutes of any object.

    .. code-block::

        import types

        obj = types.SimpleNamespace(x=0, size=(200, 300))
        await anim_attrs(clock, obj, x=100, size=(400, 400))

    The ``output_seq_type`` parameter.

    .. code-block::

        obj = types.SimpleNamespace(size=(200, 300))
        await anim_attrs(clock, obj, size=(400, 400), output_seq_type=list)
        assert type(obj.size) is list
    '''
    return _anim_attrs(clock, obj, duration, step, transition, output_seq_type, animated_properties)


def anim_attrs_abbr(clock, obj, *, d, s=0, t=_linear, output_seq_type=tuple, **animated_properties) -> Awaitable:
    '''
    :func:`anim_attrs` cannot animate attributes named ``step``, ``duration`` and ``transition`` but this one can.
    '''
    return _anim_attrs(clock, obj, d, s, t, output_seq_type, animated_properties)


class _repeat_sleeping:
    __slots__ = ('_timer', '_interval', '_event', )

    def __init__(self, clock: Clock, interval):
        self._timer = clock
        self._interval = interval

    @staticmethod
    @types.coroutine
    def _sleep(_f=_sleep_forever):
        return (yield _f)[0][0]

    @types.coroutine
    def __aenter__(self, _current_task=_current_task) -> Awaitable[Callable[[], Awaitable[TimeUnit]]]:
        task = (yield _current_task)[0][0]
        self._event = self._timer.schedule_interval(task._step, self._interval)
        return self._sleep

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._event.cancel()
