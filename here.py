from pathlib import Path
from typing import Optional
from client import Client
from direction import Direction
import flexpolyline as fp
from abstract import Expert
import numpy as np
import json
import traceback

class Here(Expert):

    def __init__(self, key: str):
        self.key = key
        self.base_url = "https://router.hereapi.com/v8/routes"
        self.client = Client(base_url=self.base_url)

    def query(self, source: np.array([], dtype=float), destination: np.array([], dtype=float),
              departure: Optional[str] = None, compute_path: Optional[bool] = False):
        # For more information, visit https://developer.here.com/documentation/routing-api/api-reference-swagger.html

        params = {}
        params["origin"] = str(source[0])+","+str(source[1])
        params["destination"] = str(destination[0])+","+str(destination[1])
        params["apiKey"] = self.key
        params["transportMode"] = "car"
        params["routingMode"] = "fast"

        if compute_path:
            params["return"] = "travelSummary,polyline"
        else:
            params["return"] = "travelSummary"

        if departure:
            # RFC 3339-format (e.g., 1996-12-19T16:39:57, 1996-12-19T16:39:57-08:00)
            params["departureTime"] = departure
        
        return self._parse_request(self.client.request_get(base_url=self.base_url, params=params,
                                                           headers={"Content-Type": "application/json"}), compute_path)

    @staticmethod
    def _parse_request(response: dict, compute_path: bool):
        try:  
            distance = response["routes"][0]["sections"][0]["travelSummary"]["length"]
            duration = response["routes"][0]["sections"][0]["travelSummary"]["duration"]

            if compute_path:
                polyline = response["routes"][0]["sections"][0]["polyline"]
                # polyline is a single string that encoded the entire path
                points = fp.decode(polyline, is_here=True)
                # points is a 2-dimensional array of [[lat0, lng0], [lat1, lng1], ...]

                path = np.array([], dtype=str)
                for node in points:
                    lat = node[0]
                    lng = node[1]
                    enc_node = fp.encode(np.array([lat, lng], dtype=float), 6)
                    path = np.append(path, enc_node)

                # path is a 1-dimensional array of polylines [polyline0, polyline1, ...]

                return Direction(distance, duration, path)
            else:
                return Direction(distance, duration)
        except:
            Path("here.json").write_text(json.dumps(response, indent=4))
            print(traceback.format_exc())           
            return None