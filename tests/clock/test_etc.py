import pytest

def test_sleep(clock):
    from asyncgui import start
    from asyncgui_ext.clock import sleep
    task_state = None

    async def async_fn():
        nonlocal task_state
        task_state = 'A'
        await sleep(clock, 10)
        task_state = 'B'
        await sleep(clock, 10)
        task_state = 'C'

    task = start(async_fn())
    assert task_state == 'A'
    clock.tick(10)
    assert task_state == 'B'
    clock.tick(10)
    assert task_state == 'C'
    assert task.finished


def test_move_on_after(clock):
    from asyncgui import start
    from asyncgui_ext.clock import move_on_after, sleep
    task_state = None

    async def async_fn():
        async with move_on_after(clock, 15) as bg_task:
            nonlocal task_state
            task_state = 'A'
            await sleep(clock, 10)
            task_state = 'B'
            await sleep(clock, 10)
            task_state = 'C'
        assert bg_task.finished

    task = start(async_fn())
    assert task_state == 'A'
    clock.tick(10)
    assert task_state == 'B'
    clock.tick(10)
    assert task_state == 'B'
    assert task.finished


def test_weakref(clock):
    from weakref import ref
    ref(clock)


@pytest.mark.parametrize("n", range(3))
def test_n_frames(clock, n):
    from asyncgui import start
    from asyncgui_ext.clock import n_frames

    task = start(n_frames(clock, n))
    for __ in range(n):
        assert not task.finished
        clock.tick(0)
    assert task.finished
