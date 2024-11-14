from flask import Flask, jsonify
from flask_cors import CORS
import dotenv
from typing import Dict, Union, Tuple, List
import re
import requests
import os
from dataclasses import dataclass
import datetime


@dataclass
class Current:
    temp_c: float
    temp_f: float
    humidity: float
    wind_speed: float
    humidity: float
    wind_speed: float
    description: str
    icon: str


@dataclass
class Forecast:
    date: str
    high_f: float
    high_c: float
    low_f: float
    low_c: float
    description: str
    icon: str


def get_coordinates(loc: str) -> Dict[str, Union[str, int]]:
    """use the geoloc api from OpenWeather to get coordinates from user input

    :param loc: zip or city name
    """
    is_zip = re.match(r"\d{5}", loc)

    if is_zip:
        location_resp = requests.get(
            f"{os.environ['OW_GEO_URL']}zip?zip={loc}&appid={os.environ['OW_KEY']}",
            timeout=5,
        )
        loc_json = location_resp.json()
        state = "N/A"
    else:
        # TODO: add logic to handle multiple locations returned from direct
        location_resp = requests.get(
            f"{os.environ['OW_GEO_URL']}direct?q={loc}&appid={os.environ['OW_KEY']}"
        )
        loc_json = location_resp.json()[0]
        state = loc_json["state"]
    # TODO: add error handling for GEO call here

    return {
        "name": loc_json["name"],
        "country": loc_json["country"],
        "state": state,
        "lon": loc_json["lon"],
        "lat": loc_json["lat"],
    }


def get_forecast(lat: float, lon: float) -> Tuple[Current, List[Forecast]]:
    """get a 5 day forcast from the OpenWeather api

    :param lat: latitude
    :param lon: longitude
    """
    forecast = requests.get(
        f"{os.environ['OW_FORECAST_URL']}lat={lat}&lon={lon}&units=metric&exclude=minutely,hourly,alerts&appid={os.environ['OW_KEY']}"
    )

    current_ctx = forecast.json()["current"]
    daily_ctx = forecast.json()["daily"][1:6]

    current = Current(
        temp_c=round(current_ctx["temp"], 2),
        temp_f=round(1.8 * current_ctx["temp"] + 32, 2),
        humidity=round(current_ctx["humidity"], 2),
        wind_speed=round(current_ctx["wind_speed"], 2),
        description=current_ctx["weather"][0]["main"],
        icon=current_ctx["weather"][0]["icon"]
    )

    daily = []
    for day in daily_ctx:
        dt = datetime.datetime.fromtimestamp(day["dt"])
        daily.append(
            Forecast(
                high_c=round(day["temp"]["max"], 2),
                low_c=round(day["temp"]["min"], 2),
                high_f=round(1.8 * day["temp"]["max"] + 32, 2),
                low_f=round(1.8 * day["temp"]["min"] + 32, 2),
                date=f"{dt.day}, {dt.month}, {dt.year}",
                description=day["weather"][0]["main"],
                icon=day["weather"][0]["icon"]
            )
        )

    return (current, daily)


def main() -> None:
    """instantiate server"""

    dotenv.load_dotenv()

    server = Flask(__name__)
    cors = CORS(server, origins="*")

    # temp home url for testing (TODO: REMOVE)
    @server.route("/api", methods=["GET"])
    def home() -> Dict[str, str]:
        """testing func"""
        return jsonify({"hello": "world"})

    # TODO: add routing functions
    @server.route("/weather/<string:loc>")
    def get_weather(loc: str) -> Dict[str, Union[str, int]]:
        """this function basically will do everything for this backend

        :param loc: either city/town name or zip code
        """
        coord_data = get_coordinates(loc)

        current, daily = get_forecast(coord_data["lat"], coord_data["lon"])

        return jsonify(
            {
                "name": coord_data["name"],
                "state": coord_data["state"],
                "country": coord_data["country"],
                "current": current,
                "daily": daily,
            }
        )

    server.run(debug=True, port=8080)


if __name__ == "__main__":
    main()
