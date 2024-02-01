from pathlib import Path
from typing import Optional
from client import Client
from direction import Direction
import flexpolyline as fp
from abstract import Expert
import numpy as np
import json
import traceback

class MapQuest(Expert):
    
    def __init__(self, key: str):
        self.key = key
        self.base_url = "https://www.mapquestapi.com/directions/v2/route"
        self.client = Client(base_url=self.base_url)
    
    def query(self, source: np.array([], dtype=float), destination: np.array([], dtype=float),
              departure: Optional[str] = None, compute_path: Optional[bool] = False):
        # For more information, visit https://developer.mapquest.com/documentation/directions-api/route/get
        
        params = {} 
        params["from"] = str(source[0])+","+str(source[1])
        params["to"] = str(destination[0])+","+str(destination[1])
        params["key"] = self.key
        params["ambiguities"] ="ignore"
        params["doReverseGeocode"] = "false"
        params["narrativeType"] = "none"
        params["unit"] = "k"
        params["manMaps"] = "false"
        params["routeType"] = "fastest"
        params["shapeFormat"] = "raw"
        params["timeType"] = "1"
        params["useTraffic"] = "true"

        if compute_path:
            params["fullShape"] = "true"
        else:
            params["fullShape"] = "false"            

        if departure:
            params["timeType"] = "2"
            # ISO 8601-format (e.g, 2023-10-31T10:37)
            params["isoLocal"] = departure

        return self._parse_request(self.client.request_get(base_url=self.base_url, params=params,
                                                           headers={"Content-Type": "application/json"}), compute_path)
    
    @staticmethod
    def _parse_request(response: dict, compute_path: bool):
        try:
            distance = response["route"]["distance"]
            # From Km to m
            distance = round(distance * 1000)
            duration = response["route"]["realTime"]
            
            if compute_path:
                points = np.array(response["route"]["shape"]["shapePoints"], dtype=float)
                # We have an array of [lat1, lng1, lat2, lng2, ...]
                path = np.array([], dtype = str)
                for i in range(points.shape[0]):
                    if i == len(points)-1:
                        break
                    elif i%2 == 0:
                        lat = points[i]
                        lng = points[i+1]
                        enc_node = fp.encode(np.array([lat, lng], dtype=float), 6)
                        path = np.append(path, enc_node)
                
                return Direction(distance, duration, path)
            else:
                return Direction(distance, duration)
        except:
            Path("mapquest.json").write_text(json.dumps(response, indent=4))
            print(traceback.format_exc())
            print("Please visit: https://developer.mapquest.com/documentation/directions-api/status-codes")
            return None