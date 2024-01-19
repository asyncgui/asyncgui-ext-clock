def test_sleep(clock):
    from asyncgui import start
    task_state = None

    async def async_fn():
        nonlocal task_state
        task_state = 'A'
        await clock.sleep(10)
        task_state = 'B'
        await clock.sleep(10)
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
    task_state = None

    async def async_fn():
        async with clock.move_on_after(15) as bg_task:
            nonlocal task_state
            task_state = 'A'
            await clock.sleep(10)
            task_state = 'B'
            await clock.sleep(10)
            task_state = 'C'
        assert bg_task.finished

    task = start(async_fn())
    assert task_state == 'A'
    clock.tick(10)
    assert task_state == 'B'
    clock.tick(10)
    assert task_state == 'B'
    assert task.finished
