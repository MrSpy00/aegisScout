import sys

file_path = r'X:\Projects\ActiveProjects\aegisScout\src\aegisScout\assets\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# FIX 1
content = content.replace('''<th>İşletme Adı</th>
                  <th>Sektör</th>
                  <th>Konum</th>
                  <th>Web</th>
                  <th>Durum</th>''', 
'''<th onclick="sortLeads('business_name')" style="cursor:pointer;user-select:none;" data-i18n="th_business_name">İşletme Adı <span id="sort-indicator-business_name"></span></th>
                  <th onclick="sortLeads('sector')" style="cursor:pointer;user-select:none;" data-i18n="th_sector">Sektör <span id="sort-indicator-sector"></span></th>
                  <th onclick="sortLeads('address')" style="cursor:pointer;user-select:none;" data-i18n="th_location">Konum <span id="sort-indicator-address"></span></th>
                  <th data-i18n="th_web">Web</th>
                  <th onclick="sortLeads('status')" style="cursor:pointer;user-select:none;" data-i18n="th_status">Durum <span id="sort-indicator-status"></span></th>''')

content = content.replace('<h1>Adaylar (Leads)</h1>', '<h1 data-i18n="leads_h1">Adaylar (Leads)</h1>')
content = content.replace('<p class="subtitle">Keşfedilmiş olan işletmeleri ve yapay zeka analizlerini inceleyin.</p>', '<p class="subtitle" data-i18n="leads_subtitle">Keşfedilmiş olan işletmeleri ve yapay zeka analizlerini inceleyin.</p>')

# FIX 2
sidebar_css = '''    .sidebar.collapsed .nav-item svg {
      margin: 0;
      flex-shrink: 0;
    }'''
sidebar_css_new = '''    .sidebar.collapsed .nav-item svg {
      margin: 0;
      flex-shrink: 0;
    }
    /* Tooltip on collapsed nav items */
    .sidebar.collapsed .nav-item::after {
      content: attr(data-tooltip);
      position: absolute;
      left: 72px;
      top: 50%;
      transform: translateY(-50%);
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.8rem;
      white-space: nowrap;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.18s;
      z-index: 100;
    }
    .sidebar.collapsed .nav-item:hover::after {
      opacity: 1;
    }
    /* Ensure sidebar toggle btn stays visible when collapsed */
    .sidebar.collapsed .sidebar-toggle-btn {
      right: auto;
      left: 50%;
      transform: translateX(-50%) rotate(180deg);
      top: 8px;
    }'''
content = content.replace(sidebar_css, sidebar_css_new)

content = content.replace('<li class="nav-item active" onclick="switchTab(\'dashboard\', this)" data-tab="dashboard">', '<li class="nav-item active" onclick="switchTab(\'dashboard\', this)" data-tab="dashboard" data-tooltip="Dashboard">')
content = content.replace('<li class="nav-item" onclick="switchTab(\'leads\', this)" data-tab="leads">', '<li class="nav-item" onclick="switchTab(\'leads\', this)" data-tab="leads" data-tooltip="Adaylar">')
content = content.replace('<li class="nav-item" onclick="switchTab(\'pipeline\', this)" data-tab="pipeline">', '<li class="nav-item" onclick="switchTab(\'pipeline\', this)" data-tab="pipeline" data-tooltip="CRM Hunisi">')
content = content.replace('<li class="nav-item" onclick="switchTab(\'campaigns\', this)" data-tab="campaigns">', '<li class="nav-item" onclick="switchTab(\'campaigns\', this)" data-tab="campaigns" data-tooltip="Kampanyalar">')
content = content.replace('<li class="nav-item" onclick="switchTab(\'waterfall\', this)" data-tab="waterfall">', '<li class="nav-item" onclick="switchTab(\'waterfall\', this)" data-tab="waterfall" data-tooltip="Derin Web">')
content = content.replace('<li class="nav-item" onclick="switchTab(\'history\', this)" data-tab="history">', '<li class="nav-item" onclick="switchTab(\'history\', this)" data-tab="history" data-tooltip="Geçmiş">')
content = content.replace('<li class="nav-item" onclick="switchTab(\'unibox\', this)" data-tab="unibox">', '<li class="nav-item" onclick="switchTab(\'unibox\', this)" data-tab="unibox" data-tooltip="AI RAG">')
content = content.replace('<li class="nav-item" onclick="switchTab(\'settings\', this)" data-tab="settings">', '<li class="nav-item" onclick="switchTab(\'settings\', this)" data-tab="settings" data-tooltip="Ayarlar">')

# FIX 3
content = content.replace('''          <div class="form-group">
            <label for="search-provider" data-i18n="lbl_search_provider">Veri Kaynağı</label>
            <select id="search-provider">
              <option value="all" selected data-i18n="opt_provider_all">Tüm Kaynaklar (Önerilen / All Sources)</option>
              <option value="osm" data-i18n="opt_provider_osm">OpenStreetMap (Ücretsiz / OSM)</option>
              <option value="web_search" data-i18n="opt_provider_web">Web Arama (DDG Scraper / Web Search)</option>
              <option value="google_places" data-i18n="opt_provider_google">Google Places (API Anahtarlı)</option>
            </select>
          </div>''', 
'''          <div class="form-group">
            <label for="search-provider" data-i18n="lbl_search_provider">Veri Kaynağı</label>
            <select id="search-provider">
              <option value="all" selected data-i18n="opt_provider_all">Tüm Kaynaklar (Önerilen / All Sources)</option>
              <option value="osm" data-i18n="opt_provider_osm">OpenStreetMap (Ücretsiz / OSM)</option>
              <option value="web_search" data-i18n="opt_provider_web">Web Arama (DDG Scraper / Web Search)</option>
              <option value="google_places" data-i18n="opt_provider_google">Google Places (API Anahtarlı)</option>
            </select>
          </div>
          <div class="form-group">
            <label for="search-scan-depth" data-i18n="lbl_scan_depth">Tarama Derinliği</label>
            <select id="search-scan-depth">
              <option value="rapid" data-i18n="opt_depth_rapid">⚡ Hızlı (İlk 20 Sonuç)</option>
              <option value="medium" selected data-i18n="opt_depth_medium">🔍 Orta (50 Sonuç, 3 Kaynak)</option>
              <option value="deep" data-i18n="opt_depth_deep">🔬 Kapsamlı (200+ Sonuç, Tüm Kaynaklar)</option>
            </select>
          </div>''')

# FIX 4
content = content.replace('''    /* Unibox styling */
    .unibox-lead-item {''', '''    /* Unibox styling */
    /* AI RAG / Unibox Panel centering */
    #panel-unibox {
      height: calc(100vh - 80px);
      max-height: calc(100vh - 80px);
    }
    .unibox-wrapper {
      display: flex;
      flex-direction: column;
      height: 100%;
      max-width: 900px;
      margin: 0 auto;
      width: 100%;
    }
    .unibox-chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .unibox-chat-input-area {
      padding: 16px 20px;
      border-top: 1px solid var(--border-subtle);
      background: var(--bg-surface);
      border-radius: 0 0 16px 16px;
    }
    .unibox-lead-item {''')

content = content.replace('''  <!-- 📥 Unified Inbox Panel -->
  <div id="panel-unibox" class="panel">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">''', '''  <!-- 📥 Unified Inbox Panel -->
  <div id="panel-unibox" class="panel">
    <div class="unibox-wrapper">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">''')

content = content.replace('''        <div id="unibox-reply-container" style="display: none; flex-direction: column; gap: 8px;">
          <div style="display: flex; gap: 8px; align-items: center;">
            <span style="font-size: 0.8rem; color: var(--text-muted);">Gönderim Kanalı:</span>
            <select id="unibox-reply-channel" style="height: 28px; padding: 0 8px; border-radius: 6px; background: var(--bg-base); border: 1px solid var(--border-accent); color: var(--text-main); font-size: 0.8rem; outline: none;">
              <option value="email">📧 E-Posta</option>
              <option value="whatsapp">💬 WhatsApp (Playwright)</option>
              <option value="linkedin">🔗 LinkedIn (Playwright)</option>
            </select>
          </div>
          <div style="display: flex; gap: 8px;">
            <textarea id="unibox-reply-text" placeholder="Yanıtınızı buraya yazın..." style="flex-grow: 1; height: 54px; padding: 8px; border-radius: 8px; background: var(--bg-base); border: 1px solid var(--border-accent); color: var(--text-main); font-size: 0.85rem; resize: none; outline: none;"></textarea>
            <button class="btn" onclick="sendUniboxReplyMessage()" style="padding: 0 20px; height: 54px; flex-shrink: 0; background: var(--color-brand); color: white;">Gönder</button>
          </div>
        </div>
      </div>
    </div>
  </div>''', '''        <div id="unibox-reply-container" style="display: none; flex-direction: column; gap: 8px;">
          <div style="display: flex; gap: 8px; align-items: center;">
            <span style="font-size: 0.8rem; color: var(--text-muted);">Gönderim Kanalı:</span>
            <select id="unibox-reply-channel" style="height: 28px; padding: 0 8px; border-radius: 6px; background: var(--bg-base); border: 1px solid var(--border-accent); color: var(--text-main); font-size: 0.8rem; outline: none;">
              <option value="email">📧 E-Posta</option>
              <option value="whatsapp">💬 WhatsApp (Playwright)</option>
              <option value="linkedin">🔗 LinkedIn (Playwright)</option>
            </select>
          </div>
          <div style="display: flex; gap: 8px;">
            <textarea id="unibox-reply-text" placeholder="Yanıtınızı buraya yazın..." style="flex-grow: 1; height: 54px; padding: 8px; border-radius: 8px; background: var(--bg-base); border: 1px solid var(--border-accent); color: var(--text-main); font-size: 0.85rem; resize: none; outline: none;"></textarea>
            <button class="btn" onclick="sendUniboxReplyMessage()" style="padding: 0 20px; height: 54px; flex-shrink: 0; background: var(--color-brand); color: white;">Gönder</button>
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>''')

# FIX 5
content = content.replace('''  <!-- ⚡ Waterfall Enrichment Panel -->
  <div id="panel-waterfall" class="panel">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">''', '''  <!-- ⚡ Waterfall Enrichment Panel -->
  <div id="panel-waterfall" class="panel" style="max-width: 1000px; margin: 0 auto; height: calc(100vh - 80px); display: flex; flex-direction: column;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">''')

# FIX 8
content = content.replace('''      const provider = document.getElementById('search-provider').value;
      const composedLocation = [location, city, region, country].filter(Boolean).join('\\n');''', '''      const provider = document.getElementById('search-provider').value;
      const scanDepth = document.getElementById('search-scan-depth')?.value || 'medium';
      const composedLocation = [location, city, region, country].filter(Boolean).join('\\n');''')

content = content.replace('''      const promise = _apiCall(
        () => window.pywebview.api.discover_leads(sector, composedLocation, radius, provider),
        { action: 'Keşif başlat' }
      );''', '''      const promise = _apiCall(
        () => window.pywebview.api.discover_leads(sector, composedLocation, radius, provider, scanDepth),
        { action: 'Keşif başlat' }
      );''')

# FIX 9
content = content.replace('''    <div id="panel-settings" class="panel">
      <div>
        <h1 data-i18n="settings_title">Ayarlar</h1>
        <p class="subtitle" data-i18n="settings_subtitle">API anahtarlarını, otomasyon ayarlarını ve bildirim kanallarını yapılandırın.</p>
      </div>

      <div class="stat-card" style="gap: 24px; max-width: 800px;">''', '''    <div id="panel-settings" class="panel">
      <div>
        <h1 data-i18n="settings_title">Ayarlar</h1>
        <p class="subtitle" data-i18n="settings_subtitle">API anahtarlarını, otomasyon ayarlarını ve bildirim kanallarını yapılandırın.</p>
      </div>

      <!-- Language & Theme Settings -->
      <div class="stat-card" style="gap: 20px; max-width: 800px; margin-bottom: 0;">
        <h2 style="font-family: var(--font-display); font-size: 1.1rem; color: var(--color-accent);" data-i18n="settings_section_ui">Arayüz Ayarları</h2>
        <div class="form-row">
          <div class="form-group">
            <label data-i18n="lbl_language">Arayüz Dili / Interface Language</label>
            <select id="cfg-language" onchange="handleLanguageChange(this.value)">
              <option value="tr">🇹🇷 Türkçe</option>
              <option value="en">🇬🇧 English</option>
            </select>
          </div>
          <div class="form-group">
            <label data-i18n="lbl_theme">Tema / Theme</label>
            <select id="cfg-theme" onchange="handleThemeChange(this.value)">
              <option value="theme-amethyst">💜 Amethyst (Varsayılan)</option>
              <option value="theme-neon">💙 Neon Dark</option>
              <option value="theme-emerald">💚 Emerald Forest</option>
              <option value="theme-cyberpunk">🌸 Cyberpunk</option>
              <option value="theme-midnight">🌊 Midnight Blue</option>
              <option value="theme-amber">🟡 Amber Gold</option>
              <option value="theme-rose">🌹 Rose</option>
              <option value="theme-dracula">🧛 Dracula</option>
              <option value="theme-solarized">☀️ Solarized Dark</option>
              <option value="theme-slate">🔷 Slate</option>
              <option value="theme-light">☀️ Light Mode</option>
              <option value="theme-monochrome">⬛ Monochrome</option>
            </select>
          </div>
        </div>
      </div>

      <div class="stat-card" style="gap: 24px; max-width: 800px;">''')

# FIX 10
content = content.replace('''        detailView.innerHTML = `
          <h2 style="font-family: var(--font-display); font-size: 1.4rem;">${escapeHtml(lead.business_name)}</h2>

          <div class="detail-section">''', '''// Profile image
        const profileImgHtml = lead.profile_image_url 
          ? `<img src="${lead.profile_image_url}" alt="Profil" style="width:60px;height:60px;border-radius:50%;object-fit:cover;border:2px solid var(--color-brand);flex-shrink:0;" onerror="this.style.display='none'">`
          : `<div style="width:60px;height:60px;border-radius:50%;background:var(--bg-card);border:2px solid var(--border-subtle);display:flex;align-items:center;justify-content:center;font-size:1.5rem;flex-shrink:0;">🏢</div>`;

        detailView.innerHTML = `
          <div style="display:flex; gap:16px; align-items:center; margin-bottom:12px;">
            ${profileImgHtml}
            <h2 style="font-family: var(--font-display); font-size: 1.4rem; margin:0;">${escapeHtml(lead.business_name)}</h2>
          </div>

          <div class="detail-section">''')

# Now missing: FIX 6, FIX 7, FIX 9 JS functions, which I'll add with a simple string replace
# For FIX 6, adding near top of script:
i18n_code = """
// ============================================================
// 🌍 i18n Translation System
// ============================================================
const TRANSLATIONS = {
  tr: {
    // Navigation
    menu_dashboard: 'Dashboard',
    menu_leads: 'Müşteri Keşfi',
    menu_pipeline: 'CRM & Satış Hunisi',
    menu_campaigns: 'Çok Kanallı Erişim',
    menu_waterfall: 'Derin Web Denetimi',
    menu_history: 'Görevler & Geçmiş',
    menu_unibox: 'AI RAG Asistanı',
    menu_settings: 'Ayarlar',
    sidebar_toggle_title: 'Menüyü Daralt/Genişlet',
    // Dashboard
    dashboard_h1: 'Dashboard',
    dashboard_subtitle_text: 'Müşteri keşif turları başlatın ve genel durum istatistiklerini takip edin.',
    stat_new_discovered: 'Yeni Keşfedilen',
    stat_ai_ready: 'AI Analizi Hazır',
    stat_contacted: 'İletişime Geçilen',
    stat_replied: 'Geri Dönüş Yapan',
    discovery_form_title: 'Yeni Keşif Başlat',
    lbl_search_sector: 'Sektör / Anahtar Kelimeler',
    lbl_search_location: 'Konum / Şehir / Bölge / Ülke',
    lbl_search_radius: 'Yarıçap (km)',
    lbl_search_provider: 'Veri Kaynağı',
    lbl_scan_depth: 'Tarama Derinliği',
    lbl_search_country: 'Ülke(ler)',
    lbl_search_city: 'Şehir(ler)',
    lbl_search_region: 'Bölge / İlçe',
    lbl_search_notes: 'Taslak Notu',
    lbl_search_preset_name: 'Taslak / Preset Adı',
    lbl_search_preset_select: 'Kayıtlı Taslaklar',
    lbl_search_draft_select: 'Kayıtlı Arama Taslakları',
    btn_save_preset: 'Preset Kaydet',
    btn_save_draft: 'Taslak Kaydet',
    btn_load_preset: 'Preset Yükle',
    btn_load_draft: 'Taslak Yükle',
    btn_start_discovery: 'Keşfi Başlat',
    lbl_discovery_progress: 'Keşif İlerleme Durumu',
    opt_provider_all: 'Tüm Kaynaklar (Önerilen)',
    opt_provider_osm: 'OpenStreetMap (Ücretsiz)',
    opt_provider_web: 'Web Arama (DDG Scraper)',
    opt_provider_google: 'Google Places (API Anahtarlı)',
    opt_depth_rapid: '⚡ Hızlı (İlk 20 Sonuç)',
    opt_depth_medium: '🔍 Orta (50 Sonuç, 3 Kaynak)',
    opt_depth_deep: '🔬 Kapsamlı (200+ Sonuç, Tüm Kaynaklar)',
    ph_search_sector: 'kuaför\\nmimar\\ndiş kliniği',
    ph_search_location: 'Kadıköy\\nİstanbul\\nTürkiye',
    ph_search_radius: 'Boş = Sınırsız (Şehir Sınırları)',
    ph_search_country: 'Türkiye\\nAlmanya',
    ph_search_city: 'İstanbul\\nBerlin',
    ph_search_region: 'Marmara\\nKadıköy',
    ph_search_notes: 'Örneğin: premium odak, yeni açılan işletmeler...',
    ph_search_preset_name: 'Örneğin: İstanbul kuaför taraması',
    opt_select_preset: 'Yüklenecek taslak seçin',
    opt_select_draft: 'Taslak seçin',
    // Leads
    leads_h1: 'Adaylar (Leads)',
    leads_subtitle: 'Keşfedilmiş olan işletmeleri ve yapay zeka analizlerini inceleyin.',
    th_business_name: 'İşletme Adı',
    th_sector: 'Sektör',
    th_location: 'Konum',
    th_web: 'Web',
    th_status: 'Durum',
    // Settings
    settings_title: 'Ayarlar',
    settings_subtitle: 'API anahtarlarını, otomasyon ayarlarını ve bildirim kanallarını yapılandırın.',
    settings_sec_env: 'Uygulama Yapılandırması (.env)',
    settings_section_llm: '1. LLM / Yapay Zeka Ayarları',
    settings_section_google: '2. Google ve Arama Servisleri',
    settings_section_ig: '3. Instagram Otomasyonu (Mod B)',
    settings_section_notif: '4. Bildirim Kanalları (SMTP / Telegram)',
    lbl_primary_llm: 'Birincil LLM Sağlayıcı',
    lbl_fallback_llm: 'Yedek (Fallback) Sağlayıcı',
    lbl_deepseek_key: 'DeepSeek API Anahtarı',
    lbl_openai_key: 'OpenAI API Anahtarı',
    lbl_anthropic_key: 'Anthropic API Anahtarı',
    lbl_openrouter_key: 'OpenRouter API Anahtarı',
    lbl_gemini_key: 'Gemini API Anahtarı',
    lbl_groq_key: 'Groq API Anahtarı',
    lbl_mistral_key: 'Mistral API Anahtarı',
    lbl_ollama_url: 'Ollama Base URL (Yerel)',
    lbl_google_places_key: 'Google Places API Anahtarı',
    lbl_google_search_key: 'Google Custom Search API Anahtarı',
    lbl_google_search_cx: 'Google Custom Search CX',
    lbl_ig_username: 'Instagram Kullanıcı Adı',
    lbl_ig_password: 'Instagram Şifresi',
    lbl_ig_encryption_key: 'Oturum Şifreleme Anahtarı',
    lbl_outreach_mode: 'Erişim Modu',
    lbl_max_outreach: 'Günlük Maksimum Mesaj Limiti',
    lbl_tg_token: 'Telegram Bot Token',
    opt_assisted: 'Assisted Mod A (Clipboard & Tarayıcı - Güvenli)',
    opt_full_auto: 'Mod B (Tam Otomasyon - Riskli)',
    opt_none: 'Yok',
    automation_risk_text: '⚠️ UYARI: Tam otomasyon modunun etkinleştirilmesi Instagram Kullanım Koşulları\\'nı (ToS) ihlal eder. Hesabınızın kısıtlanması veya kapatılması riskini anlıyor musunuz?',
    automation_confirm_label: 'Riskleri anladım, tam otomasyonu etkinleştirmek istiyorum.',
    // Info modal descriptions
    info_primary_llm_desc: 'Araştırma ve metin üretimi için kullanılacak birincil yapay zeka sağlayıcısı. DeepSeek önerilir (maliyet/kalite oranı).',
    info_fallback_llm_desc: 'Birincil sağlayıcı başarısız olduğunda kullanılacak yedek sağlayıcı.',
    info_deepseek_key_desc: 'DeepSeek API anahtarını platform.deepseek.com adresinden alabilirsiniz.',
    info_openai_key_desc: 'OpenAI API anahtarını platform.openai.com adresinden alabilirsiniz.',
    info_anthropic_key_desc: 'Anthropic Claude API anahtarını console.anthropic.com adresinden alabilirsiniz.',
    info_openrouter_key_desc: 'OpenRouter birden fazla modele erişim sağlar. openrouter.ai adresinden alabilirsiniz.',
    info_gemini_key_desc: 'Google Gemini API anahtarını aistudio.google.com adresinden alabilirsiniz.',
    info_groq_key_desc: 'Groq çok hızlı inference sunar. console.groq.com adresinden alabilirsiniz.',
    info_mistral_key_desc: 'Mistral AI API anahtarını console.mistral.ai adresinden alabilirsiniz.',
    info_ollama_url_desc: 'Ollama yerel sunucusunun adresi. Varsayılan: http://localhost:11434',
    info_google_places_key_desc: 'Google Places API ile işletme verileri çekilir. Google Cloud Console\\'dan alabilirsiniz.',
    info_google_search_key_desc: 'Google Custom Search API anahtarı. Google Cloud Console\\'dan alabilirsiniz.',
    info_google_search_cx_desc: 'Google Custom Search Engine ID. Özel arama motoru oluşturup ID alabilirsiniz.',
    info_ig_username_desc: 'Instagram otomasyon için kullanılacak hesap kullanıcı adı.',
    info_ig_password_desc: 'Instagram şifresi sadece RAM\\'de tutulur, diske yazılmaz.',
    info_ig_encryption_key_desc: 'Oturum dosyasını şifrelemek için kullanılan Fernet anahtarı.',
    info_outreach_mode_desc: 'Mod A: Mesajı panoya kopyalar, elle göndermeniz gerekir. Mod B: Otomatik gönderir (risk içerir).',
    info_max_outreach_desc: 'Günlük gönderilebilecek maksimum mesaj sayısı. Instagram için 15-20 önerilir.',
    info_tg_token_desc: 'Telegram bot bildirimleri için @BotFather\\'dan alınan token.',
  },
  en: {
    // Navigation
    menu_dashboard: 'Dashboard',
    menu_leads: 'Lead Discovery',
    menu_pipeline: 'CRM & Sales Funnel',
    menu_campaigns: 'Multi-Channel Outreach',
    menu_waterfall: 'Deep Web Audit',
    menu_history: 'Tasks & History',
    menu_unibox: 'AI RAG Assistant',
    menu_settings: 'Settings',
    sidebar_toggle_title: 'Toggle Sidebar',
    // Dashboard
    dashboard_h1: 'Dashboard',
    dashboard_subtitle_text: 'Launch business discovery rounds and track overall status statistics.',
    stat_new_discovered: 'Newly Discovered',
    stat_ai_ready: 'AI Analysis Ready',
    stat_contacted: 'Contacted',
    stat_replied: 'Replied',
    discovery_form_title: 'Start New Discovery',
    lbl_search_sector: 'Sector / Keywords',
    lbl_search_location: 'Location / City / Region / Country',
    lbl_search_radius: 'Radius (km)',
    lbl_search_provider: 'Data Source',
    lbl_scan_depth: 'Scan Depth',
    lbl_search_country: 'Country/Countries',
    lbl_search_city: 'City/Cities',
    lbl_search_region: 'Region / District',
    lbl_search_notes: 'Draft Note',
    lbl_search_preset_name: 'Preset / Draft Name',
    lbl_search_preset_select: 'Saved Presets',
    lbl_search_draft_select: 'Saved Drafts',
    btn_save_preset: 'Save Preset',
    btn_save_draft: 'Save Draft',
    btn_load_preset: 'Load Preset',
    btn_load_draft: 'Load Draft',
    btn_start_discovery: 'Start Discovery',
    lbl_discovery_progress: 'Discovery Progress',
    opt_provider_all: 'All Sources (Recommended)',
    opt_provider_osm: 'OpenStreetMap (Free)',
    opt_provider_web: 'Web Search (DDG Scraper)',
    opt_provider_google: 'Google Places (API Key Required)',
    opt_depth_rapid: '⚡ Rapid (First 20 Results)',
    opt_depth_medium: '🔍 Medium (50 Results, 3 Sources)',
    opt_depth_deep: '🔬 Deep (200+ Results, All Sources)',
    ph_search_sector: 'hair salon\\narchitect\\ndental clinic',
    ph_search_location: 'Kadıköy\\nIstanbul\\nTurkey',
    ph_search_radius: 'Empty = Unlimited (City Bounds)',
    ph_search_country: 'Turkey\\nGermany',
    ph_search_city: 'Istanbul\\nBerlin',
    ph_search_region: 'Marmara\\nKadıköy',
    ph_search_notes: 'e.g.: premium focus, newly opened businesses...',
    ph_search_preset_name: 'e.g.: Istanbul salon scan',
    opt_select_preset: 'Select preset to load',
    opt_select_draft: 'Select draft',
    // Leads
    leads_h1: 'Leads',
    leads_subtitle: 'Browse discovered businesses and their AI analysis.',
    th_business_name: 'Business Name',
    th_sector: 'Sector',
    th_location: 'Location',
    th_web: 'Web',
    th_status: 'Status',
    // Settings
    settings_title: 'Settings',
    settings_subtitle: 'Configure API keys, automation settings and notification channels.',
    settings_sec_env: 'Application Configuration (.env)',
    settings_section_llm: '1. LLM / AI Settings',
    settings_section_google: '2. Google & Search Services',
    settings_section_ig: '3. Instagram Automation (Mod B)',
    settings_section_notif: '4. Notification Channels (SMTP / Telegram)',
    lbl_primary_llm: 'Primary LLM Provider',
    lbl_fallback_llm: 'Fallback Provider',
    lbl_deepseek_key: 'DeepSeek API Key',
    lbl_openai_key: 'OpenAI API Key',
    lbl_anthropic_key: 'Anthropic API Key',
    lbl_openrouter_key: 'OpenRouter API Key',
    lbl_gemini_key: 'Gemini API Key',
    lbl_groq_key: 'Groq API Key',
    lbl_mistral_key: 'Mistral API Key',
    lbl_ollama_url: 'Ollama Base URL (Local)',
    lbl_google_places_key: 'Google Places API Key',
    lbl_google_search_key: 'Google Custom Search API Key',
    lbl_google_search_cx: 'Google Custom Search CX',
    lbl_ig_username: 'Instagram Username',
    lbl_ig_password: 'Instagram Password',
    lbl_ig_encryption_key: 'Session Encryption Key',
    lbl_outreach_mode: 'Outreach Mode',
    lbl_max_outreach: 'Daily Maximum Message Limit',
    lbl_tg_token: 'Telegram Bot Token',
    opt_assisted: 'Assisted Mode A (Clipboard & Browser - Safe)',
    opt_full_auto: 'Mode B (Full Automation - Risky)',
    opt_none: 'None',
    automation_risk_text: '⚠️ WARNING: Enabling full automation violates Instagram Terms of Service. Do you understand the risk of account restriction or termination?',
    automation_confirm_label: 'I understand the risks and want to enable full automation.',
    info_primary_llm_desc: 'Primary AI provider for research and text generation. DeepSeek recommended (cost/quality ratio).',
    info_fallback_llm_desc: 'Fallback provider when primary fails.',
    info_deepseek_key_desc: 'Get your DeepSeek API key from platform.deepseek.com.',
    info_openai_key_desc: 'Get your OpenAI API key from platform.openai.com.',
    info_anthropic_key_desc: 'Get your Anthropic Claude API key from console.anthropic.com.',
    info_openrouter_key_desc: 'OpenRouter provides access to multiple models. Get key from openrouter.ai.',
    info_gemini_key_desc: 'Get your Google Gemini API key from aistudio.google.com.',
    info_groq_key_desc: 'Groq offers very fast inference. Get key from console.groq.com.',
    info_mistral_key_desc: 'Get your Mistral AI API key from console.mistral.ai.',
    info_ollama_url_desc: 'Address of local Ollama server. Default: http://localhost:11434',
    info_google_places_key_desc: 'Google Places API for business data. Get from Google Cloud Console.',
    info_google_search_key_desc: 'Google Custom Search API key. Get from Google Cloud Console.',
    info_google_search_cx_desc: 'Google Custom Search Engine ID.',
    info_ig_username_desc: 'Instagram account username for automation.',
    info_ig_password_desc: 'Instagram password kept in RAM only, never written to disk.',
    info_ig_encryption_key_desc: 'Fernet key for encrypting session file.',
    info_outreach_mode_desc: 'Mode A: Copies message to clipboard for manual sending. Mode B: Auto-sends (risky).',
    info_max_outreach_desc: 'Max messages per day. 15-20 recommended for Instagram.',
    info_tg_token_desc: 'Token from @BotFather for Telegram bot notifications.',
  }
};

let currentLanguage = localStorage.getItem('aegis-language') || 'tr';

function getTranslation(key, lang) {
  const l = lang || currentLanguage;
  return (TRANSLATIONS[l] && TRANSLATIONS[l][key]) || (TRANSLATIONS['tr'] && TRANSLATIONS['tr'][key]) || key;
}

function applyLanguage(lang) {
  currentLanguage = lang || 'tr';
  localStorage.setItem('aegis-language', currentLanguage);
  
  // Apply data-i18n text content
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const val = getTranslation(key);
    if (val && val !== key) {
      el.textContent = val;
    }
  });
  
  // Apply data-i18n-placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    const val = getTranslation(key);
    if (val && val !== key) {
      el.placeholder = val;
    }
  });
  
  // Apply data-i18n-title
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    const val = getTranslation(key);
    if (val && val !== key) {
      el.title = val;
    }
  });
  
  // Update html lang attribute
  document.documentElement.lang = currentLanguage;
}
"""

content = content.replace('    // Global Error Logger for UI Debugging', i18n_code + '\n    // Global Error Logger for UI Debugging')

content = content.replace('''    // Load Leads List
    function loadLeads(keepScroll = false) {''', '''let _currentSortBy = 'id';
let _currentSortDir = 'desc';

function sortLeads(col) {
  if (_currentSortBy === col) {
    _currentSortDir = _currentSortDir === 'asc' ? 'desc' : 'asc';
  } else {
    _currentSortBy = col;
    _currentSortDir = 'asc';
  }
  // Update sort indicators
  document.querySelectorAll('[id^="sort-indicator-"]').forEach(el => el.textContent = '');
  const indicator = document.getElementById('sort-indicator-' + col);
  if (indicator) indicator.textContent = _currentSortDir === 'asc' ? ' ↑' : ' ↓';
  loadLeads();
}

function handleLanguageChange(lang) {
  applyLanguage(lang);
  try { pywebview.api.set_config_value('app.gui_language', lang); } catch(e) {}
}

function handleThemeChange(theme) {
  document.body.className = theme;
  localStorage.setItem('aegis-theme', theme);
  try { pywebview.api.set_config_value('app.gui_theme', theme); } catch(e) {}
}

    // Load Leads List
    function loadLeads(keepScroll = false) {''')

content = content.replace('''      _apiCall(() => window.pywebview.api.get_leads(filter, searchLogId), { action: 'Müşteri adaylarını yükle' }).then(leads => {''', '''      _apiCall(() => window.pywebview.api.get_leads(filter, searchLogId, _currentSortBy, _currentSortDir), { action: 'Müşteri adaylarını yükle' }).then(leads => {''')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
