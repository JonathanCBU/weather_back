from flask import Flask, jsonify, request
from flask_cors import CORS
import dotenv
from typing import Dict, Union, Any
import re
import requests
import os
import argparse


def get_args() -> argparse.Namespace:
    """command line args"""

    parser = argparse.ArgumentParser(
        description=("Command line args for starting the flask server")
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug mode when running the app",
    )
    parser.add_argument("--port", help="port to run server on", default=8080)
    args = parser.parse_args()
    return args


def get_coordinates(loc: str) -> Dict[str, Union[str, int]]:
    """use the geoloc api from OpenWeather to get coordinates from user input

    :param loc: zip or city name
    """
    is_zip = re.match(r"\d{5}", loc)

    if is_zip:
        location_resp = requests.get(
            f"http://api.openweathermap.org/geo/1.0/zip?zip={loc}&appid={os.environ['OW_KEY']}",
            timeout=5,
        )
        loc_json = location_resp.json()
    else:
        # TODO: add logic to handle multiple locations returned from direct
        location_resp = requests.get(
            f"http://api.openweathermap.org/geo/1.0/direct?q={loc}&appid={os.environ['OW_KEY']}",
            timeout=5,
        )
        loc_json = location_resp.json()[0]
    # TODO: add error handling for GEO call here

    return loc_json


def get_reverse_geoloc(lat: float, lon: float) -> Dict[str, Any]:
    """get location info from coordinates

    :param lat: latitude
    :param lon: longitude
    """
    location_resp = requests.get(
        f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={os.environ['OW_KEY']}",
        timeout=5,
    )
    return location_resp.json()[0]


def get_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """get a 5 day forcast from the OpenWeather api

    :param lat: latitude
    :param lon: longitude
    """
    forecast = requests.get(
        f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units=metric&exclude=minutely,hourly,alerts&appid={os.environ['OW_KEY']}",
        timeout=5,
    )
    return forecast.json()


def main() -> None:
    """instantiate server"""

    dotenv.load_dotenv()

    args = get_args()

    server = Flask(__name__)
    _ = CORS(server, origins="*")

    @server.route("/weather/<string:loc>")
    def get_weather(loc: str) -> Dict[str, Union[str, Any]]:
        """this function basically will do everything for this backend

        :param loc: either city/town name or zip code
        """
        coord_data = get_coordinates(loc)

        forecast = get_forecast(coord_data["lat"], coord_data["lon"])
        return jsonify({"location": coord_data, "forecast": forecast})

    @server.route("/coordinates")
    def get_weather_with_coords() -> Dict[str, Union[str, Any]]:
        """get weather with coords directly input"""

        lat = request.args.get("lat")
        lon = request.args.get("lon")

        # TODO: error handling for None return of lat and lon
        coord_data = get_reverse_geoloc(lat, lon)
        forecast = get_forecast(lat, lon)
        return jsonify({"location": coord_data, "forecast": forecast})

    server.run(debug=args.debug, port=args.port)


if __name__ == "__main__":
    main()
