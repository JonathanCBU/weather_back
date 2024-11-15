import pytest

from multiprocessing import Process

from typing import Iterator, Dict, List, Union
import time
from weather_back.__server__ import create_server


@pytest.fixture
def base_server() -> Iterator[Union[Process, str]]:
    """launch server before testing"""
    server = create_server()
    server_process = Process(target=server.run, kwargs={"debug": False})
    server_process.start()
    time.sleep(0.5)
    yield server_process
    server_process.terminate()
    time.sleep(0.5)
