from pathlib import Path
from typing import Optional
from client import Client
from direction import Direction
import flexpolyline as fp
from abstract import Expert
import numpy as np
import json
import traceback

class AppleMaps(Expert):

    def __init__(self, key: str):
        self.key = key
        self.base_url = "https://maps-api.apple.com/v1/directions"
        self.client = Client(base_url=self.base_url)

    def query(self, source: np.array([], dtype=float), destination: np.array([], dtype=float),
              departure: Optional[str] = None, compute_path: Optional[bool] = False):
        # For more information, visit https://developer.apple.com/documentation/applemapsserverapi/search_for_directions_and_estimated_travel_time_between_locations
        key = self.key

        params = {}
        params["origin"] = str(source[0])+","+str(source[1])
        params["destination"] = str(destination[0])+","+str(destination[1])
        params["transportType"] = "Automobile"

        if compute_path:
            # TODO
            pass

        if departure:
            # ISO 8601-format in UTC (e.g., 2023-04-15T16:42:00Z)
            params["departureDate"] = departure

        return self._parse_request(self.client.request_get(base_url=self.base_url, params=params,
                                                      headers={"Content-Type": "application/json", "Authorization": "Bearer " + key}), compute_path)

    @staticmethod
    def _parse_request(response: dict, compute_path: bool):
        try:
            distance, duration = 0
            for route in response["routes"][0]:
                distance = distance + route["distanceMeters"]
                duration = duration + route["expectedTravelTimeSeconds"]
            
            if compute_path:
                path = np.array([], dtype=str)
                for leg in response["stepPaths"][0]:
                    for node in leg[0]:
                        lat = node["latitude"]
                        lng = node["longitude"]
                        enc_node = fp.encode(np.array([lat, lng], dtype=float), 6, False)
                        path = np.append(path, enc_node)

                return Direction(distance, duration, path)
            else:
                return Direction(distance, duration)
        except:
            Path("applemaps.json").write_text(json.dumps(response, indent=4))
            print(traceback.format_exc())
            print("Please visit: https://developer.apple.com/documentation/applemapsserverapi/search_for_directions_and_estimated_travel_time_between_locations")
            return None