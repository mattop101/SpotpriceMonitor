# Northcott Monitor
# Written by Matthew Northcott
# 24-06-2018
# Python 3.6

# IMPORTS
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import datetime

# GLOBALS
URL_TOKEN = 'https://api.flick.energy/identity/oauth/token'
URL_PRICE = 'https://api.flick.energy/customer/mobile_provider/price'

FIELD_GRANT_TYPE = 'password'
FIELD_CLIENT_ID = 'le37iwi3qctbduh39fvnpevt1m2uuvz'
FIELD_CLIENT_SECRET = 'ignwy9ztnst3azswww66y9vd9zt6qnt'

# PROGRAM
class FlickUser(object):
    username = ''
    password = ''
    price = 0.0
    spot_price = 0.0
    next_update = None

    def __init__(self, username, password):
        self.username = username
        self.password = password

    """Fetches price values from Flick Electric"""
    def get_price(self):
        post_fields = {
            'grant_type': FIELD_GRANT_TYPE,
            'client_id': FIELD_CLIENT_ID,
            'client_secret': FIELD_CLIENT_SECRET,
            'username': self.username,
            'password': self.password
        }

        try:
            request_token = Request(URL_TOKEN, urlencode(post_fields).encode())
            tokens = json.loads(urlopen(request_token).read().decode())

            request = Request(URL_PRICE, headers={'Authorization': 'Bearer ' + tokens['id_token']})
            response = urlopen(request).read().decode()
            result = json.loads(response)

            components = result['needle']['components']

            self.price = float(result['needle']['price'])
            self.spot_price = sum(float(c['value']) for c in components if c['charge_method'] == 'spot_price')
        except:
            return

    """Updates price fields and determines next update time"""
    def update(self):
        self.get_price()

        now = datetime.datetime.now()

        if now.minute >= 31:
            self.next_update = now.replace(hour=now.hour + 1, minute=1, second=0, microsecond=0)
        else:
            self.next_update = now.replace(minute=31, second=0, microsecond=0)