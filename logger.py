__author__ = "Matthew Northcott"

# Spot Pricer
# Created by Matthew Northcott
# 27-02-2016
# Python 3.4.3

# IMPORTS
import datetime

# GLOBALS

# MAIN
class Logger(object):
    def __init__(self, filename, is_verbose=True, timestamp_format="%Y-%m-%d %H:%M:%S.%f"):
        self.filename = filename
        self.is_verbose = is_verbose
        self.timestamp_format = timestamp_format

        # Create the file
        with open(self.filename, 'a'):
            pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        del self

    def write(self, message):
        timestamp = datetime.datetime.now().strftime(self.timestamp_format)
        line = "[ {timestamp} ] {message}\n".format(timestamp=timestamp, message=message)
        with open(self.filename, 'a') as log:
            log.write(line)
        if self.is_verbose:
            print(line, end="")