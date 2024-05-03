def test_anim_with_dt(clock):
    from asyncgui import start
    from asyncgui_ext.clock import anim_with_dt
    dt_list = []

    async def async_fn():
        async for dt in anim_with_dt(clock, step=10):
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
    from asyncgui_ext.clock import anim_with_et
    et_list = []

    async def async_fn():
        async for et in anim_with_et(clock, step=10):
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
    from asyncgui_ext.clock import anim_with_ratio
    p_list = []

    async def async_fn():
        async for p in anim_with_ratio(clock, step=10, duration=100):
            p_list.append(p)

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


def test_anim_with_ratio_zero_duration(clock):
    from asyncgui import start
    from asyncgui_ext.clock import anim_with_ratio
    p_list = []

    async def async_fn():
        async for p in anim_with_ratio(clock, step=10, duration=0):
            p_list.append(p)

    task = start(async_fn())
    assert p_list == []
    clock.tick(6)
    assert p_list == []
    clock.tick(6)
    assert p_list == [1.0, ]
    assert task.finished


def test_anim_with_dt_et(clock):
    from asyncgui import start
    from asyncgui_ext.clock import anim_with_dt_et
    values = []

    async def async_fn():
        async for v in anim_with_dt_et(clock, step=10):
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
    from asyncgui_ext.clock import anim_with_dt_et_ratio
    values = []

    async def async_fn():
        async for v in anim_with_dt_et_ratio(clock, step=10, duration=100):
            values.extend(v)

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


def test_anim_with_dt_et_ratio_zero_duration(clock):
    from asyncgui import start
    from asyncgui_ext.clock import anim_with_dt_et_ratio
    values = []

    async def async_fn():
        async for v in anim_with_dt_et_ratio(clock, step=10, duration=0):
            values.extend(v)

    task = start(async_fn())
    assert values == []
    clock.tick(6)
    assert values == []
    clock.tick(6)
    assert values == [12, 12, 1.0]
    assert task.finished
