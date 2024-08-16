import pytest


def test_anim_with_dt(clock):
    from asyncgui import start
    dt_list = []

    async def async_fn():
        async for dt in clock.anim_with_dt(step=10):
            dt_list.append(dt)

    task = start(async_fn())
    assert dt_list == []
    clock.tick(10)
    assert dt_list == [10]
    clock.tick(20)
    assert dt_list == [10, 20]
    clock.tick(5)
    assert dt_list == [10, 20, 5]
    clock.tick(5)
    assert dt_list == [10, 20, 5, 5]
    clock.tick(5)
    assert dt_list == [10, 20, 5, 5]
    task.cancel()


def test_anim_with_et(clock):
    from asyncgui import start
    et_list = []

    async def async_fn():
        async for et in clock.anim_with_et(step=10):
            et_list.append(et)

    task = start(async_fn())
    assert et_list == []
    clock.tick(10)
    assert et_list == [10]
    clock.tick(20)
    assert et_list == [10, 30]
    clock.tick(5)
    assert et_list == [10, 30, 35]
    clock.tick(5)
    assert et_list == [10, 30, 35, 40]
    clock.tick(5)
    assert et_list == [10, 30, 35, 40]
    task.cancel()


def test_anim_with_ratio(clock):
    from pytest import approx
    from asyncgui import start
    p_list = []

    async def async_fn():
        async for p in clock.anim_with_ratio(step=10, base=100):
            p_list.append(p)
            if p >= 1:
                break

    task = start(async_fn())
    assert p_list == []
    clock.tick(10)
    assert p_list == approx([0.1])
    clock.tick(20)
    assert p_list == approx([0.1, 0.3])
    clock.tick(5)
    assert p_list == approx([0.1, 0.3, 0.35, ])
    clock.tick(5)
    assert p_list == approx([0.1, 0.3, 0.35, 0.4, ])
    clock.tick(5)
    assert p_list == approx([0.1, 0.3, 0.35, 0.4, ])
    clock.tick(105)
    assert p_list == approx([0.1, 0.3, 0.35, 0.4, 1.5])
    assert task.finished


def test_anim_with_ratio_zero_base(clock):
    from asyncgui import start
    p_list = []

    async def async_fn():
        async for p in clock.anim_with_ratio(step=10, base=0):
            p_list.append(p)

    task = start(async_fn())
    assert p_list == []
    clock.tick(6)
    assert p_list == []
    with pytest.raises(ZeroDivisionError):
        clock.tick(6)
    assert p_list == []
    assert task.cancelled


def test_anim_with_dt_et(clock):
    from asyncgui import start
    values = []

    async def async_fn():
        async for v in clock.anim_with_dt_et(step=10):
            values.extend(v)

    task = start(async_fn())
    assert values == []
    clock.tick(10)
    assert values == [10, 10] ; values.clear()
    clock.tick(20)
    assert values == [20, 30] ; values.clear()
    clock.tick(5)
    assert values == [5, 35] ; values.clear()
    clock.tick(5)
    assert values == [5, 40] ; values.clear()
    clock.tick(5)
    assert values == []
    assert not task.finished
    task.cancel()


def test_anim_with_dt_et_ratio(clock):
    from pytest import approx
    from asyncgui import start
    values = []

    async def async_fn():
        async for v in clock.anim_with_dt_et_ratio(step=10, base=100):
            values.extend(v)
            if values[2] >= 1:
                break

    task = start(async_fn())
    assert values == []
    clock.tick(10)
    assert values[:2] == [10, 10]
    assert values[2] == approx(0.1)
    values.clear()
    clock.tick(20)
    assert values[:2] == [20, 30]
    assert values[2] == approx(0.3)
    values.clear()
    clock.tick(5)
    assert values[:2] == [5, 35]
    assert values[2] == approx(0.35)
    values.clear()
    clock.tick(5)
    assert values[:2] == [5, 40]
    assert values[2] == approx(0.4)
    values.clear()
    clock.tick(5)
    assert values == []
    clock.tick(105)
    assert values[:2] == [110, 150]
    assert values[2] == approx(1.5)
    assert task.finished


def test_anim_with_dt_et_ratio_zero_base(clock):
    from asyncgui import start
    values = []

    async def async_fn():
        async for v in clock.anim_with_dt_et_ratio(step=10, base=0):
            values.extend(v)

    task = start(async_fn())
    assert values == []
    clock.tick(6)
    assert values == []
    with pytest.raises(ZeroDivisionError):
        clock.tick(6)
    assert values == []
    assert task.cancelled
