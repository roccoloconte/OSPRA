from abc import ABC, abstractmethod
from typing import Optional
import numpy as np

class Expert(ABC):
    
    @abstractmethod
    def __init__(self, key: str):
        pass

    @abstractmethod
    def query(self, source: np.array([], dtype=float), destination: np.array([], dtype=float),
              departure: Optional[str] = None, compute_path: Optional[bool] = False):
        pass

    @staticmethod
    @abstractmethod
    def _parse_request(response: dict):
        pass