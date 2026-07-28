"""
AI Product Ideation Module for aegisScout.

Generates 2-3 tailored software product ideas for each discovered business,
including pricing estimates, build timelines, and AI build prompts.

Inspired by Gropector's AI ideation feature.
"""
from __future__ import annotations

import json
from typing import Dict, Any, List, Optional
from aegisScout.utils.logger import get_logger

logger = get_logger("ai.product_ideation")


PRODUCT_IDEATION_PROMPT = """
Sen bir dijital ajans satış stratejisti ve yazılım ürün tasarımcısısın.
Aşağıdaki işletme için 2-3 adet özgün ve SATIŞ YAPILABILIR yazılım ürünü veya dijital hizmet fikri üret.

İşletme Bilgileri:
- Ad: {business_name}
- Sektör: {sector}
- Konum: {location}
- Web Sitesi: {has_website}
- Instagram: {has_instagram}
- Değerlendirme: {rating}
- Yorum Sayısı: {reviews_count}
- Mevcut Sorunlar: {audit_notes}

Her fikir için şu formatta JSON döndür (sadece JSON, başka bir şey değil):
{{
  "ideas": [
    {{
      "title": "Ürün/Hizmet Başlığı",
      "description": "2-3 cümle açıklama - neden bu işletme için uygun, ne sorunlarını çözüyor",
      "price_range": "₺X.000 - ₺Y.000",
      "build_time": "X-Y hafta",
      "type": "website|app|automation|design|seo|crm",
      "priority": "high|medium|low",
      "pitch_hook": "Kapıda söylenecek tek cümlelik satış kancası",
      "build_prompt": "Bu ürünü başka bir AI'a inşa ettirmek için kullanılacak kısa brief"
    }}
  ],
  "recommended_approach": "Bu müşteri için en iyi ilk adım önerisi"
}}

Kurallar:
- Gerçekçi fiyatlar ver (Türkiye pazarı için)
- Ürünler sektöre özel olsun (genel şeyler değil)
- Web sitesi yoksa mutlaka bir web sitesi fikrini dahil et
- Pitch hook tek cümle, doğal dil, satış jargonu yok
- JSON dışında HİÇBİR şey yazma
"""


async def generate_product_ideas(
    lead: Dict[str, Any],
    llm_client,
    language: str = "tr"
) -> Dict[str, Any]:
    """
    Generate AI-powered product ideas for a specific lead/business.
    
    Args:
        lead: Lead dict with business details
        llm_client: AegisScout LLM client instance
        language: Output language ('tr' for Turkish, 'en' for English)
    
    Returns:
        Dict with 'ideas' list and 'recommended_approach'
    """
    business_name = lead.get("business_name", "Bilinmiyor")
    sector = lead.get("sector", lead.get("category", "Genel İşletme"))
    location = lead.get("city") or lead.get("address") or lead.get("location", "Belirtilmemiş")
    has_website = "Evet" if lead.get("website") else "Hayır (Büyük Fırsat!)"
    has_instagram = "Evet" if (lead.get("instagram_url") or lead.get("instagram_username")) else "Hayır"
    rating = lead.get("rating", lead.get("google_rating", "Yok"))
    reviews_count = lead.get("reviews_count", lead.get("google_reviews_count", 0))
    
    # Get audit notes from research
    audit_notes_raw = lead.get("ai_analysis", lead.get("research_notes", ""))
    if isinstance(audit_notes_raw, list):
        audit_notes = "; ".join(str(n) for n in audit_notes_raw[:3])
    else:
        audit_notes = str(audit_notes_raw)[:300] if audit_notes_raw else "Mevcut audit notu yok"
    
    prompt = PRODUCT_IDEATION_PROMPT.format(
        business_name=business_name,
        sector=sector,
        location=location,
        has_website=has_website,
        has_instagram=has_instagram,
        rating=rating,
        reviews_count=reviews_count,
        audit_notes=audit_notes
    )
    
    logger.info(f"Generating product ideas for: {business_name}")
    
    try:
        response = await llm_client.complete(prompt, max_tokens=1500)
        
        # Parse JSON response
        response_text = response.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
        
        result = json.loads(response_text)
        logger.info(f"Generated {len(result.get('ideas', []))} product ideas for {business_name}")
        return result
        
    except json.JSONDecodeError as e:
        logger.warning(f"Product ideation JSON parse error for {business_name}: {e}")
        # Fallback: return generic ideas based on sector
        return _fallback_ideas(business_name, sector, has_website == "Hayır (Büyük Fırsat!)")
    except Exception as e:
        logger.error(f"Product ideation failed for {business_name}: {e}")
        return _fallback_ideas(business_name, sector, has_website == "Hayır (Büyük Fırsat!)")


def _fallback_ideas(business_name: str, sector: str, no_website: bool) -> Dict[str, Any]:
    """Generate generic fallback ideas when LLM is unavailable."""
    ideas = []
    
    if no_website:
        ideas.append({
            "title": f"{sector.title()} için Profesyonel Web Sitesi",
            "description": f"{business_name} için müşteri çeken, mobil uyumlu, SEO optimize edilmiş modern web sitesi.",
            "price_range": "₺3.500 - ₺8.000",
            "build_time": "2-4 hafta",
            "type": "website",
            "priority": "high",
            "pitch_hook": f"Google'da aratıldığında {business_name} çıkmıyor, bunu çözelim.",
            "build_prompt": f"Build a professional website for {business_name}, a {sector} business in Turkey."
        })
    
    ideas.append({
        "title": "Online Randevu ve Müşteri Yönetim Sistemi",
        "description": f"{sector} işletmeleri için online randevu alma, müşteri takibi ve otomatik hatırlatma sistemi.",
        "price_range": "₺5.000 - ₺12.000",
        "build_time": "3-6 hafta",
        "type": "app",
        "priority": "medium",
        "pitch_hook": "Telefona bakmak yerine müşteriler kendisi randevu alsın.",
        "build_prompt": f"Build an appointment booking system for a {sector} business."
    })
    
    return {
        "ideas": ideas,
        "recommended_approach": f"{business_name} için web sitesi ile başlamak en mantıklı ilk adım."
    }


def format_product_ideas_html(ideas_data: Dict[str, Any]) -> str:
    """
    Format product ideas as HTML for display in the GUI.
    """
    ideas = ideas_data.get("ideas", [])
    recommended = ideas_data.get("recommended_approach", "")
    
    if not ideas:
        return "<p>Ürün fikri oluşturulamadı.</p>"
    
    html_parts = []
    
    priority_colors = {"high": "#22c55e", "medium": "#f59e0b", "low": "#6b7280"}
    type_icons = {
        "website": "🌐", "app": "📱", "automation": "🤖",
        "design": "🎨", "seo": "🔍", "crm": "📊"
    }
    
    for i, idea in enumerate(ideas):
        priority = idea.get("priority", "medium")
        p_color = priority_colors.get(priority, "#6b7280")
        icon = type_icons.get(idea.get("type", ""), "💡")
        
        html_parts.append(f"""
<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);
  border-radius:12px;padding:16px;margin-bottom:12px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
    <h3 style="margin:0;font-size:1rem;color:var(--text-main,#fff);">
      {icon} {idea.get('title', 'Ürün Fikri')}
    </h3>
    <span style="background:{p_color};color:#000;padding:2px 8px;border-radius:999px;font-size:0.7rem;font-weight:700;">
      {priority.upper()}
    </span>
  </div>
  <p style="font-size:0.85rem;color:var(--text-muted,#aaa);margin:0 0 10px 0;">{idea.get('description', '')}</p>
  <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:0.8rem;">
    <span>💰 <b>{idea.get('price_range', 'N/A')}</b></span>
    <span>⏱️ <b>{idea.get('build_time', 'N/A')}</b></span>
  </div>
  <div style="margin-top:10px;padding:10px;background:rgba(168,85,247,0.1);border-radius:8px;border-left:3px solid #a855f7;">
    <span style="font-size:0.8rem;color:#a855f7;font-weight:600;">💬 Satış Kancası:</span><br>
    <span style="font-size:0.85rem;color:var(--text-main,#fff);font-style:italic;">"{ idea.get('pitch_hook', '') }"</span>
  </div>
</div>""")
    
    if recommended:
        html_parts.append(f"""
<div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);
  border-radius:10px;padding:12px;margin-top:8px;">
  <span style="font-size:0.8rem;color:#818cf8;font-weight:600;">🎯 Önerilen Yaklaşım:</span><br>
  <span style="font-size:0.85rem;color:var(--text-main,#fff);">{recommended}</span>
</div>""")
    
    return "\n".join(html_parts)


__all__ = [
    "generate_product_ideas",
    "format_product_ideas_html",
    "_fallback_ideas",
]
