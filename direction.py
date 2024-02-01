from typing import Optional
import numpy as np

class Direction(object):
    
    def __init__(self, distance: float, duration: float, path: Optional[np.ndarray] = None):
        self._distance = distance
        self._duration = duration
        self._path = path

    @property
    def distance(self):
        return self._distance

    @property
    def duration(self):
        return self._duration

    @property
    def path(self):
        return self._path