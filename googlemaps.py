from pathlib import Path
from typing import Optional
from client import Client
from direction import Direction
import flexpolyline as fp
from abstract import Expert
import numpy as np
import json
import traceback

class GoogleMaps(Expert):

    def __init__(self, key: str):
        self.key = key
        self.base_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        self.client = Client(base_url=self.base_url)

    def query(self, source: np.array([], dtype=float), destination: np.array([], dtype=float),
              departure: Optional[str] = None, compute_path: Optional[bool] = False):
        # For more information, visit https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRoutes

        key = self.key
        
        params = {}
        params["origin"]["location"]["latLng"]["latitude"] = str(source[0])
        params["origin"]["location"]["latLng"]["longitude"] = str(source[1])
        params["destination"]["location"]["latLng"]["latitude"] = str(destination[0])
        params["destination"]["location"]["latLng"]["longitude"] = str(destination[1])
        params["travelMode"] = "DRIVE"
        params["routingPreference"] = "TRAFFIC_AWARE_OPTIMAL"
        params["computeAlternativeRoutes"] = "false"
        params["units"] = "METRIC"
        params["polylineQuality"] = "HIGH_QUALITY",
        params["polylineEncoding"] = "GEO_JSON_LINESTRING"

        if compute_path:
            # TODO
            # Probably, you need to modify X-Goog-FieldMask
            pass

        # RFC 3339-format in UTC (e.g., 2014-10-02T15:01:23Z)
        if departure:
            params["departureTime"] = departure

        return self._parse_request(self.client.request_post(base_url=self.base_url, params=params, 
                                                       headers={"Content-Type": "application/json",
                                                               "X-Goog-Api-Key": key,
                                                               "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.legs.steps"}), compute_path)

    @staticmethod
    def _parse_request(response: dict, compute_path: bool):
        try:  
            distance = response["routes"][0]["distanceMeters"]
            duration = response["routes"][0]["duration"]
        
            if compute_path:
                path = np.array([], dtype = str)
                for node in response["routes"][0]["legs"][0]["steps"]:
                    # TODO
                    # Option 1
                    lat = node["polyline"]["geoJsonLinestring"]["latitude"]
                    # Option 2
                    lat = node["end_location"]["latLng"]["latitude"]
                    # Option 1
                    lng = node["polyline"]["geoJsonLinestring"]["longitude"]
                    # Option 2
                    lng = node["end_location"]["latLng"]["longitude"]
                    # After you understood which is correct, set X-Goog-FieldMask to: "routes.legs.steps.polyline.geoJsonLinestring" or "routes.legs.steps.end_location"
                    path = np.append(path, fp.encode(np.array([lat, lng], dtype=float), 6, False))
                return Direction(distance, duration, path)
            else:
                return Direction(distance, duration)
        except:
            Path("googlemaps.json").write_text(json.dumps(response, indent=4))
            print(traceback.format_exc())
            print("Please visit: https://cloud.google.com/apis/design/errors")
            return None