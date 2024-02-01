import requests
import traceback
from urllib.parse import urlencode

class Client():

    def __init__(self, base_url: str):
        self.base_url = base_url
    
    @staticmethod
    def _generate_url(base_url: str, params: dict):
        # Encode the string into URL (e.g., replace "," with %2C)
        full_url = base_url + "?" + requests.utils.unquote_unreserved(urlencode(params))
        return full_url

    def request_get(self, base_url: str, params: dict, headers: dict):
        full_url = self._generate_url(base_url, params)
        try:
            response = requests.get(full_url, headers=headers)
            return response.json()
        except:
            print(traceback.format_exc())
            return None
    
    def request_post(self, full_url: str, params: dict, headers: dict):
        try:
            response = requests.post(full_url, headers=headers, data=params)
            return response.json()
        except:
            print(traceback.format_exc())
            return None