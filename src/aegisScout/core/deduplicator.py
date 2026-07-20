"""
Lead Deduplication Engine for aegisScout (N1).
Detects potential duplicate business leads using fuzzy string matching and geographic coordinate proximity.
"""
from typing import List, Tuple, Dict, Any
from sqlmodel import Session, select
from aegisScout.core.database import engine
from aegisScout.core.models import Lead
from aegisScout.utils.logger import get_logger

logger = get_logger("core.deduplicator")

def _calculate_fuzzy_ratio(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings (0.0 to 1.0)."""
    s1, s2 = str1.lower().strip(), str2.lower().strip()
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    
    # Try rapidfuzz if installed, else difflib fallback
    try:
        from rapidfuzz import fuzz
        return fuzz.token_sort_ratio(s1, s2) / 100.0
    except ImportError:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, s1, s2).ratio()

def _calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance between two coordinates in meters."""
    import math
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_duplicates(threshold: float = 0.85, max_distance_m: float = 50.0) -> List[Dict[str, Any]]:
    """Scan stored leads and return list of duplicate candidate pairs."""
    duplicates = []
    with Session(engine) as session:
        leads = session.exec(select(Lead)).all()
        n = len(leads)
        logger.info(f"Scanning {n} leads for duplicates with threshold {threshold}...")
        
        for i in range(n):
            for j in range(i + 1, n):
                lead_a, lead_b = leads[i], leads[j]
                
                # Check name similarity
                name_score = _calculate_fuzzy_ratio(lead_a.business_name, lead_b.business_name)
                
                # Check location proximity if coordinates exist
                is_close = False
                dist_m = None
                lat_a = getattr(lead_a, "latitude", None) or getattr(lead_a, "lat", None)
                lng_a = getattr(lead_a, "longitude", None) or getattr(lead_a, "lng", None)
                lat_b = getattr(lead_b, "latitude", None) or getattr(lead_b, "lat", None)
                lng_b = getattr(lead_b, "longitude", None) or getattr(lead_b, "lng", None)
                if lat_a and lng_a and lat_b and lng_b:
                    dist_m = _calculate_distance_meters(float(lat_a), float(lng_a), float(lat_b), float(lng_b))
                    if dist_m <= max_distance_m:
                        is_close = True
                
                if name_score >= threshold or (name_score >= 0.70 and is_close):
                    duplicates.append({
                        "lead_a": lead_a.dict(),
                        "lead_b": lead_b.dict(),
                        "name_score": round(name_score, 3),
                        "distance_m": round(dist_m, 1) if dist_m is not None else None,
                        "match_reason": "High name similarity" if name_score >= threshold else "Proximity + name similarity"
                    })
                    
    logger.info(f"Found {len(duplicates)} potential duplicate lead pairs.")
    return duplicates

def merge_leads(primary_id: int, duplicate_id: int) -> bool:
    """Merge duplicate lead into primary lead and remove duplicate."""
    with Session(engine) as session:
        primary = session.get(Lead, primary_id)
        duplicate = session.get(Lead, duplicate_id)
        if not primary or not duplicate:
            return False
            
        # Enrich primary lead with missing attributes from duplicate
        if not primary.email and duplicate.email:
            primary.email = duplicate.email
        if not primary.phone and duplicate.phone:
            primary.phone = duplicate.phone
        if not primary.instagram_handle and duplicate.instagram_handle:
            primary.instagram_handle = duplicate.instagram_handle
        if not primary.website_url and duplicate.website_url:
            primary.website_url = duplicate.website_url
            
        session.delete(duplicate)
        session.commit()
        logger.info(f"Merged lead ID {duplicate_id} into primary lead ID {primary_id}.")
        return True
