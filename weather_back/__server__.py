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

    if not is_zip:
        # TODO: add logic to handle multiple locations returned from direct
        print(loc)
        loc = loc.replace(" ", "")
        if "," in loc:
            loc = loc + ",US"
        print(loc)
        location_resp = requests.get(
            f"http://api.openweathermap.org/geo/1.0/direct?q={loc}&appid={os.environ['OW_KEY']}",
            timeout=5,
        )
        print(location_resp.json())
        loc_json = location_resp.json()[0]
    else:
        location_resp = requests.get(
            f"http://api.openweathermap.org/geo/1.0/zip?zip={loc}&appid={os.environ['OW_KEY']}",
            timeout=5,
        )
        loc_json = location_resp.json()
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


def create_server() -> Flask:
    """create server object (only here to make pytest simpler)"""

    server = Flask(__name__)

    # origins * is risky, would not do in prod
    _ = CORS(server, origins="*")

    return server


def main() -> None:
    """instantiate server"""

    dotenv.load_dotenv()

    args = get_args()

    server = create_server()

    @server.route("/weather")
    def get_weather() -> Dict[str, Union[str, Any]]:
        """this function basically will do everything for this backend"""
        query = request.args.get("loc")
        coord_data = get_coordinates(query)

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
