"""
AI Auto Responder and Reply Handler for aegisScout.
Processes incoming lead replies, classifies sentiment, and schedules auto-responses.
"""
from typing import Dict, Any, Optional
from aegisScout.core.models import Lead
from aegisScout.outreach.cadence import AISequenceBuilder
from aegisScout.utils.logger import get_logger

logger = get_logger("outreach.auto_responder")


class AIAutoResponder:
    """Handles automated lead responses based on classification and sequence status."""

    def __init__(self):
        self.builder = AISequenceBuilder()

    def generate_response(self, lead: Lead, reply_category: str) -> Optional[Dict[str, str]]:
        """
        Generate automated response according to reply classification
        ('interested', 'more_info', 'not_interested', 'unsubscribe').
        """
        category = reply_category.lower().strip()
        
        if category in ("not_interested", "unsubscribe"):
            logger.info(f"Lead {lead.id} requested opt-out ({category}). No auto-response sent.")
            return None

        if category == "interested":
            subject = self.builder.render_template("Re: {{company}} - Toplantı Randevusu ve Detaylar", lead)
            body = self.builder.render_template(
                "Merhaba {{first_name}},\n\n"
                "İlginiz için teşekkür ederiz! Sizin için en uygun zaman diliminde 15 dakikalık bir demo sunumu yapmaktan memnuniyet duyarız.\n\n"
                "Müsait olduğunuz gün ve saat bilgisini iletebilir misiniz?\n\n"
                "Saygılarımızla,\nAegisScout Ekibi",
                lead
            )
            return {"subject": subject, "body": body}

        # Default fallback for more_info / questions
        subject = self.builder.render_template("Re: {{company}} - Detaylı Bilgilendirme", lead)
        body = self.builder.render_template(
            "Merhaba {{first_name}},\n\n"
            "Sorunuz için teşekkürler. {{company}} için hazırladığımız özel analiz detaylarını ekte bulabilirsiniz.\n\n"
            "Yardımcı olabileceğimiz başka bir konu olursa lütfen iletiniz.\n\n"
            "İyi çalışmalar.",
            lead
        )
        return {"subject": subject, "body": body}
