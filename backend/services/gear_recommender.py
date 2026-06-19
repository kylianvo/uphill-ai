from typing import List, Dict, Any
from db import query_shoes_catalog

class GearRecommender:
    @staticmethod
    def recommend_shoes(
        surface: str,        # 'road', 'trail'
        cushioning: str,     # 'plush', 'balanced', 'firm'
        width: str           # 'wide', 'normal', 'narrow'
    ) -> List[Dict[str, Any]]:
        """
        Recommends shoes by querying the database catalog.
        Falls back gracefully if no exact matching combination is found.
        """
        surface = surface.lower().strip()
        cushioning = cushioning.lower().strip()
        width = width.lower().strip()
        
        # Safe-guard parameters
        if surface not in ("road", "trail"):
            surface = "trail"
        if cushioning not in ("plush", "balanced", "firm"):
            cushioning = "balanced"
        if width not in ("wide", "normal", "narrow"):
            width = "normal"
            
        return query_shoes_catalog(surface, cushioning, width)
