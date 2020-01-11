# Written by Matthew Northcott
# 30 December 2019


__author__ = "Matthew Northcott"


# IMPORTS
import time
import datetime
import threading
import schedule

from importlib.machinery import SourceFileLoader

import RPi.GPIO as GPIO
import lcd
import weather
import flickuser

# GLOBALS
GPIO_LED_GREEN = 9
GPIO_LED_ORANGE = 10
GPIO_LED_RED = 11
GPIO_BUTTON = 27

TIME_FORMAT = "%d %b %H:%M"
FILE_CONFIG = "spotprice.cfg"

# MAIN BODY
conf = SourceFileLoader("conf", FILE_CONFIG).load_module()


class Monitor(object):
    led_state = False
    running = False

    def __init__(self):
        # GPIO initialisation
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(GPIO_LED_GREEN, GPIO.OUT)
        GPIO.setup(GPIO_LED_ORANGE, GPIO.OUT)
        GPIO.setup(GPIO_LED_RED, GPIO.OUT)
        GPIO.setup(GPIO_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        self.lcd = lcd.LCD()

        self.startup()

        self.weather = weather.WeatherData()
        self.flick = flickuser.FlickUser(conf.FLICK_USERNAME, conf.FLICK_PASSWORD)

        self._update()

        schedule.every().hour.at(":01").do(self.update)
        schedule.every().hour.at(":11").do(self.update)
        schedule.every().hour.at(":21").do(self.update)
        schedule.every().hour.at(":31").do(self.update)
        schedule.every().hour.at(":41").do(self.update)
        schedule.every().hour.at(":51").do(self.update)
    
    def log(self, message):
        if not conf.DEBUG:
            return
        dt = datetime.datetime.now().strftime("%d %b %Y %R")
        print("[{}] {}".format(dt, message))

    
    def startup(self):
        self.log("Performing startup sequence...")

        self.lcd.string_out("Spotprice Monitor", 1, justify="center")
        self.lcd.string_out("v3 (Dec 2019)", 2, justify="center")

        self.reset_leds()

        for _ in range(3):
            GPIO.output(GPIO_LED_GREEN, GPIO.LOW)
            time.sleep(0.4)
            GPIO.output(GPIO_LED_GREEN, GPIO.HIGH)
            GPIO.output(GPIO_LED_ORANGE, GPIO.LOW)
            time.sleep(0.4)
            GPIO.output(GPIO_LED_ORANGE, GPIO.HIGH)
            GPIO.output(GPIO_LED_RED, GPIO.LOW)
            time.sleep(0.4)
            GPIO.output(GPIO_LED_RED, GPIO.HIGH)
            time.sleep(0.4)
        
        for _ in range(3):
            GPIO.output(GPIO_LED_GREEN, GPIO.LOW)
            GPIO.output(GPIO_LED_ORANGE, GPIO.LOW)
            GPIO.output(GPIO_LED_RED, GPIO.LOW)
            time.sleep(0.2)
            GPIO.output(GPIO_LED_GREEN, GPIO.HIGH)
            GPIO.output(GPIO_LED_ORANGE, GPIO.HIGH)
            GPIO.output(GPIO_LED_RED, GPIO.HIGH)
            time.sleep(0.2)

        self.log("Completed startup sequence.")
    
    def reset_leds(self):
        GPIO.output(GPIO_LED_GREEN, GPIO.HIGH)
        GPIO.output(GPIO_LED_ORANGE, GPIO.HIGH)
        GPIO.output(GPIO_LED_RED, GPIO.HIGH)
    
    def update_leds(self):
        self.reset_leds()

        if self.flick.spot_price >= conf.PRICE_LIMIT_UPPER:
            GPIO.output(GPIO_LED_RED, GPIO.HIGH if self.led_state else GPIO.LOW)
            self.led_state = not self.led_state
        elif self.flick.spot_price < conf.PRICE_LIMIT_LOWER:
            GPIO.output(GPIO_LED_GREEN, GPIO.HIGH)
        else:
            GPIO.output(GPIO_LED_ORANGE, GPIO.HIGH)

    def _update(self):
        self.weather.update()
        self.flick.update()

        temperature = "{}C".format(self.weather.temperature)
        humidity = "{}%".format(self.weather.humidity)
        rainfall = "{}mm".format(self.weather.rainfall)
        wind_gust = "{:.0f}km/h".format(self.weather.wind_speed_gust)
        wind_mean = "{:0f}km/h".format(self.weather.wind_speed_mean)
        wind_dir = self.weather.wind_dir

        price = "{:.2f}c".format(self.flick.price)
        spot_price = "{:.2f}c".format(self.flick.spot_price)

        lines = [
            datetime.datetime.now().strftime(TIME_FORMAT),
            "{:<10}{:>10}".format(price, spot_price),
            "{:<9}{:<5}{:>6}".format(temperature, humidity, rainfall),
            "{:<9}{:<7}{:>4}".format(wind_gust, wind_mean, wind_dir),
        ]

        self.log("Outputting to LCD:\n" + '\n'.join(line for line in lines))

        for i in range(len(lines)):
            self.lcd.string_out(lines[i], i, justify="center")
        
        self.log("Update complete.")
        
    def update(self):
        self.log("Performing update...")

        thr = threading.Thread(target=self._update)
        thr.start()
    
    def mainloop(self):
        self.running = True

        while self.running:
            schedule.run_pending()
            self.update_leds()
            time.sleep(1)


def main():
    Monitor().mainloop()


if __name__ == '__main__':
    main()
