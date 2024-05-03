import pytest
from concurrent.futures import ThreadPoolExecutor
import threading


def test_thread_id(clock):
    from asyncgui import start
    from asyncgui_ext.clock import run_in_executor

    async def job():
        before = threading.get_ident()
        await run_in_executor(clock, executor, lambda: None, polling_interval=0)
        after = threading.get_ident()
        assert before == after

    with ThreadPoolExecutor() as executor:
        task = start(job())
    clock.tick(0)
    assert task.finished


def test_propagate_exception(clock):
    from asyncgui import start
    from asyncgui_ext.clock import run_in_executor

    async def job():
        with pytest.raises(ZeroDivisionError):
            await run_in_executor(clock, executor, lambda: 1 / 0, polling_interval=0)

    with ThreadPoolExecutor() as executor:
        task = start(job())
    clock.tick(0)
    assert task.finished


def test_no_exception(clock):
    from asyncgui import start
    from asyncgui_ext.clock import run_in_executor

    async def job():
        assert 'A' == await run_in_executor(clock, executor, lambda: 'A', polling_interval=0)

    with ThreadPoolExecutor() as executor:
        task = start(job())
    clock.tick(0)
    assert task.finished


def test_cancel_before_getting_excuted(clock):
    import time
    from asyncgui import Event, start
    from asyncgui_ext.clock import run_in_executor

    flag = Event()

    async def job():
        await run_in_executor(clock, executor, flag.set, polling_interval=0)

    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(time.sleep, .1)
        task = start(job())
        time.sleep(.02)
        assert not task.finished
        assert not flag.is_set
        clock.tick(0)
        task.cancel()
        assert task.cancelled
        assert not flag.is_set
        time.sleep(.2)
        assert not flag.is_set
