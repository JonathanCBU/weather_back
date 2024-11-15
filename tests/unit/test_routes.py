import os
from multiprocessing import Process

import dotenv
import pytest
import requests


def test_weather(base_server: Process) -> None:
    """weather endpoint test

    REQUIREMENTS:
        - coordinate data should match known
        - server should forward Open Weather API as "forecast"
        - server should forward location as "location"
    """
    dotenv.load_dotenv()
    weather_url = (
        "https://api.openweathermap.org/data/3.0/onecall?"
        + f"lat={pytest.gloucester['lat']}&lon={pytest.gloucester['lon']}&"
        + "units=metric&exclude=minutely,hourly,alerts&"
        + f"appid={os.environ['OW_KEY']}"
    )
    weather_resp = requests.get(weather_url, timeout=5)
    geo_url = (
        "http://api.openweathermap.org/geo/1.0/direct?"
        + f"q={pytest.gloucester['query']},US&appid={os.environ['OW_KEY']}"
    )
    geo_resp = requests.get(geo_url, timeout=5)
    server_resp = requests.get(
        f"http://127.0.0.1:8080/weather?loc={pytest.gloucester['query']}",
        timeout=5,
    )

    server_json = server_resp.json()

    assert list(server_json.keys()) == ["forecast", "location"]
    assert (
        server_json["forecast"]["current"]["weather"]
        == weather_resp.json()["current"]["weather"]
    )
    assert server_json["location"]["lat"] == geo_resp.json()[0]["lat"]
    assert server_json["location"]["lon"] == geo_resp.json()[0]["lon"]


def test_coordinates(base_server: Process) -> None:
    """coordinates endpoint test

    REQUIREMENTS:
        - coordinates should return normal location data from coordinates
    """
    dotenv.load_dotenv()

    reverse_geo_url = (
        "http://api.openweathermap.org/geo/1.0/reverse?"
        + f"lat={pytest.gloucester['lat']}&lon={pytest.gloucester['lon']}&"
        + f"limit=1&appid={os.environ['OW_KEY']}"
    )
    reverse_geo_resp = requests.get(reverse_geo_url, timeout=5)

    coord_resp = requests.get(
        f"http://127.0.0.1:8080/coordinates?lat={pytest.gloucester['lat']}&"
        + f"lon={pytest.gloucester['lon']}",
        timeout=5,
    )
    assert coord_resp.json()["location"] == reverse_geo_resp.json()[0]
