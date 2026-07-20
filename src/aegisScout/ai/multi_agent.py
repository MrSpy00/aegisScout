import json
import re
from typing import Optional
from aegisScout.ai.provider_router import ProviderRouter
from aegisScout.ai.local_rag import search_knowledge_base
from aegisScout.utils.logger import get_logger

logger = get_logger("ai.multi_agent")


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
    ai_router = ProviderRouter()
    
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
