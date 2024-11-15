import requests
import os
import dotenv
from multiprocessing import Process


def test_weather(base_server: Process) -> None:
    """weather endpoint test

    REQUIREMENTS:
        - coordinate data should match known
        - server should forward Open Weather API as "forecast"
        - server should forward location as "location"
    """
    dotenv.load_dotenv()
    lat = 42.3554334
    lon = -71.060511
    loc = "Boston"
    weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units=metric&exclude=minutely,hourly,alerts&appid={os.environ['OW_KEY']}"
    weather_resp = requests.get(weather_url, timeout=5)
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={loc},US&appid={os.environ['OW_KEY']}"
    geo_resp = requests.get(geo_url, timeout=5)
    server_resp = requests.get(f"http://127.0.0.1:8080/weather?loc={loc}", timeout=5)

    server_json = server_resp.json()

    assert list(server_json.keys()) == ["forecast", "location"]
    assert server_json["forecast"] == weather_resp.json()
    assert server_json["location"]["lat"] == geo_resp.json()[0]["lat"]
    assert server_json["location"]["lon"] == geo_resp.json()[0]["lon"]