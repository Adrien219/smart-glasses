"""
Histogramme d'Occupation Égocentrique (Egocentric Occupancy Histogram).
"""
import time
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

@dataclass
class Bin:
    min_distance: float = float('inf')
    last_update: float = 0.0
    confidence: float = 0.0
    object_class: Optional[str] = None

@dataclass
class EOHSnapshot:
    bins: List[Bin]
    min_distance: float
    closest_bearing: float
    timestamp: float
    
    def to_dict(self):
        return {
            'min_distance': self.min_distance if self.min_distance != float('inf') else None,
            'closest_bearing': self.closest_bearing,
            'timestamp': self.timestamp,
            'bins': [
                {
                    'min_distance': b.min_distance if b.min_distance != float('inf') else None,
                    'confidence': b.confidence,
                    'object_class': b.object_class
                }
                for b in self.bins
            ]
        }

class EgocentricOccupancyHistogram:
    def __init__(self, bins: int = 13, fov_deg: float = 62.2, ema_alpha: float = 0.4):
        self.bins = bins
        self.fov = fov_deg
        self.ema_alpha = ema_alpha
        
        self.bin_edges = np.linspace(-fov_deg/2, fov_deg/2, bins + 1)
        self.bin_centers = (self.bin_edges[:-1] + self.bin_edges[1:]) / 2
        self.histogram = [Bin() for _ in range(bins)]
        
        logger.info(f"EOH initialisé avec {bins} bins")

    def update(self, bearing: float, distance: float, confidence: float = 1.0, 
               object_class: Optional[str] = None, timestamp: Optional[float] = None):
        if timestamp is None:
            timestamp = time.time()
        
        # Trouver le bin
        bin_idx = None
        for i in range(self.bins):
            if self.bin_edges[i] <= bearing <= self.bin_edges[i+1]:
                bin_idx = i
                break
        
        if bin_idx is None:
            return
        
        bin_data = self.histogram[bin_idx]
        
        # EMA
        if bin_data.min_distance == float('inf'):
            weighted_distance = distance
            weighted_confidence = confidence
        else:
            time_diff = timestamp - bin_data.last_update
            alpha = self.ema_alpha if time_diff <= 1.0 else 1.0
            
            weighted_distance = alpha * distance + (1 - alpha) * bin_data.min_distance
            weighted_confidence = alpha * confidence + (1 - alpha) * bin_data.confidence
        
        # Mettre à jour
        bin_data.min_distance = weighted_distance
        bin_data.confidence = weighted_confidence
        bin_data.last_update = timestamp
        if object_class:
            bin_data.object_class = object_class
        
        # Nettoyer les vieux bins
        self._clean_old_bins(timestamp)

    def _clean_old_bins(self, current_time: float, max_age: float = 2.0):
        for bin_data in self.histogram:
            if current_time - bin_data.last_update > max_age:
                bin_data.min_distance = float('inf')
                bin_data.confidence = 0.0
                bin_data.object_class = None

    def get_snapshot(self) -> EOHSnapshot:
        current_time = time.time()
        self._clean_old_bins(current_time)
        
        min_distance = float('inf')
        closest_bin_idx = -1
        
        for i, bin_data in enumerate(self.histogram):
            if bin_data.min_distance < min_distance:
                min_distance = bin_data.min_distance
                closest_bin_idx = i
        
        closest_bearing = self.bin_centers[closest_bin_idx] if closest_bin_idx >= 0 else 0.0
        
        return EOHSnapshot(
            bins=self.histogram.copy(),
            min_distance=min_distance if min_distance != float('inf') else None,
            closest_bearing=closest_bearing,
            timestamp=current_time
        )

    def update_ultrasound_only(self, distance: float, angle: float, timestamp: Optional[float] = None):
        """
        Met à jour l'histogramme avec une mesure ultrasonique isolée.
        
        Args:
            distance (float): Distance en mètres.
            angle (float): Angle en degrés (comme bearing).
            timestamp (float, optional): Timestamp. Par défaut, time.time().
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Convertir l'angle en degrés si nécessaire (supposé déjà en degrés)
        # Si ton angle est en radians, utilise: bearing_deg = np.degrees(angle)
        bearing_deg = angle
        
        self.update(
            bearing=bearing_deg,
            distance=distance,
            confidence=1.0,
            object_class="ultrasound",
            timestamp=timestamp
        )
        logger.debug(f"EOH mis à jour par ultrason: angle={bearing_deg:.1f}°, distance={distance:.2f}m")