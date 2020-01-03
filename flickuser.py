# Written by Matthew Northcott
# 30 December 2019


__author__ = "Matthew Northcott"


# IMPORTS
import requests


# GLOBALS
URL_TOKEN = "https://api.flick.energy/identity/oauth/token"
URL_PRICE = "https://api.flick.energy/customer/mobile_provider/price"

FIELD_GRANT_TYPE = 'password'
FIELD_CLIENT_ID = 'le37iwi3qctbduh39fvnpevt1m2uuvz'
FIELD_CLIENT_SECRET = 'ignwy9ztnst3azswww66y9vd9zt6qnt'


# PROGRAM
class FlickUser(object):
    price = 0.0
    spot_price = 0.0

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self._params = {
            'grant_type': FIELD_GRANT_TYPE,
            'client_id': FIELD_CLIENT_ID,
            'client_secret': FIELD_CLIENT_SECRET,
            'username': self.username,
            'password': self.password,
        }

    """Fetches price values from Flick Electric"""
    def update(self):
        res = requests.post(URL_TOKEN, data=self._params)
        if res.status_code != 200:
            return
        tokens = res.json()
        if tokens.get('error') is not None:
            return

        res = requests.get(URL_PRICE, headers={'Authorization': "Bearer " + tokens['id_token']})
        if res.status_code != 200:
            return
        result = res.json()
        if result.get('error') is not None:
            return

        components = result['needle']['components']

        self.price = float(result['needle']['price'])
        self.spot_price = sum(float(c['value']) for c in components if c['charge_method'] == "spot_price")