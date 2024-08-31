__all__ = (
    'ClockEvent', 'Clock',
)

import types
from typing import TypeAlias, TypeVar
from collections.abc import Callable, Awaitable, AsyncIterator
from functools import partial
from dataclasses import dataclass
from contextlib import AbstractAsyncContextManager
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

from asyncgui import Cancelled, Task, move_on_when, _sleep_forever, _current_task

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
        Waits for a specified number of times the :meth:`tick` to be called.

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
        async with _repeat_sleeping(self, step) as sleep:
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
        async with _repeat_sleeping(self, step) as sleep:
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
        async with _repeat_sleeping(self, step) as sleep:
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
        async with _repeat_sleeping(self, step) as sleep:
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
        async with _repeat_sleeping(self, step) as sleep:
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

    async def interpolate_sequence(self, start, end, *, duration, step=0, transition=_linear, output_type=tuple) -> AsyncIterator:
        '''
        Same as :meth:`interpolate_scalar` except this one is for sequence type.

        .. code-block::

            async for v in clock.interpolate_sequence([0, 50], [100, 100], duration=100, step=30):
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

        if duration:
            async for p in self.anim_with_ratio(step=step, base=duration):
                if p >= 1.0:
                    break
                p = transition(p)
                yield output_type(p * slope_elem + start_elem for slope_elem, start_elem in zip_(slope, start))
        else:
            await self.sleep(0)

        p = transition(1.)
        yield output_type(p * slope_elem + start_elem for slope_elem, start_elem in zip_(slope, start))

    interpolate_seq = interpolate_sequence
    '''
    An alias for :meth:`interpolate_sequence`.
    '''

    async def run_in_thread(self, func, *, daemon=None, polling_interval) -> Awaitable:
        '''
        Creates a new thread, runs a function within it, then waits for the completion of that function.

        .. code-block::

            return_value = await clock.run_in_thread(func, polling_interval=...)
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

        Thread(target=wrapper, daemon=daemon, name="asyncgui_ext.clock.Clock.run_in_thread").start()
        async with _repeat_sleeping(self, polling_interval) as sleep:
            while not done:
                await sleep()
        if exception is not None:
            raise exception
        return return_value

    async def run_in_executor(self, executer: ThreadPoolExecutor, func, *, polling_interval) -> Awaitable:
        '''
        Runs a function within a :class:`concurrent.futures.ThreadPoolExecutor`, and waits for the completion of the
        function.

        .. code-block::

            executor = ThreadPoolExecutor()
            return_value = await clock.run_in_executor(executor, func, polling_interval=...)
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
            async with _repeat_sleeping(self, polling_interval) as sleep:
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

    _update = partial(_update, setattr, zip, min)

    @types.coroutine
    def _anim_attrs(
            self, obj, duration, step, transition, output_seq_type, animated_properties,
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
            event = self.schedule_interval(
                partial(_update, obj, duration, transition, output_seq_type, anim_params, (yield _current_task)[0][0], [0, ]),
                step,
            )
            yield _sleep_forever
        finally:
            event.cancel()

    del _update

    def anim_attrs(self, obj, *, duration, step=0, transition=_linear, output_seq_type=tuple,
                   **animated_properties) -> Awaitable:
        '''
        Animates attibutes of any object.

        .. code-block::

            import types

            obj = types.SimpleNamespace(x=0, size=(200, 300))
            await clock.anim_attrs(obj, x=100, size=(400, 400), duration=2)

        The ``output_seq_type`` parameter.

        .. code-block::

            obj = types.SimpleNamespace(size=(200, 300))
            await clock.anim_attrs(obj, size=(400, 400), duration=2, output_seq_type=list)
            assert type(obj.size) is list
        '''
        return self._anim_attrs(obj, duration, step, transition, output_seq_type, animated_properties)

    def anim_attrs_abbr(self, obj, *, d, s=0, t=_linear, output_seq_type=tuple, **animated_properties) -> Awaitable:
        '''
        :meth:`anim_attrs` cannot animate attributes named ``step``, ``duration`` and ``transition`` but this one can.
        '''
        return self._anim_attrs(obj, d, s, t, output_seq_type, animated_properties)


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
