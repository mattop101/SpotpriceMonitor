# Northcott Monitor
# Written by Matthew Northcott
# 20-08-2016
# Python 3.4.3

__author__ = "Matthew Northcott"


# IMPORTS
import threading
import time
import RPi.GPIO as GPIO
from importlib.machinery import SourceFileLoader
from lcd import LCD


# GLOBALS
ON = GPIO.LOW
OFF = GPIO.HIGH
LEFT = "left"
CENTRE = "centre"
RIGHT = "right"

GPIO_OUT = { "buzzer": 22, "led_green": 9, "led_orange": 10, "led_red": 11 }
GPIO_IN = { "switch": 27 }

ID_BUZZER = 22
ID_LED_GREEN = 9
ID_LED_ORANGE = 10
ID_LED_RED = 11
ID_BUTTON = 27

FILE_CONFIG = "/home/pi/SpotpriceMonitor/spotprice.cfg"


# MAIN BODY
conf = SourceFileLoader("conf", FILE_CONFIG).load_module()

class RPiInterface(object):
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for id in GPIO_OUT.values():
            GPIO.setup(id, GPIO.OUT)

        for id in GPIO_IN.values():
            GPIO.setup(id, GPIO.IN)

        self.is_green = False
        self.is_orange = False
        self.is_red = False
        self.is_red_buzzer = False

        self.lcd = LCD()

        self.reset_all()

        self.listener_thread = threading.Thread(target=self._button_listener)
        self.listener_thread.start()

    def reset_all(self):
        for id in GPIO_OUT.values():
            GPIO.output(id, OFF)
        self.is_green = False
        self.is_orange = False
        self.is_red = False
        self.is_red_buzzer = False
        self.buzz()

    def set_green(self):
        if self.is_green: return
        self.reset_all()
        self.is_green = True
        GPIO.output(ID_LED_GREEN, ON)

    def set_orange(self):
        if self.is_orange: return
        self.reset_all()
        self.is_orange = True
        GPIO.output(ID_LED_ORANGE, ON)

    def set_red(self):
        if self.is_red: return
        self.reset_all()
        self.is_red = True
        self.is_red_buzzer = True
        thr = threading.Thread(target=self._red_subroutine, args=(conf.TIME_BUZZER_DURATION, ))
        thr.start()

    def _red_subroutine(self, period):
        while self.is_red:
            time.sleep(period)
            GPIO.output(ID_LED_RED, ON)
            if self.is_red_buzzer:
                GPIO.output(ID_BUZZER, ON)
            time.sleep(period)
            GPIO.output(ID_LED_RED, OFF)
            GPIO.output(ID_BUZZER, OFF)

    def buzz(self):
        thr = threading.Thread(target=self._buzz, args=(conf.TIME_BUZZER_DURATION, ))
        thr.start()

    def _buzz(self, duration):
        GPIO.output(ID_BUZZER, ON)
        time.sleep(duration)
        GPIO.output(ID_BUZZER, OFF)

    def _button_listener(self):
        while True:
            if GPIO.input(ID_BUTTON):
                self.is_red_buzzer = False
            time.sleep(0.050)

    def lcd_out(self, string, line, justify="left"):
        self.lcd.string_out(string, line, justify)
