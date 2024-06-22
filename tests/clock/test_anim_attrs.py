import pytest


def test_scalar(clock):
    from types import SimpleNamespace
    import asyncgui

    obj = SimpleNamespace(num=0)
    task = asyncgui.start(clock.anim_attrs(obj, num=20, duration=100))

    assert int(obj.num) == 0
    clock.tick(30)
    assert int(obj.num) == 6
    clock.tick(30)
    assert int(obj.num) == 12
    clock.tick(30)
    assert int(obj.num) == 18
    clock.tick(30)
    assert int(obj.num) == 20
    assert task.finished


def test_sequence(clock):
    from types import SimpleNamespace
    from pytest import approx
    import asyncgui

    obj = SimpleNamespace(pos=[0, 100])
    task = asyncgui.start(clock.anim_attrs(obj, pos=[100, 0], duration=100))

    assert obj.pos == approx([0, 100])
    clock.tick(30)
    assert obj.pos == approx([30, 70])
    clock.tick(30)
    assert obj.pos == approx([60, 40])
    clock.tick(30)
    assert obj.pos == approx([90, 10])
    clock.tick(30)
    assert obj.pos == approx([100, 0])
    assert task.finished


@pytest.mark.parametrize('output_seq_type', [list, tuple])
def test_seq_type_parameter(clock, output_seq_type):
    from types import SimpleNamespace
    import asyncgui

    obj = SimpleNamespace(size=(0, 0), pos=[0, 0])
    task = asyncgui.start(clock.anim_attrs(obj, size=[10, 10], pos=(10, 10), duration=10, output_seq_type=output_seq_type))
    clock.tick(0)
    assert type(obj.size) is output_seq_type
    assert type(obj.pos) is output_seq_type
    assert not task.finished
    task.cancel()
