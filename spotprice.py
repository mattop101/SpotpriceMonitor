# Spot Price Monitor
# Created by Matthew Northcott
# 21-07-2016
# Python 3.4.4

__author__ = "Matthew Northcott"

# IMPORTS
import time
import threading
import webpage
import conf
import datetime
import holidays
import RPi.GPIO as GPIO
import lcd


# GLOBALS
WEBPAGE_MAIN = "http://electricityinfo.co.nz/comitFta/ftapage.main"
REGEX_PRICE = "(?<=ISL2201 \$)\d{1,4}\.\d{2}"
REGEX_TIME = "(?<=Last updated at )[\d\/]{10} [\d\:]{8}"

ON = GPIO.LOW
OFF = GPIO.HIGH
LEFT = "left"
CENTRE = "centre"
RIGHT = "right"

IDS_OUT = { "buzzer": 22, "led_green": 9, "led_orange": 10, "led_red": 11 }
IDS_IN = { "switch": 27 }

# MAIN
class GPIOInterface(object):
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.lcd = lcd.LCD()
        self.buzzer_active = False
        self.strobe_active = False

        self.refresh()

        self.listener("switch", target=self.stop_buzzer)

    def on(self, id):
        GPIO.output(IDS_OUT[id], ON)

    def off(self, id):
        GPIO.output(IDS_OUT[id], OFF)

    def _buzzer(self):
        self.on("buzzer")
        time.sleep(conf.BUZZER_DURATION)
        self.off("buzzer")

    def buzzer(self):
        thr = threading.Thread(target=self._buzzer)
        thr.start()

    def _buzzer_long(self):
        self.buzzer_active = True
        while self.buzzer_active:
            for _ in range(2):
                self.on("buzzer")
                time.sleep(conf.BUZZER_DURATION)
                self.off("buzzer")
                time.sleep(conf.BUZZER_DURATION)
            time.sleep(5 - 2*conf.BUZZER_DURATION)

    def buzzer_long(self):
        thr = threading.Thread(target=self._buzzer_long)
        thr.start()

    def stop_buzzer(self):
        self.buzzer_active = False

    def refresh(self):
        for tag, id in IDS_OUT.items():
            GPIO.setup(id, GPIO.OUT)
            GPIO.output(id, OFF)

        for tag, id in IDS_IN.items():
            GPIO.setup(id, GPIO.IN)

    def _strobe(self, id, interval):
        self.strobe_active = True
        while self.strobe_active:
            self.on(id)
            time.sleep(interval)
            self.off(id)
            time.sleep(interval)

    def strobe(self, id, interval):
        thr = threading.Thread(target=self._strobe, args=(id, interval))
        thr.start()

    def stop_strobe(self):
        self.strobe_active = False

    def lcd(self, string, line=1, justify="left"):
        self.lcd.string_out(string, line, justify)

    def _listener(self, id, target, args):
        prev = GPIO.input(IDS_IN[id])
        now = prev
        while True:
            if (now and (not prev)):
                target(*args)
            prev = now
            now = GPIO.input(IDS_IN[id])

            time.sleep(0.05)

    def listener(self, id, target, args=[]):
        thr = threading.Thread(target=self._listener, args=(id, target, args))
        thr.start()


class SpotPriceMonitor(object):
    def __init__(self):
        self.webpage = webpage.Webpage(WEBPAGE_MAIN)
        self.spotprice = 0
        self.network_charge = 0
        self.time_last = None
        self.interface = GPIOInterface()
        self.led_id = "led_green"

        self.update_all()

    def update_all(self):
        self.interface.lcd.string_out("Updating...", line=1, justify=CENTRE)
        self.update_spotprice()
        self.update_network_charge()
        self.update_interface()

    def update_spotprice(self):
        if self.webpage.open():
            self.spotprice = float(self.webpage.search(REGEX_PRICE))
            self.time_last = datetime.datetime.strptime(self.webpage.search(REGEX_TIME), "%d/%m/%Y %H:%M:%S")

    def get_network_charge(self):
        weekday = datetime.datetime.weekday(self.time_last)
        is_weekend = weekday > 4
        is_holiday = self.time_last in holidays.NewZealand()
        is_winter = 4 < self.time_last.month < 9

        filename = conf.FILE_NETWORK_SUMMER
        if is_winter:
            filename = conf.FILE_NETWORK_WINTER
        if is_weekend or is_holiday:
            filename = conf.FILE_NETWORK_WEEKEND

        with open(filename, 'r') as cfg:
            data = [(datetime.time(int(h), int(m)), float(price)) for h, m, price in (line.split() for line in cfg)]

        data.sort(key=lambda x: x[0])

        for i in range(1, len(data)):
            if data[i-1][0] <= datetime.datetime.now().time() < data[i][0]:
                return data[i-1][1]

        return data[-1][1]

    def update_network_charge(self):
        """"""
        if self.spotprice == 0: return
        self.network_charge = (self.spotprice / 10.0) + self.get_network_charge() + conf.PROVIDER_CHARGE

    def update_interface(self):
        # Turn all LEDs off
        for id in ["led_green", "led_orange", "led_red"]:
            self.interface.off(id)

        self.interface.stop_strobe()

        # Determine LED to turn on
        id = "led_green"
        if conf.PRICE_LIMIT_LOWER <= self.network_charge < conf.PRICE_LIMIT_UPPER:
            id = "led_orange"
        elif self.network_charge >= conf.PRICE_LIMIT_UPPER:
            id = "led_red"
            self.interface.strobe(id, 1)

        if IDS_OUT[id] != IDS_OUT[self.led_id]:
            if id == "led_red":
                self.interface.buzzer_long()
            else:
                self.interface.buzzer()

        self.led_id = id
        self.interface.on(self.led_id)

        str_time = self.time_last.strftime("%d %b %H:%M")
        str_price = "${:.2f}".format(self.spotprice)
        str_rate = "{:.2f}c".format(self.network_charge)

        line_top = str_time
        line_bottom = str_price + " "*(lcd.LCD_WIDTH-len(str_price)-len(str_rate)) + str_rate

        self.interface.lcd.string_out(line_top, line=1, justify=CENTRE)
        self.interface.lcd.string_out(line_bottom, line=2, justify=CENTRE)

    def run(self, run_time=0):
        if run_time == 0:
            time_complete = time.time() + 3.154e9
        else:
            time_complete = time.time() + run_time

        while time.time() < time_complete:
            t = time.perf_counter()
            self.update_all()
            t = time.perf_counter() - t

            time.sleep(conf.UPDATE_INTERVAL - t)


def main():
    monitor = SpotPriceMonitor()
    monitor.run()


if __name__ == '__main__':
    main()