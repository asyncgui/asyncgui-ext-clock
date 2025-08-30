__all__ = (
    'ClockEvent', 'Clock',
)

import types
from typing import TypeAlias, TypeVar
from collections.abc import Callable, Awaitable, AsyncIterator
from functools import partial
from dataclasses import dataclass
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from asyncgui import Task, move_on_when, _sleep_forever, _current_task, ExclusiveEvent, _wait_args_0, current_task

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

    def __enter__(self):
        return self

    def __exit__(self, *__):
        self._cancelled = True


class Clock:
    def __init__(self, initial_time=0):
        self._cur_time = initial_time
        self._events: list[ClockEvent] = []
        self._events_to_be_added: list[ClockEvent] = []  # double buffering

    @property
    def current_time(self) -> TimeUnit:
        return self._cur_time

    def advance(self, delta_time):
        '''
        Advances the clock time and triggers scheduled events accordingly.

        :param delta_time: Must be 0 or greater.

        .. warning::

            Don't call this method recursively.
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
            e.callback(cur_time - e._last_tick)
            e._deadline += e._interval
            e._last_tick = cur_time
            tba_append(e)
        events.clear()
        # swap
        self._events = events_tba
        self._events_to_be_added = events

    tick = advance
    '''An alias of :meth:`advance`.'''

    def schedule_interval(self, func, interval) -> ClockEvent:
        '''
        Schedules the ``func`` to be called repeatedly at a specified interval.
        '''
        cur_time = self._cur_time
        event = ClockEvent(cur_time + interval, cur_time, func, interval)
        self._events_to_be_added.append(event)
        return event

    @types.coroutine
    def sleep(self, duration) -> Awaitable:
        '''
        Waits for a specified period of time.

        .. code-block::

            await clock.sleep(10)
        '''
        task = (yield _current_task)[0][0]
        event = self.schedule_interval(task._step, duration)
        try:
            yield _sleep_forever
        finally:
            event.cancel()

    def move_on_after(self, timeout) -> AbstractAsyncContextManager[Task]:
        '''
        Returns an async context manager that applies a time limit to its code block,
        like :func:`trio.move_on_after` does.

        .. code-block::

            async with clock.move_on_after(10) as timeout_tracker:
                ...

            if timeout_tracker.finished:
                print("The code block was interrupted due to a timeout")
            else:
                print("The code block exited gracefully.")
        '''
        return move_on_when(self.sleep(timeout))

    @types.coroutine
    def n_frames(self, n: int) -> Awaitable:
        '''
        Waits for a specified number of times the :meth:`advance` to be called.

        .. code-block::

            await clock.n_frames(2)

        If you want to wait for one time, :meth:`sleep` is preferable for a performance reason.

        .. code-block::

            await clock.sleep(0)
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

        event = self.schedule_interval(callback, 0)

        try:
            yield _sleep_forever
        finally:
            event.cancel()

    @asynccontextmanager
    async def sleep_freq(self, duration, *, free_to_await=False) -> AsyncIterator[Callable[[], Awaitable[TimeUnit]]]:
        '''
        An async form of :meth:`schedule_interval`. The following callback-style code:

        .. code-block::

            def callback(dt):
                print(dt)
                if some_condition:
                    event.cancel()

            event = clock.schedule_interval(callback, 10)

        is equivalent to the following async-style code:

        .. code-block::

            async with clock.sleep_freq(10) as sleep:
                while True:
                    dt = await sleep()
                    print(dt)
                    if some_condition:
                        break

        .. versionadded:: 0.6.1

        The ``free_to_await`` parameter:

        If set to False (the default), the only permitted async operation within the with-block is ``await xxx()``,
        where ``xxx`` is the identifier specified in the as-clause. To lift this restriction, set ``free_to_await`` to
        True — at the cost of slightly reduced performance.
        '''
        clock_event = self.schedule_interval(None, duration)
        try:
            if free_to_await:
                e = ExclusiveEvent()
                clock_event.callback = e.fire
                yield e.wait_args_0
            else:
                task = await current_task()
                clock_event.callback = task._step
                yield _wait_args_0
        finally:
            clock_event.cancel()

    async def anim_with_dt(self, *, step=0) -> AsyncIterator[TimeUnit]:
        '''
        An async form of :meth:`schedule_interval`.

        .. code-block::

            async for dt in clock.anim_with_dt(step=10):
                print(dt)
                if some_condition:
                    break

        The code above is quivalent to the below.

        .. code-block::

            def callback(dt):
                print(dt)
                if some_condition:
                    event.cancel()

            event = clock.schedule_interval(callback, 10)

        **Restriction**

        You are not allowed to perform any kind of async operations during the loop.

        .. code-block::

            async for dt in clock.anim_with_dt():
                await awaitable  # NOT ALLOWED
                async with async_context_manager:  # NOT ALLOWED
                    ...
                async for __ in async_iterator:  # NOT ALLOWED
                    ...

        This is also true of other ``anim_with_xxx`` APIs.
        '''
        async with self.sleep_freq(step) as sleep:
            while True:
                yield await sleep()

    async def anim_with_et(self, *, step=0) -> AsyncIterator[TimeUnit]:
        '''
        .. code-block::

            async for et in clock.anim_with_et():
                print(et)

        The code above is equivalent to the below.

        .. code-block::

            et = 0
            async for dt in clock.anim_with_dt():
                et += dt
                print(et)
        '''
        et = 0
        async with self.sleep_freq(step) as sleep:
            while True:
                et += await sleep()
                yield et

    async def anim_with_dt_et(self, *, step=0) -> AsyncIterator[tuple[TimeUnit, TimeUnit]]:
        '''
        :meth:`anim_with_dt` and :meth:`anim_with_et` combined.

        .. code-block::

            async for dt, et in clock.anim_with_dt_et():
                ...
        '''
        et = 0
        async with self.sleep_freq(step) as sleep:
            while True:
                dt = await sleep()
                et += dt
                yield dt, et

    async def anim_with_ratio(self, *, base, step=0) -> AsyncIterator[float]:
        '''
        .. code-block::

            async for p in clock.anim_with_ratio(base=100):
                print(p * 100, "%")

        The code above is equivalent to the below.

        .. code-block::

            base = 100
            async for et in clock.anim_with_et():
                print(et / base * 100, "%")

        If you want to progress at a non-consistant rate, you may find the
        `source code <https://github.com/kivy/kivy/blob/master/kivy/animation.py>`__
        of the :class:`kivy.animation.AnimationTransition` helpful.

        .. code-block::

            async for p in clock.anim_with_ratio(base=...):
                p = p * p  # quadratic
                print(p * 100, "%")

        .. versionchanged:: 0.5.0

            The ``duration`` parameter was replaced with the ``base`` parameter.
            The loop no longer stops when the progression reaches 1.0.
        '''
        et = 0
        async with self.sleep_freq(step) as sleep:
            while True:
                et += await sleep()
                yield et / base

    async def anim_with_dt_et_ratio(self, *, base, step=0) -> AsyncIterator[tuple[TimeUnit, TimeUnit, float]]:
        '''
        :meth:`anim_with_dt`, :meth:`anim_with_et` and :meth:`anim_with_ratio` combined.

        .. code-block::

            async for dt, et, p in clock.anim_with_dt_et_ratio(...):
                ...

        .. versionchanged:: 0.5.0

            The ``duration`` parameter was replaced with the ``base`` parameter.
            The loop no longer stops when the progression reaches 1.0.
        '''
        async with self.sleep_freq(step) as sleep:
            et = 0.
            while True:
                dt = await sleep()
                et += dt
                yield dt, et, et / base

    def _linear(p):
        return p

    async def interpolate_scalar(self, start, end, *, duration, step=0, transition=_linear) -> AsyncIterator:
        '''
        Interpolates between the values ``start`` and ``end`` in an async-manner.

        .. code-block::

            async for v in clock.interpolate(0, 100, duration=100, step=30):
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
        if duration:
            async for p in self.anim_with_ratio(step=step, base=duration):
                if p >= 1.0:
                    break
                yield transition(p) * slope + start
        else:
            await self.sleep(0)
        yield transition(1.) * slope + start

    interpolate = interpolate_scalar
    '''
    An alias of :meth:`interpolate_scalar`.

    .. versionadded:: 0.5.2
    '''

    async def interpolate_sequence(self, start, end, *, duration, step=0, transition=_linear) -> AsyncIterator:
        '''
        Same as :meth:`interpolate_scalar` except this one is for sequence types.

        .. code-block::

            async for v in clock.interpolate_sequence([0, 50], [100, 100], duration=100, step=30):
                print(v)

        ============ ==========
        elapsed time output
        ============ ==========
        0            [0, 50]
        30           [30, 65]
        60           [60, 80]
        90           [90, 95]
        **120**      [100, 100]
        ============ ==========
        '''
        zip_ = zip
        slope = [end_elem - start_elem for end_elem, start_elem in zip_(end, start)]

        p = transition(0.)
        yield [p * slope_elem + start_elem for slope_elem, start_elem in zip_(slope, start)]

        if duration:
            async for p in self.anim_with_ratio(step=step, base=duration):
                if p >= 1.0:
                    break
                p = transition(p)
                yield [p * slope_elem + start_elem for slope_elem, start_elem in zip_(slope, start)]
        else:
            await self.sleep(0)

        p = transition(1.)
        yield [p * slope_elem + start_elem for slope_elem, start_elem in zip_(slope, start)]

    interpolate_seq = interpolate_sequence
    '''
    An alias of :meth:`interpolate_sequence`.
    '''

    def _update(setattr, zip, min, obj, duration, transition, anim_params, task, p_time, dt):
        time = p_time[0] + dt
        p_time[0] = time

        # calculate progression
        progress = min(1., time / duration)
        t = transition(progress)

        # apply progression on obj
        for attr_name, org_value, slope, is_seq in anim_params:
            if is_seq:
                new_value = [
                    slope_elem * t + org_elem
                    for org_elem, slope_elem in zip(org_value, slope)
                ]
                setattr(obj, attr_name, new_value)
            else:
                setattr(obj, attr_name, slope * t + org_value)

        # time to stop ?
        if progress >= 1.:
            task._step()

    _update = partial(_update, setattr, zip, min)

    @types.coroutine
    def _anim_attrs(
            self, obj, duration, step, transition, animated_properties,
            getattr=getattr, isinstance=isinstance, tuple=tuple, partial=partial, native_seq_types=(tuple, list),
            zip=zip, _update=_update,
            _current_task=_current_task, _sleep_forever=_sleep_forever, /):
        # get current values & calculate slopes
        anim_params = [
            (
                org_value := getattr(obj, attr_name),
                is_seq := isinstance(org_value, native_seq_types),
                (
                    org_value := tuple(org_value),
                    slope := [goal_elem - org_elem for goal_elem, org_elem in zip(goal_value, org_value)],
                ) if is_seq else (slope := goal_value - org_value),
            ) and (attr_name, org_value, slope, is_seq, )
            for attr_name, goal_value in animated_properties.items()
        ]

        try:
            event = self.schedule_interval(
                partial(_update, obj, duration, transition, anim_params, (yield _current_task)[0][0], [0, ]),
                step,
            )
            yield _sleep_forever
        finally:
            event.cancel()

    del _update

    def anim_attrs(self, obj, *, duration, step=0, transition=_linear, **animated_properties) -> Awaitable:
        '''
        Animates attributes of any object.

        .. code-block::

            import types

            obj = types.SimpleNamespace(x=0, size=(200, 300))
            await clock.anim_attrs(obj, x=100, size=(400, 400), duration=2)

        Only numbers and flat numeric sequences are supported.
        Nested sequences and dictionaries are not supported.

        .. code-block::

            await anim_attrs(obj, dictionary={'x': 1.})  # not supported
            await anim_attrs(obj, nested_sequence=[[10, 20, ]])  # not supported

            await anim_attrs(obj, number=1, flat_sequence=(100, 200))  # OK
        '''
        return self._anim_attrs(obj, duration, step, transition, animated_properties)

    def anim_attrs_abbr(self, obj, *, d, s=0, t=_linear, **animated_properties) -> Awaitable:
        '''
        :meth:`anim_attrs` cannot animate attributes named ``step``, ``duration`` and ``transition`` but this one can.
        '''
        return self._anim_attrs(obj, d, s, t, animated_properties)
