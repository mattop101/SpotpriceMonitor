__author__ = "Matthew Northcott"

# Spot Price Monitor
# Created by Matthew Northcott
# 04-07-2016
# Python 3.4.3

# IMPORTS
import time
import threading
import webpage
import datetime
import RPi.GPIO as GPIO
from lcd import LCD


# GLOBALS
WEBPAGE_SPOTPRICE = "http://electricityinfo.co.nz/comitFta/ftapage.main"
AREA_CODE = "ISL2201"
REGEX_PRICE = "(?<=" + AREA_CODE + " \$)\d{1,4}\.\d{2}"
REGEX_TIME = "(?<=Last updated at )[\d\/]{10} [\d\:]{8}"

TIME_REFRESH = 60
TIME_WEB_TIMEOUT = 10

SPOT_PRICE_LIMIT_UPPER = 150.0
SPOT_PRICE_LIMIT_LOWER = 70.0
SPOT_PRICE_ADD = 0.0

BUZZER_INTERVAL = 0.05

ON = GPIO.LOW
OFF = GPIO.HIGH
LEFT = "left"
CENTRE = "centre"
RIGHT = "right"

GPIO_OUT = { "buzzer": 22, "led_green": 9, "led_orange": 10, "led_red": 11 }
GPIO_IN = { "switch": 27 }


class SpotPriceMonitor(object):
    def __init__(self):
        self.webpage = webpage.Webpage(WEBPAGE_SPOTPRICE)
        self.last_updated = datetime.datetime.now()
        self.spotprice = 0.00

    def update_spotprice(self):
        is_successful = self.webpage.open(TIME_WEB_TIMEOUT)
        if is_successful:
            self.spotprice = float(self.webpage.search(REGEX_PRICE))
            self.last_updated = datetime.datetime.strptime(self.webpage.search(REGEX_TIME), "%d/%m/%Y %H:%M:%S")

class GPIOInterface(object):
    def __init__(self, inputs, outputs):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.lcd = LCD()

        self.inputs = inputs
        self.outputs = outputs

        for tag, id in self.inputs.items():
            GPIO.setup(id, GPIO.IN)

        for tag, id in self.outputs.items():
            GPIO.setup(id, GPIO.OUT)
            GPIO.output(id, OFF)

    def display(self, string, line, justify):
        self.lcd.string_out(string, line, justify)

    def set(self, id, option):
        setting = OFF
        if option:
            setting = ON
        GPIO.output(self.outputs[id], setting)