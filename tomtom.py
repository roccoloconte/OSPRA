from pathlib import Path
from typing import Optional
from client import Client
from direction import Direction
import flexpolyline as fp
from abstract import Expert
import numpy as np
import json
import traceback

class TomTom(Expert):

    def __init__(self, key: str):
        self.key = key
        self.base_url = "https://api.tomtom.com/routing/1/calculateRoute/"
        self.client = Client(base_url=self.base_url)
    
    def query(self, source: np.array([], dtype=float), destination: np.array([], dtype=float),
              departure: Optional[str] = None, compute_path: Optional[bool] = False):
        # For more information, visit the GET request for calculateRoute at https://developer.tomtom.com/routing-api/documentation/routing/calculate-route

        params = {}
        params["key"] = self.key
        params["travelMode"] = "car"
        params["routeType"] = "fastest"
        params["traffic"] = "true"

        if compute_path:
            params["routeRepresentation"] = "polyline"
        else:
            params["routeRepresentation"] = "summaryOnly"

        if departure:
            # RFC 3339-format (e.g., 1996-12-19T16:39:57, 1996-12-19T16:39:57-08:00)
            params["departAt"] = departure
        else:
            params["departAt"] = "now"

        str_source = str(source[0])+","+str(source[1])
        str_destination = str(destination[0])+","+str(destination[1])

        url = self.base_url+str_source+":"+str_destination+"/json"

        return self._parse_request(self.client.request_get(base_url=url, params=params,
                                                           headers={"Content-Type": "application/json"}), compute_path)

    @staticmethod
    def _parse_request(response: dict, compute_path: bool):
        try:
            distance = response["routes"][0]["summary"]["lengthInMeters"]
            time = response["routes"][0]["summary"]["travelTimeInSeconds"]
            traffic = response["routes"][0]["summary"]["trafficDelayInSeconds"]
            duration = time + traffic
            
            if compute_path:
                path = np.array([], dtype = str)
                for node in response["routes"][0]["legs"][0]["points"]:
                    lat = node["latitude"]
                    lng = node["longitude"]
                    enc_node = fp.encode(np.array([lat, lng], dtype=float), 6)
                    path = np.append(path, enc_node)
                
                return Direction(distance, duration, path)
            else:
                return Direction(distance, duration)
        except:
            Path("tomtom.json").write_text(json.dumps(response, indent=4))
            print(traceback.format_exc())
            print("Please visit: https://developer.tomtom.com/routing-api/documentation/routing/common-routing-parameters")
            return None