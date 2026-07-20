"""
Take English screenshots of aegisScout GUI panels for README documentation.

This script extracts the HTML from gui_assets.py, modifies it to work
standalone (without pywebview), and captures each panel as a PNG image.
"""

import re
import sys
from pathlib import Path

# Add project src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Extract HTML from gui_assets module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "gui_assets",
    Path(__file__).parent.parent / "src" / "aegisScout" / "gui_assets.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
html = mod.HTML_CONTENT

# Inject a mock pywebview API so the page renders without errors
mock_api_js = """
<script>
// Mock pywebview API for screenshot rendering
window.pywebview = {
  api: {
    get_stats: function() { 
      return Promise.resolve({ new: 42, researched: 18, contacted: 7, replied: 3, total: 70 });
    },
    get_leads: function() { return Promise.resolve([]); },
    get_sessions: function() { return Promise.resolve([{ id: 1, name: 'Default Session', is_active: true, created_at: '2025-01-01' }]); },
    get_campaigns: function() { return Promise.resolve([]); },
    get_activity_logs: function() { return Promise.resolve([]); },
    list_search_presets: function() { return Promise.resolve([]); },
    list_search_drafts: function() { return Promise.resolve([]); },
    get_lead_details: function() { return Promise.resolve({ lead: {}, notes: [], messages: [] }); },
    log_js_error: function() { return Promise.resolve({}); },
    set_config_value: function() { return Promise.resolve({}); },
    open_logs_folder: function() { return Promise.resolve({}); },
    get_settings: function() { return Promise.resolve({}); },
    is_configured: function() { return Promise.resolve({ configured: {} }); },
  }
};
// Prevent Google Fonts from blocking (they're already removed but just in case)
document.addEventListener('DOMContentLoaded', function() {
  // Force all panels to be visible for screenshot
  document.querySelectorAll('.panel').forEach(function(p) { p.style.display = 'block'; });
});
</script>
"""

# Insert mock API after the opening <head> tag
html = html.replace("<head>", "<head>" + mock_api_js, 1)

# Remove the pywebviewready and DOMContentLoaded listeners to avoid double-init
html = re.sub(
    r"window\.addEventListener\('pywebviewready'.*?}\);\s*\);\s*",
    "",
    html,
    flags=re.DOTALL,
)

# Save modified HTML for debugging
output_dir = Path(__file__).parent.parent / "assets"
output_dir.mkdir(exist_ok=True)

# Define panels to capture
panels = [
    {
        "id": "panel-dashboard",
        "file": "screenshot_dashboard.png",
        "title": "Dashboard",
        "init_js": """
          // Set stats display values
          document.getElementById('count-new').innerText = '42';
          document.getElementById('count-researched').innerText = '18';
          document.getElementById('count-contacted').innerText = '7';
          document.getElementById('count-replied').innerText = '3';
        """
    },
    {
        "id": "panel-leads",
        "file": "screenshot_leads.png",
        "title": "Leads Manager",
        "init_js": """
          // Populate leads table with sample data
          var tbody = document.getElementById('leads-table-body');
          if (tbody) {
            var sampleLeads = [
              { name: 'Sunrise Hair Studio', sector: 'kuaför', address: 'Moda, Kadıköy', website: true, status: 'new' },
              { name: 'Quantum Barber Shop', sector: 'berber', address: 'Caferağa, Kadıköy', website: true, status: 'researched' },
              { name: 'Elite Dental Clinic', sector: 'diş kliniği', address: 'Levent, Beşiktaş', website: true, status: 'contacted' },
              { name: 'Green Garden Cafe', sector: 'kafe', address: 'Bebek, Beşiktaş', website: false, status: 'replied' },
              { name: 'Prestige Nail Art', sector: 'güzellik salonu', address: 'Bağdat Cad., Kadıköy', website: true, status: 'new' },
              { name: 'Urban Fitness Center', sector: 'spor salonu', address: 'Nişantaşı, Şişli', website: true, status: 'researched' },
              { name: 'TechFix Electronics', sector: 'teknik servis', address: 'Mecidiyeköy, Şişli', website: true, status: 'contacted' },
              { name: 'Bella Pizza House', sector: 'restoran', address: 'Ortaköy, Beşiktaş', website: true, status: 'replied' },
              { name: 'Golden Nails & Spa', sector: 'güzellik salonu', address: 'Etiler, Beşiktaş', website: true, status: 'new' },
              { name: 'Smart Web Agency', sector: 'dijital ajans', address: 'Maslak, Sarıyer', website: true, status: 'researched' },
            ];
            var rows = '';
            sampleLeads.forEach(function(l) {
              rows += '<tr style="cursor:pointer">' +
                '<td><b>' + l.name + '</b></td>' +
                '<td style="color:var(--color-accent);font-size:0.8rem;">' + l.sector + '</td>' +
                '<td style="color:var(--text-muted);">' + l.address + '</td>' +
                '<td>' + (l.website ? 'Evet' : 'Hayır') + '</td>' +
                '<td><span class="badge badge-' + l.status + '">' + l.status + '</span></td>' +
                '</tr>';
            });
            tbody.innerHTML = rows;
          }
          // Update total count
          var bar = document.getElementById('leads-total-bar');
          if (bar) bar.textContent = '10 aday listeleniyor';
        """
    },
    {
        "id": "panel-campaigns",
        "file": "screenshot_campaigns.png",
        "title": "Campaigns",
        "init_js": """
          var tbody = document.getElementById('campaigns-table-body');
          if (tbody) {
            tbody.innerHTML = '' +
              '<tr><td>Kadıköy Kuaförler</td><td style="text-align:right">12</td><td style="text-align:right">%33.3 (4/12)</td><td style="text-align:right"><button style="padding:4px 8px;border-radius:6px;background:var(--border-subtle);color:var(--text-main);border:none;cursor:pointer">Detay</button></td></tr>' +
              '<tr><td>Beşiktaş Restoranlar</td><td style="text-align:right">8</td><td style="text-align:right">%50.0 (4/8)</td><td style="text-align:right"><button style="padding:4px 8px;border-radius:6px;background:var(--border-subtle);color:var(--text-main);border:none;cursor:pointer">Detay</button></td></tr>' +
              '<tr><td>Nişantaşı Güzellik</td><td style="text-align:right">15</td><td style="text-align:right">%26.7 (4/15)</td><td style="text-align:right"><button style="padding:4px 8px;border-radius:6px;background:var(--border-subtle);color:var(--text-main);border:none;cursor:pointer">Detay</button></td></tr>' +
              '<tr><td>Maslak IT Şirketleri</td><td style="text-align:right">20</td><td style="text-align:right">%15.0 (3/20)</td><td style="text-align:right"><button style="padding:4px 8px;border-radius:6px;background:var(--border-subtle);color:var(--text-main);border:none;cursor:pointer">Detay</button></td></tr>';
          }
        """
    },
    {
        "id": "panel-settings",
        "file": "screenshot_settings.png",
        "title": "Settings",
        "init_js": """
          // Mark some providers as configured (show green indicators)
          var labels = document.querySelectorAll('.form-group label');
          // No visual changes needed - the form renders by default
        """
    },
]

# Use Playwright to capture screenshots
from playwright.sync_api import sync_playwright

full_html_file = output_dir / "_full_app.html"
with open(full_html_file, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Full HTML written to {full_html_file}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        viewport={"width": 1440, "height": 900},
        device_scale_factor=2,
    )

    for panel in panels:
        panel_id = panel["id"]
        filename = panel["file"]
        init_js = panel["init_js"]

        page.goto(f"file:///{full_html_file}", wait_until="networkidle")
        page.wait_for_timeout(500)

        # Activate the panel
        page.evaluate(f"""
            (function() {{
                // Hide all panels, show this one
                document.querySelectorAll('.panel').forEach(function(p) {{
                    p.classList.remove('active');
                    p.style.display = 'none';
                }});
                var target = document.getElementById('{panel_id}');
                if (target) {{
                    target.classList.add('active');
                    target.style.display = 'flex';
                }}
                // Deactivate all nav items
                document.querySelectorAll('.nav-item').forEach(function(n) {{
                    n.classList.remove('active');
                }});
                // Run panel-specific init
                {init_js}
            }})();
        """)
        page.wait_for_timeout(800)

        out_path = output_dir / filename
        page.screenshot(path=str(out_path), full_page=False)
        size_kb = out_path.stat().st_size / 1024
        print(f"  [OK] {filename} ({size_kb:.0f} KB)")

    # Take a full-page screenshot of the dashboard
    full_path = output_dir / "screenshot_dashboard_full.png"
    page.evaluate("""
        (function() {
            document.querySelectorAll('.panel').forEach(function(p) { p.style.display = 'none'; p.classList.remove('active'); });
            var dash = document.getElementById('panel-dashboard');
            if (dash) { dash.classList.add('active'); dash.style.display = 'flex'; }
            // Restore stats
            document.getElementById('count-new').innerText = '42';
            document.getElementById('count-researched').innerText = '18';
            document.getElementById('count-contacted').innerText = '7';
            document.getElementById('count-replied').innerText = '3';
        })();
    """)
    page.wait_for_timeout(500)
    page.screenshot(path=str(full_path), full_page=True)
    print(f"  [OK] screenshot_dashboard_full.png")

    browser.close()

print("\n[OK] All screenshots captured successfully!")
print(f"   Output directory: {output_dir}")
