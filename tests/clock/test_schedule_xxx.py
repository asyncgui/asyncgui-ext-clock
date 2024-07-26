def test_interval(clock):
    dt_list = []

    clock.schedule_interval(dt_list.append, 100)
    assert dt_list == []
    clock.tick(50)
    assert dt_list == []
    clock.tick(50)
    assert dt_list == [100, ]
    clock.tick(50)
    assert dt_list == [100, ]
    clock.tick(100)
    assert dt_list == [100, 150, ]
    clock.tick(100)
    assert dt_list == [100, 150, 100]


def test_interval_zero_interval(clock):
    dt_list = []

    clock.schedule_interval(dt_list.append, 0)
    assert dt_list == []
    clock.tick(0)
    assert dt_list == [0, ]
    clock.tick(20)
    assert dt_list == [0, 20, ]
    clock.tick(0)
    assert dt_list == [0, 20, 0, ]


def test_interval_cancel(clock):
    dt_list = []
    func = dt_list.append

    e = clock.schedule_interval(func, 100)
    assert dt_list == []
    clock.tick(100)
    assert dt_list == [100, ]
    e.cancel()
    clock.tick(100)
    assert dt_list == [100, ]


def test_interval_cancel_from_a_callback(clock):
    dt_list = []

    def func(dt):
        dt_list.append(dt)
        if dt > 80:
            e.cancel()

    e = clock.schedule_interval(func, 30)
    clock.schedule_interval(dt_list.append, 30)
    clock.tick(30)
    assert dt_list == [30, 30, ]
    clock.tick(60)
    assert dt_list == [30, 30, 60, 60, ]
    clock.tick(90)
    assert dt_list == [30, 30, 60, 60, 90, 90, ]
    clock.tick(120)
    assert dt_list == [30, 30, 60, 60, 90, 90, 120, ]


def test_interval_schedule_from_a_callback(clock):
    dt_list = []

    def func(dt):
        dt_list.append(dt)
        clock.schedule_interval(dt_list.append, 10)

    clock.schedule_interval(func, 10)
    assert dt_list == []
    clock.tick(10)
    assert dt_list == [10, ]
    clock.tick(20)
    assert dt_list == [10, 20, 20, ]
    clock.tick(30)
    assert dt_list == [10, 20, 20, 30, 30, 30, ]


def test_interval_context_manager(clock):
    dt_list = []
    func = dt_list.append

    with clock.schedule_interval(func, 10) as e:
        clock.tick(10)
        assert dt_list == [10, ]
        clock.tick(10)
        assert dt_list == [10, 10, ]
    clock.tick(100)
    assert dt_list == [10, 10, ]
