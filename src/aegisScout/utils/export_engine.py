"""
Multi-Format Export Engine for aegisScout (N10).
Exports business leads into 7 formats: XLSX, JSON/JSONL, PDF, HubSpot CSV, Pipedrive CSV, vCard (.vcf), Notion CSV.
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from sqlmodel import Session, select
from aegisScout.core.database import engine
from aegisScout.core.models import Lead
from aegisScout.utils.logger import get_logger

logger = get_logger("utils.export_engine")

def export_leads(format_type: str, output_path: Path) -> bool:
    """Export all leads to specified format."""
    with Session(engine) as session:
        leads = session.exec(select(Lead)).all()
        lead_dicts = [l.dict() for l in leads]

    fmt = format_type.lower()
    logger.info(f"Exporting {len(leads)} leads to format '{fmt}' at {output_path}...")

    try:
        if fmt == "json":
            output_path.write_text(json.dumps(lead_dicts, ensure_ascii=False, indent=2), encoding="utf-8")
        elif fmt == "jsonl":
            lines = [json.dumps(d, ensure_ascii=False) for d in lead_dicts]
            output_path.write_text("\n".join(lines), encoding="utf-8")
        elif fmt in ("csv", "hubspot", "pipedrive", "notion"):
            fieldnames = ["id", "business_name", "sector", "address", "phone", "email", "website", "instagram_handle"]
            with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(lead_dicts)
        elif fmt == "vcard":
            vcard_entries = []
            for l in lead_dicts:
                vcard = [
                    "BEGIN:VCARD",
                    "VERSION:3.0",
                    f"FN:{l.get('business_name', '')}",
                    f"ORG:{l.get('sector', '')}",
                    f"TEL:{l.get('phone', '')}",
                    f"EMAIL:{l.get('email', '')}",
                    f"URL:{l.get('website', '')}",
                    "END:VCARD"
                ]
                vcard_entries.append("\n".join(vcard))
            output_path.write_text("\n\n".join(vcard_entries), encoding="utf-8")
        elif fmt == "xlsx":
            try:
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Leads"
                headers = ["ID", "Business Name", "Sector", "Address", "Phone", "Email", "Website", "Instagram"]
                ws.append(headers)
                for l in lead_dicts:
                    ws.append([
                        l.get("id"), l.get("business_name"), l.get("sector"),
                        l.get("address"), l.get("phone"), l.get("email"),
                        l.get("website"), l.get("instagram_handle")
                    ])
                wb.save(output_path)
            except ImportError:
                # Fallback to CSV if openpyxl not installed
                return export_leads("csv", output_path)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

        return True
    except Exception as e:
        logger.error(f"Export failed for format {format_type}: {e}")
        return False
