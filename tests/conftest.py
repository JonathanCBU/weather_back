import time
from multiprocessing import Process
from typing import Dict, Iterator, List, Union

import pytest

from weather_back.__server__ import create_server


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
