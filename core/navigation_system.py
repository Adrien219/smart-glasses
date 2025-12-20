import geopy.distance
from geopy.geocoders import Nominatim
import threading
import time

class NavigationSystem:
    def __init__(self, voice_assistant):
        self.voice_assistant = voice_assistant
        self.geolocator = Nominatim(user_agent="smart_glasses")
        self.current_location = None
        self.destination = None
        self.navigation_active = False
        
    def set_destination(self, address):
        """Définir une destination par adresse"""
        try:
            location = self.geolocator.geocode(address)
            if location:
                self.destination = (location.latitude, location.longitude)
                self.voice_assistant.speak(f"Destination définie: {address}")
                return True
        except Exception as e:
            print(f"❌ Erreur géocodage: {e}")
        return False
    
    def calculate_distance(self, coord1, coord2):
        """Calculer la distance entre deux points"""
        return geopy.distance.distance(coord1, coord2).meters
    
    def get_direction_guidance(self, current_lat, current_lon):
        """Obtenir des instructions de navigation"""
        if not self.destination:
            return "Aucune destination définie"
        
        current_coords = (current_lat, current_lon)
        distance = self.calculate_distance(current_coords, self.destination)
        
        if distance < 10:  # 10 mètres
            return "Vous êtes arrivé à destination"
        elif distance < 50:  # 50 mètres
            return f"Destination dans {int(distance)} mètres"
        else:
            return f"Continuez tout droit, {int(distance)} mètres restants"