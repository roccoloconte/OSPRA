from pathlib import Path
from typing import Optional
from client import Client
from direction import Direction
import flexpolyline as fp
from abstract import Expert
import numpy as np
import json
import traceback

class BingMaps(Expert):

    def __init__(self, key: str):
        self.key = key
        self.base_url = "http://dev.virtualearth.net/REST/V1/Routes/Driving"
        self.client = Client(base_url=self.base_url)
    
    def query(self, source: np.array([], dtype=float), destination: np.array([], dtype=float),
              departure: Optional[str] = None, compute_path: Optional[bool] = False):
        # For more information, visit https://learn.microsoft.com/en-us/bingmaps/rest-services/routes/calculate-a-route

        params = {}
        params["wp.0"] = str(source[0])+","+str(source[1])
        params["wp.1"] = str(destination[0])+","+str(destination[1])
        params["key"] = self.key
        params["optimize"] = "timeWithTraffic"

        if compute_path:
            params["routeAttributes"] = "routePath,excludeItinerary"
            params["tolerances"] = "0.000001"
        else:
            params["routeAttributes"] = "routeSummariesOnly"    

        if departure:
            # ISO 8601-format (e.g, 2023-10-31T10:37)
            params["timeType"] = "Departure"
            params["dateTime"] = departure
        
        return self._parse_request(self.client.request_get(base_url=self.base_url, params=params,
                                                           headers={"Content-Type": "application/json"}), compute_path)

    @staticmethod
    def _parse_request(response: dict, compute_path: bool):
        try:           
            distance = response["resourceSets"][0]["resources"][0]["travelDistance"]
            # From Km to m
            distance = round(distance * 1000)
            duration = response["resourceSets"][0]["resources"][0]["travelDurationTraffic"]
            
            if compute_path:
                path = np.array([], dtype = str)
                points = np.array(response["resourceSets"][0]["resources"][0]["routePath"]["line"]["coordinates"], dtype=float)
                path = fp.encode(points, 6, True)
                
                return Direction(distance, duration, path)
            else:
                return Direction(distance, duration)
        except:
            Path("bingmaps.json").write_text(json.dumps(response, indent=4))
            print(traceback.format_exc())
            print("Please visit: https://learn.microsoft.com/en-us/bingmaps/rest-services/status-codes-and-error-handling")
            return None