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
import interface
from importlib.machinery import SourceFileLoader


# GLOBALS
WEBPAGE_SPOTPRICE = "http://electricityinfo.co.nz/comitFta/ftapage.main"
WEBPAGE_WEATHER = "http://192.168.0.150/wx_data/data.txt"

REGEX_SPOTPRICE = "(?<=ISL2201 \$)\d{1,4}\.\d{2}"
REGEX_SPOTPRICE_TIME = "(?<=Last updated at )[\d\/]{10} [\d\:]{8}"

WEATHER_LIST_LEN = 11

STRING_TIME = "%d %b %H:%M"
STRING_PRICE = "{0:<10}{1:>10}"
STRING_TEMPERATURE = "{:<9}{:<5}{:>6}"
STRING_WIND = "{:<9}{:<7}{:>4}"

LEFT = "left"
CENTRE = "centre"
RIGHT = "right"

GPIO_OUT = { "buzzer": 22, "led_green": 9, "led_orange": 10, "led_red": 11 }
GPIO_IN = { "switch": 27 }

FILE_CONFIG = "/home/pi/SpotpriceMonitor/spotprice.cfg"


# MAIN BODY
conf = SourceFileLoader("conf", FILE_CONFIG).load_module()

class Monitor(object):
    def __init__(self, url):
        self.webpage = webpage.Webpage(url)
        self.has_data = False
        self.update_values()

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

        self.spotprice = float(self.webpage.search(REGEX_SPOTPRICE)) + conf.ADDITIONAL_SPOTPRICE
        self.time = datetime.datetime.strptime(self.webpage.search(REGEX_SPOTPRICE_TIME), "%d/%m/%Y %H:%M:%S")
        self.has_data = True

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

        data.sort(key=lambda x: x[0])

        network_charge = data[-1][1]

        for i in range(1, len(data)):
            if data[i-1][0] <= self.time.time() < data[i][0]:
                network_charge = data[i-1][1]
                break

        self.network_charge = (self.spotprice / 10.0) + network_charge + conf.PROVIDER_CHARGE + conf.ADDITIONAL_NETWORK

    def status(self):
        s = 0
        if conf.PRICE_LIMIT_LOWER <= self.network_charge < conf.PRICE_LIMIT_UPPER:
            s = 1
        elif self.network_charge >= conf.PRICE_LIMIT_UPPER:
            s = 2

        return s

    def time_string(self):
        return self.time.strftime(STRING_TIME)

    def price_string(self):
        str_price = "${:.2f}".format(self.spotprice)
        str_network = "{:.2f}c".format(self.network_charge)

        return STRING_PRICE.format(str_price, str_network)


class WeatherMonitor(Monitor):
    def __init__(self):
        super().__init__(WEBPAGE_WEATHER)

    def update_values(self):
        if not self.webpage.open(): return

        weather_data = pickle.loads(self.webpage.response, encoding="latin1")

        if len(weather_data) != WEATHER_LIST_LEN: return

        _, _, self.temperature, self.wind_dir, self.rainfall, self.wind_speed_gust, self.wind_speed_mean, \
        self.wind_run, self.humidity, self.barometer, self.dewpoint = weather_data

        self.weather_data = weather_data

        self.has_data = True

    def temp_string(self):
        temp = "{}C".format(self.temperature)
        humidity = "{}%".format(self.humidity)
        rainfall = "{}mm".format(self.rainfall)

        return STRING_TEMPERATURE.format(temp, humidity, rainfall)

    def wind_string(self):
        gust = "{}km/h".format(int(self.wind_speed_gust))
        mean = "{}km/h".format(int(self.wind_speed_mean))

        return STRING_WIND.format(gust, mean, self.wind_dir)


class MonitorInterface(object):
    def __init__(self):
        self.weather_mon = WeatherMonitor()
        self.spotprice_mon = SpotpriceMonitor()
        self.interface = interface.RPiInterface()

        self.spotprice_mon.update_values()
        self.weather_mon.update_values()
        self.update_interface()

    def update_interface(self):
        # Update LED & buzzer
        [self.interface.set_green, self.interface.set_orange, self.interface.set_red][self.spotprice_mon.status()]()

        spotprice_top = "No spotprice data"
        spotprice_bottom = ""
        weather_top = "No weather data"
        weather_bottom = ""

        # Update LCD
        if self.spotprice_mon.has_data:
            spotprice_top = self.spotprice_mon.time_string()
            spotprice_bottom = self.spotprice_mon.price_string()

        if self.weather_mon.has_data:
            weather_top = self.weather_mon.temp_string()
            weather_bottom = self.weather_mon.wind_string()

        self.interface.lcd_out(spotprice_top, 0, "centre")
        self.interface.lcd_out(spotprice_bottom, 1, "centre")
        self.interface.lcd_out(weather_top, 2, "centre")
        self.interface.lcd_out(weather_bottom, 3, "centre")

    def mainloop(self):

        update = False

        while True:
            now = datetime.datetime.now()

            if now.second == 0:
                if now.minute % 5 == 0:
                    self.spotprice_mon.update_values()
                    update = True

                if now.minute % 10 == 0:
                    self.weather_mon.update_values()
                    update = True

            if update:
                self.update_interface()
                update = False

            time.sleep(0.90)


def main():
    mon = MonitorInterface()
    mon.mainloop()

if __name__ == '__main__':
    main()
