"""
Module de navigation pour smart-glasses.
"""
from .navigation_module import NavigationModule, NavigationState

# Importations simples sans try/except complexes
try:
    from .fusion.eoh import EgocentricOccupancyHistogram
except ImportError:
    EgocentricOccupancyHistogram = None

try:
    from .decision.priority_engine import PriorityEngine
except ImportError:
    PriorityEngine = None

try:
    from .adapters.camera_adapter import CameraAdapter
except ImportError:
    CameraAdapter = None

try:
    from .adapters.hc_sr04_adapter import UltrasonicAdapter
except ImportError:
    UltrasonicAdapter = None

__version__ = "1.0.0"
__all__ = [
    'NavigationModule',
    'NavigationState',
    'EgocentricOccupancyHistogram',
    'PriorityEngine',
    'CameraAdapter',
    'UltrasonicAdapter'
]