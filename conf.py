# Spot Price Monitor
# Created by Matthew Northcott
# 21-07-2016
# Python 3.4.4

import configparser

PRICE_LIMIT_UPPER = None
PRICE_LIMIT_LOWER = None
BUZZER_DURATION = None
UPDATE_INTERVAL = None

FILE_NETWORK_SUMMER = None
FILE_NETWORK_WINTER = None
FILE_NETWORK_WEEKEND = None
PROVIDER_CHARGE = None

FILE_CFG = "/home/pi/spotprice/spotprice.cfg"

OPTIONS = ["PriceLimitLower", "PriceLimitUpper", "BuzzerDuration", "UpdateInterval", "FileNetworkSummer",
           "FileNetworkWinter", "FileNetworkWeekend"]


def read(filename):
    conf = configparser.ConfigParser()
    conf.read(filename)

    spotprice = conf["Spotprice"]
    network = conf["Network"]

    global PRICE_LIMIT_LOWER, PRICE_LIMIT_UPPER, BUZZER_DURATION, UPDATE_INTERVAL, FILE_NETWORK_SUMMER, \
    FILE_NETWORK_WINTER, FILE_NETWORK_WEEKEND, PROVIDER_CHARGE

    PRICE_LIMIT_LOWER = float(spotprice["PriceLimitLower"])
    PRICE_LIMIT_UPPER = float(spotprice["PriceLimitUpper"])
    BUZZER_DURATION = float(spotprice["BuzzerDuration"])
    UPDATE_INTERVAL = float(spotprice["UpdateInterval"])
    PROVIDER_CHARGE = float(network["ProviderCharge"])
    FILE_NETWORK_SUMMER = network["FileNetworkSummer"]
    FILE_NETWORK_WINTER = network["FileNetworkWinter"]
    FILE_NETWORK_WEEKEND = network["FileNetworkWeekend"]


def main():
    read(FILE_CFG)

main()