import types
from typing import TypeAlias, TypeVar
from collections.abc import Callable, Awaitable, AsyncIterator
from dataclasses import dataclass
from contextlib import AbstractAsyncContextManager
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

from asyncgui import ISignal, Cancelled, Task, wait_any_cm, _sleep_forever, _current_task

TimeUnit = TypeVar("TimeUnit")
TimerCallback: TypeAlias = Callable[[TimeUnit], None]


@dataclass(slots=True)
class TimerEvent:
    _deadline: TimeUnit
    _last_tick: TimeUnit
    callback: TimerCallback
    '''
    The callback function registered using the ``Timer.schedule_xxx()`` call that returned this instance.
    You can replace it with another one by simply assigning to this attribute.

    .. code-block::

        event = timer.schedule_xxx(...)
        event.callback = another_function
    '''

    _interval: TimeUnit | None
    _cancelled: bool = False

    def cancel(self):
        self._cancelled = True


class Timer:
    '''
    The Timer class allows you to schedule a function call in the future; once or repeatedly at specified intervals.
    You can get the time elapsed between the scheduling and the calling of the callback via the ``dt`` argument:

    .. code-block::

        # 'dt' means delta-time
        def my_callback(dt):
            pass

        timer = Timer()

        # call my_callback every 100 time units
        timer.schedule_interval(my_callback, 100)

        # call my_callback in 100 time unit
        timer.schedule_once(my_callback, 100)

        # call my_callback in the next 'timer.progress()' call
        timer.schedule_once(my_callback, 0)

    To unschedule:

    .. code-block::

        event = timer.schedule_xxx(...)
        event.cancel()
    '''
    __slots__ = ('_cur_time', '_events', '_events_to_be_added', )

    def __init__(self):
        self._cur_time = 0
        self._events: list[TimerEvent] = []
        self._events_to_be_added: list[TimerEvent] = []  # double buffering

    @property
    def current_time(self) -> TimeUnit:
        return self._cur_time

    def progress(self, delta_time):
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

    def schedule_once(self, func, delay=0) -> TimerEvent:
        '''
        Schedules the ``func`` to be called in 'delay' time units.

        :param delay: If 0, the ``func`` will be called in the next :meth:`progress` call.
        '''
        cur_time = self._cur_time
        event = TimerEvent(cur_time + delay, cur_time, func, None)
        self._events_to_be_added.append(event)
        return event

    def schedule_interval(self, func, interval) -> TimerEvent:
        '''
        Schedules the ``func`` to be called every 'delay' time units.

        :param interval: If 0, the ``func`` will be called every :meth:`progress` call.
        '''
        cur_time = self._cur_time
        event = TimerEvent(cur_time + interval, cur_time, func, interval)
        self._events_to_be_added.append(event)
        return event

    async def sleep(self, duration) -> Awaitable:
        '''
        Waits for a specified period of time.

        .. code-block::

            await timer.sleep(10)
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

            async with timer.move_on_after(10) as bg_task:
                ...

            if bg_task.finished:
                print("The code block was interrupted due to a timeout")
            else:
                print("The code block exited gracefully.")
        '''
        return wait_any_cm(self.sleep(timeout))

    async def anim_with_dt(self, *, step=0) -> AsyncIterator[TimeUnit]:
        '''
        Repeats sleeping at specified intervals.

        .. code-block::

            async for dt in timer.anim_with_dt(step=1000):
                print(dt)

        **Restriction**

        You are not allowed to perform any kind of async operations during the loop.

        .. code-block::

            async for dt in anim_with_dt():
                await awaitable  # NOT ALLOWED
                async with async_context_manager:  # NOT ALLOWED
                    ...
                async for __ in async_iterator:  # NOT ALLOWED
                    ...
        '''
        async with repeat_sleeping(self, step) as sleep:
            while True:
                yield await sleep()


    async def anim_with_et(self, *, step=0) -> AsyncIterator[TimeUnit]:
        et = 0.
        async with repeat_sleeping(self, step) as sleep:
            while True:
                et += await sleep()
                yield et


    async def anim_with_dt_et(self, *, step=0) -> AsyncIterator[tuple[TimeUnit, TimeUnit]]:
        et = 0.
        async with repeat_sleeping(self, step) as sleep:
            while True:
                dt = await sleep()
                et += dt
                yield dt, et


    async def anim_with_ratio(self, *, duration, step=0) -> AsyncIterator[float]:
        et = 0.
        async with repeat_sleeping(self, step) as sleep:
            while et < duration:
                et += await sleep()
                yield et / duration


    async def anim_with_dt_et_ratio(self, *, duration, step=0) -> AsyncIterator[tuple[TimeUnit, TimeUnit, float]]:
        et = 0.
        async with repeat_sleeping(self, step) as sleep:
            while et < duration:
                dt = await sleep()
                et += dt
                yield dt, et, et / duration

    async def run_in_thread(self, func, *, daemon=None, polling_interval) -> Awaitable:
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
            async with repeat_sleeping(polling_interval) as sleep:
                while not done:
                    await sleep()
        except Cancelled:
            future.cancel()
            raise
        if exception is not None:
            raise exception
        return return_value


class repeat_sleeping:
    '''
    :meta private:
    '''
    __slots__ = ('_timer', '_interval', '_event', )

    def __init__(self, timer: Timer, interval):
        self._timer = timer
        self._interval = interval

    @staticmethod
    @types.coroutine
    def _sleep(_f=_sleep_forever):
        return (yield _f)[0][0]

    @types.coroutine
    def __aenter__(self) -> Awaitable[Callable[[], Awaitable[TimeUnit]]]:
        task = (yield _current_task)[0][0]
        self._event = self._timer.schedule_interval(task._step, self._interval)
        return self._sleep

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._event.cancel()
