import argparse
import os
import re
from typing import Any, Dict, Tuple, Union

import dotenv
import requests
import werkzeug
from flask import Flask, jsonify, request
from flask_cors import CORS


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


def get_coordinates(loc: str) -> Tuple[Dict[str, Union[str, int]], int]:
    """use the geoloc api from OpenWeather to get coordinates from user input

    :param loc: zip or city name
    """
    is_zip = re.match(r"\d{5}", loc)

    try:
        if not is_zip:
            # TODO: add logic to handle multiple locations returned from direct
            loc = loc.replace(" ", "")
            if "," in loc:
                loc = loc + ",US"
            location_resp = requests.get(
                "http://api.openweathermap.org/geo/1.0/direct?"
                + f"q={loc}&appid={os.environ['OW_KEY']}",
                timeout=5,
            )
            loc_json = location_resp.json()[0]
        else:
            location_resp = requests.get(
                "http://api.openweathermap.org/geo/1.0/zip?"
                + f"zip={loc}&appid={os.environ['OW_KEY']}",
                timeout=5,
            )
            loc_json = location_resp.json()
    # broad error handling might be bad, but it's what I am band-aiding for now
    except Exception as err:
        loc_json = {"error": err}

    return (loc_json, location_resp.status_code)


def get_reverse_geoloc(lat: float, lon: float) -> Tuple[Dict[str, Any], int]:
    """get location info from coordinates

    :param lat: latitude
    :param lon: longitude
    """
    try:
        location_resp = requests.get(
            "http://api.openweathermap.org/geo/1.0/reverse?"
            + f"lat={lat}&lon={lon}&limit=1&appid={os.environ['OW_KEY']}",
            timeout=5,
        )
        location_data = location_resp.json()[0]
    except Exception as err:
        location_data = {"error": err}
    return (location_data, location_resp.status_code)


def get_forecast(lat: float, lon: float) -> Tuple[Dict[str, Any], int]:
    """get a 5 day forcast from the OpenWeather api

    :param lat: latitude
    :param lon: longitude
    """
    try:
        forecast = requests.get(
            "https://api.openweathermap.org/data/3.0/onecall?"
            + f"lat={lat}&lon={lon}&units=metric&"
            + "exclude=minutely,hourly,alerts&"
            + f"appid={os.environ['OW_KEY']}",
            timeout=5,
        )
        forecast_data = forecast.json()
    except Exception as err:
        forecast_data = {"error": err}
    return (forecast_data, forecast.status_code)


def create_server(config: Dict[str, Any] = {}) -> Flask:
    """create server object (only here to make pytest simpler)"""

    server = Flask(__name__)

    if config:
        server.config.from_mapping(config)

    # origins * is risky, would not do in prod
    _ = CORS(server, origins="*")

    @server.route("/weather")
    def get_weather() -> Tuple[Dict[str, Union[str, Any]], int]:
        """this function basically will do everything for this backend"""
        query = request.args.get("loc")
        coord_data, coord_status = get_coordinates(query)

        if coord_status != 200:
            return (
                jsonify(coord_data),
                coord_status,
            )

        forecast, forecast_status = get_forecast(
            coord_data["lat"], coord_data["lon"]
        )

        if forecast_status != 200:
            return (
                jsonify(forecast),
                forecast_status,
            )

        return (jsonify({"location": coord_data, "forecast": forecast}), 200)

    @server.route("/coordinates")
    def get_weather_with_coords() -> Tuple[Dict[str, Union[str, Any]], int]:
        """get weather with coords directly input"""

        lat = request.args.get("lat")
        lon = request.args.get("lon")

        if lat is None or lon is None:
            return (
                jsonify(
                    {
                        "error": "Location call requires both lat and lon."
                        + f"Recieved '{lat}' and '{lon}'"
                    }
                ),
                400,
            )

        coord_data, coord_status = get_reverse_geoloc(lat, lon)
        if coord_status != 200:
            return (
                jsonify(coord_data),
                coord_status,
            )

        forecast, forecast_status = get_forecast(
            coord_data["lat"], coord_data["lon"]
        )

        if forecast_status != 200:
            return (
                jsonify(forecast),
                forecast_status,
            )
        return jsonify({"location": coord_data, "forecast": forecast})

    @server.errorhandler(werkzeug.exceptions.BadRequest)
    def handle_bad_request(
        error: Exception,
    ) -> Tuple[Dict[str, Union[str, Any]], int]:
        """Bubble up errors to client"""
        return (
            {
                "error": error,
                "msg": "Request not understood",
                "request": request.base_url,
            },
            400,
        )

    @server.errorhandler(werkzeug.exceptions.NotFound)
    def handle_server_error(
        error: Exception,
    ) -> Tuple[Dict[str, Union[str, Any]], int]:
        """Bubble up errors to client"""

        return (
            {
                "error": error,
                "msg": "Flask server error",
                "request": request.base_url,
            },
            404,
        )

    @server.errorhandler(werkzeug.exceptions.InternalServerError)
    def handle_not_found(
        error: Exception,
    ) -> Tuple[Dict[str, Union[str, Any]], int]:
        """Bubble up errors to client"""

        return (
            {
                "error": error,
                "msg": "Flask server error",
                "request": request.base_url,
            },
            500,
        )

    return server


def main() -> None:
    """instantiate server"""

    dotenv.load_dotenv()

    args = get_args()

    server = create_server()

    server.run(debug=args.debug, port=args.port)
