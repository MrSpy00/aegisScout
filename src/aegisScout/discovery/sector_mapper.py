"""
Sector → URL Slug Mapper for aegisScout Turkish Directory Providers.

Maps user-entered sector keywords to the correct URL slugs used by each
Turkish directory site (Bulurum, Haritane, Tikla, Find.com.tr).

Supports fuzzy matching so "psikolog", "Psikolog", "psikoloji" all resolve
to the correct slugs.
"""
from __future__ import annotations

import re
from typing import Dict, Optional, List

# ---------------------------------------------------------------------------
# Master sector mapping table
# Format: "canonical_key": {
#     "bulurum": "slug-for-bulurum.com/search/",
#     "haritane": "slug-for-haritane.com/kategori/",
#     "tikla": "slug-for-tikla.com.tr/sektorler/",
#     "find": "SLUG-FOR-find.com.tr/Search/",
# }
# ---------------------------------------------------------------------------
_SECTOR_MAP: Dict[str, Dict[str, str]] = {
    # ── Sağlık ──────────────────────────────────────────────────────────────
    "psikolog": {
        "bulurum": "psikologlar",
        "haritane": "psikolog",
        "tikla": "psikolog",
        "find": "PSIKOLOG",
    },
    "diyetisyen": {
        "bulurum": "diyetisyenler",
        "haritane": "diyetisyen",
        "tikla": "diyetisyen",
        "find": "DIYETISYEN",
    },
    "doktor": {
        "bulurum": "doktorlar",
        "haritane": "doktor",
        "tikla": "doktor",
        "find": "DOKTOR",
    },
    "hekim": {
        "bulurum": "doktorlar",
        "haritane": "doktor",
        "tikla": "doktor",
        "find": "DOKTOR",
    },
    "diş hekimi": {
        "bulurum": "dis-hekimleri",
        "haritane": "dis-hekimi",
        "tikla": "dis-poliklinigi",
        "find": "DIS-HEKIMI",
    },
    "diş": {
        "bulurum": "dis-hekimleri",
        "haritane": "dis-hekimi",
        "tikla": "dis-poliklinigi",
        "find": "DIS-HEKIMI",
    },
    "dişçi": {
        "bulurum": "dis-hekimleri",
        "haritane": "dis-hekimi",
        "tikla": "dis-poliklinigi",
        "find": "DIS-HEKIMI",
    },
    "eczane": {
        "bulurum": "eczaneler",
        "haritane": "eczane",
        "tikla": "eczane",
        "find": "ECZANE",
    },
    "veteriner": {
        "bulurum": "veterinerler",
        "haritane": "veteriner",
        "tikla": "veteriner",
        "find": "VETERINER",
    },
    "fizyoterapist": {
        "bulurum": "fizyoterapistler",
        "haritane": "fizyoterapist",
        "tikla": "fizyoterapi",
        "find": "FIZYOTERAPIST",
    },
    "optisyen": {
        "bulurum": "optisyenler",
        "haritane": "optisyen",
        "tikla": "optisyen",
        "find": "OPTISYEN",
    },
    "hastane": {
        "bulurum": "hastaneler",
        "haritane": "hastane",
        "tikla": "hastane",
        "find": "HASTANE",
    },
    "klinik": {
        "bulurum": "klinikler",
        "haritane": "klinik",
        "tikla": "klinik",
        "find": "KLINIK",
    },
    "hemşire": {
        "bulurum": "hemsireler",
        "haritane": "hemsire",
        "tikla": "hemsire",
        "find": "HEMSIRE",
    },

    # ── Hukuk & Finans ───────────────────────────────────────────────────────
    "avukat": {
        "bulurum": "avukatlar",
        "haritane": "avukat",
        "tikla": "avukat",
        "find": "AVUKAT",
    },
    "noterlik": {
        "bulurum": "noterler",
        "haritane": "noter",
        "tikla": "noter",
        "find": "NOTER",
    },
    "muhasebeci": {
        "bulurum": "muhasebe-burosu",
        "haritane": "muhasebe",
        "tikla": "muhasebe",
        "find": "MUHASEBE",
    },
    "mali müşavir": {
        "bulurum": "mali-musavirler",
        "haritane": "mali-musavir",
        "tikla": "mali-musavir",
        "find": "MALI-MUSAVIR",
    },
    "banka": {
        "bulurum": "bankalar",
        "haritane": "banka",
        "tikla": "banka",
        "find": "BANKA",
    },
    "sigorta": {
        "bulurum": "sigorta-acenteleri",
        "haritane": "sigorta",
        "tikla": "sigorta",
        "find": "SIGORTA",
    },

    # ── Güzellik & Kişisel Bakım ─────────────────────────────────────────────
    "kuaför": {
        "bulurum": "kuaforler",
        "haritane": "kuafor",
        "tikla": "bayan-kuafor",
        "find": "KUAFOR",
    },
    "güzellik merkezi": {
        "bulurum": "guzellik-salonlari",
        "haritane": "guzellik-merkezi",
        "tikla": "guzellik-merkezi",
        "find": "GUZELLIK-MERKEZI",
    },
    "berber": {
        "bulurum": "berberler",
        "haritane": "berber",
        "tikla": "berber",
        "find": "BERBER",
    },
    "spa": {
        "bulurum": "spa-merkezleri",
        "haritane": "spa",
        "tikla": "spa",
        "find": "SPA",
    },
    "masaj": {
        "bulurum": "masaj-salonlari",
        "haritane": "masaj",
        "tikla": "masaj",
        "find": "MASAJ",
    },
    "güzellik salonu": {
        "bulurum": "guzellik-salonlari",
        "haritane": "guzellik-merkezi",
        "tikla": "guzellik-merkezi",
        "find": "GUZELLIK-SALONU",
    },
    "epilasyon": {
        "bulurum": "epilasyon-merkezleri",
        "haritane": "epilasyon",
        "tikla": "epilasyon",
        "find": "EPILASYON",
    },

    # ── Eğitim ──────────────────────────────────────────────────────────────
    "okul": {
        "bulurum": "okullar",
        "haritane": "okul",
        "tikla": "okul",
        "find": "OKUL",
    },
    "dershane": {
        "bulurum": "dershaneler",
        "haritane": "dershane",
        "tikla": "dershane",
        "find": "DERSHANE",
    },
    "kurs": {
        "bulurum": "kurslar",
        "haritane": "kurs",
        "tikla": "kurs",
        "find": "KURS",
    },
    "anaokulu": {
        "bulurum": "anaokullari",
        "haritane": "anaokulu",
        "tikla": "anaokulu",
        "find": "ANAOKULU",
    },
    "kreş": {
        "bulurum": "kresler",
        "haritane": "kres",
        "tikla": "kres",
        "find": "KRES",
    },
    "üniversite": {
        "bulurum": "universiteler",
        "haritane": "universite",
        "tikla": "universite",
        "find": "UNIVERSITE",
    },

    # ── Yeme & İçme ─────────────────────────────────────────────────────────
    "restoran": {
        "bulurum": "restoranlar",
        "haritane": "restoran",
        "tikla": "restoran",
        "find": "RESTORAN",
    },
    "kafe": {
        "bulurum": "kafeler",
        "haritane": "kafe",
        "tikla": "kafe",
        "find": "KAFE",
    },
    "pastane": {
        "bulurum": "pastaneler",
        "haritane": "pastane",
        "tikla": "pastane",
        "find": "PASTANE",
    },
    "fırın": {
        "bulurum": "firinlar",
        "haritane": "firin",
        "tikla": "firin",
        "find": "FIRIN",
    },
    "pizza": {
        "bulurum": "pizza-restoranlar",
        "haritane": "pizza",
        "tikla": "pizza",
        "find": "PIZZA",
    },

    # ── Konaklama ────────────────────────────────────────────────────────────
    "otel": {
        "bulurum": "oteller",
        "haritane": "otel",
        "tikla": "otel",
        "find": "OTEL",
    },
    "pansiyon": {
        "bulurum": "pansiyonlar",
        "haritane": "pansiyon",
        "tikla": "pansiyon",
        "find": "PANSIYON",
    },

    # ── Spor & Fitness ───────────────────────────────────────────────────────
    "spor salonu": {
        "bulurum": "spor-salonlari",
        "haritane": "spor-salonu",
        "tikla": "spor-salonu",
        "find": "SPOR-SALONU",
    },
    "gym": {
        "bulurum": "spor-salonlari",
        "haritane": "spor-salonu",
        "tikla": "spor-salonu",
        "find": "GYM",
    },
    "yüzme havuzu": {
        "bulurum": "yuzme-havuzlari",
        "haritane": "yuzme-havuzu",
        "tikla": "yuzme-havuzu",
        "find": "YUZME-HAVUZU",
    },

    # ── Perakende & Alışveriş ────────────────────────────────────────────────
    "pet shop": {
        "bulurum": "pet-shoplar",
        "haritane": "pet-shop",
        "tikla": "evcil-hayvan",
        "find": "PET-SHOP",
    },
    "market": {
        "bulurum": "marketler",
        "haritane": "market",
        "tikla": "market",
        "find": "MARKET",
    },
    "çiçekçi": {
        "bulurum": "cicekcilik",
        "haritane": "cicekci",
        "tikla": "cicekci",
        "find": "CICEKCI",
    },
    "kırtasiye": {
        "bulurum": "kirtasiyeler",
        "haritane": "kirtasiye",
        "tikla": "kirtasiye",
        "find": "KIRTASIYE",
    },

    # ── Teknik & Hizmet ──────────────────────────────────────────────────────
    "elektrikçi": {
        "bulurum": "elektrikciler",
        "haritane": "elektrikci",
        "tikla": "elektrik",
        "find": "ELEKTRIKCI",
    },
    "tesisatçı": {
        "bulurum": "tesisatcilar",
        "haritane": "tesisatci",
        "tikla": "tesisat",
        "find": "TESISATCI",
    },
    "boyacı": {
        "bulurum": "boyacilar",
        "haritane": "boyaci",
        "tikla": "boya",
        "find": "BOYACI",
    },
    "nakliyat": {
        "bulurum": "nakliyat-firmalari",
        "haritane": "nakliyat",
        "tikla": "nakliyat",
        "find": "NAKLIYAT",
    },
    "temizlik": {
        "bulurum": "temizlik-firmalari",
        "haritane": "temizlik",
        "tikla": "ev-temizligi",
        "find": "TEMIZLIK",
    },
    "çilingir": {
        "bulurum": "cilingirler",
        "haritane": "cilingir",
        "tikla": "cilingir",
        "find": "CILINGIR",
    },

    # ── Otomotiv ─────────────────────────────────────────────────────────────
    "oto servis": {
        "bulurum": "oto-servisleri",
        "haritane": "oto-servis",
        "tikla": "oto-servis",
        "find": "OTO-SERVIS",
    },
    "oto yıkama": {
        "bulurum": "oto-yikamalar",
        "haritane": "oto-yikama",
        "tikla": "oto-yikama",
        "find": "OTO-YIKAMA",
    },
    "lastikçi": {
        "bulurum": "lastikcilik",
        "haritane": "lastikci",
        "tikla": "lastik",
        "find": "LASTIKCI",
    },

    # ── İnşaat & Emlak ───────────────────────────────────────────────────────
    "emlak": {
        "bulurum": "emlak-ofisleri",
        "haritane": "emlak",
        "tikla": "emlak",
        "find": "EMLAK",
    },
    "mimar": {
        "bulurum": "mimarlar",
        "haritane": "mimar",
        "tikla": "mimar",
        "find": "MIMAR",
    },
    "iç mimar": {
        "bulurum": "ic-mimarlar",
        "haritane": "ic-mimar",
        "tikla": "ic-mimarlik",
        "find": "IC-MIMAR",
    },

    # ── Teknoloji ────────────────────────────────────────────────────────────
    "bilgisayar tamiri": {
        "bulurum": "bilgisayar-tamir",
        "haritane": "bilgisayar-servis",
        "tikla": "bilgisayar-tamir",
        "find": "BILGISAYAR-TAMIR",
    },
    "web tasarım": {
        "bulurum": "web-tasarim-firmalari",
        "haritane": "web-tasarim",
        "tikla": "web-tasarim",
        "find": "WEB-TASARIM",
    },
    "yazılım": {
        "bulurum": "yazilim-firmalari",
        "haritane": "yazilim",
        "tikla": "yazilim",
        "find": "YAZILIM",
    },

    # ── Diğer ────────────────────────────────────────────────────────────────
    "fotoğrafçı": {
        "bulurum": "fotografcilar",
        "haritane": "fotografci",
        "tikla": "fotografci",
        "find": "FOTOGRAFCI",
    },
    "düğün salonu": {
        "bulurum": "dugun-salonlari",
        "haritane": "dugun-salonu",
        "tikla": "dugun-salonu",
        "find": "DUGUN-SALONU",
    },
    "organizasyon": {
        "bulurum": "organizasyon-firmalari",
        "haritane": "organizasyon",
        "tikla": "organizasyon",
        "find": "ORGANIZASYON",
    },
}

# ---------------------------------------------------------------------------
# Alias table: maps common alternative spellings to canonical keys
# ---------------------------------------------------------------------------
_ALIASES: Dict[str, str] = {
    "psikoloji": "psikolog",
    "terapist": "psikolog",
    "terapi": "psikolog",
    "danışman": "psikolog",
    "aile danışmanı": "psikolog",
    "pratisyen": "doktor",
    "uzman doktor": "doktor",
    "tabip": "doktor",
    "dişhekimi": "diş hekimi",
    "dishekimi": "diş hekimi",
    "diş kliniği": "diş hekimi",
    "dental": "diş hekimi",
    "muhasebe": "muhasebeci",
    "mali müşavirlik": "mali müşavir",
    "mali musavir": "mali müşavir",
    "hukuk bürosu": "avukat",
    "hukuk": "avukat",
    "fitness": "spor salonu",
    "jimnastik": "spor salonu",
    "evcil hayvan": "pet shop",
    "petshop": "pet shop",
    "kafe restoran": "kafe",
    "cafe": "kafe",
    "servis": "oto servis",
    "araba tamir": "oto servis",
    "emlakçı": "emlak",
    "gayrimenkul": "emlak",
    "kurye": "nakliyat",
    "taşımacılık": "nakliyat",
    "kreche": "kreş",
    "kreş yuvası": "kreş",
    "university": "üniversite",
    "lise": "okul",
    "ilkokul": "okul",
    "fotoğraf": "fotoğrafçı",
    "kuafor": "kuaför",
    "photo": "fotoğrafçı",
    "photography": "fotoğrafçı",
    "güzellik": "güzellik merkezi",
    "kozmetik": "güzellik merkezi",
    "bayan kuafor": "kuaför",
    "erkek kuafor": "berber",
    "erkek berber": "berber",
    "oto": "oto servis",
    "otomotiv": "oto servis",
    "sigorta acente": "sigorta",
    "noterlik": "noterlik",
    "noterde": "noterlik",
    "bakkal": "market",
    "supermarket": "market",
    "süpermarket": "market",
    "pizza salonu": "pizza",
    "hamburger": "restoran",
    "fast food": "restoran",
    "yüzme": "yüzme havuzu",
    "havuz": "yüzme havuzu",
    "fizik tedavi": "fizyoterapist",
    "fizik terapi": "fizyoterapist",
    "rehabilitasyon": "fizyoterapist",
    "temizlik şirketi": "temizlik",
    "ev temizleme": "temizlik",
    "boyacılık": "boyacı",
    "elektrik": "elektrikçi",
    "tesisat": "tesisatçı",
    "çiçek": "çiçekçi",
}


def normalize(text: str) -> str:
    """Lowercase + strip accents for fuzzy matching."""
    text = text.lower().strip()
    replacements = {
        "ı": "i", "ğ": "g", "ü": "u", "ş": "s", "ö": "o", "ç": "c",
        "İ": "i", "Ğ": "g", "Ü": "u", "Ş": "s", "Ö": "o", "Ç": "c",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def get_slug(sector: str, provider: str) -> Optional[str]:
    """
    Return the URL slug for a given sector and provider.

    Args:
        sector:   User-entered sector keyword (e.g. "psikolog", "Psikolog", "psikoloji")
        provider: One of "bulurum", "haritane", "tikla", "find"

    Returns:
        The slug string, or None if no mapping found.
    """
    sector_clean = sector.strip().lower()

    # 1. Direct lookup
    if sector_clean in _SECTOR_MAP:
        return _SECTOR_MAP[sector_clean].get(provider)

    # 2. Alias lookup
    canonical = _ALIASES.get(sector_clean)
    if canonical and canonical in _SECTOR_MAP:
        return _SECTOR_MAP[canonical].get(provider)

    # 3. Fuzzy: check if sector is a substring of any canonical key
    for key, slugs in _SECTOR_MAP.items():
        if sector_clean in key or key in sector_clean:
            return slugs.get(provider)

    # 4. Fuzzy: normalized (accent-stripped) comparison
    sector_norm = normalize(sector_clean)
    for key, slugs in _SECTOR_MAP.items():
        if normalize(key) == sector_norm:
            return slugs.get(provider)
    for alias, canonical in _ALIASES.items():
        if normalize(alias) == sector_norm and canonical in _SECTOR_MAP:
            return _SECTOR_MAP[canonical].get(provider)

    # 5. Last resort: auto-generate a basic plural slug
    # e.g. "muayenehane" → "muayenehaneler"
    return None


def get_all_slugs(sector: str) -> Dict[str, Optional[str]]:
    """Return slugs for all providers for a given sector."""
    return {
        "bulurum": get_slug(sector, "bulurum"),
        "haritane": get_slug(sector, "haritane"),
        "tikla": get_slug(sector, "tikla"),
        "find": get_slug(sector, "find"),
    }


def auto_slugify(sector: str) -> str:
    """
    Auto-generate a URL-safe slug when no mapping exists.
    Replaces spaces with hyphens, removes special characters.
    """
    slug = normalize(sector.lower().strip())
    slug = re.sub(r"[^a-z0-9\-]", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def get_slug_or_auto(sector: str, provider: str) -> str:
    """
    Return known slug or auto-generate one if not in the map.
    Never returns None.
    """
    return get_slug(sector, provider) or auto_slugify(sector)


__all__ = [
    "get_slug",
    "get_slug_or_auto",
    "get_all_slugs",
    "auto_slugify",
    "normalize",
    "_SECTOR_MAP",
]
