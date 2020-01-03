# Written by Matthew Northcott
# 30 December 2019


__author__ = "Matthew Northcott"


# IMPORTS
import time
import threading
import schedule

from importlib.machinery import SourceFileLoader

import RPi.GPIO as GPIO
import lcd
import weather
import flickuser

# GLOBALS
GPIO_BUZZER = 22
GPIO_LED_GREEN = 9
GPIO_LED_ORANGE = 10
GPIO_LED_RED = 11
GPIO_BUTTON = 27

TIME_FORMAT = "%d %b %H:%M"
FILE_CONFIG = "spotprice.cfg"

# MAIN BODY
conf = SourceFileLoader("conf", FILE_CONFIG).load_module()


class Monitor(object):
    enable_buzzer = True
    led_state = False
    running = False

    def __init__(self):
        # GPIO initialisation
        GPIO.setmode(rpi.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(GPIO_BUZZER, GPIO.OUT)
        GPIO.setup(GPIO_LED_GREEN, GPIO.OUT)
        GPIO.setup(GPIO_LED_ORANGE, GPIO.OUT)
        GPIO.setup(GPIO_LED_RED, GPIO.OUT)
        GPIO.setup(GPIO_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        self.startup()
        GPIO.add_event_detect(GPIO_BUTTON, GPIO.RISING, callback=self.toggle_buzzer, bouncetime=200)

        self.lcd = lcd.LCD()
        self.weather = weather.WeatherData()
        self.flick = flickuser.FlickUser(conf.FLICK_USERNAME, conf.FLICK_PASSWORD)

        schedule.every().hour.at(":01").do(self.update)
        schedule.every().hour.at(":11").do(self.update)
        schedule.every().hour.at(":21").do(self.update)
        schedule.every().hour.at(":31").do(self.update)
        schedule.every().hour.at(":41").do(self.update)
        schedule.every().hour.at(":51").do(self.update)
    
    def startup(self):
        self.lcd.string_out("Spotprice Monitor", 1, justify="center")
        self.lcd.string_out("v3 (Dec 2019)", 2, justify="center")

        self.reset_leds()

        for _ in range(3):
            GPIO.output(GPIO_LED_GREEN, GPIO.LOW)
            time.sleep(1)
            GPIO.output(GPIO_LED_GREEN, GPIO.HIGH)
            GPIO.output(GPIO_LED_ORANGE, GPIO.LOW)
            time.sleep(1)
            GPIO.output(GPIO_LED_ORANGE, GPIO.HIGH)
            GPIO.output(GPIO_LED_RED, GPIO.LOW)
            time.sleep(1)
            GPIO.output(GPIO_LED_RED, GPIO.HIGH)
            time.sleep(1)
        
        for _ in range(3):
            GPIO.output(GPIO_LED_GREEN, GPIO.LOW)
            GPIO.output(GPIO_LED_ORANGE, GPIO.LOW)
            GPIO.output(GPIO_LED_RED, GPIO.LOW)
            time.sleep(0.5)
            GPIO.output(GPIO_LED_GREEN, GPIO.HIGH)
            GPIO.output(GPIO_LED_ORANGE, GPIO.HIGH)
            GPIO.output(GPIO_LED_RED, GPIO.HIGH)
            time.sleep(0.5)

    def toggle_buzzer(self):
        self.enable_buzzer = not self.enable_buzzer

        if not self.enable_buzzer:
            GPIO.output(GPIO_BUZZER, GPIO.HIGH)
    
    def reset_leds(self):
        GPIO.output(GPIO_BUZZER, GPIO.HIGH)
        GPIO.output(GPIO_LED_GREEN, GPIO.HIGH)
        GPIO.output(GPIO_LED_ORANGE, GPIO.HIGH)
        GPIO.output(GPIO_LED_RED, GPIO.HIGH)
    
    def update_leds(self):
        self.reset_leds()

        if self.flick.spot_price >= conf.PRICE_LIMIT_UPPER:
            state = GPIO.HIGH if self.led_state else GPIO.LOW

            GPIO.output(GPIO_LED_RED, state)

            if self.enable_buzzer:
                GPIO.output(GPIO_BUZZER, state)

            self.led_state = not self.led_state

        elif self.flick.spot_price < conf.PRICE_LIMIT_LOWER:
            GPIO.output(GPIO_LED_GREEN, GPIO.HIGH)
            
        else:
            GPIO.output(GPIO_LED_ORANGE, GPIO.HIGH)

    def _update(self):
        self.weather.update()
        self.flick.update()

        temperature = f"{self.weather.temperature}C"
        humidity = f"{self.weather.humidity}%"
        rainfall = f"{self.weather.rainfall}mm"
        wind_gust = f"{self.weather.wind_speed_gust:.0f}km/h"
        wind_mean = f"{self.weather.wind_speed_mean:0f}km/h"
        wind_dir = self.weather.wind_dir

        price = f"{self.flick.price:.2f}c"
        spot_price = f"{self.flick.spot_price:.2f}c"

        lines = [
            datetime.datetime.now().strftime(TIME_FORMAT),
            f"{price:<10}{spot_price:>10}",
            f"{temperature:<9}{humidity:<5}{rainfall:>6}",
            f"{wind_gust:<9}{wind_mean:<7}{wind_dir:>4}",
        ]

        for i in range(len(lines)):
            self.lcd.string_out(lines[i], i, justify="center")
        
    def update(self):
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
