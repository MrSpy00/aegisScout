import json
import re

def extract_json(text: str) -> dict:
    """
    Robustly extracts and parses a JSON object from text.
    Handles markdown blocks (e.g. ```json ... ```) and extra conversational wrapper text.
    """
    # 1. Clean basic whitespace
    cleaned = text.strip()
    
    # 2. Try parsing directly
    try:
        return json.loads(cleaned)
    except Exception:
        pass
        
    # 3. Clean markdown wrappers
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```json") or lines[0].startswith("```"):
            cleaned = "\n".join(lines[1:-1]).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            pass
            
    # 4. Search for the first '{' and matching last '}' using regex/brackets
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        extracted = match.group(1)
        try:
            return json.loads(extracted)
        except Exception:
            pass

    # 5. Fallback manual curly brace match
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        extracted = cleaned[first_brace:last_brace+1]
        try:
            return json.loads(extracted)
        except Exception:
            pass

    raise ValueError("No valid JSON structure found in the provided text.")
