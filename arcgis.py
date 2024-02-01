from pathlib import Path
from typing import Optional
from client import Client
from direction import Direction
import flexpolyline as fp
from abstract import Expert
import numpy as np
import json
import traceback

class ArcGIS(Expert):

    def __init__(self, key: str):
        self.key = key
        self.base_url = "https://route.arcgis.com/arcgis/rest/services/World/Route/NAServer/Route_World/solve"
        self.client = Client(base_url=self.base_url)
    
    def query(self, source: np.array([], dtype=float), destination: np.array([], dtype=float),
              departure: Optional[str] = None, compute_path: Optional[bool] = False):
        # For more information, visit https://developers.arcgis.com/rest/network/api-reference/route-synchronous-service.htm
        
        # [lng, lat]-format
        str_source = str(source[1])+","+str(source[0])
        str_destination = str(destination[1])+","+str(destination[0])
        params = {}
        params["stops"] = str_source+";"+str_destination
        params["token"] = self.key
        params["f"] = "json"
        params["impedanceAttributeName"] = "TravelTime"
        params["accumulateAttributeNames"] = "Kilometers"
        params["returnDirections"] = "false"
        params["returnRoutes"] = "true"

        if compute_path:
            params["outputLines"] = "esriNAOutputLineTrueShape"
            params["outputGeometryPrecision"] = "0.1"
            params["outputGeometryPrecisionUnits"] = "esriMeters"
        else:
            params["outputLines"] = "esriNAOutputLineNone"

        # UNIX-format (e.g., 1699599600)
        if departure:
            params["startTime"] = departure

        return self._parse_request(self.client.request_get(base_url=self.base_url, params=params,
                                                           headers={"Content-Type": "application/json"}), compute_path)

    @staticmethod
    def _parse_request(response: dict, compute_path: bool):
        try:
            distance = response["routes"]["features"][0]["attributes"]["Total_Kilometers"]
            # From Km to m
            distance = round(distance * 1000)
            duration = response["routes"]["features"][0]["attributes"]["Total_TravelTime"]
            # From minutes to seconds
            duration = round(duration * 60)
            
            if compute_path:
                path = np.array([], dtype=str)
                points = np.array(response["routes"]["features"][0]["geometry"]["paths"][0], dtype=float)
                # points is an array of [[lng1, lat1], [lng2, lat2], ...]
                
                for p in points:
                    lat = p[1]
                    lng = p[0]
                    enc_node = fp.encode(np.array([lat, lng], dtype=float), 6)
                    path = np.append(path, enc_node)
            
                return Direction(distance, duration, path)
            else:
                return Direction(distance, duration)
        except:
            Path("arcgis.json").write_text(json.dumps(response, indent=4))
            print(traceback.format_exc())
            return None