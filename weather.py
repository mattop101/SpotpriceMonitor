# Written by Matthew Northcott
# 30 December 2019


__author__ = "Matthew Northcott"


# IMPORTS
import requests
import pickle


# GLOBALS
URL_WEATHER = "http://192.168.0.150/wx_data/data.txt"


# PROGRAM
class WeatherData(object):
    date = ""
    time = ""
    temperature = 0
    wind_dir = ""
    rainfall = 0
    wind_speed_gust = 0
    wind_speed_mean = 0
    wind_run = 0
    humidity = 0.0
    barometer = 0
    dew_point = 0

    def update(self):
        res = requests.get(URL_WEATHER)
        result = pickle.loads(res.content)

        self.date, self.time, self.temperature, self.wind_dir, self.rainfall, \
            self.wind_speed_gust, self.wind_speed_mean, self.wind_run, \
                self.humidity, self.barometer, self.dew_point = result