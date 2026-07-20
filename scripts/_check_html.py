import re
h = open('src/aegisScout/gui_assets.py', 'r', encoding='utf-8').read()
start = h.find('HTML_CONTENT')
if start < 0:
    print("HTML_CONTENT not found")
    exit()
html = h[start:]
tabs = re.findall(r'data-tab="([^"]+)"', html)
print("TABS:", tabs)
# Look for specific features
features = ['warmup', 'waterfall', 'audit', 'scoring', 'kanban', 'crm', 'proxy', 'smtp', 'imap', 'whatsapp', 'linkedin', 'knowledge', 'rag', 'task', 'queue', 'inbox', 'followup', 'campaign', 'email.verify', 'page.speed', 'tech', 'kvkk']
for f in features:
    if f.lower() in html.lower():
        print(f'  FOUND: {f}')
print(f"HTML length: {len(html)} chars")
