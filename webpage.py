# Northcott Monitor
# Written by Matthew Northcott
# 20-08-2016
# Python 3.4.3

__author__ = "Matthew Northcott"


# IMPORTS
import urllib.request, urllib.error
import re

# GLOBALS
HEADERS = { 'User-Agent': 'Mozilla/5.0' }

# MAIN
class Webpage(object):
    def __init__(self, url):
        self.url = url
        self.response = None

    def __str__(self):
        return str(self.response)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        del self

    def open(self):
        try:
            request = urllib.request.Request(self.url, headers=HEADERS)
            response = urllib.request.urlopen(request).read()
        except urllib.error.URLError:
            response = None

        if response is None:
            return False

        self.response = response
        return True

    def search(self, regex_term):
        try:
            result = re.search(regex_term, str(self)).group(0)
        except AttributeError:
            return None
        return result

    def find_all(self, regex_term):
        return re.findall(regex_term, str(self))