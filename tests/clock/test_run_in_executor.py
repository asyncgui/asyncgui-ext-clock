import pytest
from concurrent.futures import ThreadPoolExecutor
import threading


def test_thread_id(clock):
    from asyncgui import start

    async def job():
        before = threading.get_ident()
        await clock.run_in_executor(executor, lambda: None, polling_interval=0)
        after = threading.get_ident()
        assert before == after

    with ThreadPoolExecutor() as executor:
        task = start(job())
    clock.tick(0)
    assert task.finished


def test_propagate_exception(clock):
    from asyncgui import start

    async def job():
        with pytest.raises(ZeroDivisionError):
            await clock.run_in_executor(executor, lambda: 1 / 0, polling_interval=0)

    with ThreadPoolExecutor() as executor:
        task = start(job())
    clock.tick(0)
    assert task.finished


def test_no_exception(clock):
    from asyncgui import start

    async def job():
        assert 'A' == await clock.run_in_executor(executor, lambda: 'A', polling_interval=0)

    with ThreadPoolExecutor() as executor:
        task = start(job())
    clock.tick(0)
    assert task.finished


def test_cancel_before_getting_excuted(clock):
    import time
    from asyncgui import Box, start

    box = Box()

    async def job():
        await clock.run_in_executor(executor, box.put, polling_interval=0)

    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(time.sleep, .1)
        task = start(job())
        time.sleep(.02)
        assert not task.finished
        assert box.is_empty
        clock.tick(0)
        task.cancel()
        assert task.cancelled
        assert box.is_empty
        time.sleep(.2)
        assert box.is_empty
