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
import RPi.GPIO as GPIO
from importlib.machinery import SourceFileLoader


# GLOBALS
WEBPAGE_SPOTPRICE = "http://electricityinfo.co.nz/comitFta/ftapage.main"
WEBPAGE_WEATHER = "http://192.168.0.150/wx_data/data.txt"

REGEX_SPOTPRICE = "(?<=ISL2201 \$)\d{1,4}\.\d{2}"
REGEX_SPOTPRICE_TIME = "(?<=Last updated at )[\d\/]{10} [\d\:]{8}"

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

        data.sort(key=lambda x: x[0])

        network_charge = data[-1][1]

        for i in range(1, len(data)):
            if data[i-1][0] <= self.time.time() < data[i][0]:
                network_charge = data[i-1][1]
                break

        self.network_charge = (self.spotprice / 10.0) + network_charge + conf.PROVIDER_CHARGE

    def status(self):
        s = 0
        if conf.PRICE_LIMIT_LOWER <= self.network_charge < conf.PRICE_LIMIT_UPPER:
            s = 1
        elif self.network_charge >= conf.PRICE_LIMIT_UPPER:
            s = 2

        return s

    def time_string(self):
        return self.time.strftime("%d %b %H:%M")

    def price_string(self):
        str_price = "${:.2f}".format(self.spotprice)
        str_network = "{:.2f}c".format(self.network_charge)

        return "{0:<10}{1:>10}".format(str_price, str_network)

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

    def temp_string(self):
        temp = "{}C".format(self.temperature)
        humidity = "{}%".format(self.humidity)
        rainfall = "{}mm".format(self.wind_dir)

        return "{:<6}  {:<4}  {:>6}".format(temp, humidity, rainfall)

    def wind_string(self):
        gust = "{}km/h".format(self.wind_speed_gust)
        mean = "{}km/h".format(self.wind_speed_mean)

        return "{:<7} {:<7}  {:>3}".format(gust, mean, self.wind_dir)


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

        # Update LCD
        self.interface.lcd_out(self.spotprice_mon.time_string(), 0, "centre")
        self.interface.lcd_out(self.spotprice_mon.price_string(), 1, "centre")
        self.interface.lcd_out(self.weather_mon.temp_string(), 2, "centre")
        self.interface.lcd_out(self.weather_mon.wind_string(), 3, "centre")

    def mainloop(self, length):
        """ Create a loop in which to perform tasks, updating weather information at every 11-minute point and the
            spotprice every 5 minutes from start (possibly every 6 and 11 minute point)
        """

        update = False

        while True:
            now = datetime.datetime.now()

            if now.second == 0:
                if now.minute % 5 == 1:
                    self.spotprice_mon.update_values()
                    update = True

                if now.minute % 10 == 1:
                    self.weather_mon.update_values()
                    update = True

            if update:
                self.update_interface()
                update = False

            time.sleep(0.50)


def main():
    mon = MonitorInterface()
    mon.mainloop(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        RPi.GPIO.cleanup()