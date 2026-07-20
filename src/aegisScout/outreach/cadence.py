"""
Multi-Step AI Sequence Builder and Cadence Engine for aegisScout.
Renders dynamic personalized email templates with variable substitution.
"""
import re
from typing import Dict, Any, List, Optional
from aegisScout.core.models import Lead
from aegisScout.utils.logger import get_logger

logger = get_logger("outreach.cadence")


DEFAULT_STEP_1_TEMPLATE = {
    "step": 1,
    "delay_days": 0,
    "subject": "Sayın {{company}} Yetkilisi - {{industry}} İçin Performans İyileştirme Önerileri",
    "body": (
        "Merhaba {{first_name}},\n\n"
        "{{company}} web sitenizi inceledik ve dijital varlığınızda tespit ettiğimiz "
        "önemli bir konuyu paylaşmak istedik: {{website_flaw}}.\n\n"
        "AegisScout Yapay Zeka Analizimize göre işletmeniz {{custom_ai_score}}/100 potansiyel skora sahiptir. "
        "Bu konuda kısa bir görüşme yapabilir miyiz?\n\n"
        "Saygılarımızla,\nAegisScout Ekibi"
    ),
}

DEFAULT_STEP_2_TEMPLATE = {
    "step": 2,
    "delay_days": 3,
    "subject": "Takip: {{company}} İçin Özel Teklifimiz",
    "body": (
        "Merhaba {{first_name}},\n\n"
        "3 gün önce {{company}} için gönderdiğimiz e-postayı takip etmek istedim. "
        "Sitenizdeki {{website_flaw}} problemini çözerek dönüşüm oranlarınızı belirgin şekilde artırabiliriz.\n\n"
        "Sizin için 10 dakikalık bir demo organize edelim mi?\n\n"
        "İyi çalışmalar."
    ),
}

DEFAULT_STEP_3_TEMPLATE = {
    "step": 3,
    "delay_days": 7,
    "subject": "{{company}} İçin Son Değer Değerlendirmesi",
    "body": (
        "Merhaba {{first_name}},\n\n"
        "{{company}} için hazırladığımız özel analiz raporumuz hazır. "
        "Sektörünüz olan {{industry}} alanındaki rakiplerinizle kıyaslandığında yüksek büyüme fırsatı görüyoruz.\n\n"
        "Eğer ilgilenirseniz doğrudan bu e-postaya yanıt verebilirsiniz.\n\n"
        "Başarılar dileriz."
    ),
}


class AISequenceBuilder:
    """Builds and renders multi-step outreach cadences."""

    @staticmethod
    def render_template(template_str: str, lead: Lead, custom_vars: Optional[Dict[str, Any]] = None) -> str:
        """
        Replace template variables like {{first_name}}, {{company}}, {{website_flaw}} etc.
        """
        if not template_str:
            return ""

        context = {
            "first_name": lead.business_name.split()[0] if lead.business_name else "Yetkili",
            "company": lead.business_name or "Şirketiniz",
            "industry": lead.category or "İşletme",
            "website_flaw": lead.outreach_hook or lead.broken_links_details or "web sitesi hız ve mobil optimize eksikliği",
            "custom_ai_score": str(int(lead.score)) if lead.score else "85",
            "city": lead.city or "Türkiye",
            "phone": lead.phone or "",
            "domain": lead.domain or "",
        }
        if custom_vars:
            context.update(custom_vars)

        rendered = template_str
        for key, val in context.items():
            pattern = re.compile(r"\{\{\s*" + re.escape(key) + r"\s*\}\}", re.IGNORECASE)
            rendered = pattern.sub(str(val), rendered)

        return rendered

    @staticmethod
    def get_default_sequence() -> List[Dict[str, Any]]:
        """Return standard 3-step AI email sequence templates."""
        return [
            DEFAULT_STEP_1_TEMPLATE.copy(),
            DEFAULT_STEP_2_TEMPLATE.copy(),
            DEFAULT_STEP_3_TEMPLATE.copy(),
        ]

    def build_lead_sequence(self, lead: Lead, sequence_templates: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Generate ready-to-send rendered email steps for a given lead."""
        templates = sequence_templates or self.get_default_sequence()
        rendered_steps = []
        for step_tpl in templates:
            rendered_steps.append({
                "step": step_tpl.get("step", 1),
                "delay_days": step_tpl.get("delay_days", 0),
                "subject": self.render_template(step_tpl.get("subject", ""), lead),
                "body": self.render_template(step_tpl.get("body", ""), lead),
            })
        return rendered_steps
