__author__ = "Matthew Northcott"

# Spot Pricer
# Created by Matthew Northcott
# 27-02-2016
# Python 3.4.3

# IMPORTS
import urllib.request, urllib.error
import re
import threading
import time
import queue

# GLOBALS
HEADERS = {'User-Agent': 'Mozilla/5.0'}

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

    def _open(self, request, q):
        try:
            response = urllib.request.urlopen(request).read()
        except urllib.error.URLError:
            response = None
        q.put(response)

    def open(self, timeout=10.0):
        q = queue.Queue()
        request = urllib.request.Request(self.url, headers=HEADERS)

        thr = threading.Thread(target=self._open, args=(request, q))
        thr.start()

        t = 0
        while t < timeout and thr.is_alive():
            time.sleep(0.10)
            t += 0.10

        if thr.is_alive():
            del thr
            return False

        response = q.get()
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