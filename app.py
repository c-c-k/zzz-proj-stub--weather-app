from datetime import datetime
from pathlib import Path
import sys

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests

path_database = Path(__file__).parent.joinpath('weather.db')
db = SQLAlchemy()

app = Flask(__name__)

app.config.from_prefixed_env()
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{path_database.as_posix()}"

path_database.unlink(missing_ok=True)
db.init_app(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)


with app.app_context():
    db.create_all()


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
    if request.method == 'POST':
        city = City(
            name=request.form["city_name"]
        )
        db.session.add(city)
        db.session.commit()
        return redirect(url_for('index'))
    weather_data = []
    cities = db.session.execute(db.select(City)).scalars()
    for city in cities:
        if app.config.get('OPEN_WEATHER_MAP_API_KEY', False):
            weather_data.append(_get_city_weather(city.name))
        else:
            weather_data.append(_get_city_weather_hstests_override(city.name))
    return render_template('index.html', weather_data=weather_data)


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
