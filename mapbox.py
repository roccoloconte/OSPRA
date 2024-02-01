from pathlib import Path
from typing import Optional
from client import Client
from direction import Direction
import flexpolyline as fp
from abstract import Expert
import numpy as np
import json
import traceback

class Mapbox(Expert):

    def __init__(self, key: str):
        self.key = key
        
        # driving-traffic enables the trafficMode
        self.base_url = "https://api.mapbox.com/directions/v5/mapbox/driving-traffic"
        self.client = Client(base_url=self.base_url)
    
    def query(self, source: np.array([], dtype=float), destination: np.array([], dtype=float),
              departure: Optional[str] = None, compute_path: Optional[bool] = False): 
        # For more information, visit https://docs.mapbox.com/api/navigation/directions/ and https://docs.mapbox.com/api/navigation/http-post/

        url = self.base_url+"?"+"access_token="+self.key
        
        # [lng, lat]-format 
        str_source = str(source[1])+","+str(source[0])
        str_destination = str(destination[1])+","+str(destination[0])

        params = {}
        params["coordinates"] = str_source+";"+str_destination

        if compute_path:
            params["geometries"] = "geojson"
            params["overview"] = "full"
        else:
            params["overview"] = "false"

        if departure:
            # ISO 8601-format (e.g, 2023-10-31T10:37)
            params["depart_at"] = departure
        
        return self._parse_request(self.client.request_post(full_url=url, params=params,
                                                            headers={"Content-Type": "application/x-www-form-urlencoded"}), compute_path)

    @staticmethod
    def _parse_request(response: dict, compute_path: bool):
        try:
            # Round the numbers (e.g., from 31585.699 to 31586) since all the other APIs give rounded numbers
            distance = round(response["routes"][0]["distance"])
            duration = round(response["routes"][0]["duration"])

            if compute_path:
                path = np.array([], dtype=str)
                points = np.array(response["routes"][0]["geometry"]["coordinates"], dtype=float)
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
            Path("mapbox.json").write_text(json.dumps(response, indent=4))
            print(traceback.format_exc())
            return None