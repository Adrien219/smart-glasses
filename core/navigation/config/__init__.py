"""
Module de navigation pour smart-glasses.
Fournit une navigation fiable et réactive pour personnes malvoyantes.
"""

from .navigation_module import NavigationModule, NavigationState
from .fusion.eoh import EgocentricOccupancyHistogram
from .decision.priority_engine import PriorityEngine
from .adapters.camera_adapter import CameraAdapter
from .adapters.hc_sr04_adapter import UltrasonicAdapter

__version__ = "1.0.0"
__all__ = [
    'NavigationModule',
    'NavigationState',
    'EgocentricOccupancyHistogram',
    'PriorityEngine',
    'CameraAdapter',
    'UltrasonicAdapter'
]