# Northcott Monitor
# Written by Matthew Northcott
# 20-08-2016
# Python 3.4.3

__author__ = "Matthew Northcott"

# IMPORTS
import pickle
import datetime
import time
import holidays
import webpage
# import RPi.GPIO
from importlib.machinery import SourceFileLoader




# GLOBALS
WEBPAGE_SPOTPRICE = "http://electricityinfo.co.nz/comitFta/ftapage.main"
WEBPAGE_WEATHER = "http://192.168.0.150/wx_data/data.txt"

REGEX_SPOTPRICE = "(?<=ISL2201 \$)\d{1,4}\.\d{2}"
REGEX_SPOTPRICE_TIME = "(?<=Last updated at )[\d\/]{10} [\d\:]{8}"

# ON = GPIO.LOW
# OFF = GPIO.HIGH
LEFT = "left"
CENTRE = "centre"
RIGHT = "right"

GPIO_OUT = { "buzzer": 22, "led_green": 9, "led_orange": 10, "led_red": 11 }
GPIO_IN = { "switch": 27 }

FILE_CONFIG = "E:/Programming/SpotpriceMonitor/spotprice.cfg"


# MAIN BODY
conf = SourceFileLoader("conf", FILE_CONFIG).load_module()

class Monitor(object):
    def __init__(self, url):
        self.webpage = webpage.Webpage(url)
        self._open_webpage(url)
        self.update_values()

    def _open_webpage(self, url):
        success = self.webpage.open()


    def update_values(self):
        pass


class SpotpriceMonitor(Monitor):
    def __init__(self):
        super().__init__(WEBPAGE_SPOTPRICE)

    def update_values(self):
        self.update_spotprice()
        self.update_network_charge()

    def update_spotprice(self):
        if not self.webpage.open(): return

        self.spotprice = float(self.webpage.search(REGEX_SPOTPRICE))
        self.time = datetime.datetime.strptime(self.webpage.search(REGEX_SPOTPRICE_TIME), "%d/%m/%Y %H:%M:%S")

    def update_network_charge(self):
        if self.spotprice == 0: return

        weekday = datetime.datetime.weekday(self.time)
        is_weekend = weekday > 4
        is_holiday = self.time in holidays.NewZealand()
        is_winter = 4 < self.time.month < 9

        filename = conf.FILE_NETWORK_SUMMER
        if is_winter:
            filename = conf.FILE_NETWORK_WINTER
        if is_weekend or is_holiday:
            filename = conf.FILE_NETWORK_WEEKEND

        with open(filename, 'r') as cfg:
            data = [(datetime.time(int(h), int(m)), float(price)) for h, m, price in (line.split() for line in cfg)]

        #
        # data.sort(key=lambda x: x[0])
        #
        # network_charge = data[-1][1]
        #
        # for i in range(1, len(data)):
        #     if data[i-1][0] <= self.time.time() < data[i][0]:
        #         network_charge = data[i-1][1]
        #         break
        #
        # self.network_charge = (self.spotprice / 10.0) + network_charge + conf.PROVIDER_CHARGE


class WeatherMonitor(Monitor):
    def __init__(self):
        super().__init__(WEBPAGE_WEATHER)

    def update_values(self):
        weather_data = pickle.loads(self.webpage.response, encoding="latin1")

        self.temperature = weather_data[2]
        self.wind_dir = weather_data[3]
        self.rainfall = weather_data[4]
        self.wind_speed_gust = weather_data[5]
        self.wind_speed_mean = weather_data[6]
        self.wind_run = weather_data[7]
        self.humidity = weather_data[8]
        self.barometer = weather_data[9]
        self.dewpoint = weather_data[10]

        self.weather_data = weather_data


class MonitorInterface(object):
    def __init__(self):
        self.weather_mon = WeatherMonitor()
        self.spotprice_mon = SpotpriceMonitor()


    def mainloop(self, length):
        """ Create a loop in which to perform tasks, updating weather information at every 11-minute point and the
            spotprice every 5 minutes from start (possibly every 6 and 11 minute point)
        """

        while True:
            now = datetime.datetime.now()

            if now.minute % 5 == 1:
                self.spotprice_mon.update_values()

            if now.minute % 10 == 1:
                self.weather_mon.update_values()


def main():
    x = SpotpriceMonitor()
    print(x.spotprice)
    print(x.time)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        # RPi.GPIO.cleanup()