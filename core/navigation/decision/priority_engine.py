"""
Moteur de priorité pour les alertes de navigation.
"""
import time
import logging
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Classes locales pour éviter les imports circulaires
class NavigationState(Enum):
    IDLE = "idle"
    SCANNING = "scanning"
    ALERT = "alert"
    GUIDANCE = "guidance"
    EMERGENCY = "emergency"
    RECOVER = "recover"

class AlertPriority(Enum):
    EMERGENCY = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4

class AlertType(Enum):
    OBSTACLE_EMERGENCY = "obstacle_emergency"
    OBSTACLE_ALERT = "obstacle_alert"
    OBSTACLE_WARNING = "obstacle_warning"
    DIRECTION_GUIDANCE = "direction_guidance"
    APPROACHING_OBJECT = "approaching_object"
    PATH_CLEAR = "path_clear"
    SYSTEM_INFO = "system_info"

@dataclass
class Decision:
    action_needed: bool = False
    message: str = ""
    priority: int = 0
    suggested_action: str = ""
    alert_type: str = ""
    confidence: float = 0.0
    new_state: Optional[NavigationState] = None

class PriorityEngine:
    def __init__(self, emergency_dist: float = 35.0, alert_dist: float = 100.0,
                 warning_dist: float = 200.0, min_vocal_interval: float = 2.5):
        self.emergency_dist = emergency_dist
        self.alert_dist = alert_dist
        self.warning_dist = warning_dist
        self.min_vocal_interval = min_vocal_interval
        
        logger.info(f"PriorityEngine initialisé")
    
    def evaluate(self, eoh_snapshot, current_state: NavigationState = NavigationState.SCANNING) -> Decision:
        current_time = time.time()
        decision = Decision(
            action_needed=False,
            message="",
            priority=AlertPriority.INFO.value,
            suggested_action="continue",
            alert_type=AlertType.SYSTEM_INFO.value,
            confidence=0.0,
            new_state=None
        )
        
        if eoh_snapshot.min_distance is None:
            return decision
        
        min_distance = eoh_snapshot.min_distance
        
        if min_distance < self.emergency_dist:
            decision.action_needed = True
            decision.message = f"Attention! Obstacle très proche à {int(min_distance)} cm. Arrêtez!"
            decision.priority = AlertPriority.EMERGENCY.value
            decision.alert_type = AlertType.OBSTACLE_EMERGENCY.value
            decision.new_state = NavigationState.EMERGENCY
            
        elif min_distance < self.alert_dist:
            decision.action_needed = True
            decision.message = f"Obstacle à {int(min_distance)} cm. Ralentissez."
            decision.priority = AlertPriority.HIGH.value
            decision.alert_type = AlertType.OBSTACLE_ALERT.value
            decision.new_state = NavigationState.ALERT
            
        elif min_distance < self.warning_dist:
            decision.action_needed = True
            decision.message = f"Obstacle à {int(min_distance)} cm. Prudence."
            decision.priority = AlertPriority.MEDIUM.value
            decision.alert_type = AlertType.OBSTACLE_WARNING.value
            decision.new_state = NavigationState.SCANNING
        
        return decision