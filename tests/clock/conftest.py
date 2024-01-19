import pytest


@pytest.fixture()
def clock():
    from asyncgui_ext.clock import Clock
    return Clock()
