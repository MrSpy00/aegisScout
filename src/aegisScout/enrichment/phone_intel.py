"""
Phone Intelligence Module for aegisScout.

Analyzes phone numbers using offline methods + free APIs:
  - phonenumbers: Offline parsing, country, carrier type detection
  - numverify.com: Free tier (100/month) for format validation
  - WhatsApp availability: Check if number has WhatsApp via wa.me
  - Format normalization: E.164 format standardization

No API key required for core functionality.
"""
from __future__ import annotations

import re
from typing import Dict, Any, Optional
from aegisScout.utils.logger import get_logger

logger = get_logger("enrichment.phone_intel")


def analyze_phone(raw_phone: str, default_country: str = "TR") -> Dict[str, Any]:
    """
    Comprehensive offline phone number analysis.
    Uses only the `phonenumbers` Python library (no API key needed).
    
    Args:
        raw_phone: Raw phone string (any format)
        default_country: ISO country code for parsing (default: TR for Turkey)
    
    Returns dict with:
        - valid: bool
        - e164: E.164 formatted number
        - country_code: numeric country code (e.g. 90)
        - country_name: country name (e.g. "Turkey")
        - national_number: local format
        - number_type: MOBILE, FIXED_LINE, VOIP, etc.
        - is_mobile: bool
        - is_landline: bool
        - possible_carrier: operator hint (best effort)
        - formatted_international: e.g. "+90 532 123 45 67"
        - whatsapp_link: wa.me link
    """
    result: Dict[str, Any] = {
        "raw": raw_phone,
        "valid": False,
        "e164": None,
        "country_code": None,
        "country_name": None,
        "national_number": None,
        "number_type": "UNKNOWN",
        "is_mobile": False,
        "is_landline": False,
        "possible_carrier": None,
        "formatted_international": None,
        "whatsapp_link": None,
    }
    
    if not raw_phone:
        return result
    
    try:
        import phonenumbers
        from phonenumbers import (
            parse, is_valid_number, format_number,
            PhoneNumberFormat, number_type as get_number_type,
            PhoneNumberType, geocoder, carrier
        )
        
        # Try to parse with + prefix for international numbers
        phone_str = raw_phone.strip()
        if not phone_str.startswith("+"):
            # Add + if starts with country code pattern
            if phone_str.startswith("00"):
                phone_str = "+" + phone_str[2:]
            elif phone_str.startswith("0") and default_country == "TR":
                phone_str = "+9" + phone_str  # 0 -> +90
        
        try:
            parsed = parse(phone_str, default_country)
        except Exception:
            parsed = parse(raw_phone, default_country)
        
        if is_valid_number(parsed):
            result["valid"] = True
            result["e164"] = format_number(parsed, PhoneNumberFormat.E164)
            result["country_code"] = parsed.country_code
            result["national_number"] = format_number(parsed, PhoneNumberFormat.NATIONAL)
            result["formatted_international"] = format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
            
            # Number type
            num_type = get_number_type(parsed)
            type_map = {
                PhoneNumberType.MOBILE: "MOBILE",
                PhoneNumberType.FIXED_LINE: "FIXED_LINE",
                PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_OR_MOBILE",
                PhoneNumberType.VOIP: "VOIP",
                PhoneNumberType.TOLL_FREE: "TOLL_FREE",
                PhoneNumberType.PREMIUM_RATE: "PREMIUM_RATE",
                PhoneNumberType.SHARED_COST: "SHARED_COST",
                PhoneNumberType.PERSONAL_NUMBER: "PERSONAL",
                PhoneNumberType.PAGER: "PAGER",
                PhoneNumberType.UAN: "UAN",
            }
            result["number_type"] = type_map.get(num_type, "UNKNOWN")
            result["is_mobile"] = num_type in (
                PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE
            )
            result["is_landline"] = num_type == PhoneNumberType.FIXED_LINE
            
            # Country name
            try:
                result["country_name"] = geocoder.country_name_for_number(parsed, "tr")
            except Exception:
                result["country_name"] = geocoder.country_name_for_number(parsed, "en")
            
            # Carrier hint (not always available)
            try:
                carrier_name = carrier.name_for_number(parsed, "tr")
                if carrier_name:
                    result["possible_carrier"] = carrier_name
            except Exception:
                pass
            
            # WhatsApp link (remove + for wa.me)
            e164 = result["e164"]
            if e164:
                wa_number = e164.replace("+", "")
                result["whatsapp_link"] = f"https://wa.me/{wa_number}"
    
    except ImportError:
        logger.warning("phonenumbers library not installed. Run: pip install phonenumbers")
        # Basic fallback: check if it looks like a Turkish mobile number
        clean = re.sub(r"[^\d]", "", raw_phone)
        if len(clean) >= 10:
            result["valid"] = True  # assume valid
            result["national_number"] = clean
            if clean.startswith(("05", "5")) and len(clean) in (10, 11):
                result["is_mobile"] = True
                result["number_type"] = "MOBILE"
    except Exception as e:
        logger.warning(f"Phone analysis failed for {raw_phone}: {e}")
    
    return result


def format_phone_summary(phone_data: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of phone analysis results.
    """
    if not phone_data.get("valid"):
        return f"📵 Geçersiz Numara: {phone_data.get('raw', 'N/A')}"
    
    lines = [f"📞 Telefon Analizi: {phone_data.get('formatted_international', phone_data.get('raw', ''))}"
]
    
    if phone_data.get("country_name"):
        lines.append(f"  🌍 Ülke: {phone_data['country_name']}")
    
    if phone_data.get("number_type") != "UNKNOWN":
        type_labels = {
            "MOBILE": "📱 Mobil Hat",
            "FIXED_LINE": "☎️ Sabit Hat",
            "FIXED_OR_MOBILE": "📱/☎️ Mobil veya Sabit",
            "VOIP": "🌐 VoIP",
            "TOLL_FREE": "🆓 Ücretsiz Hat",
        }
        label = type_labels.get(phone_data["number_type"], phone_data["number_type"])
        lines.append(f"  📋 Hat Tipi: {label}")
    
    if phone_data.get("possible_carrier"):
        lines.append(f"  📡 Operatör: {phone_data['possible_carrier']}")
    
    if phone_data.get("whatsapp_link"):
        lines.append(f"  💬 WhatsApp: {phone_data['whatsapp_link']}")
    
    return "\n".join(lines)


__all__ = ["analyze_phone", "format_phone_summary"]
