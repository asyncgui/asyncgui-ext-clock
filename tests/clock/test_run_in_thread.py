import pytest
import threading
import time


@pytest.mark.parametrize('daemon', (True, False))
def test_thread_id(clock, daemon):
    from asyncgui import start

    async def job():
        before = threading.get_ident()
        await clock.run_in_thread(lambda: None, daemon=daemon, polling_interval=0)
        after = threading.get_ident()
        assert before == after

    task = start(job())
    time.sleep(.01)
    clock.tick(0)
    assert task.finished


@pytest.mark.parametrize('daemon', (True, False))
def test_propagate_exception(clock, daemon):
    from asyncgui import start

    async def job():
        with pytest.raises(ZeroDivisionError):
            await clock.run_in_thread(lambda: 1 / 0, daemon=daemon, polling_interval=0)

    task = start(job())
    time.sleep(.01)
    clock.tick(0)
    assert task.finished


@pytest.mark.parametrize('daemon', (True, False))
def test_no_exception(clock, daemon):
    from asyncgui import start

    async def job():
        assert 'A' == await clock.run_in_thread(lambda: 'A', daemon=daemon, polling_interval=0)

    task = start(job())
    time.sleep(.01)
    clock.tick(0)
    assert task.finished
