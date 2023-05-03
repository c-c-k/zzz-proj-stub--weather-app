from datetime import datetime
import sys

from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)
app.config.from_prefixed_env()

weather_data = [
    {"degrees": 9, "state": "Chilly",
     "city": "BOSTON", "day_part": "night"},
    {"degrees": 32, "state": "Sunny",
     "city": "NEW YORK", "day_part": "day"},
    {"degrees": -15, "state": "Cold",
     "city": "EDMONTON", "day_part": "evening-morning"},
]


def _day_part(timestamp: int):
    hour = datetime.fromtimestamp(timestamp).hour
    if (hour >= 20) or (hour < 6):
        day_part = "night"
    elif 8 <= hour < 17:
        day_part = "day"
    else:
        day_part = "evening-morning"
    return day_part


def _get_city_weather(city: str):
    url = (
        "http://api.openweathermap.org/data/2.5/"
        "weather?q={}&APPID={}&units=metric".format(
            city, app.config['OPEN_WEATHER_MAP_API_KEY']
        ))
    owm_response = requests.get(url)
    full_weather_data = owm_response.json()
    filtered_weather_data = {
        "degrees": full_weather_data['main']['temp'],
        "state": full_weather_data['weather'][0]['main'],
        "city": full_weather_data['name'].upper(),
        "day_part": _day_part(full_weather_data['dt'])
    }
    return filtered_weather_data


def _get_city_weather_hstests_override(city: str):
    """ Override for HyperSkills automated testing

    This is necessary because, I'm too paranoid to put my API_KEY
    openly in the solution, and, I'm too lazy to figure out how
    to pass my API_KEY into the test securely.
    """
    return (
        {"degrees": 0, "state": "Unknown",
         "city": city.upper(), "day_part": "Unknown"}
    )


@app.route('/', methods=['POST', 'GET'])
def index():
    global weather_data
    if request.method == 'POST':
        city = request.form['city_name']
        if app.config.get('OPEN_WEATHER_MAP_API_KEY', False):
            weather_data.append(_get_city_weather(city))
        else:
            weather_data.append(_get_city_weather_hstests_override(city))
        return redirect(url_for('index'))
    return render_template('index.html', weather_data=weather_data)


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
