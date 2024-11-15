import requests
import os
import dotenv
from multiprocessing import Process


def test_weather(base_server: Process) -> None:
    """weather endpoint test

    REQUIREMENTS:
        - weather endpoint should return equivalent json to raw api call to
            OpenWeather onecall.
    """
    dotenv.load_dotenv()
    lat = 40.688662
    lon = -73.9630079
    loc = "New York"
    breakpoint()
    raw_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units=metric&exclude=minutely,hourly,alerts&appid={os.environ['OW_KEY']}"
    raw_resp = requests.get(raw_url, timeout=5)
    server_resp = requests.get(f"http://127.0.0.1:8080/weather?loc={loc}", timeout=5)
    print(server_resp.json())
