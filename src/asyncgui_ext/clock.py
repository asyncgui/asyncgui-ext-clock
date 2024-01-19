__all__ = ('ClockEvent', 'Clock', 'Transition', )

import types
from typing import TypeAlias, TypeVar
from collections.abc import Callable, Awaitable, AsyncIterator
from functools import partial
import math
from dataclasses import dataclass
from contextlib import AbstractAsyncContextManager
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

from asyncgui import ISignal, Cancelled, Task, wait_any_cm, _sleep_forever, _current_task

TimeUnit = TypeVar("TimeUnit")
ClockCallback: TypeAlias = Callable[[TimeUnit], None]


class Transition:
    '''
    :class:`kivy.animation.AnimationTransition`
    '''
    def linear(p):
        return p

    def in_quad(p):
        return p * p

    def out_quad(p):
        return -1.0 * p * (p - 2.0)

    def in_out_quad(p):
        p = p * 2
        if p < 1:
            return 0.5 * p * p
        p -= 1.0
        return -0.5 * (p * (p - 2.0) - 1.0)

    def in_cubic(p):
        return p * p * p

    def out_cubic(p):
        p = p - 1.0
        return p * p * p + 1.0

    def in_out_cubic(p):
        p = p * 2
        if p < 1:
            return 0.5 * p * p * p
        p -= 2
        return 0.5 * (p * p * p + 2.0)

    def in_quart(p):
        return p * p * p * p

    def out_quart(p):
        p = p - 1.0
        return -1.0 * (p * p * p * p - 1.0)

    def in_out_quart(p):
        p = p * 2
        if p < 1:
            return 0.5 * p * p * p * p
        p -= 2
        return -0.5 * (p * p * p * p - 2.0)

    def in_quint(p):
        return p * p * p * p * p

    def out_quint(p):
        p = p - 1.0
        return p * p * p * p * p + 1.0

    def in_out_quint(p):
        p = p * 2
        if p < 1:
            return 0.5 * p * p * p * p * p
        p -= 2.0
        return 0.5 * (p * p * p * p * p + 2.0)

    def in_sine(p, cos=math.cos, pi=math.pi):
        return -1.0 * cos(p * (pi / 2.0)) + 1.0

    def out_sine(p, sin=math.sin, pi=math.pi):
        return sin(p * (pi / 2.0))

    def in_out_sine(p, cos=math.cos, pi=math.pi):
        return -0.5 * (cos(pi * p) - 1.0)

    def in_expo(p, pow=pow):
        if p == 0:
            return 0.0
        return pow(2, 10 * (p - 1.0))

    def out_expo(p, pow=pow):
        if p == 1.0:
            return 1.0
        return -pow(2, -10 * p) + 1.0

    def in_out_expo(p, pow=pow):
        if p == 0:
            return 0.0
        if p == 1.:
            return 1.0
        p = p * 2
        if p < 1:
            return 0.5 * pow(2, 10 * (p - 1.0))
        p -= 1.0
        return 0.5 * (-pow(2, -10 * p) + 2.0)

    def in_circ(p, sqrt=math.sqrt):
        return -1.0 * (sqrt(1.0 - p * p) - 1.0)

    def out_circ(p, sqrt=math.sqrt):
        p = p - 1.0
        return sqrt(1.0 - p * p)

    def in_out_circ(p, sqrt=math.sqrt):
        p = p * 2
        if p < 1:
            return -0.5 * (sqrt(1.0 - p * p) - 1.0)
        p -= 2.0
        return 0.5 * (sqrt(1.0 - p * p) + 1.0)

    def in_elastic(p, sin=math.sin, pi=math.pi, pow=pow):
        p = .3
        s = p / 4.0
        q = p
        if q == 1:
            return 1.0
        q -= 1.0
        return -(pow(2, 10 * q) * sin((q - s) * (2 * pi) / p))

    def out_elastic(p, sin=math.sin, pi=math.pi, pow=pow):
        p = .3
        s = p / 4.0
        q = p
        if q == 1:
            return 1.0
        return pow(2, -10 * q) * sin((q - s) * (2 * pi) / p) + 1.0

    def in_out_elastic(p, sin=math.sin, pi=math.pi, pow=pow):
        p = .3 * 1.5
        s = p / 4.0
        q = p * 2
        if q == 2:
            return 1.0
        if q < 1:
            q -= 1.0
            return -.5 * (pow(2, 10 * q) * sin((q - s) * (2.0 * pi) / p))
        else:
            q -= 1.0
            return pow(2, -10 * q) * sin((q - s) * (2.0 * pi) / p) * .5 + 1.0

    def in_back(p):
        return p * p * ((1.70158 + 1.0) * p - 1.70158)

    def out_back(p):
        p = p - 1.0
        return p * p * ((1.70158 + 1) * p + 1.70158) + 1.0

    def in_out_back(p):
        p = p * 2.
        s = 1.70158 * 1.525
        if p < 1:
            return 0.5 * (p * p * ((s + 1.0) * p - s))
        p -= 2.0
        return 0.5 * (p * p * ((s + 1.0) * p + s) + 2.0)

    def _out_bounce_internal(t, d):
        p = t / d
        if p < (1.0 / 2.75):
            return 7.5625 * p * p
        elif p < (2.0 / 2.75):
            p -= (1.5 / 2.75)
            return 7.5625 * p * p + .75
        elif p < (2.5 / 2.75):
            p -= (2.25 / 2.75)
            return 7.5625 * p * p + .9375
        else:
            p -= (2.625 / 2.75)
            return 7.5625 * p * p + .984375

    def _in_bounce_internal(t, d, _out_bounce_internal=_out_bounce_internal):
        return 1.0 - _out_bounce_internal(d - t, d)

    def in_bounce(p, _in_bounce_internal=_in_bounce_internal):
        return _in_bounce_internal(p, 1.)

    def out_bounce(p, _out_bounce_internal=_out_bounce_internal):
        return _out_bounce_internal(p, 1.)

    def in_out_bounce(p, _in_bounce_internal=_in_bounce_internal, _out_bounce_internal=_out_bounce_internal):
        p = p * 2.
        if p < 1.:
            return _in_bounce_internal(p, 1.) * .5
        return _out_bounce_internal(p - 1., 1.) * .5 + .5


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
    __slots__ = ('_cur_time', '_events', '_events_to_be_added', )

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

    async def sleep(self, duration) -> Awaitable:
        '''
        Waits for a specified period of time.

        .. code-block::

            await clock.sleep(10)
        '''
        sig = ISignal()
        event = self.schedule_once(sig.set, duration)

        try:
            await sig.wait()
        except Cancelled:
            event.cancel()
            raise

    def move_on_after(self, timeout) -> AbstractAsyncContextManager[Task]:
        '''
        Returns an async context manager that applies a time limit to its code block,
        like :func:`trio.move_on_after` does.

        .. code-block::

            async with clock.move_on_after(10) as bg_task:
                ...

            if bg_task.finished:
                print("The code block was interrupted due to a timeout")
            else:
                print("The code block exited gracefully.")
        '''
        return wait_any_cm(self.sleep(timeout))

    async def anim_with_dt(self, *, step=0) -> AsyncIterator[TimeUnit]:
        '''
        An async form of :meth:`schedule_interval`.

        .. code-block::

            async for dt in clock.anim_with_dt(step=10):
                print(dt)
                if some_condition:
                    break

        The code above is quivalent to the code below.

        .. code-block::

            def callback(dt):
                print(dt)
                if some_condition:
                    return False

            clock.schedule_interval(callback, 10)

        **Restriction**

        You are not allowed to perform any kind of async operations during the loop.

        .. code-block::

            async for dt in clock.anim_with_dt():
                await awaitable  # NOT ALLOWED
                async with async_context_manager:  # NOT ALLOWED
                    ...
                async for __ in async_iterator:  # NOT ALLOWED
                    ...

        This is also true for other ``anim_with_xxx`` APIs.
        '''
        async with repeat_sleeping(self, step) as sleep:
            while True:
                yield await sleep()

    async def anim_with_et(self, *, step=0) -> AsyncIterator[TimeUnit]:
        '''
        Total elapsed time of iterations.

        .. code-block::

            timeout = ...
            async for et in clock.anim_with_et(...):
                ...
                if et > timeout:
                    break
        '''
        et = 0.
        async with repeat_sleeping(self, step) as sleep:
            while True:
                et += await sleep()
                yield et

    async def anim_with_dt_et(self, *, step=0) -> AsyncIterator[tuple[TimeUnit, TimeUnit]]:
        '''
        :meth:`anim_with_dt` and :meth:`anim_with_et` combined.

        .. code-block::

            async for dt, et in clock.anim_with_dt_et(...):
                ...
        '''
        et = 0.
        async with repeat_sleeping(self, step) as sleep:
            while True:
                dt = await sleep()
                et += dt
                yield dt, et

    async def anim_with_ratio(self, *, duration, step=0) -> AsyncIterator[float]:
        '''
        .. code-block::

            async for p in clock.anim_with_ratio(duration=...):
                print(p * 100, "%")
        '''
        if not duration:
            await self.sleep(step)
            yield 1.0
            return
        et = 0.
        async with repeat_sleeping(self, step) as sleep:
            while et < duration:
                et += await sleep()
                yield et / duration

    async def anim_with_dt_et_ratio(self, *, duration, step=0) -> AsyncIterator[tuple[TimeUnit, TimeUnit, float]]:
        '''
        :meth:`anim_with_dt`, :meth:`anim_with_et` and :meth:`anim_with_ratio` combined.

        .. code-block::

            async for dt, et, p in clock.anim_with_dt_et_ratio(...):
                ...
        '''
        async with repeat_sleeping(self, step) as sleep:
            if not duration:
                dt = await sleep()
                yield dt, dt, 1.0
                return
            et = 0.
            while et < duration:
                dt = await sleep()
                et += dt
                yield dt, et, et / duration

    async def interpolate_scalar(self, start, end, *, duration, step=0, transition=Transition.linear) -> AsyncIterator:
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
        async for p in self.anim_with_ratio(step=step, duration=duration):
            if p >= 1.0:
                break
            yield transition(p) * slope + start
        yield transition(1.) * slope + start

    async def interpolate_sequence(self, start, end, *, duration, step=0, transition=Transition.linear,
                                   output_type=tuple) -> AsyncIterator:
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

        async for p in self.anim_with_ratio(step=step, duration=duration):
            if p >= 1.0:
                break
            p = transition(p)
            yield output_type(p * slope_elem + start_elem for slope_elem, start_elem in zip_(slope, start))

        p = transition(1.)
        yield output_type(p * slope_elem + start_elem for slope_elem, start_elem in zip_(slope, start))

    async def run_in_thread(self, func, *, daemon=None, polling_interval) -> Awaitable:
        '''
        Creates a new thread, runs a function within it, then waits for the completion of that function.

        .. code-block::

            return_value = await clock.run_in_thread(func)
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
        async with repeat_sleeping(self, polling_interval) as sleep:
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
            return_value = await clock.run_in_executor(executor, func)
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
            async with repeat_sleeping(self, polling_interval) as sleep:
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
            self, obj, duration, step, transition, output_seq_type, animated_properties,
            getattr=getattr, isinstance=isinstance, tuple=tuple, str=str, partial=partial, native_seq_types=(tuple, list),
            zip=zip, Transition=Transition, _update=_update,
            _current_task=_current_task, _sleep_forever=_sleep_forever, /):
        if isinstance(transition, str):
            transition = getattr(Transition, transition)

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

    def anim_attrs(self, obj, *, duration, step=0, transition=Transition.linear, output_seq_type=tuple,
                   **animated_properties) -> Awaitable:
        '''
        Animates attibutes of any object.

        .. code-block::

            import types

            obj = types.SimpleNamespace(x=0, size=(200, 300))
            await clock.anim_attrs(obj, x=100, size=(400, 400))

        The ``output_seq_type`` parameter.

        .. code-block::

            obj = types.SimpleNamespace(size=(200, 300))
            await clock.anim_attrs(obj, size=(400, 400), output_seq_type=list)
            assert type(obj.size) is list
        '''
        return self._anim_attrs(obj, duration, step, transition, output_seq_type, animated_properties)

    def anim_attrs_abbr(self, obj, *, d, s=0, t=Transition.linear, output_seq_type=tuple,
                        **animated_properties) -> Awaitable:
        '''
        :meth:`anim_attrs` cannot animate attributes named ``step``, ``duration`` and ``transition`` but this one can.
        '''
        return self._anim_attrs(obj, d, s, t, output_seq_type, animated_properties)


class repeat_sleeping:
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
