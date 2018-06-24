# Northcott Monitor
# Written by Matthew Northcott
# 24-06-2018
# Python 3.6

__author__ = "Matthew Northcott"

# IMPORTS
import RPi.GPIO as GPIO
from lcd import LCD

# GLOBALS
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

LED_GREEN = 0
LED_ORANGE = 1
LED_RED = 2
LED_MAP = 9, 10, 11

# PROGRAM
class RPiInterface(object):
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for id in GPIO_OUT.values():
            GPIO.setup(id, GPIO.OUT)

        for id in GPIO_IN.values():
            GPIO.setup(id, GPIO.IN)

        self.lcd = LCD()

    def input_button(self):
        return GPIO.input(ID_BUTTON)

    def output_led(self, led, state):
        GPIO.output(LED_MAP[led], state)

    def output_buzzer(self, state):
        GPIO.output(ID_BUZZER, state)

    def lcd_out(self, string, line, justify=LEFT):
        self.lcd.string_out(string, line, justify)