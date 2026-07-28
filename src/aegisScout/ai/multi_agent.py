import json
import re
from typing import Optional
from aegisScout.ai.provider_router import ProviderRouter
from aegisScout.ai.local_rag import search_knowledge_base
from aegisScout.utils.logger import get_logger

logger = get_logger("ai.multi_agent")


_router: Optional[ProviderRouter] = None


def _get_router() -> ProviderRouter:
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router


async def generate_multi_agent_draft(
    business_name: str,
    sector: str,
    has_website: bool,
    website_notes: str,
    instagram_bio: str,
    review_highlights: str,
    opportunities: str,
    language: str = "tr",
    tone: str = "warm"
) -> dict:
    """
    Runs the 3-Agent Workflow (Inspector -> Copywriter -> Editor) to generate
    a highly personalized, natural outbound draft message.
    """
    ai_router = _get_router()
    
    # RAG lookup: search for case studies matching the sector/details
    rag_context = ""
    try:
        search_query = f"{sector} {business_name}"
        matches = search_knowledge_base(search_query, top_k=2)
        if matches:
            rag_context = "\n".join([f"Case Study / Service: {m['content']}" for m in matches])
            logger.info(f"RAG context retrieved for {business_name}: found {len(matches)} matches.")
    except Exception as e:
        logger.error(f"RAG search failed during agent draft generation: {e}")

    # Step 1: Agent 1 - Inspector
    inspector_prompt = f"""[AGENT: TECHNICAL INSPECTOR]
Analyze the business details below and identify the top opportunities/technical faults (e.g. missing pixel, slow pagespeed, broken links, no website).
Also check if the RAG context contains any relevant case studies or portfolio services that can be used as a reference.

Business Name: {business_name}
Sector: {sector}
Has Website: {"Evet" if has_website else "Hayır"}
Website Technical Notes: {website_notes}
Instagram Bio: {instagram_bio}
Google Reviews highlights: {review_highlights}
Discovered Tech Audit Issues: {opportunities}
Portfolyo/RAG Context: {rag_context}

Output a clean, bulleted list of 2-3 specific technical opportunities or references to use for this lead (in Turkish).
"""
    logger.info("Running Agent 1 (Inspector)...")
    inspector_report = await ai_router.generate(inspector_prompt)
    if not inspector_report:
        inspector_report = f"Opportunities: {opportunities or 'None'}"
        
    logger.debug(f"Inspector Report: {inspector_report}")

    # Step 2: Agent 2 - Copywriter
    copywriter_prompt = f"""[AGENT: COPYWRITER]
You are a world-class cold outreach copywriter. Write a short, highly personalized cold message (3-4 sentences max) to {business_name} in {language} language with a {tone} tone.
Use the inspector report below to address specific opportunities or references.

Guidelines:
- KESİNLİKLE emoji kullanma (sıfır emoji).
- KESİNLİKLE uydurma istatistik veya genel kalıp pitching cümleleri kullanma.
- Mesaj düz metin olmalı, markdown (*, _, # vb.) KESİNLİKLE kullanma.
- Samimi, merak uyandıran ve doğrudan konuya giren bir dil kullan.

Inspector Report:
{inspector_report}

Business details:
Business Name: {business_name}
Sector: {sector}

Output ONLY the raw outreach message text.
"""
    logger.info("Running Agent 2 (Copywriter)...")
    raw_draft = await ai_router.generate(copywriter_prompt)
    if not raw_draft:
        raw_draft = f"Merhaba {business_name}, {sector} alanındaki çalışmalarınızı inceledim..."

    logger.debug(f"Copywriter Raw Draft: {raw_draft}")

    # Step 3: Agent 3 - Editor
    editor_prompt = f"""[AGENT: EDITOR]
Review the cold outreach draft below. Clean up any AI-like jargon or cliché salutations (e.g., "Umarım iyisinizdir", "Harika haber!", "Sadece size ulaşmak istedim").
Make it sound 100% natural, human-written, warm, and highly relevant. Keep it short (3-4 sentences).

Draft:
{raw_draft}

Output format MUST be a valid JSON with the following structure:
{{"analysis": "kısa iç değerlendirme", "opening_message": "düzenlenmiş nihai mesaj"}}
"""
    logger.info("Running Agent 3 (Editor)...")
    editor_output = await ai_router.generate(editor_prompt)
    
    analysis = "Multi-Agent output."
    final_message = raw_draft
    
    if editor_output:
        try:
            cleaned_json_str = editor_output.strip()
            if cleaned_json_str.startswith("```"):
                cleaned_json_str = re.sub(r"^```[a-zA-Z0-9_+-]*\n?", "", cleaned_json_str)
                cleaned_json_str = re.sub(r"\n?```$", "", cleaned_json_str).strip()
            
            data = json.loads(cleaned_json_str)
            analysis = data.get("analysis", "Multi-Agent analysis.")
            final_message = data.get("opening_message", raw_draft) or raw_draft
        except Exception as pe:
            logger.warning(f"Failed to parse JSON from Editor: {pe}. Using raw copywriter draft.")
            analysis = f"Editor JSON Parse Failed: {pe}"
            final_message = raw_draft
            
    return {
        "analysis": analysis,
        "opening_message": final_message
    }


async def generate_sales_pitch_mode(
    business_name: str,
    sector: str,
    has_website: bool,
    website_notes: str,
    instagram_bio: str,
    review_highlights: str,
    address: str = "",
    phone: str = "",
    rating: Optional[float] = None,
    review_count: Optional[int] = None,
    language: str = "tr",
) -> dict:
    """
    Generates a structured Field Sales Pitch package for in-person sales visits.

    Returns a dict with:
      - profile_md: Business profile summary (markdown)
      - pitch_script_md: Verbal pitch script for the salesperson to say at the door
      - ideas: List of product ideas, each with title, description, price_estimate,
                needs_cms, and build_prompt
      - error: (optional) error message if generation failed
    """
    ai_router = _get_router()

    # Pricing rules embedded in the prompt (from Gropector's validated approach)
    pricing_rules = """
FIYATLANDIRMA KURALLARI (TL cinsinden, 2025 Türkiye pazarı):
- Statik tek sayfa / dijital kartvizit: 500-1.200 TL (tek seferlik)
- Orta karmaşıklık statik site (3-5 sayfa): 1.200-2.500 TL
- CMS + yönetim paneli (müşteri kendi güncelleyebilir): 3.000-6.000 TL + aylık 300-750 TL bakım
- Entegrasyon gerektiren sistem (rezervasyon, API, ödeme): 5.000-10.000 TL

YASAKLI FİKİR TÜRLERİ (bunları ÖNERME):
- E-ticaret / online satış mağazası
- Muhasebe veya ERP sistemi
- Sadece QR kod yönlendirme (ürün olarak sunulamaz)
- Sosyal medya yönetimi (hizmet, yazılım değil)
"""

    rag_context = ""
    try:
        matches = search_knowledge_base(f"{sector} {business_name}", top_k=2)
        if matches:
            rag_context = "\n".join([f"Referans: {m['content']}" for m in matches])
    except Exception:
        pass

    # Build the combined pitch generation prompt
    rating_str = f"{rating:.1f}/5.0 ({review_count} yorum)" if rating else "Bilinmiyor"
    pitch_prompt = f"""[SAHA SATIŞ PITCH OLUŞTURUCUSU]

Aşağıdaki işletme için kapsamlı bir saha satış paketi oluştur.
ÇIKTIYI TÜRKÇE VER.

# İŞLETME BİLGİLERİ
İşletme Adı: {business_name}
Sektör: {sector}
Adres: {address or "Bilinmiyor"}
Telefon: {phone or "Bilinmiyor"}
Web Sitesi: {"Var" if has_website else "YOK (Büyük Fırsat!)"}
Web Notu: {website_notes or "Bilgi yok"}
Instagram Biyografi: {instagram_bio or "Bilgi yok"}
Google Yorumları: {review_highlights or "Yok"}
Google Puanı: {rating_str}
Portfolyo/RAG Referanslar: {rag_context or "Yok"}

{pricing_rules}

# GÖREV
Aşağıdaki yapıya UYGUN bir JSON üret. SADECE JSON döndür, başka hiçbir şey ekleme.

ÇIKTI FORMATI:
{{
  "profile_md": "İşletmenin 4-6 cümlelik özet profili. Güçlü yönleri, zayıflıkları ve dijital fırsatları içermeli.",
  "pitch_script_md": "Kapıda söylenecek 5-8 cümlelik sözlü pitch scripti. Doğal ve samimi olmalı. Emoji kullanma. İlk cümle kapıyı açmalı, ikinci cümle spesifik bir sorunu belirtmeli, son cümle öneriye geçiş yapmalı.",
  "ideas": [
    {{
      "title": "Ürün/Hizmet Adı (kısa ve net)",
      "description": "Bu çözümün işletmeye spesifik katkısı (2-3 cümle)",
      "price_estimate": "X.XXX-Y.YYY TL",
      "needs_cms": true,
      "build_prompt": "Bu sistemi geliştirmek için detaylı teknik geliştirme promptu. Hangi teknolojiler kullanılacak, hangi özellikler olacak, nasıl yapılandırılacak — tüm teknik detaylar."
    }}
  ]
}}

NOTLAR:
- ideas listesinde 2-3 fikir olmalı, fazla değil.
- En az bir fikir web sitesi YOK ise basit bir dijital varlık (landing page) olsun.
- needs_cms: müşteri kendi içerikleri güncelleyebilecekse true, statik sayfa ise false.
- build_prompt: Geliştirici olarak ben bu fikri hemen kodlamaya başlayabileceğim kadar detaylı olmalı.
- Fiyatları yukarıdaki kurallara göre belirle. Uydurma fiyat verme.
"""

    logger.info(f"Running Sales Pitch Agent for: {business_name}")
    raw_output = await ai_router.generate(pitch_prompt)

    if not raw_output:
        return {
            "error": "AI yanıt vermedi.",
            "profile_md": f"{business_name} — {sector}",
            "pitch_script_md": f"Merhaba, {business_name} işletmenizi ziyaret ettim...",
            "ideas": [],
        }

    # Parse JSON output
    try:
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z0-9_+-]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned).strip()
        result = json.loads(cleaned)
        # Validate required keys
        if "profile_md" not in result:
            result["profile_md"] = f"{business_name} — {sector}"
        if "pitch_script_md" not in result:
            result["pitch_script_md"] = ""
        if "ideas" not in result or not isinstance(result["ideas"], list):
            result["ideas"] = []
        return result
    except Exception as parse_err:
        logger.warning(f"Sales pitch JSON parse failed: {parse_err}. Returning raw output.")
        return {
            "profile_md": f"{business_name} — {sector}",
            "pitch_script_md": raw_output,
            "ideas": [],
            "parse_error": str(parse_err),
        }
