import time
from multiprocessing import Process
from typing import Iterator, Union

import pytest

from weather_back.__server__ import create_server


def pytest_configure() -> None:
    pytest.gloucester = {
        "query": "Gloucester,MA",
        "lat": 42.6208,
        "lon": -70.6721,
        "z_code": "01930",
    }


@pytest.fixture
def base_server() -> Iterator[Union[Process, str]]:
    """launch server before testing"""
    server = create_server({"TESTING": True})
    server_process = Process(
        target=server.run, kwargs={"debug": False, "port": 8080}
    )
    server_process.start()
    time.sleep(0.5)
    yield server_process
    server_process.terminate()
    time.sleep(0.5)
