# Northcott Monitor
# Written by Matthew Northcott
# 24-06-2018
# Python 3.6

# IMPORTS
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import pickle
import datetime

# GLOBALS
URL_WEATHER = 'http://192.168.0.150/wx_data/data.txt'

# PROGRAM
class WeatherData(object):
    temperature = 0
    wind_dir = ''
    rainfall = 0
    wind_speed_gust = 0
    wind_speed_mean = 0
    wind_run = 0
    humidity = 0.0
    barometer = 0
    dew_point = 0
    next_update = None

    def get_weather(self):
        try:
            request = Request(URL_WEATHER)
            response = urlopen(request).read()
            result = pickle.loads(response)

            _, _, self.temperature, self.wind_dir, self.rainfall, self.wind_speed_gust, self.wind_speed_mean, \
            self.wind_run, self.humidity, self.barometer, self.dew_point = result
        except Exception as e:
            with open('error.log', 'a') as f:
                f.write('\n' + str(e))

    def update(self):
        self.get_weather()

        now = datetime.datetime.now()

        if now.minute >= 51:
            self.next_update = now.replace(hour=now.hour + 1, minute=1, second=0, microsecond=0)
        else:
            self.next_update = now.replace(minute=now.minute // 10 * 10 + 11 , second=0, microsecond=0)