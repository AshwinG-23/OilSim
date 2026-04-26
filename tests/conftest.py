import simpy
import pytest


@pytest.fixture
def env():
    return simpy.Environment()
