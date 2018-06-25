# Northcott Monitor
# Written by Matthew Northcott
# 24-06-2018
# Python 3.6

__author__ = "Matthew Northcott"

# IMPORTS
import interface
import weather
import flickuser
import datetime
import time
from importlib.machinery import SourceFileLoader

# GLOBALS
STRING_TIME = "%d %b %H:%M"
STRING_PRICE = "{0:<10}{1:>10}"
STRING_TEMPERATURE = "{:<9}{:<5}{:>6}"
STRING_WIND = "{:<9}{:<7}{:>4}"

LEFT = "left"
CENTRE = "centre"
RIGHT = "right"

FILE_CONFIG = "/home/pi/SpotpriceMonitor/spotprice.cfg"

UPDATE_FREQUENCY = 50

# MAIN BODY
conf = SourceFileLoader("conf", FILE_CONFIG).load_module()


class Monitor(object):
    interface = None
    weather = None
    spot_price = None

    enable_buzzer = True
    led_state = False

    now = None
    next_update = 0
    is_running = True

    def __init__(self):
        self.interface = interface.RPiInterface()
        self.weather = weather.WeatherData()
        self.spot_price = flickuser.FlickUser(conf.FLICK_USERNAME, conf.FLICK_PASSWORD)
        self.now = datetime.datetime.now()

        self.update_weather()
        self.update_spot_price()

    def update_interface(self):
        # Reset all
        self.interface.output_led(interface.LED_GREEN, False)
        self.interface.output_led(interface.LED_ORANGE, False)
        self.interface.output_led(interface.LED_RED, False)

        # Check button input
        if self.interface.input_button():
            self.enable_buzzer = not self.enable_buzzer

        # Output LED
        if self.spot_price.price >= conf.PRICE_LIMIT_UPPER:
            self.interface.output_led(interface.LED_RED, self.led_state)
            self.interface.output_buzzer(self.led_state and self.enable_buzzer)
            self.led_state = not self.led_state
        else:
            self.led_state = True

            self.interface.output_led(interface.LED_GREEN if self.spot_price.price < conf.PRICE_LIMIT_LOWER
                                      else interface.LED_ORANGE, self.led_state)

    def update_spot_price(self):
        self.spot_price.update()

        str_price = "{:.2f}c".format(self.spot_price.price)
        str_spot_price = "{:.2f}c".format(self.spot_price.spot_price)
        l1 = STRING_PRICE.format(str_spot_price, str_price)

        self.interface.lcd_out(l1, 1, CENTRE)

    def update_weather(self):
        self.weather.update()

        l0 = self.now.strftime(STRING_TIME)

        str_temp = "{}C".format(self.weather.temperature)
        str_humidity = "{}%".format(self.weather.humidity)
        str_rainfall = "{}mm".format(self.weather.rainfall)
        l2 = STRING_TEMPERATURE.format(str_temp, str_humidity, str_rainfall)

        str_wind_gust = "{}km/h".format(round(self.weather.wind_speed_gust))
        str_wind_mean = "{}km/h".format(round(self.weather.wind_speed_mean))
        str_wind_dir = self.weather.wind_dir
        l3 = STRING_WIND.format(str_wind_gust, str_wind_mean, str_wind_dir)

        self.interface.lcd_out(l0, 0, CENTRE)
        self.interface.lcd_out(l2, 2, CENTRE)
        self.interface.lcd_out(l3, 3, CENTRE)


    def mainloop(self):
        while self.is_running:
            self.now = datetime.datetime.now()
            t = time.time()

            if t > self.next_update:
                self.update_interface()
                self.next_update = t + conf.ALERT_DURATION

            elif self.now >= self.weather.next_update:
                self.update_weather()

            elif self.now >= self.spot_price.next_update:
                self.update_spot_price()

            time.sleep(1 / UPDATE_FREQUENCY)


def main():
    mon = Monitor()
    mon.mainloop()

if __name__ == '__main__':
    main()
