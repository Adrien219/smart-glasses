"""
Planificateur de guidage pour la navigation.
Décide des directions à suggérer pour éviter les obstacles.
"""
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple

from ..fusion.eoh import EOHSnapshot

logger = logging.getLogger(__name__)

class GuidancePlanner:
    """Planificateur de directions pour éviter les obstacles."""
    
    def __init__(self, clear_path_threshold: float = 150.0,
                 min_safe_angle: float = 20.0,
                 preferred_direction: str = 'right'):
        """
        Initialise le planificateur de guidage.
        
        Args:
            clear_path_threshold: Distance minimale pour un chemin dégagé (cm)
            min_safe_angle: Angle minimum pour considérer un virage sécuritaire (degrés)
            preferred_direction: Direction préférée ('left' ou 'right')
        """
        self.clear_path_threshold = clear_path_threshold
        self.min_safe_angle = min_safe_angle
        self.preferred_direction = 1 if preferred_direction == 'right' else -1
        
        # Cache pour les décisions récentes
        self.last_guidance = None
        self.last_guidance_time = 0
        
        logger.info(f"GuidancePlanner initialisé: seuil={clear_path_threshold}cm, "
                   f"angle_min={min_safe_angle}°, préférence={'droite' if preferred_direction == 'right' else 'gauche'}")
    
    def get_guidance(self, eoh_snapshot: EOHSnapshot) -> Dict:
        """
        Calcule la meilleure direction à suggérer.
        
        Args:
            eoh_snapshot: Snapshot de l'EOH
            
        Returns:
            Dictionnaire avec la suggestion de guidage
        """
        import time
        current_time = time.time()
        
        # Vérifier si on a besoin de recalculer
        if (self.last_guidance and 
            current_time - self.last_guidance_time < 0.5):  # Cache de 500ms
            return self.last_guidance
        
        # Initialiser la réponse par défaut
        guidance = {
            'action': 'none',
            'clear_distance': 0.0,
            'direction_angle': 0.0,
            'confidence': 0.0,
            'reason': 'no_obstacle'
        }
        
        # Analyser la grille d'occupation
        occupancy_grid = eoh_snapshot.get_occupancy_grid(self.clear_path_threshold)
        
        # Trouver les chemins dégagés
        clear_paths = eoh_snapshot.get_clear_paths(self.clear_path_threshold)
        
        # Si aucun obstacle dans le seuil
        if not any(clear_paths):
            guidance['action'] = 'continue'
            guidance['clear_distance'] = self.clear_path_threshold
            guidance['confidence'] = 1.0
            guidance['reason'] = 'path_clear'
            self.last_guidance = guidance
            self.last_guidance_time = current_time
            return guidance
        
        # Analyser la situation d'obstacle
        min_distance = eoh_snapshot.min_distance
        closest_bearing = eoh_snapshot.closest_bearing
        
        if min_distance is None:
            # Pas d'obstacle détecté
            guidance['action'] = 'continue'
            guidance['reason'] = 'no_obstacles'
            self.last_guidance = guidance
            self.last_guidance_time = current_time
            return guidance
        
        # Situation critique - obstacle très proche
        if min_distance < 50:
            return self._handle_critical_situation(eoh_snapshot, current_time)
        
        # Trouver le meilleur chemin alternatif
        best_direction = self._find_best_direction(
            eoh_snapshot, occupancy_grid, clear_paths)
        
        if best_direction:
            angle, clear_distance, confidence = best_direction
            
            # Déterminer l'action
            if abs(angle) < self.min_safe_angle:
                # Chemin presque droit devant
                if clear_distance > min_distance * 1.5:
                    guidance['action'] = 'move_slightly'
                    direction = 'right' if angle > 0 else 'left'
                    guidance['direction_angle'] = angle
                    guidance['reason'] = f'slightly_{direction}'
                else:
                    guidance['action'] = 'slow_down'
                    guidance['reason'] = 'narrow_path'
            else:
                # Virage nécessaire
                guidance['action'] = 'move_left' if angle < 0 else 'move_right'
                guidance['direction_angle'] = abs(angle)
                guidance['reason'] = 'clear_path_found'
            
            guidance['clear_distance'] = clear_distance
            guidance['confidence'] = confidence
        
        else:
            # Aucun chemin dégagé trouvé
            guidance['action'] = 'stop'
            guidance['reason'] = 'no_clear_path'
            guidance['confidence'] = 0.8
        
        self.last_guidance = guidance
        self.last_guidance_time = current_time
        return guidance
    
    def _handle_critical_situation(self, eoh_snapshot: EOHSnapshot, 
                                  current_time: float) -> Dict:
        """Gère une situation critique (obstacle très proche)."""
        # Recherche urgente d'un chemin de sortie
        bin_distances = eoh_snapshot.get_bin_distances()
        bin_centers = eoh_snapshot.bin_centers
        
        # Chercher la direction avec la plus grande distance
        max_distance = 0.0
        best_angle = 0.0
        
        for i, distance in enumerate(bin_distances):
            if distance is not None and distance > max_distance:
                max_distance = distance
                best_angle = bin_centers[i]
        
        if max_distance > 80:  # Au moins 80cm de clearance
            return {
                'action': 'move_left' if best_angle < 0 else 'move_right',
                'clear_distance': max_distance,
                'direction_angle': abs(best_angle),
                'confidence': 0.7,
                'reason': 'critical_escape'
            }
        else:
            return {
                'action': 'stop',
                'clear_distance': max_distance,
                'direction_angle': 0.0,
                'confidence': 0.9,
                'reason': 'critical_no_escape'
            }
    
    def _find_best_direction(self, eoh_snapshot: EOHSnapshot,
                            occupancy_grid: np.ndarray,
                            clear_paths: List[bool]) -> Optional[Tuple[float, float, float]]:
        """
        Trouve la meilleure direction alternative.
        
        Returns:
            Tuple (angle, clear_distance, confidence) ou None
        """
        bin_centers = eoh_snapshot.bin_centers
        bin_distances = eoh_snapshot.get_bin_distances()
        
        # Préparer les scores pour chaque direction
        scores = []
        
        for i, is_clear in enumerate(clear_paths):
            angle = bin_centers[i]
            distance = bin_distances[i] if bin_distances[i] is not None else float('inf')
            
            # Score basé sur plusieurs facteurs
            if is_clear:
                # Facteur 1: Distance de clearance
                distance_score = min(1.0, distance / self.clear_path_threshold)
                
                # Facteur 2: Angle par rapport à la direction préférée
                if self.preferred_direction > 0:  # Préfère droite
                    angle_score = 1.0 - abs(angle - 30) / 60  # Préfère 30° à droite
                else:  # Préfère gauche
                    angle_score = 1.0 - abs(angle + 30) / 60  # Préfère 30° à gauche
                
                # Facteur 3: Éviter les angles trop extrêmes
                extremity_score = 1.0 - abs(angle) / 60  # Pénalise les angles > 60°
                
                # Score combiné
                combined_score = (
                    distance_score * 0.5 +
                    angle_score * 0.3 +
                    extremity_score * 0.2
                )
                
                scores.append((angle, distance, combined_score))
        
        if not scores:
            return None
        
        # Trier par score décroissant
        scores.sort(key=lambda x: x[2], reverse=True)
        
        # Retourner la meilleure direction
        best_angle, best_distance, best_score = scores[0]
        
        # Ajuster la confiance basée sur le score
        confidence = min(0.95, best_score * 1.2)
        
        return (best_angle, best_distance, confidence)
    
    def suggest_immediate_action(self, eoh_snapshot: EOHSnapshot) -> str:
        """
        Suggère une action immédiate (pour feedback rapide).
        
        Returns:
            Chaîne d'action: 'stop', 'left', 'right', 'slow', 'continue'
        """
        guidance = self.get_guidance(eoh_snapshot)
        
        action_map = {
            'stop': 'stop',
            'move_left': 'left',
            'move_right': 'right',
            'slow_down': 'slow',
            'move_slightly': 'continue',
            'continue': 'continue'
        }
        
        return action_map.get(guidance['action'], 'continue')
    
    def get_safe_directions(self, eoh_snapshot: EOHSnapshot, 
                           min_clearance: float = 100.0) -> List[float]:
        """
        Retourne la liste des directions sécuritaires.
        
        Args:
            eoh_snapshot: Snapshot de l'EOH
            min_clearance: Distance minimale requise
            
        Returns:
            Liste des angles sécuritaires en degrés
        """
        safe_directions = []
        bin_distances = eoh_snapshot.get_bin_distances()
        bin_centers = eoh_snapshot.bin_centers
        
        for i, distance in enumerate(bin_distances):
            if distance is None or distance >= min_clearance:
                safe_directions.append(bin_centers[i])
        
        return safe_directions
    
    def update_preferences(self, clear_path_threshold: Optional[float] = None,
                          min_safe_angle: Optional[float] = None,
                          preferred_direction: Optional[str] = None):
        """Met à jour les préférences de guidage."""
        if clear_path_threshold is not None:
            self.clear_path_threshold = max(50, clear_path_threshold)
        
        if min_safe_angle is not None:
            self.min_safe_angle = max(5, min(45, min_safe_angle))
        
        if preferred_direction is not None:
            if preferred_direction.lower() in ['right', 'droite']:
                self.preferred_direction = 1
            elif preferred_direction.lower() in ['left', 'gauche']:
                self.preferred_direction = -1
        
        logger.info(f"Préférences mises à jour: seuil={self.clear_path_threshold}cm, "
                   f"angle={self.min_safe_angle}°, direction={'droite' if self.preferred_direction > 0 else 'gauche'}")
    
    def get_configuration(self) -> Dict:
        """Retourne la configuration actuelle."""
        return {
            'clear_path_threshold': self.clear_path_threshold,
            'min_safe_angle': self.min_safe_angle,
            'preferred_direction': 'right' if self.preferred_direction > 0 else 'left',
            'last_guidance': self.last_guidance,
            'last_guidance_time': self.last_guidance_time
        }