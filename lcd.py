# IMPORTS
import RPi.GPIO as GPIO
import time


# GLOBALS
# GPIO to LCD mapping
LCD_RS = 7
LCD_E  = 8
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18
LED_ON = 15

# Device constants
LCD_WIDTH = 20    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

# RAM addresses
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0
LCD_LINE_3 = 0x94
LCD_LINE_4 = 0xD4

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

class LCD(object):
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
        GPIO.setup(LCD_E, GPIO.OUT)  # E
        GPIO.setup(LCD_RS, GPIO.OUT) # RS
        GPIO.setup(LCD_D4, GPIO.OUT) # DB4
        GPIO.setup(LCD_D5, GPIO.OUT) # DB5
        GPIO.setup(LCD_D6, GPIO.OUT) # DB6
        GPIO.setup(LCD_D7, GPIO.OUT) # DB7
        GPIO.setup(LED_ON, GPIO.OUT) # Backlight enable

        # Initialise display
        self._byte(0x33, LCD_CMD) # 110011 Initialise
        self._byte(0x32, LCD_CMD) # 110010 Initialise
        self._byte(0x06, LCD_CMD) # 000110 Cursor move direction
        self._byte(0x0C, LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
        self._byte(0x28, LCD_CMD) # 101000 Data length, number of lines, font size
        self._byte(0x01, LCD_CMD) # 000001 Clear display
        time.sleep(E_DELAY)

    def _byte(self, bits, mode):
        """Send byte to data pins. Mode is true for character, false for a command """

        GPIO.output(LCD_RS, mode) # RS

        # High bits
        GPIO.output(LCD_D4, False)
        GPIO.output(LCD_D5, False)
        GPIO.output(LCD_D6, False)
        GPIO.output(LCD_D7, False)

        if bits & 0x10 == 0x10:
            GPIO.output(LCD_D4, True)
        if bits & 0x20 == 0x20:
            GPIO.output(LCD_D5, True)
        if bits & 0x40 == 0x40:
            GPIO.output(LCD_D6, True)
        if bits & 0x80 == 0x80:
            GPIO.output(LCD_D7, True)

        self._toggle_enable()

        # Low bits
        GPIO.output(LCD_D4, False)
        GPIO.output(LCD_D5, False)
        GPIO.output(LCD_D6, False)
        GPIO.output(LCD_D7, False)

        if bits & 0x01 == 0x01:
            GPIO.output(LCD_D4, True)
        if bits & 0x02 == 0x02:
            GPIO.output(LCD_D5, True)
        if bits & 0x04 == 0x04:
            GPIO.output(LCD_D6, True)
        if bits & 0x08 == 0x08:
            GPIO.output(LCD_D7, True)

        self._toggle_enable()

    def _toggle_enable(self):
        time.sleep(E_DELAY)
        GPIO.output(LCD_E, True)
        time.sleep(E_PULSE)
        GPIO.output(LCD_E, False)
        time.sleep(E_DELAY)

    def set_backlight(self, flag):
        GPIO.output(LED_ON, flag)

    def string_out(self, string, line=0, justify="left"):
        if justify == "left":
            string = string.ljust(LCD_WIDTH, " ")
        elif justify == "centre":
            string = string.center(LCD_WIDTH, " ")
        elif justify == "right":
            string = string.rjust(LCD_WIDTH, " ")

        self._byte([LCD_LINE_1, LCD_LINE_2, LCD_LINE_3, LCD_LINE_4][line], LCD_CMD)

        for c in string:
            self._byte(ord(c), LCD_CHR)