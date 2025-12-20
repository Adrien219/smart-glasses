<<<<<<< HEAD
"""
Package perception - Détection d'objets et OCR
"""

# N'IMPORTE PAS NavigationModule ici !
# Seulement les wrappers de perception

from .yolo_wrapper import ObjectDetector
from .ocr_wrapper import OCRWrapper

=======
"""
Package perception - Détection d'objets et OCR
"""

# N'IMPORTE PAS NavigationModule ici !
# Seulement les wrappers de perception

from .yolo_wrapper import ObjectDetector
from .ocr_wrapper import OCRWrapper

>>>>>>> 8b3abaa (Major update: Complete smart glasses system)
__all__ = ['ObjectDetector', 'OCRWrapper']