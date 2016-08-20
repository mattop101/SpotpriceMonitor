# Northcott Monitor
# Written by Matthew Northcott
# 20-08-2016
# Python 3.4.3

__author__ = "Matthew Northcott"


# IMPORTS
import RPi.GPIO
from importlib.machinery import SourceFileLoader


# GLOBALS
ON = GPIO.LOW
OFF = GPIO.HIGH
LEFT = "left"
CENTRE = "centre"
RIGHT = "right"

GPIO_OUT = { "buzzer": 22, "led_green": 9, "led_orange": 10, "led_red": 11 }
GPIO_IN = { "switch": 27 }

FILE_CONFIG = "E:/Programming/SpotpriceMonitor/spotprice.cfg"


# MAIN BODY
conf = SourceFileLoader("conf", FILE_CONFIG).load_module()

