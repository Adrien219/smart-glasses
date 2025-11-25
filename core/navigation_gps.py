# core/navigation_gps.py

import geopy.distance
from geopy.geocoders import Nominatim

class NavigationGPS:
    def __init__(self, voice_assistant):
        self.voice = voice_assistant
        self.geolocator = Nominatim(user_agent="smart_glasses")
        self.destination = None

    def set_destination(self, address):
        try:
            loc = self.geolocator.geocode(address)
            if loc:
                self.destination = (loc.latitude, loc.longitude)
                self.voice.say(f"Destination définie : {address}")
                return True
        except:
            pass
        return False

    def distance_remaining(self, current_lat, current_lon):
        if not self.destination:
            return None

        return geopy.distance.distance(
            (current_lat, current_lon),
            self.destination
        ).meters
