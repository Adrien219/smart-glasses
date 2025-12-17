"""
Package perception - Détection d'objets et OCR
"""

# N'IMPORTE PAS NavigationModule ici !
# Seulement les wrappers de perception

from .yolo_wrapper import ObjectDetector
from .ocr_wrapper import OCRWrapper

__all__ = ['ObjectDetector', 'OCRWrapper']