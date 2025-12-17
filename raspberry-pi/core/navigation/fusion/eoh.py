class EgocentricOccupancyHistogram:
    """Histogramme d'occupation égocentrique (EOH)."""
    
    def __init__(self, bins=13):
        self.bins = bins
        self.histogram = [{'min_distance': float('inf')} for _ in range(bins)]
        print("✓ EOH initialisé avec", bins, "bins")
    
    def update(self, detections):
        print(f"EOH mis à jour avec {len(detections)} détections")
        # Implémentation temporaire
        return True
    
    def get_snapshot(self):
        return {'bins': self.bins, 'state': 'actif'}