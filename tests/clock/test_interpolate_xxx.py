import pytest


def test_interpolate_scalar(clock):
    from asyncgui import start
    values = []

    async def async_fn():
        async for v in clock.interpolate_scalar(100, 0, duration=100):
            values.append(int(v))

    task = start(async_fn())
    assert values == [100, ]
    clock.advance(30)
    assert values == [100, 70]
    clock.advance(20)
    assert values == [100, 70, 50, ]
    clock.advance(40)
    assert values == [100, 70, 50, 10, ]
    clock.advance(40)
    assert values == [100, 70, 50, 10, 0, ]
    assert task.finished


@pytest.mark.parametrize('step', [0, 10])
def test_interpolate_scalar_zero_duration(clock, step):
    from asyncgui import start
    values = []

    async def async_fn():
        async for v in clock.interpolate_scalar(100, 0, duration=0, step=step):
            values.append(int(v))

    task = start(async_fn())
    assert values == [100, ]
    clock.advance(step)
    assert values == [100, 0]
    assert task.finished


def test_interpolate_sequence(clock):
    from asyncgui import start
    values = []

    async def async_fn():
        async for v1, v2 in clock.interpolate_sequence([0, 100], [100, 0], duration=100):
            values.append(int(v1))
            values.append(int(v2))

    task = start(async_fn())
    assert values == [0, 100] ; values.clear()
    clock.advance(30)
    assert values == [30, 70] ; values.clear()
    clock.advance(30)
    assert values == [60, 40] ; values.clear()
    clock.advance(30)
    assert values == [90, 10] ; values.clear()
    clock.advance(30)
    assert values == [100, 0] ; values.clear()
    assert task.finished


@pytest.mark.parametrize('step', [0, 10])
def test_interpolate_sequence_zero_duration(clock, step):
    from asyncgui import start
    values = []

    async def async_fn():
        async for v1, v2 in clock.interpolate_sequence([0, 100], [100, 0], duration=0, step=step):
            values.append(int(v1))
            values.append(int(v2))

    task = start(async_fn())
    assert values == [0, 100] ; values.clear()
    clock.advance(step)
    assert values == [100, 0] ; values.clear()
    assert task.finished
