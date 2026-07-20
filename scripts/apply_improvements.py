"""
Helper script to apply aegisScout roadmap improvements to gui.py and gui_assets.py.
"""

import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "aegisScout"
GUI_PY = SRC / "gui.py"
GUI_ASSETS_PY = SRC / "gui_assets.py"


def update_gui_py():
    print(f"Updating {GUI_PY}...")
    content = GUI_PY.read_text(encoding="utf-8")

    # Add bridge methods to GuiApi if not already present
    bridge_code = '''
    # -------------------------------------------------------------------
    # Multichannel Outreach, Email Verification & Vision Audit Bridges
    # -------------------------------------------------------------------
    def send_whatsapp_assisted(self, lead_id):
        try:
            lead_id = int(lead_id)
            with Session(engine) as session:
                lead = session.get(Lead, lead_id)
                if not lead:
                    return {"error": "Aday bulunamadı."}
                if not lead.phone:
                    return {"error": "Telefon numarası bulunamadı."}

                msg_stmt = select(Message).where(
                    (Message.lead_id == lead.id) & (Message.status == "draft")
                )
                message = session.exec(msg_stmt).first()
                draft = message.content if message else f"Merhaba {lead.business_name}, web sitenizi inceledik..."

                from aegisScout.outreach.assisted_mode import send_whatsapp_assisted
                res = send_whatsapp_assisted(lead.phone, draft)
                if res.get("success"):
                    if message:
                        message.status = "sent"
                        message.channel = "whatsapp_manual"
                        message.sent_at = _utcnow()
                        session.add(message)
                    lead.status = "contacted"
                    lead.updated_at = _utcnow()
                    session.add(lead)
                    session.commit()
                return res
        except Exception as e:
            return {"error": str(e)}

    def send_linkedin_assisted(self, lead_id):
        try:
            lead_id = int(lead_id)
            with Session(engine) as session:
                lead = session.get(Lead, lead_id)
                if not lead:
                    return {"error": "Aday bulunamadı."}

                msg_stmt = select(Message).where(
                    (Message.lead_id == lead.id) & (Message.status == "draft")
                )
                message = session.exec(msg_stmt).first()
                draft = message.content if message else f"Merhaba {lead.business_name}, profilinizi inceledik..."

                from aegisScout.outreach.assisted_mode import send_linkedin_assisted
                res = send_linkedin_assisted(lead.business_name, draft, lead.website_url)
                if res.get("success"):
                    if message:
                        message.status = "sent"
                        message.channel = "linkedin_manual"
                        message.sent_at = _utcnow()
                        session.add(message)
                    lead.status = "contacted"
                    lead.updated_at = _utcnow()
                    session.add(lead)
                    session.commit()
                return res
        except Exception as e:
            return {"error": str(e)}

    def verify_email_local(self, email: str):
        try:
            from aegisScout.outreach.email_verifier import EmailVerifier
            verifier = EmailVerifier(check_smtp=True, timeout=5.0)
            return verifier.verify(email)
        except Exception as e:
            return {"error": str(e)}

    def run_vision_audit(self, url: str):
        try:
            import asyncio
            from aegisScout.ai.vision_audit import VisionAuditManager
            mgr = VisionAuditManager()
            loop = asyncio.new_event_loop()
            res = loop.run_until_complete(mgr.audit_url(url))
            loop.close()
            return res
        except Exception as e:
            return {"error": str(e)}

    def get_proxy_status(self):
        try:
            from aegisScout.utils.proxy_pool import ProxyPoolManager
            pool = ProxyPoolManager.get_instance()
            return {
                "total_configured": len(pool.proxies),
                "active_healthy": len(pool.active_proxies),
                "proxies": pool.proxies
            }
        except Exception as e:
            return {"error": str(e)}

    def refresh_proxy_pool(self):
        try:
            import asyncio
            from aegisScout.utils.proxy_pool import ProxyPoolManager
            pool = ProxyPoolManager.get_instance()
            loop = asyncio.new_event_loop()
            res = loop.run_until_complete(pool.refresh_active_pool())
            loop.close()
            return {"success": True, "results": res}
        except Exception as e:
            return {"error": str(e)}
'''

    if "send_whatsapp_assisted" not in content:
        # Insert before class definition or before start_gui
        content = content.replace("def is_configured(self) -> dict:", bridge_code + "\n    def is_configured(self) -> dict:")

    GUI_PY.write_text(content, encoding="utf-8")
    print("gui.py updated successfully.")


def update_gui_assets_py():
    print(f"Updating {GUI_ASSETS_PY}...")
    content = GUI_ASSETS_PY.read_text(encoding="utf-8")

    # Update nav-links tab order
    new_nav_links = '''    <ul class="nav-links">
      <li class="nav-item active" onclick="switchTab('dashboard', this)" data-tab="dashboard">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>
        <span data-i18n="menu_dashboard">Dashboard</span>
      </li>
      <li class="nav-item" onclick="switchTab('leads', this)" data-tab="leads">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        <span data-i18n="menu_leads">Müşteri Keşfi</span>
      </li>
      <li class="nav-item" onclick="switchTab('pipeline', this)" data-tab="pipeline">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12H3m18-6H3m18 12H3"/></svg>
        <span data-i18n="menu_pipeline">CRM & Satış Hunisi</span>
      </li>
      <li class="nav-item" onclick="switchTab('campaigns', this)" data-tab="campaigns">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
        <span data-i18n="menu_campaigns">Çok Kanallı Erişim</span>
      </li>
      <li class="nav-item" onclick="switchTab('waterfall', this)" data-tab="waterfall">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        <span data-i18n="menu_waterfall">Derin Web Denetimi</span>
      </li>
      <li class="nav-item" onclick="switchTab('history', this)" data-tab="history">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>
        <span data-i18n="menu_history">Görevler & Geçmiş</span>
      </li>
      <li class="nav-item" onclick="switchTab('unibox', this)" data-tab="unibox">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
        <span data-i18n="menu_unibox">AI RAG Asistanı</span>
      </li>
      <li class="nav-item" onclick="switchTab('settings', this)" data-tab="settings">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        <span data-i18n="menu_settings">Ayarlar</span>
      </li>
    </ul>'''

    # Replace <ul class="nav-links"> ... </ul>
    pattern_nav = re.compile(r'<ul class="nav-links">.*?</ul>', re.DOTALL)
    if pattern_nav.search(content):
        content = pattern_nav.sub(new_nav_links, content)

    # Improve applyLanguage with fallback
    old_apply = '''function applyLanguage(langId) {
      currentLang = langId || 'tr';
      const lang = TRANSLATIONS[currentLang];
      if (!lang) return;'''

    new_apply = '''function applyLanguage(langId) {
      currentLang = langId || 'tr';
      const langObj = TRANSLATIONS[currentLang] || TRANSLATIONS['tr'];
      const fallbackObj = TRANSLATIONS['tr'] || {};'''

    content = content.replace(old_apply, new_apply)

    # Add toggleSidebar implementation if missing or update
    toggle_sidebar_js = '''
    function toggleSidebar() {
      const sidebar = document.getElementById('app-sidebar');
      if (!sidebar) return;
      sidebar.classList.toggle('collapsed');
      const isCollapsed = sidebar.classList.contains('collapsed');
      localStorage.setItem('sidebar_collapsed', isCollapsed ? 'true' : 'false');
    }

    document.addEventListener('DOMContentLoaded', () => {
      if (localStorage.getItem('sidebar_collapsed') === 'true') {
        const sidebar = document.getElementById('app-sidebar');
        if (sidebar) sidebar.classList.add('collapsed');
      }
    });
'''

    if "function toggleSidebar()" not in content:
        content = content.replace("function applyLanguage(langId) {", toggle_sidebar_js + "\n    function applyLanguage(langId) {")

    GUI_ASSETS_PY.write_text(content, encoding="utf-8")
    print("gui_assets.py updated successfully.")


if __name__ == "__main__":
    update_gui_py()
    update_gui_assets_py()
