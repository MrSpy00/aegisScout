HTML_CONTENT = """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>aegisScout — İşletme Keşif ve Satış Otomasyonu</title>
  
  <!-- Local fonts only - prevents PyWebView content blocking when offline -->
  <style>
    @font-face { font-family: 'Plus Jakarta Sans'; font-style: normal; font-weight: 400; src: local('Segoe UI'), local('Arial'); }
    @font-face { font-family: 'Plus Jakarta Sans'; font-style: normal; font-weight: 500; src: local('Segoe UI Semibold'), local('Arial'); }
    @font-face { font-family: 'Plus Jakarta Sans'; font-style: normal; font-weight: 600; src: local('Segoe UI Semibold'), local('Arial Bold'); }
    @font-face { font-family: 'Plus Jakarta Sans'; font-style: normal; font-weight: 700; src: local('Segoe UI Bold'), local('Arial Bold'); }
    @font-face { font-family: 'Sora'; font-style: normal; font-weight: 500; src: local('Segoe UI Semibold'), local('Arial'); }
    @font-face { font-family: 'Sora'; font-style: normal; font-weight: 600; src: local('Segoe UI Bold'), local('Arial Bold'); }
    @font-face { font-family: 'Sora'; font-style: normal; font-weight: 700; src: local('Segoe UI Bold'), local('Arial Bold'); }
    @font-face { font-family: 'Sora'; font-style: normal; font-weight: 800; src: local('Segoe UI Black'), local('Arial Black'); }
  </style>
  
  <style>
    /* 🎨 Core CSS Design System */
    :root {
      --bg-base: #0b0c10;
      --bg-surface: #13141a;
      --bg-card: #1b1d25;
      --border-subtle: #262933;
      --border-accent: #323645;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --color-brand: #3b82f6; /* Modern Vibrant Cobalt Blue */
      --color-brand-hover: #1d4ed8;
      --color-accent: #60a5fa;
      --color-success: #10b981;
      --color-warning: #f59e0b;
      --color-danger: #ef4444;
      
      --font-body: 'Plus Jakarta Sans', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-display: 'Sora', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      
      --transition-fast: 0.18s cubic-bezier(0.4, 0, 0.2, 1);
      --transition-normal: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* 🎨 Theme Systems (Neon Dark, Emerald Forest, Cyberpunk, aegis Light) */
    body.theme-neon {
      --bg-base: #0b0c10;
      --bg-surface: #13141a;
      --bg-card: #1b1d25;
      --border-subtle: #262933;
      --border-accent: #323645;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --color-brand: #3b82f6;
      --color-brand-hover: #1d4ed8;
      --color-accent: #60a5fa;
    }

    body.theme-emerald {
      --bg-base: #07110e;
      --bg-surface: #0f1e1a;
      --bg-card: #162c26;
      --border-subtle: #1f3f37;
      --border-accent: #2c5c50;
      --text-main: #f1f7f5;
      --text-muted: #8ea39d;
      --color-brand: #10b981;
      --color-brand-hover: #047857;
      --color-accent: #34d399;
    }

    body.theme-cyberpunk {
      --bg-base: #0f051d;
      --bg-surface: #1a0b36;
      --bg-card: #281452;
      --border-subtle: #3a1e74;
      --border-accent: #522d9b;
      --text-main: #00ffcc;
      --text-muted: #ff007f;
      --color-brand: #ff007f;
      --color-brand-hover: #cc0066;
      --color-accent: #00ffcc;
    }

    body.theme-light {
      --bg-base: #f3f4f6;
      --bg-surface: #ffffff;
      --bg-card: #f9fafb;
      --border-subtle: #e5e7eb;
      --border-accent: #d1d5db;
      --text-main: #111827;
      --text-muted: #4b5563;
      --color-brand: #3b82f6;
      --color-brand-hover: #2563eb;
      --color-accent: #1d4ed8;
    }

    body.theme-midnight {
      --bg-base: #060b13;
      --bg-surface: #0c1424;
      --bg-card: #142036;
      --border-subtle: #1c2d4a;
      --border-accent: #283f66;
      --text-main: #e2e8f0;
      --text-muted: #94a3b8;
      --color-brand: #06b6d4;
      --color-brand-hover: #0891b2;
      --color-accent: #22d3ee;
    }

    body.theme-amber {
      --bg-base: #110d06;
      --bg-surface: #1c150c;
      --bg-card: #2c2214;
      --border-subtle: #3c2e1c;
      --border-accent: #523f26;
      --text-main: #fef3c7;
      --text-muted: #d97706;
      --color-brand: #f59e0b;
      --color-brand-hover: #d97706;
      --color-accent: #fbbf24;
    }

    body.theme-amethyst {
      --bg-base: #0e0517;
      --bg-surface: #180c29;
      --bg-card: #24143d;
      --border-subtle: #351e57;
      --border-accent: #482c75;
      --text-main: #fae8ff;
      --text-muted: #d8b4fe;
      --color-brand: #a855f7;
      --color-brand-hover: #9333ea;
      --color-accent: #c084fc;
    }

    body.theme-rose {
      --bg-base: #14050a;
      --bg-surface: #220c15;
      --bg-card: #321621;
      --border-subtle: #451f2e;
      --border-accent: #5c2c3f;
      --text-main: #ffe4e6;
      --text-muted: #fda4af;
      --color-brand: #f43f5e;
      --color-brand-hover: #e11d48;
      --color-accent: #fb7185;
    }

    body.theme-dracula {
      --bg-base: #1e1f29;
      --bg-surface: #282a36;
      --bg-card: #343746;
      --border-subtle: #44475a;
      --border-accent: #6272a4;
      --text-main: #f8f8f2;
      --text-muted: #8be9fd;
      --color-brand: #ff79c6;
      --color-brand-hover: #bd93f9;
      --color-accent: #50fa7b;
    }

    body.theme-solarized {
      --bg-base: #002b36;
      --bg-surface: #073642;
      --bg-card: #0a404e;
      --border-subtle: #586e75;
      --border-accent: #93a1a1;
      --text-main: #fdf6e3;
      --text-muted: #859900;
      --color-brand: #268bd2;
      --color-brand-hover: #2aa198;
      --color-accent: #cb4b16;
    }

    body.theme-slate {
      --bg-base: #0f172a;
      --bg-surface: #1e293b;
      --bg-card: #334155;
      --border-subtle: #475569;
      --border-accent: #64748b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --color-brand: #38bdf8;
      --color-brand-hover: #0ea5e9;
      --color-accent: #7dd3fc;
    }

    body.theme-monochrome {
      --bg-base: #000000;
      --bg-surface: #111111;
      --bg-card: #222222;
      --border-subtle: #333333;
      --border-accent: #444444;
      --text-main: #ffffff;
      --text-muted: #a3a3a3;
      --color-brand: #ffffff;
      --color-brand-hover: #cccccc;
      --color-accent: #e5e5e5;
    }

    /* 👁️ Password visibility wrapper & Info Icon */
    .input-wrapper {
      position: relative;
      display: flex;
      align-items: center;
      width: 100%;
    }

    .toggle-password-btn {
      position: absolute;
      right: 12px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 6px;
      font-size: 1.1rem;
      transition: color 0.18s;
      user-select: none;
    }

    .toggle-password-btn:hover {
      color: var(--color-brand);
    }

    .info-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background-color: var(--border-accent);
      color: var(--text-muted);
      font-size: 10px;
      font-weight: bold;
      cursor: pointer;
      margin-left: 6px;
      vertical-align: middle;
      transition: background-color 0.18s, color 0.18s;
      user-select: none;
    }

    .info-icon:hover {
      background-color: var(--color-brand);
      color: white;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-base);
      color: var(--text-main);
      font-family: var(--font-body);
      overflow: hidden;
      height: 100vh;
      width: 100vw;
      display: flex;
    }

    /* 🧭 Navigation Sidebar */
    .sidebar {
      width: 260px;
      background-color: var(--bg-surface);
      border-right: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      height: 100%;
      flex-shrink: 0;
      padding: 24px 16px;
      position: relative;
      z-index: 10;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 12px 32px 12px;
    }

    .brand-logo {
      width: 42px;
      height: 42px;
      display: block;
      object-fit: contain !important;
      object-position: center;
      background: transparent;
      border-radius: 12px;
      flex: 0 0 auto;
      box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08);
    }

    .brand-name {
      font-family: var(--font-display);
      font-size: 1.1rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }

    .session-indicator {
      font-size: 0.72rem;
      color: var(--color-success);
      opacity: 0.8;
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 160px;
    }

    .nav-links {
      display: flex;
      flex-direction: column;
      gap: 8px;
      list-style: none;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 16px;
      color: var(--text-muted);
      border-radius: 12px;
      text-decoration: none;
      font-weight: 500;
      cursor: pointer;
      transition: var(--transition-fast);
    }

    .nav-item:hover {
      background-color: var(--border-subtle);
      color: var(--text-main);
    }

    .nav-item.active {
      background-color: var(--color-brand);
      color: white;
    }

    /* 🖥️ Main Window Area */
    .main-content {
      flex-grow: 1;
      height: 100%;
      overflow-y: auto;
      padding: 40px;
      display: flex;
      flex-direction: column;
      gap: 32px;
    }

    .panel {
      display: none;
      animation: fadeIn 0.22s ease-out;
      flex-direction: column;
      gap: 28px;
    }

    .panel.active {
      display: flex;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* 🏷️ Headers and Typography */
    h1 {
      font-family: var(--font-display);
      font-size: 2rem;
      font-weight: 700;
      letter-spacing: -0.03em;
    }

    .subtitle {
      color: var(--text-muted);
      font-size: 0.95rem;
      margin-top: 4px;
    }

    /* 📊 Cards & Grids */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
    }

    .stat-card {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      transition: var(--transition-normal);
    }

    .stat-card:hover {
      transform: translateY(-2px);
      border-color: var(--border-accent);
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
    }

    .stat-val {
      font-family: var(--font-display);
      font-size: 2.2rem;
      font-weight: 700;
      color: var(--text-main);
    }

    .stat-lbl {
      color: var(--text-muted);
      font-size: 0.85rem;
      font-weight: 500;
    }

    /* ⏳ Custom Webkit Scrollbars for premium feel */
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: transparent;
    }
    ::-webkit-scrollbar-thumb {
      background: var(--border-accent);
      border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: var(--text-muted);
    }

    /* 🛠️ Forms & Fields */
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .form-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
    }

    label {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text-muted);
    }

    input, select, textarea {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      color: var(--text-main);
      font-family: var(--font-body);
      font-size: 0.95rem;
      padding: 12px 16px;
      outline: none;
      transition: var(--transition-fast);
    }

    input:hover, select:hover, textarea:hover {
      border-color: var(--border-accent);
    }

    input:focus, select:focus, textarea:focus {
      border-color: var(--color-brand);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
      background-color: var(--bg-base);
    }

    .btn {
      background: linear-gradient(135deg, var(--color-brand) 0%, #1d4ed8 100%);
      color: white;
      border: none;
      border-radius: 12px;
      cursor: pointer;
      font-family: var(--font-body);
      font-weight: 600;
      font-size: 0.95rem;
      padding: 12px 24px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
      text-align: center;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }

    .btn:hover {
      background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-brand) 100%);
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(59, 130, 246, 0.35);
    }

    .btn:active {
      transform: scale(0.96);
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.03);
      color: var(--text-main);
      border: 1px solid var(--border-subtle);
      box-shadow: none;
    }

    .btn-secondary:hover {
      background-color: var(--border-subtle);
      border-color: var(--border-accent);
      transform: translateY(-1px);
    }

    .btn-danger {
      background-color: var(--color-danger);
      color: #ffffff;
      border: 1px solid var(--color-danger);
      box-shadow: 0 2px 6px rgba(239, 68, 68, 0.2);
    }

    .btn-danger:hover {
      background-color: #dc2626;
      color: #ffffff;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(239, 68, 68, 0.35);
    }

    /* 🔒 Button disabled / loading state — prevent double-clicks */
    .btn:disabled,
    .btn[disabled],
    .btn-secondary:disabled,
    .btn-secondary[disabled],
    .btn-danger:disabled,
    .btn-danger[disabled] {
      pointer-events: none;
      opacity: 0.55;
      cursor: not-allowed !important;
      transform: none !important;
      box-shadow: none !important;
      filter: grayscale(0.3);
    }

    /* ⏳ Tiny inline spinner for buttons */
    .btn .btn-spinner {
      display: inline-block;
      width: 12px;
      height: 12px;
      border: 2px solid rgba(255, 255, 255, 0.35);
      border-top-color: #ffffff;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      margin-right: 6px;
      vertical-align: middle;
    }

    /* 📊 Data Tables */
    .table-container {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      overflow: hidden;
    }

    /* Scrollable table wrapper used inside split-left */
    .table-container.scrollable {
      overflow-y: auto;
      max-height: 100%;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }

    th {
      background-color: #181a22;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text-muted);
      font-size: 0.85rem;
      font-weight: 600;
      padding: 16px 24px;
    }

    td {
      border-bottom: 1px solid var(--border-subtle);
      padding: 16px 24px;
      font-size: 0.9rem;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:hover td {
      background-color: #161820;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 4px 10px;
      border-radius: 99px;
      font-size: 0.75rem;
      font-weight: 600;
    }

    .badge-new { background-color: rgba(59, 130, 246, 0.15); color: #60a5fa; }
    .badge-researched { background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; }
    .badge-drafted { background-color: rgba(168, 85, 247, 0.15); color: #c084fc; }
    .badge-contacted { background-color: rgba(16, 185, 129, 0.15); color: #34d399; }
    .badge-replied { background-color: rgba(139, 92, 246, 0.15); color: #a78bfa; }
    .badge-converted { background-color: rgba(16, 185, 129, 0.25); color: #10b981; }
    .badge-rejected { background-color: rgba(239, 68, 68, 0.15); color: #f87171; }
    .badge-do_not_contact { background-color: rgba(239, 68, 68, 0.25); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }

    /* 🛠️ Split Details Layout */
    .split-layout {
      display: flex;
      gap: 32px;
      min-height: 500px;
      height: calc(100vh - 220px);
    }

    .split-left {
      flex: 1.2;
      display: flex;
      flex-direction: column;
      gap: 16px;
      min-height: 0; /* allow children to scroll */
      overflow: hidden;
    }

    .split-right {
      flex: 1;
      background-color: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      padding: 32px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .detail-section {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .detail-section h3 {
      font-family: var(--font-display);
      font-size: 1.1rem;
      margin-bottom: 4px;
    }

    .social-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 8px;
    }
    .social-chip {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      background-color: var(--bg-base);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      font-size: 0.8rem;
      color: var(--text-muted);
      min-height: 36px;
    }
    .social-chip .social-icon {
      flex: 0 0 22px;
      width: 22px;
      height: 22px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 5px;
      font-size: 0.7rem;
      font-weight: 700;
      color: #fff;
      letter-spacing: 0.02em;
    }
    .social-chip.is-active a { color: var(--color-accent); }
    .social-chip.is-inactive { opacity: 0.55; font-style: italic; }
    .social-chip.is-inactive .social-icon { background: var(--border-accent) !important; }

    /* 🔔 Premium Notification System */
    .notif-container {
      position: fixed;
      top: 24px;
      right: 24px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      z-index: 9999;
      pointer-events: none;
    }

    .notif {
      background: linear-gradient(135deg, rgba(27,29,37,0.97) 0%, rgba(19,20,26,0.97) 100%);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 16px;
      padding: 0;
      min-width: 340px;
      max-width: 400px;
      box-shadow: 0 20px 60px -10px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.04);
      overflow: hidden;
      pointer-events: all;
      transform: translateX(120%);
      opacity: 0;
      transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
    }

    .notif.show {
      transform: translateX(0);
      opacity: 1;
    }

    .notif.hide {
      transform: translateX(120%);
      opacity: 0;
      transition: transform 0.35s cubic-bezier(0.4, 0, 0.6, 1), opacity 0.3s ease;
    }

    .notif-inner {
      display: flex;
      align-items: flex-start;
      gap: 14px;
      padding: 18px 20px 14px 20px;
    }

    .notif-icon {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      font-size: 17px;
    }

    .notif.success .notif-icon { background: rgba(16,185,129,0.15); }
    .notif.error   .notif-icon { background: rgba(239,68,68,0.15); }
    .notif.info    .notif-icon { background: rgba(59,130,246,0.15); }
    .notif.warning .notif-icon { background: rgba(245,158,11,0.15); }

    .notif-body {
      flex: 1;
      min-width: 0;
    }

    .notif-title {
      font-family: var(--font-display);
      font-size: 0.88rem;
      font-weight: 700;
      margin-bottom: 3px;
      letter-spacing: -0.01em;
    }

    .notif.success .notif-title { color: #34d399; }
    .notif.error   .notif-title { color: #f87171; }
    .notif.info    .notif-title { color: #60a5fa; }
    .notif.warning .notif-title { color: #fbbf24; }

    .notif-msg {
      font-size: 0.84rem;
      color: var(--text-muted);
      line-height: 1.45;
      word-break: break-word;
    }

    .notif-close {
      width: 24px;
      height: 24px;
      border-radius: 6px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: background 0.15s;
      margin-top: -2px;
    }

    .notif-close:hover { background: rgba(255,255,255,0.08); color: var(--text-main); }

    .notif-progress {
      height: 3px;
      width: 100%;
      background: rgba(255,255,255,0.06);
      position: relative;
      overflow: hidden;
    }

    .notif-progress-bar {
      height: 100%;
      width: 100%;
      transition: width linear;
    }

    .notif.success .notif-progress-bar { background: linear-gradient(90deg, #10b981, #34d399); }
    .notif.error   .notif-progress-bar { background: linear-gradient(90deg, #ef4444, #f87171); }
    .notif.info    .notif-progress-bar { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
    .notif.warning .notif-progress-bar { background: linear-gradient(90deg, #f59e0b, #fbbf24); }

    /* 🪟 Custom Modal Dialog */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.65);
      backdrop-filter: blur(8px);
      z-index: 9998;
      display: none;
      align-items: center;
      justify-content: center;
      opacity: 0;
    }

    .modal-overlay.show {
      display: flex;
      opacity: 1;
    }

    .modal-card {
      background: linear-gradient(145deg, #1b1d25, #13141a);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 20px;
      padding: 32px;
      width: 420px;
      max-width: 90vw;
      box-shadow: 0 32px 80px -10px rgba(0,0,0,0.8);
      transform: scale(0.92) translateY(10px);
      transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    .modal-overlay.show .modal-card {
      transform: scale(1) translateY(0);
    }

    .modal-icon {
      width: 52px;
      height: 52px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      margin-bottom: 20px;
    }

    .modal-icon.confirm-del { background: rgba(239,68,68,0.15); }
    .modal-icon.prompt-icon  { background: rgba(59,130,246,0.15); }
    .modal-icon.confirm-icon { background: rgba(245,158,11,0.15); }

    .modal-title {
      font-family: var(--font-display);
      font-size: 1.2rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin-bottom: 8px;
    }

    .modal-desc {
      font-size: 0.88rem;
      color: var(--text-muted);
      line-height: 1.55;
      margin-bottom: 20px;
    }

    .modal-input {
      width: 100%;
      background: var(--bg-base);
      border: 1px solid var(--border-accent);
      border-radius: 12px;
      color: var(--text-main);
      font-family: var(--font-body);
      font-size: 0.95rem;
      padding: 12px 16px;
      outline: none;
      margin-bottom: 20px;
      transition: border-color 0.18s, box-shadow 0.18s;
    }

    .modal-input:focus {
      border-color: var(--color-brand);
      box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
    }

    .modal-actions {
      display: flex;
      gap: 12px;
      justify-content: flex-end;
    }

    /* ⏳ Spinner Loader */
    .loader {
      border: 3px solid rgba(255, 255, 255, 0.1);
      border-top: 3px solid var(--color-brand);
      border-radius: 50%;
      width: 20px;
      height: 20px;
      animation: spin 0.8s linear infinite;
      display: inline-block;
      vertical-align: middle;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    li.nav-item {
      user-select: none;
      -webkit-user-select: none;
    }

    .hidden {
      display: none !important;
    }

    /* 📋 Kanban Board Styles */
    .kanban-board {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 16px;
      padding: 8px 0;
      height: calc(100vh - 200px);
      align-items: start;
      min-width: 1000px;
    }
    .kanban-column {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      max-height: 100%;
      padding: 12px;
    }
    .kanban-column-header {
      font-size: 0.9rem;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 2px solid var(--color-brand);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .kanban-column-cards {
      display: flex;
      flex-direction: column;
      gap: 10px;
      overflow-y: auto;
      flex-grow: 1;
      padding-right: 4px;
    }
    .kanban-card {
      background-color: var(--bg-base);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 10px;
      cursor: grab;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .kanban-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      border-color: var(--color-brand);
    }
    .kanban-card:active {
      cursor: grabbing;
    }
    
    /* Switch toggle styling */
    .switch input:checked + .slider {
      background-color: var(--color-success) !important;
    }
    .slider:before {
      position: absolute;
      content: "";
      height: 18px;
      width: 18px;
      left: 3px;
      bottom: 3px;
      background-color: white;
      transition: .3s;
      border-radius: 50%;
    }
    .switch input:checked + .slider:before {
      transform: translateX(20px);
    }
    /* Unibox styling */
    .unibox-lead-item {
      padding: 10px 12px;
      border-radius: 8px;
      background: var(--bg-base);
      border: 1px solid var(--border-subtle);
      cursor: pointer;
      transition: background 0.18s, border-color 0.18s;
    }
    .unibox-lead-item:hover, .unibox-lead-item.active {
      background: rgba(59, 130, 246, 0.08);
      border-color: var(--color-brand);
    }
    .unibox-msg-bubble {
      max-width: 70%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 0.85rem;
      line-height: 1.4;
      word-break: break-word;
    }
    .unibox-msg-bubble.outbound {
      align-self: flex-end;
      background: var(--color-brand);
      color: white;
      border-bottom-right-radius: 2px;
    }
    .unibox-msg-bubble.inbound {
      align-self: flex-start;
      background: var(--bg-card);
      color: var(--text-main);
      border-bottom-left-radius: 2px;
      border: 1px solid var(--border-subtle);
    }
    /* Waterfall visual styling */
    .waterfall-flow-step {
      width: 100%;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 10px 14px;
      text-align: center;
      font-size: 0.85rem;
      font-weight: 600;
      position: relative;
    }
    .waterfall-flow-step:not(:last-child)::after {
      content: "↓";
      position: absolute;
      bottom: -22px;
      left: 50%;
      transform: translateX(-50%);
      font-size: 1.1rem;
      color: var(--text-muted);
    }
  </style>
</head>
<body>

  <!-- 🧭 Sidebar Navigation -->
  <div class="sidebar">
    <div class="brand">
      <img src="data:image/png;base64,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" class="brand-logo" style="object-fit: cover;" />
      <div>
        <div class="brand-name">aegisScout</div>
        <div class="session-indicator" id="sidebar-session-name">● Varsayılan Oturum</div>
      </div>
    </div>
    <ul class="nav-links">
      <li class="nav-item active" onclick="switchTab('dashboard', this)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>
        <span data-i18n="menu_dashboard">Dashboard</span>
      </li>
      <li class="nav-item" onclick="switchTab('leads', this)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        <span data-i18n="menu_leads">Adaylar (Leads)</span>
      </li>
      <li class="nav-item" onclick="switchTab('campaigns', this)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
        <span data-i18n="menu_campaigns">Kampanyalar</span>
      </li>
      <li class="nav-item" onclick="switchTab('history', this)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>
        <span data-i18n="menu_history">Geçmiş</span>
      </li>
      <li class="nav-item" onclick="switchTab('searches', this)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <span>Arama Geçmişi</span>
      </li>
      <li class="nav-item" onclick="switchTab('sessions', this)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polygon points="2 17 12 22 22 17"/><polygon points="2 12 12 17 22 12"/></svg>
        <span data-i18n="menu_sessions">Oturumlar</span>
      </li>
      <li class="nav-item" onclick="switchTab('settings', this)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        <span data-i18n="menu_settings">Ayarlar</span>
      </li>
      <li class="nav-item" onclick="switchTab('pipeline', this)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12H3m18-6H3m18 12H3"/></svg>
        <span>Satış Hunisi (Kanban)</span>
      </li>
      <li class="nav-item" onclick="switchTab('unibox', this)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
        <span>Ortak Gelen Kutusu</span>
      </li>
      <li class="nav-item" onclick="switchTab('waterfall', this)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        <span>Şelale Akışı</span>
      </li>
      <li class="nav-item" onclick="switchTab('warmup', this)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        <span>E-Posta Isıtma</span>
      </li>
    </ul>
  </div>

  <!-- 🖥️ Main View Area -->
  <div class="main-content">
    
    <!-- 🎛️ Dashboard Panel -->
    <div id="panel-dashboard" class="panel active">
      <div>
        <h1>Dashboard</h1>
        <p class="subtitle">Müşteri keşif turları başlatın ve genel durum istatistiklerini takip edin.</p>
      </div>

      <!-- 📈 Counter Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-val" id="count-new">0</div>
          <div class="stat-lbl">Yeni Keşfedilen</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" id="count-researched">0</div>
          <div class="stat-lbl">AI Analizi Hazır</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" id="count-contacted">0</div>
          <div class="stat-lbl">İletişime Geçilen</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" id="count-replied">0</div>
          <div class="stat-lbl">Geri Dönüş Yapan</div>
        </div>
      </div>

      <!-- 🔎 Discovery Form Card -->
      <div class="stat-card" style="gap: 20px;">
        <h2 style="font-family: var(--font-display); font-size: 1.3rem;">Yeni Keşif Başlat</h2>
        <div class="form-row">
          <div class="form-group">
            <label for="search-sector">Sektör / Anahtar Kelimeler</label>
            <textarea id="search-sector" rows="3" placeholder="kuaför\nmimar\ndiş kliniği">kuaför</textarea>
          </div>
          <div class="form-group">
            <label for="search-location">Konum / Şehir / Bölge / Ülke</label>
            <textarea id="search-location" rows="3" placeholder="Kadıköy\nİstanbul\nTürkiye">Kadıköy, İstanbul</textarea>
          </div>
          <div class="form-group">
            <label for="search-radius">Yarıçap (km)</label>
            <input type="number" id="search-radius" min="0" placeholder="Boş = Sınırsız" value="10">
          </div>
          <div class="form-group">
            <label for="search-provider">Veri Kaynağı</label>
            <select id="search-provider">
              <option value="all" selected>Tüm Kaynaklar (Önerilen / All Sources)</option>
              <option value="osm">OpenStreetMap (Ücretsiz / OSM)</option>
              <option value="web_search">Web Arama (DDG Scraper / Web Search)</option>
              <option value="google_places">Google Places (API Anahtarlı)</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="search-country">Ülke(ler)</label>
            <textarea id="search-country" rows="2" placeholder="Türkiye\nAlmanya"></textarea>
          </div>
          <div class="form-group">
            <label for="search-city">Şehir(ler)</label>
            <textarea id="search-city" rows="2" placeholder="İstanbul\nBerlin"></textarea>
          </div>
          <div class="form-group">
            <label for="search-region">Bölge / İlçe</label>
            <textarea id="search-region" rows="2" placeholder="Marmara\nKadıköy"></textarea>
          </div>
          <div class="form-group">
            <label for="search-notes">Taslak Notu</label>
            <input type="text" id="search-notes" placeholder="Örneğin: premium odak, yeni açılan işletmeler...">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="search-preset-name">Taslak / Preset Adı</label>
            <input type="text" id="search-preset-name" placeholder="Örneğin: İstanbul kuaför taraması">
          </div>
          <div class="form-group">
            <label for="search-preset-select">Kayıtlı Taslaklar</label>
            <select id="search-preset-select">
              <option value="">Yüklenecek taslak seçin</option>
            </select>
          </div>
          <div class="form-group">
            <label for="search-draft-select">Kayıtlı Arama Taslakları</label>
            <select id="search-draft-select">
              <option value="">Taslak seçin</option>
            </select>
          </div>
          <div class="form-group" style="justify-content: end;">
            <label>&nbsp;</label>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
              <button class="btn btn-secondary" type="button" onclick="saveSearchPresetFromUI()">Preset Kaydet</button>
              <button class="btn btn-secondary" type="button" onclick="saveSearchDraftFromUI()">Taslak Kaydet</button>
              <button class="btn btn-secondary" type="button" onclick="loadSelectedSearchPreset()">Preset Yükle</button>
              <button class="btn btn-secondary" type="button" onclick="loadSelectedSearchDraft()">Taslak Yükle</button>
            </div>
          </div>
        </div>
        <div>
          <button class="btn" id="btn-start-discovery" onclick="triggerDiscovery()">
            <span id="discovery-btn-text">Keşfi Başlat</span>
            <span id="discovery-loader" class="loader hidden"></span>
          </button>
        </div>
        <!-- Progress bar and detailed log area -->
        <div id="discovery-progress-box" class="hidden" style="margin-top: 16px; padding: 16px; background-color: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-weight: 600; font-size: 0.9rem; color: var(--color-accent);">Keşif İlerleme Durumu</span>
            <span id="discovery-percent" style="font-size: 0.85rem; color: var(--text-muted);">0%</span>
          </div>
          <!-- Progress bar track -->
          <div style="width: 100%; height: 6px; background-color: #1a1e27; border-radius: 3px; overflow: hidden; margin-bottom: 12px;">
            <div id="discovery-progress-bar" style="width: 0%; height: 100%; background: linear-gradient(90deg, var(--color-accent), #8b5cf6); transition: width 0.3s ease;"></div>
          </div>
          <!-- Live step logs list -->
          <div id="discovery-progress-text" style="font-family: monospace; font-size: 0.8rem; color: var(--text-muted); max-height: 120px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; border-left: 2px solid var(--border-subtle); padding-left: 10px;">
            <!-- Step log lines injected here -->
          </div>
        </div>
      </div>
    </div>

    <!-- 👤 Leads Panel -->
    <div id="panel-leads" class="panel">
      <div>
        <h1>Adaylar (Leads)</h1>
        <p class="subtitle">Keşfedilmiş olan işletmeleri ve yapay zeka analizlerini inceleyin.</p>
      </div>

      <div class="split-layout">
        <!-- Leads List (Left) -->
        <div class="split-left">
          <div style="display: flex; gap: 8px; margin-bottom: 12px; align-items: center; width: 100%;">
            <input type="text" id="search-leads-input" oninput="filterLeadsTable()" placeholder="Aday listesinde ara..." style="flex-grow: 1; height: 36px; padding: 0 12px; font-size: 0.85rem; border-radius: 8px; background-color: var(--bg-surface); border: 1px solid var(--border-subtle); color: var(--text-main);">
            <select id="filter-status" onchange="loadLeads()" style="width: 140px; height: 36px; padding: 0 8px; border-radius: 8px; background-color: var(--bg-surface); border: 1px solid var(--border-subtle); color: var(--text-main); font-size: 0.8rem; flex-shrink: 0;">
              <option value="all">Tüm Durumlar</option>
              <option value="new">Yeni (Taranmamış)</option>
              <option value="researched">AI Taslağı Hazır</option>
              <option value="drafted">Taslak Var</option>
              <option value="contacted">İletişime Geçildi</option>
              <option value="replied">Yanıt Alındı</option>
              <option value="converted">Dönüştürüldü</option>
              <option value="rejected">Pas Geçildi</option>
              <option value="do_not_contact">İletişim Kurma</option>
            </select>
            <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem; height: 36px; flex-shrink: 0;" onclick="openExportModal()" title="Adayları dışa aktar">
              📥 Dışa Aktar
            </button>
            <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem; height: 36px; flex-shrink: 0;" onclick="openAdvancedDeleteModal()" title="Detaylı silme kriterleri belirleyin">
              🗑️ Detaylı Sil
            </button>
            <button class="btn btn-danger" style="padding: 6px 12px; font-size: 0.8rem; height: 36px; flex-shrink: 0;" onclick="triggerClearLeadsAll()" title="Bu oturumdaki tüm aday verilerini kalıcı olarak siler">
              Tümünü Sil 🗑️
            </button>
          </div>
          
          <!-- Active Search Filter Badge -->
          <div id="active-leads-filters" style="display: none; align-items: center; gap: 8px; margin-bottom: 12px; padding: 6px 12px; background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.2); border-radius: 8px; font-size: 0.8rem; color: var(--text-main);">
            <span id="active-filter-text">Arama Filtresi Aktif</span>
            <span style="cursor: pointer; font-weight: bold; color: #ef4444; margin-left: auto;" onclick="clearActiveSearchFilter()">Temizle ✕</span>
          </div>

          <div id="leads-total-bar" style="font-size:0.8rem; color:var(--text-muted); margin-bottom:6px; padding-left:4px;"></div>

          <div class="table-container scrollable" id="leads-table-container" style="flex:1; min-height:0;">
            <table>
              <thead>
                <tr>
                  <th>İşletme Adı</th>
                  <th>Sektör</th>
                  <th>Konum</th>
                  <th>Web</th>
                  <th>Durum</th>
                </tr>
              </thead>
              <tbody id="leads-table-body">
                <!-- Row template inserted here -->
              </tbody>
            </table>
          </div>
        </div>

        <!-- Lead Detailed View (Right) -->
        <div class="split-right" id="lead-detail-view">
          <div style="text-align: center; color: var(--text-muted); margin-top: 100px;">
            <p>Detayları görmek için sol listeden bir işletme seçin.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 📋 CRM Kanban Pipeline Panel -->
    <div id="panel-pipeline" class="panel">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <div>
          <h1>Satış Hunisi (CRM Kanban)</h1>
          <p class="subtitle">Adaylarınızı sürükleyip bırakarak satış süreçlerinizi yönetin.</p>
        </div>
        <button class="btn btn-secondary" onclick="loadPipeline()" style="padding: 6px 12px; font-size: 0.8rem; height: 36px;">🔄 Yenile</button>
      </div>
      
      <div class="kanban-board" style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; overflow-x: auto; height: calc(100vh - 200px); align-items: start;">
        <!-- Columns -->
        <div class="kanban-column" data-status="new" ondragover="allowDrop(event)" ondrop="dropLead(event)">
          <div class="kanban-column-header">Yeni Adaylar</div>
          <div class="kanban-column-cards scrollable" id="kanban-new" style="display: flex; flex-direction: column; gap: 8px; min-height: 200px; max-height: calc(100vh - 250px); padding: 4px;"></div>
        </div>
        
        <div class="kanban-column" data-status="researched" ondragover="allowDrop(event)" ondrop="dropLead(event)">
          <div class="kanban-column-header">AI Araştırıldı</div>
          <div class="kanban-column-cards scrollable" id="kanban-researched" style="display: flex; flex-direction: column; gap: 8px; min-height: 200px; max-height: calc(100vh - 250px); padding: 4px;"></div>
        </div>
        
        <div class="kanban-column" data-status="contacted" ondragover="allowDrop(event)" ondrop="dropLead(event)">
          <div class="kanban-column-header">Erişim Yapıldı</div>
          <div class="kanban-column-cards scrollable" id="kanban-contacted" style="display: flex; flex-direction: column; gap: 8px; min-height: 200px; max-height: calc(100vh - 250px); padding: 4px;"></div>
        </div>
        
        <div class="kanban-column" data-status="replied" ondragover="allowDrop(event)" ondrop="dropLead(event)">
          <div class="kanban-column-header">Yanıt Alındı</div>
          <div class="kanban-column-cards scrollable" id="kanban-replied" style="display: flex; flex-direction: column; gap: 8px; min-height: 200px; max-height: calc(100vh - 250px); padding: 4px;"></div>
        </div>

        <div class="kanban-column" data-status="meeting_scheduled" ondragover="allowDrop(event)" ondrop="dropLead(event)">
          <div class="kanban-column-header">Toplantı Planlandı</div>
          <div class="kanban-column-cards scrollable" id="kanban-meeting_scheduled" style="display: flex; flex-direction: column; gap: 8px; min-height: 200px; max-height: calc(100vh - 250px); padding: 4px;"></div>
        </div>
        
        <div class="kanban-column" data-status="converted" ondragover="allowDrop(event)" ondrop="dropLead(event)">
          <div class="kanban-column-header">Kazanıldı</div>
          <div class="kanban-column-cards scrollable" id="kanban-converted" style="display: flex; flex-direction: column; gap: 8px; min-height: 200px; max-height: calc(100vh - 250px); padding: 4px;"></div>
        </div>
      </div>
    </div>

    <!-- 🎯 Campaigns Panel -->
    <div id="panel-campaigns" class="panel">
      <div>
        <h1>Kampanyalar</h1>
        <p class="subtitle">Aday gruplarınızı yönetin, yanıt oranlarını izleyin ve kampanya bazlı raporlar alın.</p>
      </div>

      <div class="split-layout">
        <!-- Campaigns List & Form (Left) -->
        <div class="split-left" style="gap: 20px;">
          <!-- Campaign Creation Form -->
          <div class="stat-card" style="gap: 16px;">
            <h2 style="font-family: var(--font-display); font-size: 1.1rem; color: var(--color-accent);">Yeni Kampanya Oluştur</h2>
            <div class="form-row">
              <div class="form-group">
                <label for="camp-name">Kampanya Adı</label>
                <input type="text" id="camp-name" placeholder="ör. Kadıköy Kuaförler Kampanyası">
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="camp-sector-filter">Sektör Filtresi (Opsiyonel)</label>
                <input type="text" id="camp-sector-filter" placeholder="kuaför">
              </div>
              <div class="form-group">
                <label for="camp-location-filter">Konum Filtresi (Opsiyonel)</label>
                <input type="text" id="camp-location-filter" placeholder="Kadıköy">
              </div>
            </div>
            <div>
              <button class="btn" onclick="triggerCreateCampaign()">Kampanya Oluştur</button>
            </div>
          </div>

          <!-- Campaigns Table -->
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Kampanya Adı</th>
                  <th style="text-align: right;">Aday Sayısı</th>
                  <th style="text-align: right;">Yanıt Oranı</th>
                  <th style="text-align: right; width: 60px;">İşlem</th>
                </tr>
              </thead>
              <tbody id="campaigns-table-body">
                <!-- Campaigns injected dynamically -->
              </tbody>
            </table>
          </div>
        </div>

        <!-- Campaign Detailed View (Right) -->
        <div class="split-right" id="campaign-detail-view">
          <div style="text-align: center; color: var(--text-muted); margin-top: 100px;">
            <p>Detayları görmek ve adayları atamak için sol listeden bir kampanya seçin.</p>
          </div>
        </div>
      </div>
    </div>
    <!-- 📜 History Panel -->
    <div id="panel-history" class="panel">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
        <div>
          <h1>İşlem Geçmişi & Oturumlar</h1>
          <p class="subtitle">Yerel veritabanına kaydedilen tüm geçmiş taramalar, araştırmalar ve sistem günlükleri.</p>
        </div>
        <div style="display: flex; gap: 12px;">
          <button class="btn btn-secondary" onclick="triggerNewSession()">Yeni Oturum Başlat</button>
          <button class="btn btn-danger" onclick="triggerClearHistory()">Geçmişi Temizle</button>
        </div>
      </div>

      <div class="table-container" style="max-height: calc(100vh - 280px); overflow-y: auto;">
        <table>
          <thead>
            <tr>
              <th style="width: 180px;">Tarih / Saat</th>
              <th style="width: 150px;">Eylem</th>
              <th>Detaylar</th>
              <th style="width: 60px; text-align: right;">İşlem</th>
            </tr>
          </thead>
          <tbody id="history-table-body">
            <!-- Logs injected dynamically -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- 🔍 Searches Panel -->
    <div id="panel-searches" class="panel">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
        <div>
          <h1>Arama Geçmişi</h1>
          <p class="subtitle">Bu oturumda yapılmış olan tüm müşteri arama/keşif turlarının geçmişi.</p>
        </div>
        <div style="display: flex; gap: 12px; align-items: center;">
          <input type="text" id="filter-search-sector" oninput="filterSearchesTable()" placeholder="Sektör ara..." style="height: 36px; padding: 0 12px; border-radius: 8px; background: var(--bg-surface); border: 1px solid var(--border-subtle); color: var(--text-main); font-size: 0.8rem;">
          <input type="text" id="filter-search-location" oninput="filterSearchesTable()" placeholder="Konum ara..." style="height: 36px; padding: 0 12px; border-radius: 8px; background: var(--bg-surface); border: 1px solid var(--border-subtle); color: var(--text-main); font-size: 0.8rem;">
          <button class="btn btn-secondary" onclick="loadSearchesHistory()" style="padding: 0 16px; height: 36px; font-size: 0.8rem;">🔄 Yenile</button>
        </div>
      </div>

      <div class="table-container" style="max-height: calc(100vh - 220px); overflow-y: auto;">
        <table>
          <thead>
            <tr>
              <th style="width: 180px;">Tarih / Saat</th>
              <th>Sektör / Alan</th>
              <th>Konum / Merkez</th>
              <th>Sağlayıcı</th>
              <th style="width: 180px; text-align: center;">Bulunan Sonuçlar</th>
              <th style="width: 250px; text-align: right;">İşlemler</th>
            </tr>
          </thead>
          <tbody id="searches-table-body">
            <!-- Dynamically loaded search entries -->
          </tbody>
        </table>
      </div>
    </div>

    <div id="panel-settings" class="panel">
      <div>
        <h1 data-i18n="settings_title">Ayarlar</h1>
        <p class="subtitle" data-i18n="settings_subtitle">API anahtarlarını, otomasyon ayarlarını ve bildirim kanallarını yapılandırın.</p>
      </div>

      <div class="stat-card" style="gap: 24px; max-width: 800px;">
        <h2 style="font-family: var(--font-display); font-size: 1.3rem;" data-i18n="settings_sec_env">Uygulama Yapılandırması (.env)</h2>
        
        <!-- LLM Config Section -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <h3 style="font-family: var(--font-display); font-size: 1rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px; color: var(--color-accent);" data-i18n="settings_section_llm">1. LLM / Yapay Zeka Ayarları</h3>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-primary-llm"><span data-i18n="lbl_primary_llm">Birincil LLM Sağlayıcı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_primary_llm'), getTranslation('info_primary_llm_desc'))">!</span></label>
              <select id="cfg-primary-llm">
                <option value="deepseek">DeepSeek API</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic Claude</option>
                <option value="openrouter">OpenRouter API</option>
                <option value="gemini">Google Gemini</option>
                <option value="groq">Groq API</option>
                <option value="mistral">Mistral AI</option>
                <option value="ollama">Ollama (Lokal / Çevrimdışı)</option>
              </select>
            </div>
            <div class="form-group">
              <label for="cfg-fallback-llm"><span data-i18n="lbl_fallback_llm">Yedek (Fallback) Sağlayıcı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_fallback_llm'), getTranslation('info_fallback_llm_desc'))">!</span></label>
              <select id="cfg-fallback-llm">
                <option value="" data-i18n="opt_none">Yok</option>
                <option value="deepseek">DeepSeek API</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic Claude</option>
                <option value="openrouter">OpenRouter API</option>
                <option value="gemini">Google Gemini</option>
                <option value="groq">Groq API</option>
                <option value="mistral">Mistral AI</option>
                <option value="ollama">Ollama</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-deepseek-key"><span data-i18n="lbl_deepseek_key">DeepSeek API Anahtarı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_deepseek_key'), getTranslation('info_deepseek_key_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-deepseek-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-deepseek-key', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="cfg-openai-key"><span data-i18n="lbl_openai_key">OpenAI API Anahtarı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_openai_key'), getTranslation('info_openai_key_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-openai-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-openai-key', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="cfg-anthropic-key"><span data-i18n="lbl_anthropic_key">Anthropic API Anahtarı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_anthropic_key'), getTranslation('info_anthropic_key_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-anthropic-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-anthropic-key', this)">👁️</button>
              </div>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-openrouter-key"><span data-i18n="lbl_openrouter_key">OpenRouter API Anahtarı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_openrouter_key'), getTranslation('info_openrouter_key_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-openrouter-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-openrouter-key', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="cfg-gemini-key"><span data-i18n="lbl_gemini_key">Gemini API Anahtarı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_gemini_key'), getTranslation('info_gemini_key_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-gemini-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-gemini-key', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="cfg-groq-key"><span data-i18n="lbl_groq_key">Groq API Anahtarı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_groq_key'), getTranslation('info_groq_key_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-groq-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-groq-key', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="cfg-mistral-key"><span data-i18n="lbl_mistral_key">Mistral API Anahtarı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_mistral_key'), getTranslation('info_mistral_key_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-mistral-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-mistral-key', this)">👁️</button>
              </div>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-ollama-url"><span data-i18n="lbl_ollama_url">Ollama Base URL (Yerel)</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_ollama_url'), getTranslation('info_ollama_url_desc'))">!</span></label>
              <input type="text" id="cfg-ollama-url" value="http://localhost:11434">
            </div>
            <div class="form-group">
              <label for="cfg-ollama-model"><span>Ollama Model Seçimi</span></label>
              <input type="text" id="cfg-ollama-model" value="llama3.2:3b" placeholder="Örn: llama3.2:3b, qwen2.5:7b">
            </div>
            <div class="form-group" style="display: flex; align-items: flex-end; gap: 8px;">
              <button type="button" class="btn btn-secondary" onclick="checkOllamaStatus()" style="height:36px; padding:0 12px; font-size:0.8rem;">Durum Kontrol</button>
              <button type="button" class="btn btn-secondary" onclick="downloadOllamaModel()" style="height:36px; padding:0 12px; font-size:0.8rem;">Modeli İndir</button>
            </div>
          </div>
          <div id="ollama-status-banner" style="display:none; font-size:0.8rem; padding:8px 12px; border-radius:6px; margin-top:8px; margin-bottom: 12px;"></div>
        </div>

        <!-- Google Places & Discovery Config -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <h3 style="font-family: var(--font-display); font-size: 1rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px; color: var(--color-accent);" data-i18n="settings_section_google">2. Google ve Arama Servisleri</h3>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-google-places-key"><span data-i18n="lbl_google_places_key">Google Places API Anahtarı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_google_places_key'), getTranslation('info_google_places_key_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-google-places-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-google-places-key', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="cfg-google-search-key"><span data-i18n="lbl_google_search_key">Google Custom Search API Anahtarı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_google_search_key'), getTranslation('info_google_search_key_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-google-search-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-google-search-key', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="cfg-google-search-cx"><span data-i18n="lbl_google_search_cx">Google Custom Search CX (Arama Motoru ID)</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_google_search_cx'), getTranslation('info_google_search_cx_desc'))">!</span></label>
              <input type="text" id="cfg-google-search-cx">
            </div>
          </div>
        </div>

        <!-- Instagram Automation Config -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <h3 style="font-family: var(--font-display); font-size: 1rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px; color: var(--color-accent);" data-i18n="settings_section_ig">3. Instagram Otomasyonu (Mod B)</h3>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-ig-username"><span data-i18n="lbl_ig_username">Instagram Kullanıcı Adı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_ig_username'), getTranslation('info_ig_username_desc'))">!</span></label>
              <input type="text" id="cfg-ig-username">
            </div>
            <div class="form-group">
              <label for="cfg-ig-password"><span data-i18n="lbl_ig_password">Instagram Şifresi</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_ig_password'), getTranslation('info_ig_password_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-ig-password">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-ig-password', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="cfg-ig-encryption-key"><span data-i18n="lbl_ig_encryption_key">Oturum Şifreleme Anahtarı</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_ig_encryption_key'), getTranslation('info_ig_encryption_key_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-ig-encryption-key" placeholder="Fernet formatında 32 byte base64 anahtar">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-ig-encryption-key', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <div class="form-row" style="display:flex; gap:8px;">
                <button type="button" class="btn btn-secondary" onclick="loginInstagram()" style="padding:10px 18px;font-size:0.85rem;">🔐 Instagram Giriş Yap</button>
                <button type="button" class="btn btn-secondary" onclick="logoutInstagram()" style="padding:10px 18px;font-size:0.85rem;">🚪 Oturumu Kapat</button>
              </div>
              <small style="color: var(--text-muted); font-size: 0.78rem; display: block; margin-top: 6px;">
                Giriş bilgileri sadece bellekte tutulur, .env'e yazılmaz. Oturum Fernet ile şifrelenmiş dosyada saklanır.
              </small>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-outreach-mode"><span data-i18n="lbl_outreach_mode">Erişim Modu (Outreach Mode)</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_outreach_mode'), getTranslation('info_outreach_mode_desc'))">!</span></label>
              <select id="cfg-outreach-mode" onchange="toggleAutomationAlert()">
                <option value="assisted" data-i18n="opt_assisted">Assisted Mod A (Clipboard & Tarayıcı - Güvenli)</option>
                <option value="full_auto" data-i18n="opt_full_auto">Mod B (Tam Otomasyon - Riskli)</option>
              </select>
            </div>
            <div class="form-group">
              <label for="cfg-max-outreach"><span data-i18n="lbl_max_outreach">Günlük Maksimum Mesaj Limiti</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_max_outreach'), getTranslation('info_max_outreach_desc'))">!</span></label>
              <input type="number" id="cfg-max-outreach" value="15">
            </div>
          </div>

          <!-- Mod B Risk Confirmation Alert -->
          <div id="automation-risk-box" class="hidden" style="background-color: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 12px;">
            <p style="color: var(--color-danger); font-size: 0.85rem; font-weight: 500; line-height: 1.4;" data-i18n="automation_risk_text">
              ⚠️ <b>UYARI:</b> Tam otomasyon modunun etkinleştirilmesi Instagram Kullanım Koşulları'nı (ToS) ihlal eder. Hesabınızın kısıtlanması veya kapatılması riskini anlıyor musunuz?
            </p>
            <div style="display: flex; align-items: center; gap: 8px;">
              <input type="checkbox" id="cfg-confirm-risk" style="width: 18px; height: 18px; cursor: pointer;">
              <label for="cfg-confirm-risk" style="color: var(--text-main); font-weight: 500; cursor: pointer;" data-i18n="automation_confirm_label">Riskleri anladım, tam otomasyonu etkinleştirmek istiyorum.</label>
            </div>
          </div>
        </div>

        <!-- Notifications SMTP/Telegram Config -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <h3 style="font-family: var(--font-display); font-size: 1rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px; color: var(--color-accent);" data-i18n="settings_section_notif">4. Bildirim Kanalları (SMTP / Telegram)</h3>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-tg-token"><span data-i18n="lbl_tg_token">Telegram Bot Token</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_tg_token'), getTranslation('info_tg_token_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-tg-token">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-tg-token', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="cfg-tg-chatid"><span data-i18n="lbl_tg_chatid">Telegram Chat ID</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_tg_chatid'), getTranslation('info_tg_chatid_desc'))">!</span></label>
              <input type="text" id="cfg-tg-chatid">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-smtp-host"><span data-i18n="lbl_smtp_host">SMTP Host</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_smtp_host'), getTranslation('info_smtp_host_desc'))">!</span></label>
              <input type="text" id="cfg-smtp-host">
            </div>
            <div class="form-group">
              <label for="cfg-smtp-port"><span data-i18n="lbl_smtp_port">SMTP Port</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_smtp_port'), getTranslation('info_smtp_port_desc'))">!</span></label>
              <input type="number" id="cfg-smtp-port" value="587">
            </div>
            <div class="form-group">
              <label for="cfg-smtp-user"><span data-i18n="lbl_smtp_user">E-posta Kullanıcı Adı (From)</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_smtp_user'), getTranslation('info_smtp_user_desc'))">!</span></label>
              <input type="text" id="cfg-smtp-user">
            </div>
            <div class="form-group">
              <label for="cfg-smtp-pass"><span data-i18n="lbl_smtp_pass">E-posta Şifresi</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_smtp_pass'), getTranslation('info_smtp_pass_desc'))">!</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-smtp-pass">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-smtp-pass', this)">👁️</button>
              </div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="cfg-imap-host"><span>IMAP Host</span></label>
              <input type="text" id="cfg-imap-host" placeholder="Örn: imap.gmail.com">
            </div>
            <div class="form-group">
              <label for="cfg-imap-port"><span>IMAP Port</span></label>
              <input type="number" id="cfg-imap-port" value="993">
            </div>
            <div class="form-group">
              <label for="cfg-imap-user"><span>IMAP E-posta (Username)</span></label>
              <input type="text" id="cfg-imap-user">
            </div>
            <div class="form-group">
              <label for="cfg-imap-pass"><span>IMAP Şifresi</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-imap-pass">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-imap-pass', this)">👁️</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Proxy, LinkedIn & Scraper APIs Config -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <h3 style="font-family: var(--font-display); font-size: 1rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px; color: var(--color-accent);">4b. Proxy Havuzu &amp; Kazıma API Ayarları</h3>
          <div class="form-row">
            <div class="form-group" style="grid-column: span 2; width: 100%;">
              <label for="cfg-proxy-pool"><span>Proxy Havuzu (Proxy Pool)</span></label>
              <textarea id="cfg-proxy-pool" rows="2" placeholder="http://ip:port, socks5://ip:port (Virgülle ayırın)" style="width:100%; height:60px; resize:vertical; background-color: var(--bg-surface); border: 1px solid var(--border-subtle); color: var(--text-main); padding: 8px; border-radius: 8px; font-family: monospace;"></textarea>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-scraper-key"><span>ScraperAPI Key</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-scraper-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-scraper-key', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="cfg-zenrows-key"><span>ZenRows API Key</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-zenrows-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-zenrows-key', this)">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="cfg-crawlbase-key"><span>Crawlbase Token</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-crawlbase-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-crawlbase-key', this)">👁️</button>
              </div>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-apify-key"><span>Apify API Key</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-apify-key">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-apify-key', this)">👁️</button>
              </div>
            </div>
            <div class="form-group" style="grid-column: span 2;">
              <label for="cfg-linkedin-cookie"><span>LinkedIn Session Cookie (li_at)</span></label>
              <div class="input-wrapper">
                <input type="password" id="cfg-linkedin-cookie">
                <button type="button" class="toggle-password-btn" onclick="togglePasswordVisibility('cfg-linkedin-cookie', this)">👁️</button>
              </div>
            </div>
          </div>
        </div>

        <!-- UI Settings Config -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <h3 style="font-family: var(--font-display); font-size: 1rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 8px; color: var(--color-accent);" data-i18n="settings_section_ui">5. Arayüz Ayarları</h3>
          <div class="form-row">
            <div class="form-group">
              <label for="cfg-lang"><span data-i18n="lbl_cfg_lang">Arayüz Dili (Language)</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_cfg_lang'), getTranslation('info_cfg_lang_desc'))">!</span></label>
              <select id="cfg-lang" onchange="changeLang(this.value)">
                <option value="tr">Türkçe</option>
                <option value="en">English</option>
                <option value="ar">العربية (Arabic)</option>
                <option value="zh">中文 (Chinese)</option>
                <option value="ru">Русский (Russian)</option>
                <option value="de">Deutsch (German)</option>
                <option value="hi">हिन्दी (Hindi)</option>
                <option value="fr">Français (French)</option>
                <option value="es">Español (Spanish)</option>
              </select>
            </div>
            <div class="form-group">
              <label for="cfg-theme"><span data-i18n="lbl_cfg_theme">Arayüz Teması (Theme)</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_cfg_theme'), getTranslation('info_cfg_theme_desc'))">!</span></label>
              <select id="cfg-theme" onchange="changeTheme(this.value)">
                <option value="theme-neon">Neon Dark (Varsayılan)</option>
                <option value="theme-emerald">Emerald Forest</option>
                <option value="theme-cyberpunk">Cyberpunk High-Contrast</option>
                <option value="theme-light">aegis Light Mode</option>
                <option value="theme-midnight">Midnight Ocean</option>
                <option value="theme-amber">Amber Gold</option>
                <option value="theme-amethyst">Amethyst Purple</option>
                <option value="theme-rose">Crimson Rose</option>
                <option value="theme-dracula">Dracula Vampire</option>
                <option value="theme-solarized">Solarized Dark</option>
                <option value="theme-slate">Nordic Slate</option>
                <option value="theme-monochrome">Monochrome Dark</option>
              </select>
            </div>
          </div>
          <div class="form-row" style="margin-top: 12px;">
            <div class="form-group">
              <label for="cfg-show-console"><span data-i18n="lbl_cfg_show_console">Geliştirici Konsolu (CMD)</span> <span class="info-icon" onclick="showInfoModal(getTranslation('lbl_cfg_show_console'), getTranslation('info_cfg_show_console_desc'))">!</span></label>
              <select id="cfg-show-console" onchange="safeSetConfigValue('app.show_console', this.value === 'true')">
                <option value="true">Açık (Log Takibi İçin)</option>
                <option value="false">Kapalı (Sadece Arayüz)</option>
              </select>
            </div>
            <div class="form-group">
              <label><span data-i18n="lbl_open_logs">Log Dosyaları (Logs)</span></label>
              <button class="btn btn-secondary" onclick="safeOpenLogsFolder()" style="margin-top: 4px; padding: 10px 16px; font-size: 0.85rem;" data-i18n="btn_open_logs">Log Klasörünü Aç</button>
            </div>
          </div>
        </div>

        <!-- Action Button -->
        <div>
          <button class="btn" onclick="saveSettings()" data-i18n="btn_save_settings">Ayarları Kaydet</button>
        </div>
      </div>
    </div>

    <!-- 📁 Sessions Panel -->
    <div id="panel-sessions" class="panel">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
        <div>
          <h1>Çalışma Oturumları</h1>
          <p class="subtitle">Her oturumun adayları, kampanyaları ve istatistikleri bağımsız olarak saklanır.</p>
        </div>
        <div>
          <button class="btn" onclick="triggerCreateSession()">Yeni Oturum Başlat</button>
        </div>
      </div>

      <div class="table-container" style="max-height: calc(100vh - 200px); overflow-y: auto;">
        <table style="width: 100%;">
          <thead>
            <tr>
              <th>Oturum Adı</th>
              <th>Oluşturulma Tarihi</th>
              <th style="text-align: right; width: 250px;">Durum / İşlem</th>
            </tr>
          </thead>
          <tbody id="sessions-table-body">
            <!-- Sessions list injected dynamically -->
          </tbody>
        </table>
      </div>
    </div>

  </div>

  <!-- 🔔 Premium Notification Container -->
  <div class="notif-container" id="notif-container"></div>

  <!-- 🪟 Custom Modal Overlay -->
  <div class="modal-overlay" id="modal-overlay">
    <div class="modal-card" id="modal-card">
      <div class="modal-icon" id="modal-icon"></div>
      <div class="modal-title" id="modal-title"></div>
      <div class="modal-desc" id="modal-desc"></div>
      <input class="modal-input" id="modal-input" type="text" style="display:none">
      <div class="modal-actions" id="modal-actions"></div>
    </div>
  </div>

  <!-- 📥 Export Modal -->
  <div class="modal-overlay" id="export-modal">
    <div class="modal-card" style="width: 480px;">
      <div class="modal-icon" style="background: rgba(16,185,129,0.15); color: #10b981; width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 20px;">📥</div>
      <div class="modal-title" style="font-family: var(--font-display); font-size: 1.2rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 8px;">Adayları Dışa Aktar</div>
      <div class="modal-desc" style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.55; margin-bottom: 20px;">Veritabanındaki adayları istediğiniz konum ve formatta kaydedin.</div>
      
      <div style="display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; text-align: left;">
        <div>
          <label style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 6px;">Aktarılacak Kapsam</label>
          <select id="export-scope" style="width: 100%; height: 38px; padding: 0 10px; border-radius: 8px; background: var(--bg-base); border: 1px solid var(--border-accent); color: var(--text-main); font-size: 0.85rem;">
            <option value="all">Tüm Adaylar (Oturumdakiler)</option>
            <option value="filtered">Şu Anki Filtre Eşleşenleri</option>
          </select>
        </div>
        
        <div>
          <label style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 6px;">Dosya Formatı</label>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;" id="export-format-grid">
            <label class="format-select-label" style="display: flex; align-items: center; justify-content: center; gap: 6px; padding: 10px; border: 1px solid var(--border-accent); border-radius: 8px; cursor: pointer; font-size: 0.8rem; background: var(--bg-base);">
              <input type="radio" name="export-format" value=".xlsx" checked style="display:none;">
              📊 Excel
            </label>
            <label class="format-select-label" style="display: flex; align-items: center; justify-content: center; gap: 6px; padding: 10px; border: 1px solid var(--border-accent); border-radius: 8px; cursor: pointer; font-size: 0.8rem; background: var(--bg-base);">
              <input type="radio" name="export-format" value=".csv" style="display:none;">
              📄 CSV
            </label>
            <label class="format-select-label" style="display: flex; align-items: center; justify-content: center; gap: 6px; padding: 10px; border: 1px solid var(--border-accent); border-radius: 8px; cursor: pointer; font-size: 0.8rem; background: var(--bg-base);">
              <input type="radio" name="export-format" value=".pdf" style="display:none;">
              📕 PDF
            </label>
            <label class="format-select-label" style="display: flex; align-items: center; justify-content: center; gap: 6px; padding: 10px; border: 1px solid var(--border-accent); border-radius: 8px; cursor: pointer; font-size: 0.8rem; background: var(--bg-base);">
              <input type="radio" name="export-format" value=".json" style="display:none;">
              💻 JSON
            </label>
            <label class="format-select-label" style="display: flex; align-items: center; justify-content: center; gap: 6px; padding: 10px; border: 1px solid var(--border-accent); border-radius: 8px; cursor: pointer; font-size: 0.8rem; background: var(--bg-base);">
              <input type="radio" name="export-format" value=".html" style="display:none;">
              🌐 HTML
            </label>
          </div>
        </div>
      </div>

      <div class="modal-actions" style="display: flex; gap: 12px; justify-content: flex-end;">
        <button class="btn btn-secondary" onclick="closeExportModal()">İptal</button>
        <button class="btn btn-success" onclick="executeExportLeads()" style="background: #10b981; border-color: #10b981; padding: 10px 22px; font-size: 0.9rem;">Dışa Aktar</button>
      </div>
    </div>
  </div>

  <!-- 🗑️ Advanced Delete Modal -->
  <div class="modal-overlay" id="advanced-delete-modal">
    <div class="modal-card" style="width: 500px; max-height: 90vh; overflow-y: auto;">
      <div class="modal-icon" style="background: rgba(239,68,68,0.15); color: #ef4444; width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 20px;">🗑️</div>
      <div class="modal-title" style="font-family: var(--font-display); font-size: 1.2rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 8px;">Gelişmiş Aday Silme</div>
      <div class="modal-desc" style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.55; margin-bottom: 20px;">Kriterlerinize uyan adayları kalıcı olarak veritabanından silin.</div>
      
      <div style="display: flex; flex-direction: column; gap: 14px; margin-bottom: 24px; text-align: left;">
        <div>
          <label style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Anahtar Kelime (İsim, Web, Adres veya Sektörde Geçen)</label>
          <input type="text" id="del-filter-keyword" placeholder="Örn: berber, instagram.com" style="width:100%; height:36px; padding:0 10px; border-radius:8px; background:var(--bg-base); border:1px solid var(--border-accent); color:var(--text-main); font-size:0.85rem; outline:none;">
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div>
            <label style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Durum / Kategori</label>
            <select id="del-filter-status" style="width:100%; height:36px; padding:0 8px; border-radius:8px; background:var(--bg-base); border:1px solid var(--border-accent); color:var(--text-main); font-size:0.85rem; outline:none;">
              <option value="all">Tüm Durumlar</option>
              <option value="new">Yeni (Taranmamış)</option>
              <option value="researched">AI Analizi Hazır</option>
              <option value="drafted">Taslak Var</option>
              <option value="contacted">İletişime Geçildi</option>
              <option value="replied">Yanıt Alındı</option>
              <option value="converted">Dönüştürüldü</option>
              <option value="rejected">Pas Geçildi</option>
              <option value="do_not_contact">İletişim Kurma</option>
            </select>
          </div>
          <div>
            <label style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Sektör</label>
            <input type="text" id="del-filter-sector" placeholder="Örn: berber" style="width:100%; height:36px; padding:0 10px; border-radius:8px; background:var(--bg-base); border:1px solid var(--border-accent); color:var(--text-main); font-size:0.85rem; outline:none;">
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div>
            <label style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Veri Kaynağı / Sağlayıcı</label>
            <select id="del-filter-source" style="width:100%; height:36px; padding:0 8px; border-radius:8px; background:var(--bg-base); border:1px solid var(--border-accent); color:var(--text-main); font-size:0.85rem; outline:none;">
              <option value="all">Tüm Kaynaklar</option>
              <option value="osm">OSM (OpenStreetMap)</option>
              <option value="google_places">Google Places</option>
              <option value="web_search">Web Search</option>
            </select>
          </div>
          <div>
            <label style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Web Sitesi</label>
            <select id="del-filter-website" style="width:100%; height:36px; padding:0 8px; border-radius:8px; background:var(--bg-base); border:1px solid var(--border-accent); color:var(--text-main); font-size:0.85rem; outline:none;">
              <option value="all">Önemsiz</option>
              <option value="yes">Web Sitesi Olanlar</option>
              <option value="no">Web Sitesi Olmayanlar</option>
            </select>
          </div>
        </div>

        <div>
          <label style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Arama Turları Geçmişinden Seç</label>
          <select id="del-filter-search-log" style="width:100%; height:36px; padding:0 8px; border-radius:8px; background:var(--bg-base); border:1px solid var(--border-accent); color:var(--text-main); font-size:0.85rem; outline:none;">
            <option value="">Arama seçilmedi</option>
          </select>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div>
            <label style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Başlangıç Tarihi</label>
            <input type="date" id="del-filter-start-date" style="width:100%; height:36px; padding:0 10px; border-radius:8px; background:var(--bg-base); border:1px solid var(--border-accent); color:var(--text-main); font-size:0.85rem; outline:none;">
          </div>
          <div>
            <label style="font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Bitiş Tarihi</label>
            <input type="date" id="del-filter-end-date" style="width:100%; height:36px; padding:0 10px; border-radius:8px; background:var(--bg-base); border:1px solid var(--border-accent); color:var(--text-main); font-size:0.85rem; outline:none;">
          </div>
        </div>
        
        <div id="del-calc-summary" style="font-size: 0.8rem; font-weight: bold; color: var(--text-muted); margin-top: 4px; padding: 6px 10px; background: rgba(255,255,255,0.05); border-radius: 6px; text-align: center;">
          Eşleşen aday sayısını görmek için "Hesapla" butonuna basın.
        </div>
      </div>

      <div class="modal-actions" style="display: flex; gap: 12px; justify-content: space-between; align-items: center;">
        <button class="btn btn-secondary" onclick="calculateAdvancedDeleteMatches()" style="font-size: 0.8rem; padding: 8px 16px;">🔍 Eşleşenleri Hesapla</button>
        <div style="display: flex; gap: 12px;">
          <button class="btn btn-secondary" onclick="closeAdvancedDeleteModal()">İptal</button>
          <button class="btn btn-danger" onclick="executeAdvancedDeleteLeads()" id="btn-execute-adv-delete" disabled style="opacity: 0.6; padding: 10px 22px; font-size: 0.9rem;">Kalıcı Olarak Sil</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 📥 Unified Inbox Panel -->
  <div id="panel-unibox" class="panel">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
      <div>
        <h1 style="font-family: var(--font-display);">Ortak Gelen Kutusu (Unified Inbox)</h1>
        <p class="subtitle">E-posta, WhatsApp ve LinkedIn üzerinden gelen tüm yanıtları tek bir ekrandan yönetin.</p>
      </div>
      <button class="btn btn-secondary" onclick="loadUnibox()" style="padding: 6px 12px; font-size: 0.8rem; height: 36px;">🔄 Yenile / Eşitle</button>
    </div>

    <div style="display: flex; gap: 16px; height: calc(100vh - 200px); background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; padding: 12px;">
      <!-- Left Pane: Leads List -->
      <div style="width: 280px; border-right: 1px solid var(--border-subtle); display: flex; flex-direction: column; gap: 8px; padding-right: 12px; overflow-y: auto;" id="unibox-leads-list">
        <p style="color: var(--text-muted); font-size: 0.85rem; text-align: center; margin-top: 20px;">Sohbet geçmişi olan adaylar burada listelenir.</p>
      </div>
      
      <!-- Right Pane: Message Thread & Reply Input -->
      <div style="flex-grow: 1; display: flex; flex-direction: column; height: 100%;">
        <!-- Thread View -->
        <div id="unibox-thread-view" style="flex-grow: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 12px; background: rgba(0,0,0,0.1); border-radius: 8px; margin-bottom: 12px;">
          <div style="text-align: center; color: var(--text-muted); margin-top: 100px;">Soldaki listeden bir aday seçerek sohbeti görüntüleyin.</div>
        </div>
        
        <!-- Reply Input Container -->
        <div id="unibox-reply-container" style="display: none; flex-direction: column; gap: 8px;">
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

  <!-- ⚡ Waterfall Enrichment Panel -->
  <div id="panel-waterfall" class="panel">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
      <div>
        <h1 style="font-family: var(--font-display);">Dinamik Şelale Akış Editörü (Waterfall Enrichment)</h1>
        <p class="subtitle">Veri toplama, zenginleştirme ve doğrulama adımlarının sıralamasını ve kurallarını özelleştirin.</p>
      </div>
      <button class="btn btn-secondary" onclick="saveWaterfallConfigUi()" style="padding: 6px 16px; font-size: 0.8rem; height: 36px; background-color: var(--color-success); color: white;">💾 Kaydet</button>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; height: calc(100vh - 200px); overflow-y: auto;">
      <!-- Left: Config Form -->
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 16px;">
        <h3>Akış Adımları</h3>
        <div id="waterfall-steps-list" style="display: flex; flex-direction: column; gap: 12px;">
          <!-- Rendered by JS -->
        </div>
      </div>
      
      <!-- Right: Flow Visualisation -->
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; position: relative;">
        <h3>Aktif Şelale Şeması</h3>
        <div id="waterfall-flow-visual" style="display: flex; flex-direction: column; align-items: center; gap: 12px; width: 100%; max-width: 320px; margin-top: 20px;">
          <!-- Rendered dynamically by JS -->
        </div>
      </div>
    </div>
  </div>

  <!-- 📈 Email Warmup Panel -->
  <div id="panel-warmup" class="panel">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
      <div>
        <h1 style="font-family: var(--font-display);">P2P E-Posta Isıtma (Email Warm-up)</h1>
        <p class="subtitle">SMTP/IMAP adreslerinizin spame düşmesini engellemek için arka planda yapay zeka ile ısıtın.</p>
      </div>
      <div style="display: flex; gap: 8px;">
        <button class="btn btn-secondary" id="btn-run-warmup-manual" onclick="runWarmupManual()" style="padding: 6px 12px; font-size: 0.8rem; height: 36px; background-color: #6366f1; color: white;">⚡ Manuel Döngü Çalıştır</button>
        <button class="btn btn-secondary" onclick="loadWarmupStatus()" style="padding: 6px 12px; font-size: 0.8rem; height: 36px;">🔄 Yenile</button>
      </div>
    </div>

    <!-- Stats Cards Grid -->
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px;">
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 16px; text-align: center;">
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;">GÖNDERİLEN E-POSTA</div>
        <div id="warmup-stat-sent" style="font-size: 2.2rem; font-weight: 800; color: var(--color-brand);">0</div>
      </div>
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 16px; text-align: center;">
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;">YAPAY CEVAPLAR</div>
        <div id="warmup-stat-replied" style="font-size: 2.2rem; font-weight: 800; color: var(--color-accent);">0</div>
      </div>
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 16px; text-align: center;">
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;">SPAMDAN KURTARILAN</div>
        <div id="warmup-stat-spam_rescued" style="font-size: 2.2rem; font-weight: 800; color: var(--color-success);">0</div>
      </div>
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 16px; text-align: center;">
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;">YILDIZLANAN / ÖNEMLİ</div>
        <div id="warmup-stat-starred" style="font-size: 2.2rem; font-weight: 800; color: var(--color-warning);">0</div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <!-- Warmup Control -->
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 16px;">
        <h3>Isıtma Durumu ve Ayarları</h3>
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; background: var(--bg-base); border-radius: 8px; border: 1px solid var(--border-subtle);">
          <div>
            <div style="font-weight: 600; font-size: 0.95rem;">E-Posta Isıtma (Warm-up)</div>
            <div style="font-size: 0.8rem; color: var(--text-muted);">Aktif olduğunda, tanımlı hesaplar kendi arasında çapraz yazışma simüle eder.</div>
          </div>
          <div>
            <label class="switch" style="position: relative; display: inline-block; width: 44px; height: 24px;">
              <input type="checkbox" id="warmup-toggle-checkbox" onchange="toggleWarmupState(this.checked)" style="opacity: 0; width: 0; height: 0;">
              <span class="slider" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--border-accent); transition: .3s; border-radius: 24px;"></span>
            </label>
          </div>
        </div>
        <div style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.4;">
          <p><b>Nasıl Çalışır?</b></p>
          <p style="margin-top: 4px;">Uygulamanın Unified Watcher arka plan servisi aktif SMTP/IMAP hesaplarınız arasından rastgele iki tanesini seçer. Birinden diğerine yapay zeka tarafından üretilen tamamen doğal iş mailleri gönderilir. Alıcı hesap IMAP ile bağlanıp bu mailleri okur, spam klasöründeyse kurtarır, yıldızlar ve otomatik olarak mantıklı bir cevap yazar.</p>
        </div>
      </div>

      <!-- Accounts Overview -->
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 16px;">
        <h3>Isıtmada Kullanılan SMTP/IMAP Hesapları</h3>
        <div id="warmup-accounts-list" style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px; max-height: 250px; overflow-y: auto;">
          <!-- Populated by JS -->
        </div>
      </div>
    </div>
  </div>

  <!-- ⚙️ JavaScript Application Bridge logic -->
  <script>
    // Global Error Logger for UI Debugging
    window.onerror = function(message, source, lineno, colno, error) {
      // Always attempt to close any stuck modals so buttons behind them stay clickable
      try { _forceCloseAllModals(); } catch (_) { /* best-effort */ }
      try {
        if (window.pywebview && window.pywebview.api) {
          window.pywebview.api.log_js_error(message, source, lineno, colno, error ? error.stack : '');
        }
      } catch (_) { /* swallow */ }
      // Also surface to dev console for live debugging
      try { console.error('[aegisScout JS Error]', message, source, lineno, colno, error); } catch (_) {}
      return false;
    };
    window.onunhandledrejection = function(event) {
      try { _forceCloseAllModals(); } catch (_) {}
      try {
        if (window.pywebview && window.pywebview.api) {
          window.pywebview.api.log_js_error("Unhandled Rejection: " + (event && event.reason ? event.reason : ''), "", 0, 0, "");
        }
      } catch (_) {}
      try { console.error('[aegisScout Unhandled Rejection]', event && event.reason); } catch (_) {}
    };

    /* ══════════════════════════════════════════════
       🛡️ PyWebView Bridge Readiness + Safety Helpers
       ══════════════════════════════════════════════ */
    // Bridge readiness flag — handlers must check this before calling the API.
    window.pywebviewReady = false;
    // Track buttons that are busy so we can re-enable on success/failure.
    const _busyButtons = new WeakSet();
    // Track if scroll event listener has been added
    let _scrollListenerAdded = false;

    function _isBridgeReady() {
      return !!(window.pywebview && window.pywebview.api);
    }

    // Fire a user-visible error when the bridge is missing — never silent.
    function _bridgeUnavailableError(actionName) {
      const msg = (actionName || 'Bu işlem')
        + ' gerçekleştirilemedi: Python köprüsü hazır değil. '
        + 'Lütfen uygulamayı yeniden başlatın veya `aegisScout.log` dosyasını kontrol edin.';
      try { showToast(msg, 'error', 'Köprü Hatası', 6000); } catch (_) {}
      try { console.error('[aegisScout bridge unavailable]', actionName); } catch (_) {}
    }

    // Wrap a Promise-returning pywebview.api call with consistent error UX.
    // Returns a new Promise so `await`/`then` chains keep working.
    function _apiCall(promiseFactory, errContext) {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError(errContext && errContext.action);
        return Promise.reject(new Error('pywebview bridge not ready'));
      }
      try {
        const p = promiseFactory();
        if (!p || typeof p.then !== 'function') {
          // Not a promise — just return it.
          return Promise.resolve(p);
        }
        return p.catch(err => {
          const msg = (errContext && errContext.action ? errContext.action + ': ' : '')
            + (err && err.message ? err.message : (err && err.toString ? err.toString() : 'Bilinmeyen hata'));
          try { showToast(msg, 'error', 'İşlem Hatası', 5000); } catch (_) {}
          try { console.error('[aegisScout api error]', errContext, err); } catch (_) {}
          throw err;
        });
      } catch (err) {
        const msg = (errContext && errContext.action ? errContext.action + ': ' : '')
          + (err && err.message ? err.message : (err && err.toString ? err.toString() : 'Bilinmeyen hata'));
        try { showToast(msg, 'error', 'İşlem Hatası', 5000); } catch (_) {}
        try { console.error('[aegisScout sync api error]', errContext, err); } catch (_) {}
        return Promise.reject(err);
      }
    }

    // Disable a button while a Promise is pending; re-enable on settle.
    // Returns the original Promise so the caller can still await it.
    function _withButtonBusy(btn, promise) {
      if (!btn || !promise || typeof promise.then !== 'function') return promise;
      if (_busyButtons.has(btn)) return promise; // already busy
      _busyButtons.add(btn);
      const prevDisabled = btn.disabled;
      const prevHTML = btn.innerHTML;
      btn.disabled = true;
      btn.setAttribute('aria-busy', 'true');
      // Try to inject a spinner without clobbering the visible text.
      if (btn.querySelector('.btn-spinner') === null) {
        // Use a hidden span for the original text so we can restore it.
        const textHolder = document.createElement('span');
        textHolder.className = 'btn-original-text';
        while (btn.firstChild) textHolder.appendChild(btn.firstChild);
        const spinner = document.createElement('span');
        spinner.className = 'btn-spinner';
        btn.appendChild(spinner);
        btn.appendChild(textHolder);
      } else {
        const existing = btn.querySelector('.btn-spinner');
        if (existing) existing.style.display = 'inline-block';
      }
      const restore = () => {
        try {
          // Move the original text back out and remove the spinner.
          const holder = btn.querySelector('.btn-original-text');
          if (holder) {
            btn.innerHTML = '';
            while (holder.firstChild) btn.appendChild(holder.firstChild);
          } else {
            btn.innerHTML = prevHTML;
          }
        } catch (_) { btn.innerHTML = prevHTML; }
        
        // Background buttons (like discovery and lead research) are managed by separate threads
        // and have explicit callbacks (finishDiscovery, finishResearch) to re-enable them.
        // For other buttons, they should be enabled (disabled = false) once the busy operation settles.
        const isBackgroundBtn = btn.id && (btn.id === 'btn-start-discovery' || btn.id.startsWith('btn-research-'));
        btn.disabled = isBackgroundBtn ? true : false;
        
        btn.removeAttribute('aria-busy');
        _busyButtons.delete(btn);
      };
      return promise.then(v => { restore(); return v; }, err => { restore(); throw err; });
    }

    function safeSetConfigValue(key, val) {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Ayar güncelleme');
        return;
      }
      _apiCall(() => window.pywebview.api.set_config_value(key, val), { action: 'Ayar kaydetme' })
        .then(res => {
          if (res && res.success) {
            showToast('Ayar başarıyla güncellendi.', 'success', 'Başarılı', 3000);
          } else if (res && res.error) {
            showToast('Ayar güncellenemedi: ' + res.error, 'error');
          }
        })
        .catch(() => {});
    }

    function safeOpenLogsFolder() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Log klasörünü açma');
        return;
      }
      _apiCall(() => window.pywebview.api.open_logs_folder(), { action: 'Log klasörünü açma' })
        .catch(() => {});
    }

    // Force-close all known modals (safety net for stuck UI).
    function _forceCloseAllModals() {
      const ids = ['modal-overlay', 'export-modal', 'advanced-delete-modal'];
      ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('show');
      });
      // If a custom modal is open, resolve its promise as cancelled.
      if (typeof _modalResolve === 'function' && _modalResolve) {
        try { _modalResolve(null); } catch (_) {}
        _modalResolve = null;
      }
    }

    // Safe LocalStorage Wrapper
    const safeLocalStorage = {
      getItem: (key) => {
        try {
          return localStorage.getItem(key);
        } catch (e) {
          return null;
        }
      },
      setItem: (key, val) => {
        try {
          localStorage.setItem(key, val);
        } catch (e) {}
      }
    };

    // Helper to safely escape HTML attributes and text
    function escapeHtml(str) {
      if (!str) return "";
      return str
        .split("&").join("&amp;")
        .split("<").join("&lt;")
        .split(">").join("&gt;")
        .split('"').join("&quot;")
        .split("'").join("&#039;");
    }

    // Helper to clean analytical/statistic/chart emojis from AI message drafts
    function cleanDraftText(text) {
      if (!text) return "";
      return text
        .replace(/[📊📈📉💹🔢📋📌📍🗂️🗃️💼🏆🥇🎯⭐⭐️🌟💫✨🔥❗❕⚡🔴🟡🟢📱💻📧📞✉️]/gu, '')
        .replace(/\\s{2,}/g, ' ')
        .trim();
    }

    // Tab switching controller — accepts explicit element to avoid unreliable global `event`
    function switchTab(tabId, el) {
      // Resolve the clicked nav item: prefer explicit `el`, fall back to data attribute lookup
      const navEl = el || document.querySelector(`.nav-item[data-tab="${tabId}"]`);

      document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));

      if (navEl) navEl.classList.add('active');
      const panel = document.getElementById('panel-' + tabId);
      if (panel) panel.classList.add('active');
      saveUiStateDebounced();

      // Load relevant tab data
      if (tabId === 'leads')         loadLeads();
      else if (tabId === 'dashboard') loadStats();
      else if (tabId === 'settings') loadSettings();
      else if (tabId === 'campaigns') loadCampaigns();
      else if (tabId === 'history')   loadHistory();
      else if (tabId === 'sessions')  loadSessions();
      else if (tabId === 'searches')  loadSearchesHistory();
      else if (tabId === 'pipeline')  loadPipeline();
      else if (tabId === 'unibox')    loadUnibox();
      else if (tabId === 'waterfall') loadWaterfallConfig();
      else if (tabId === 'warmup')    loadWarmupStatus();
    }

    /* ══════════════════════════════════════════════
       🔔 PREMIUM NOTIFICATION SYSTEM
       ══════════════════════════════════════════════ */
    const NOTIF_ICONS = {
      success: '✓',
      error:   '✕',
      info:    'ℹ',
      warning: '⚠'
    };
    const NOTIF_TITLES = {
      success: 'Başarılı',
      error:   'Hata',
      info:    'Bilgi',
      warning: 'Uyarı'
    };

    function showToast(message, type = 'info', title = null, duration = 4200) {
      const container = document.getElementById('notif-container');
      const el = document.createElement('div');
      el.className = `notif ${type}`;

      const resolvedTitle = title || NOTIF_TITLES[type] || 'Bildirim';
      const icon = NOTIF_ICONS[type] || 'ℹ';

      el.innerHTML = `
        <div class="notif-inner">
          <div class="notif-icon">${icon}</div>
          <div class="notif-body">
            <div class="notif-title">${resolvedTitle}</div>
            <div class="notif-msg">${message}</div>
          </div>
          <button class="notif-close" onclick="_dismissNotif(this.closest('.notif'))">✕</button>
        </div>
        <div class="notif-progress">
          <div class="notif-progress-bar" id="npb-${Date.now()}"></div>
        </div>
      `;

      container.appendChild(el);

      // Trigger entrance animation
      requestAnimationFrame(() => {
        requestAnimationFrame(() => el.classList.add('show'));
      });

      // Animated progress bar countdown
      const bar = el.querySelector('.notif-progress-bar');
      bar.style.transition = `width ${duration}ms linear`;
      requestAnimationFrame(() => {
        requestAnimationFrame(() => { bar.style.width = '0%'; });
      });

      // Auto dismiss
      const timer = setTimeout(() => _dismissNotif(el), duration);
      el._dismissTimer = timer;
    }

    function _dismissNotif(el) {
      if (!el || el._dismissed) return;
      el._dismissed = true;
      clearTimeout(el._dismissTimer);
      el.classList.remove('show');
      el.classList.add('hide');
      setTimeout(() => el.remove(), 400);
    }

    /* ══════════════════════════════════════════════
       🪟 CUSTOM MODAL SYSTEM (replaces prompt/confirm)
       ══════════════════════════════════════════════ */
    let _modalResolve = null;

    function _openModal({ icon, iconClass, title, desc, inputValue, inputPlaceholder, confirmText, confirmClass, cancelText, showInput, hideCancel }) {
      return new Promise(resolve => {
        _modalResolve = resolve;
        const overlay   = document.getElementById('modal-overlay');
        const iconEl    = document.getElementById('modal-icon');
        const titleEl   = document.getElementById('modal-title');
        const descEl    = document.getElementById('modal-desc');
        const inputEl   = document.getElementById('modal-input');
        const actionsEl = document.getElementById('modal-actions');

        iconEl.className  = `modal-icon ${iconClass || ''}`;
        iconEl.textContent = icon || '?';
        titleEl.textContent = title || '';
        descEl.innerHTML   = desc || '';

        if (showInput) {
          inputEl.style.display = 'block';
          inputEl.value = inputValue || '';
          inputEl.placeholder = inputPlaceholder || '';
          setTimeout(() => inputEl.focus(), 200);
          inputEl.onkeydown = e => { if (e.key === 'Enter') _confirmModal(); if (e.key === 'Escape') _cancelModal(); };
        } else {
          inputEl.style.display = 'none';
        }

        actionsEl.innerHTML = `
          ${hideCancel ? '' : `<button class="btn btn-secondary" onclick="_cancelModal()" style="padding:10px 22px;font-size:0.9rem;">${cancelText || 'İptal'}</button>`}
          <button class="btn ${confirmClass || ''}" onclick="_confirmModal()" style="padding:10px 22px;font-size:0.9rem;">${confirmText || 'Tamam'}</button>
        `;

        overlay.classList.add('show');
      });
    }

    function _confirmModal() {
      const overlay = document.getElementById('modal-overlay');
      const inputEl = document.getElementById('modal-input');
      overlay.classList.remove('show');
      if (_modalResolve) _modalResolve(inputEl.style.display !== 'none' ? inputEl.value.trim() : true);
      _modalResolve = null;
    }

    function _cancelModal() {
      const overlay = document.getElementById('modal-overlay');
      overlay.classList.remove('show');
      if (_modalResolve) _modalResolve(null);
      _modalResolve = null;
    }

    function showInfoModal(title, desc) {
      return _openModal({ icon: 'ℹ️', iconClass: 'prompt-icon', title, desc, confirmText: 'Kapat', showInput: false, hideCancel: true });
    }

    // Close on overlay click
    document.getElementById('modal-overlay').addEventListener('click', e => {
      if (e.target === document.getElementById('modal-overlay')) _cancelModal();
    });

    function showPrompt(title, desc, defaultVal, placeholder) {
      return _openModal({ icon: '✏️', iconClass: 'prompt-icon', title, desc, inputValue: defaultVal, inputPlaceholder: placeholder || '', confirmText: 'Kaydet', cancelText: 'İptal', showInput: true });
    }

    function showConfirm(title, desc, confirmText, isDanger) {
      return _openModal({ icon: isDanger ? '🗑️' : '⚠️', iconClass: isDanger ? 'confirm-del' : 'confirm-icon', title, desc, confirmText: confirmText || 'Onayla', cancelText: 'İptal', showInput: false, confirmClass: isDanger ? 'btn-danger' : '' });
    }

    // Load Dashboard Statistics — uses efficient get_stats() endpoint
    function loadStats() {
      if (!_isBridgeReady()) return;
      // Try new efficient get_stats() first, fall back to get_leads() for compat
      if (window.pywebview.api.get_stats) {
        _apiCall(() => window.pywebview.api.get_stats(), { action: 'İstatistikleri yükle' }).then(stats => {
          if (!stats) return;
          if (stats.error) {
            showToast("İstatistikler alınamadı: " + stats.error, "error");
            return;
          }
          document.getElementById('count-new').innerText = stats.new || 0;
          document.getElementById('count-researched').innerText = stats.researched || 0;
          document.getElementById('count-contacted').innerText = stats.contacted || 0;
          document.getElementById('count-replied').innerText = stats.replied || 0;
        });
      } else {
        _apiCall(() => window.pywebview.api.get_leads(), { action: 'İstatistikleri yükle (uyumluluk)' }).then(leads => {
          if (!leads) return;
          if (leads.error) {
            showToast("İstatistikler alınamadı: " + leads.error, "error");
            return;
          }
          let counts = { new: 0, researched: 0, contacted: 0, replied: 0 };
          leads.forEach(l => { if (counts[l.status] !== undefined) counts[l.status]++; });
          document.getElementById('count-new').innerText = counts.new;
          document.getElementById('count-researched').innerText = counts.researched;
          document.getElementById('count-contacted').innerText = counts.contacted;
          document.getElementById('count-replied').innerText = counts.replied;
        });
      }
    }

    // Trigger Lead Discovery
    function triggerDiscovery() {
      const sector = document.getElementById('search-sector').value;
      const location = document.getElementById('search-location').value;
      const country = document.getElementById('search-country').value;
      const city = document.getElementById('search-city').value;
      const region = document.getElementById('search-region').value;
      const notes = document.getElementById('search-notes').value;
      const radius = document.getElementById('search-radius').value;
      const provider = document.getElementById('search-provider').value;
      const composedLocation = [location, city, region, country].filter(Boolean).join('\\n');

      if (!sector || !location) {
        showToast("Lütfen sektör ve konum alanlarını doldurun.", "error");
        return;
      }

      // Reset progress views
      document.getElementById('discovery-progress-text').innerHTML = '';
      document.getElementById('discovery-progress-bar').style.width = '0%';
      document.getElementById('discovery-percent').innerText = '0%';
      document.getElementById('discovery-progress-box').classList.remove('hidden');

      // Toggle loaders (legacy — also covered by _withButtonBusy below)
      document.getElementById('btn-start-discovery').disabled = true;
      document.getElementById('discovery-btn-text').innerText = "Keşfediliyor...";
      document.getElementById('discovery-loader').classList.remove('hidden');

      updateDiscoveryProgress("Talep alındı, keşif başlatılıyor...");

      const startBtn = document.getElementById('btn-start-discovery');
      const promise = _apiCall(
        () => window.pywebview.api.discover_leads(sector, composedLocation, radius, provider),
        { action: 'Keşif başlat' }
      );
      // Hard-disable while in-flight (defence in depth) — async finishDiscovery
      // callback re-enables the button on the Python side.
      startBtn.disabled = true;
      const wrapped = _withButtonBusy(startBtn, promise);
      wrapped.then(res => {
        if (!res) return;
        if (!res.success) {
          document.getElementById('btn-start-discovery').disabled = false;
          document.getElementById('discovery-btn-text').innerText = "Keşfi Başlat";
          document.getElementById('discovery-loader').classList.add('hidden');
          showToast("Hata: " + (res.error || 'Bilinmeyen hata'), "error");
        }
      }).catch(err => {
        document.getElementById('btn-start-discovery').disabled = false;
        document.getElementById('discovery-btn-text').innerText = "Keşfi Başlat";
        document.getElementById('discovery-loader').classList.add('hidden');
        try { console.error('[aegisScout] discovery failed', err); } catch (_) {}
      });
    }

    function populateSearchPresetLists(presets, drafts) {
      const presetSelect = document.getElementById('search-preset-select');
      const draftSelect = document.getElementById('search-draft-select');
      if (presetSelect) {
        presetSelect.innerHTML = '<option value="">Yüklenecek taslak seçin</option>';
        (presets || []).forEach(item => {
          const option = document.createElement('option');
          option.value = item.id;
          option.textContent = `${item.name} · ${item.provider_name || 'all'}`;
          presetSelect.appendChild(option);
        });
      }
      if (draftSelect) {
        draftSelect.innerHTML = '<option value="">Taslak seçin</option>';
        (drafts || []).forEach(item => {
          const option = document.createElement('option');
          option.value = item.id;
          option.textContent = `${item.name} · ${item.provider_name || 'all'}`;
          draftSelect.appendChild(option);
        });
      }
    }

    async function refreshSearchPresetLists() {
      if (!_isBridgeReady()) return;
      try {
        const [presets, drafts] = await Promise.all([
          _apiCall(() => window.pywebview.api.list_search_presets(), { action: 'Arama şablonlarını listele' }),
          _apiCall(() => window.pywebview.api.list_search_drafts(), { action: 'Arama taslaklarını listele' }),
        ]);
        populateSearchPresetLists(Array.isArray(presets) ? presets : [], Array.isArray(drafts) ? drafts : []);
      } catch (err) {
        console.error('search preset refresh failed', err);
      }
    }

    function refreshSearchPresetListsLater() {
      setTimeout(refreshSearchPresetLists, 0);
    }

    function setSearchFormValues(payload) {
      if (!payload) return;
      const fields = {
        'search-sector': payload.sector_query,
        'search-location': payload.location_query,
        'search-radius': payload.radius_km,
        'search-notes': payload.notes,
        'search-country': payload.country_query,
        'search-city': payload.city_query,
        'search-region': payload.region_query,
      };
      Object.entries(fields).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el && value !== undefined && value !== null) {
          el.value = value;
        }
      });
      const provider = document.getElementById('search-provider');
      if (provider && payload.provider_name) {
        provider.value = payload.provider_name;
      }
    }

    async function saveSearchPresetFromUI() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Arama şablonu kaydetme');
        return;
      }
      const name = document.getElementById('search-preset-name').value.trim();
      const sector = document.getElementById('search-sector').value;
      const location = document.getElementById('search-location').value;
      const radius = document.getElementById('search-radius').value;
      const provider = document.getElementById('search-provider').value;
      const notes = document.getElementById('search-notes').value;
      const res = await _apiCall(() => window.pywebview.api.save_search_preset(name, sector, location, radius, provider, notes), { action: 'Arama şablonu kaydetme' });
      if (!res) return;
      if (res.error) {
        showToast('Preset kaydedilemedi: ' + res.error, 'error');
        return;
      }
      showToast('Preset kaydedildi.', 'success');
      refreshSearchPresetLists();
    }

    async function saveSearchDraftFromUI() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Arama taslağı kaydetme');
        return;
      }
      const name = document.getElementById('search-preset-name').value.trim();
      const sector = document.getElementById('search-sector').value;
      const location = document.getElementById('search-location').value;
      const radius = document.getElementById('search-radius').value;
      const provider = document.getElementById('search-provider').value;
      const country = document.getElementById('search-country').value;
      const city = document.getElementById('search-city').value;
      const region = document.getElementById('search-region').value;
      const keywords = document.getElementById('search-sector').value;
      const notes = document.getElementById('search-notes').value;
      const res = await _apiCall(() => window.pywebview.api.save_search_draft(name, sector, location, radius, provider, country, city, region, keywords, notes), { action: 'Arama taslağı kaydetme' });
      if (!res) return;
      if (res.error) {
        showToast('Taslak kaydedilemedi: ' + res.error, 'error');
        return;
      }
      showToast('Taslak kaydedildi.', 'success');
      refreshSearchPresetLists();
    }

    async function loadSelectedSearchPreset() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Arama şablonu yükleme');
        return;
      }
      const select = document.getElementById('search-preset-select');
      if (!select || !select.value) {
        showToast('Lütfen bir preset seçin.', 'error');
        return;
      }
      const presets = await _apiCall(() => window.pywebview.api.list_search_presets(), { action: 'Arama şablonlarını listele' });
      if (!presets) return;
      const preset = (Array.isArray(presets) ? presets : []).find(item => String(item.id) === String(select.value));
      if (!preset) {
        showToast('Preset bulunamadı.', 'error');
        return;
      }
      setSearchFormValues(preset);
      showToast('Preset yüklendi.', 'success');
    }

    async function loadSelectedSearchDraft() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Arama taslağı yükleme');
        return;
      }
      const select = document.getElementById('search-draft-select');
      if (!select || !select.value) {
        showToast('Lütfen bir taslak seçin.', 'error');
        return;
      }
      const res = await _apiCall(() => window.pywebview.api.load_search_draft(select.value), { action: 'Arama taslağı yükleme' });
      if (!res) return;
      if (res.error) {
        showToast('Taslak yüklenemedi: ' + res.error, 'error');
        return;
      }
      setSearchFormValues(res.draft);
      showToast('Taslak yüklendi.', 'success');
    }

    let allLeads = [];
    let currentSearchLogId = null;
    let allSearches = [];
    let renderLimit = 50;
    let nextRenderIndex = 0;

    // Load Leads List
    function loadLeads(keepScroll = false) {
      if (!_isBridgeReady()) return;
      const filter = document.getElementById('filter-status').value;
      const searchLogId = currentSearchLogId || null;
      
      // Update active search filter badge visibility
      const activeFilterBadge = document.getElementById('active-leads-filters');
      if (activeFilterBadge) {
        if (currentSearchLogId) {
          activeFilterBadge.style.display = 'flex';
        } else {
          activeFilterBadge.style.display = 'none';
        }
      }
      
      _apiCall(() => window.pywebview.api.get_leads(filter, searchLogId), { action: 'Müşteri adaylarını yükle' }).then(leads => {
        if (!leads) return;
        if (leads.error) {
          showToast("Leads alınamadı: " + leads.error, "error");
          return;
        }
        
        allLeads = leads;
        
        const container = document.getElementById('leads-table-container');
        const savedScroll = keepScroll && container ? container.scrollTop : 0;
        
        // Reset scroll and container
        const body = document.getElementById('leads-table-body');
        if (body) body.innerHTML = '';
        
        if (container && !keepScroll) container.scrollTop = 0;
        
        nextRenderIndex = 0;
        
        // Render first chunk
        renderMoreLeads();
        
        // Restore scroll after render
        if (keepScroll && container) {
          requestAnimationFrame(() => { container.scrollTop = savedScroll; });
        }
      });
    }

    // Render more leads (lazy loading/infinite scroll)
    function renderMoreLeads() {
      const body = document.getElementById('leads-table-body');
      if (!body) return;

      const searchInput = document.getElementById('search-leads-input');
      const q = searchInput ? searchInput.value.toLowerCase().trim() : '';

      // Filter array client-side
      const filtered = allLeads.filter(l => {
        if (!q) return true;
        const name = (l.business_name || '').toLowerCase();
        const sector = (l.sector || '').toLowerCase();
        const address = (l.address || '').toLowerCase();
        return name.includes(q) || sector.includes(q) || address.includes(q);
      });

      // Update total matching count bar
      const totalBar = document.getElementById('leads-total-bar');
      if (totalBar) {
        if (q) {
          totalBar.textContent = `${filtered.length} aday eşleşiyor (Toplam: ${allLeads.length})`;
        } else {
          totalBar.textContent = `${allLeads.length} aday listeleniyor`;
        }
      }

      if (filtered.length === 0 && nextRenderIndex === 0) {
        body.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Kayıt bulunamadı.</td></tr>';
        return;
      }

      const end = Math.min(nextRenderIndex + renderLimit, filtered.length);
      for (let i = nextRenderIndex; i < end; i++) {
        const l = filtered[i];
        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        row.onclick = () => selectLead(l.id);

        const websiteText = l.has_website ? 'Evet' : 'Hayır';
        const safeName = escapeHtml(l.business_name);
        const safeAddr = escapeHtml(l.address || '-');
        const safeSector = escapeHtml(l.sector || '-');
        const badgeStatus = escapeHtml(l.status);

        row.innerHTML = `
          <td><b>${safeName}</b></td>
          <td style="color: var(--color-accent); font-size:0.8rem;">${safeSector}</td>
          <td style="color: var(--text-muted);">${safeAddr}</td>
          <td>${websiteText}</td>
          <td>
            <div style="display: flex; gap: 8px; align-items: center; justify-content: space-between; min-width: 90px;">
              <span class="badge badge-${badgeStatus}">${badgeStatus}</span>
              <button style="border: none; background: transparent; padding: 4px; color: var(--color-danger); cursor: pointer; display: flex; align-items: center; justify-content: center;" onclick="event.stopPropagation(); triggerDeleteLead(this)" data-id="${l.id}" data-name="${escapeHtml(l.business_name)}" title="Adayı Sil">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              </button>
            </div>
          </td>
        `;
        body.appendChild(row);
      }

      nextRenderIndex = end;
    }

    // Filter Leads Table by Search Input
    function filterLeadsTable() {
      const body = document.getElementById('leads-table-body');
      if (body) body.innerHTML = '';
      nextRenderIndex = 0;
      renderMoreLeads();
    }

    // Select and view detailed Lead info
    function selectLead(leadId) {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Lead detaylarını yükleme');
        return;
      }
      const detailView = document.getElementById('lead-detail-view');
      detailView.innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 100px;"><span class="loader"></span><p style="margin-top: 12px;">Detaylar yükleniyor...</p></div>';
      
      _apiCall(() => window.pywebview.api.get_lead_details(leadId), { action: 'Lead detaylarını yükle' }).then(res => {
        if (!res) return;
        if (res.error) {
          showToast("Hata: " + res.error, "error");
          return;
        }

        const lead = res.lead;
        const notes = res.notes;
        const messages = res.messages;

        // Find draft message
        let draftMessage = "";
        messages.forEach(m => { if (m.status === 'draft') draftMessage = cleanDraftText(m.content); });

        // Safe URL helpers
        const safeWebUrl = lead.website_url || null;
        const safeIgUrl  = lead.instagram_url || null;
        const webLink    = safeWebUrl
          ? `<a href="${escapeHtml(safeWebUrl)}" target="_blank" style="color: var(--color-accent);">${escapeHtml(safeWebUrl)}</a>`
          : '<span style="color:var(--text-muted)">-</span>';
        const igLink     = safeIgUrl
          ? `<a href="${escapeHtml(safeIgUrl)}" target="_blank" style="color: var(--color-accent);">@${escapeHtml(lead.instagram_handle)}</a>`
          : '<span style="color:var(--text-muted)">-</span>';

        // Build the multi-platform social grid. Each chip shows an icon + handle.
        const socialChips = [
          { key: 'youtube',   label: 'YouTube',   url: lead.youtube_url,  handle: lead.youtube_url,  bg: '#ff0033' },
          { key: 'linkedin',  label: 'LinkedIn',  url: lead.linkedin_url, handle: lead.linkedin_url, bg: '#0a66c2' },
          { key: 'tiktok',    label: 'TikTok',    url: lead.tiktok_url,   handle: lead.tiktok_url,   bg: '#000000' },
          { key: 'facebook',  label: 'Facebook',  url: lead.facebook_url, handle: lead.facebook_url, bg: '#1877f2' },
          { key: 'telegram',  label: 'Telegram',  url: lead.telegram_url, handle: lead.telegram_url, bg: '#229ed9' },
          { key: 'twitter',   label: 'X/Twitter', url: lead.twitter_url,  handle: lead.twitter_url,  bg: '#1d1d1d' },
        ];
        const socialGridHtml = socialChips.map(chip => {
          if (chip.url) {
            return `<div class="social-chip is-active">
              <span class="social-icon" style="background:${chip.bg};">${escapeHtml(chip.label.charAt(0))}</span>
              <a href="${escapeHtml(chip.url)}" target="_blank" title="${escapeHtml(chip.url)}">${escapeHtml(chip.label)}</a>
            </div>`;
          }
          return `<div class="social-chip is-inactive">
            <span class="social-icon" style="background:${chip.bg};">${escapeHtml(chip.label.charAt(0))}</span>
            <span>${escapeHtml(chip.label)}</span>
          </div>`;
        }).join('');

        let notesHtml = notes.map(n =>
          `<div style="background-color: var(--bg-base); padding: 12px; border-radius: 8px; font-size: 0.85rem;">
            <span style="color: var(--color-accent); font-weight: 600;">[${escapeHtml(n.source)}]</span>
            ${escapeHtml(n.content)}
          </div>`
        ).join('') || '<p style="color: var(--text-muted); font-size: 0.85rem;">Henüz araştırma notu eklenmemiş.</p>';

        let messagesHtml = messages.map(m =>
          `<div style="background-color: var(--bg-base); padding: 12px; border-radius: 8px; font-size: 0.85rem; display: flex; flex-direction: column; gap: 4px;">
            <div style="display: flex; justify-content: space-between; font-weight: 600; color: var(--text-muted); font-size: 0.75rem;">
              <span>${m.direction === 'outbound' ? 'Giden' : 'Gelen'} (${escapeHtml(m.channel)})</span>
              <span>${escapeHtml(m.status)}</span>
            </div>
            <div>${escapeHtml(m.content)}</div>
          </div>`
        ).join('') || '<p style="color: var(--text-muted); font-size: 0.85rem;">Mesajlaşma geçmişi yok.</p>';

        detailView.innerHTML = `
          <h2 style="font-family: var(--font-display); font-size: 1.4rem;">${escapeHtml(lead.business_name)}</h2>

          <div class="detail-section">
            <div style="display: flex; gap: 24px; font-size: 0.85rem; color: var(--text-muted);">
              <span><b>Sektör:</b> ${escapeHtml(lead.sector || '-')}</span>
              <span><b>Puan:</b> ${lead.rating || '-'} (${lead.review_count || '0'} yorum)</span>
            </div>
            <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">
              <span><b>Adres:</b> ${escapeHtml(lead.address || '-')}</span>
            </div>
            <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">
              <span><b>Telefon:</b> ${escapeHtml(lead.phone || '-')}</span>
            </div>
            <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">
              <span><b>Web:</b> ${webLink}</span>
            </div>
            <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">
              <span><b>Instagram:</b> ${igLink}</span>
            </div>
          </div>

          <div class="detail-section">
            <h3>Sosyal Medya</h3>
            <div class="social-grid">${socialGridHtml}</div>
            <div style="display: flex; gap: 8px; margin-top: 6px; flex-wrap: wrap;">
              <button class="btn btn-secondary" id="btn-social-${lead.id}" style="font-size: 0.8rem;" onclick="triggerSocialDiscovery(${lead.id})">🌐 Çoklu Platform Keşfi</button>
              <button class="btn btn-secondary" id="btn-verify-email-${lead.id}" style="font-size: 0.8rem; background-color: #10b981; color: white;" onclick="triggerEmailVerify('${lead.email}', ${lead.id})">🛡️ E-Postayı Doğrula</button>
              <button class="btn btn-secondary" id="btn-screen-audit-${lead.id}" style="font-size: 0.8rem; background-color: #6366f1; color: white;" onclick="triggerScreenAudit(${lead.id})">🚀 Screen-Audit Başlat</button>
              <button class="btn btn-secondary" id="btn-waterfall-${lead.id}" style="font-size: 0.8rem; background-color: #f59e0b; color: white;" onclick="triggerWaterfall(${lead.id})">⚡ Şelale Akışı Çalıştır</button>
            </div>
            ${lead.instagram_bio ? `
            <div style="margin-top: 8px; padding: 10px 12px; background: var(--bg-base); border: 1px solid var(--border-subtle); border-radius: 8px; font-size: 0.8rem; color: var(--text-muted); white-space: pre-wrap;">${escapeHtml(lead.instagram_bio)}</div>
            ` : ''}
          </div>

          <div style="display: flex; gap: 12px; flex-wrap: wrap;">
            <button class="btn btn-secondary" id="btn-research-${lead.id}" onclick="triggerResearch(${lead.id})">Araştır &amp; AI Taslağı Üret</button>
            <button class="btn btn-danger" onclick="pasGecLead(${lead.id})">Pas Geç</button>
            <button class="btn btn-secondary" style="font-size:0.8rem;" onclick="doNotContactLead(${lead.id})">🚫 İletişim Kurma</button>
          </div>

          <div class="detail-section">
            <h3>Teknik Denetim &amp; AI Öncelik Skoru</h3>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 12px;">
              <div style="background-color: var(--bg-base); padding: 10px; border-radius: 8px; border: 1px solid var(--border-subtle);">
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px;">AI ÖNCELİK ETİKETİ</div>
                <div style="font-size: 0.95rem; font-weight: bold; color: ${lead.priority_score >= 75 ? '#ef4444' : '#3b82f6'};">
                  ${escapeHtml(lead.priority_label || 'Hesaplanmadı')}
                </div>
              </div>
              <div style="background-color: var(--bg-base); padding: 10px; border-radius: 8px; border: 1px solid var(--border-subtle);">
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px;">ÖNCELİK SKORU</div>
                <div style="font-size: 0.95rem; font-weight: bold; color: var(--text-main);">
                  ${lead.priority_score !== null ? lead.priority_score.toFixed(0) + '/100' : 'Hesaplanmadı'}
                </div>
              </div>
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.85rem;">
              <div><b>E-posta:</b> ${escapeHtml(lead.email || 'Bulunamadı')}</div>
              <div><b>Doğrulama Durumu:</b> 
                ${lead.email_verification_status ? `
                  <span style="font-weight:bold; color:${lead.email_verification_status === 'valid' ? '#10b981' : (lead.email_verification_status === 'mx_only' ? '#3b82f6' : '#ef4444')};">
                    ${lead.email_verification_status.toUpperCase()}
                  </span>
                  <br><small style="color:var(--text-muted);">${escapeHtml(lead.email_verification_details || '')}</small>
                ` : '<span style="color:var(--text-muted)">Doğrulanmadı</span>'}
              </div>
              <div><b>KVKK / Çerez Uyumluluğu:</b> 
                ${lead.kvkk_compliant === true ? '<span style="color:#10b981; font-weight:bold;">✓ Uyumlu</span>' : (lead.kvkk_compliant === false ? '<span style="color:#ef4444; font-weight:bold;">✕ Uyumsuz (Politika eksik)</span>' : '<span style="color:var(--text-muted)">Denetlenmedi</span>')}
              </div>
              <div><b>Kırık Link Denetimi:</b> 
                ${lead.has_broken_links === true ? `<span style="color:#ef4444; font-weight:bold;">⚠ Kırık Link Var</span><br><small style="color:var(--text-muted);">${escapeHtml(lead.broken_links_details || '')}</small>` : (lead.has_broken_links === false ? '<span style="color:#10b981; font-weight:bold;">✓ Kırık Link Yok</span>' : '<span style="color:var(--text-muted)">Denetlenmedi</span>')}
              </div>
              <div style="display: flex; gap: 16px; margin-top: 4px;">
                <span><b>PageSpeed (Masaüstü):</b> ${lead.page_speed_desktop !== null ? lead.page_speed_desktop + '/100' : '-'}</span>
                <span><b>PageSpeed (Mobil):</b> ${lead.page_speed_mobile !== null ? lead.page_speed_mobile + '/100' : '-'}</span>
              </div>
              <div style="margin-top: 4px; padding: 8px; background: rgba(255,255,255,0.02); border-radius: 6px; font-family: monospace; font-size:0.75rem; border: 1px dashed var(--border-subtle); word-break: break-all;">
                <b>Kullanılan Teknolojiler:</b> ${escapeHtml(lead.technologies || 'Bilinmiyor')}
              </div>
              
              ${lead.screenshot_path ? `
              <div style="margin-top: 12px;">
                <b>Sitenin Ekran Görüntüsü:</b>
                <div style="margin-top: 6px; border: 1px solid var(--border-subtle); border-radius: 8px; overflow: hidden; max-height: 180px;">
                  <img src="file:///${lead.screenshot_path}" style="width:100%; object-fit:cover; cursor:pointer;" onclick="viewFullImage('file:///${lead.screenshot_path}')" />
                </div>
              </div>
              ` : ''}
              ${lead.visual_audit_notes ? `
              <div style="margin-top: 8px; padding: 10px; background: rgba(99,102,241,0.05); border: 1px solid rgba(99,102,241,0.2); border-radius: 8px;">
                <div style="font-size: 0.75rem; font-weight: bold; color: #818cf8; margin-bottom: 4px;">GÖRSEL ANALİZ NOTLARI</div>
                <div style="font-size: 0.8rem; color: var(--text-main);">${escapeHtml(lead.visual_audit_notes)}</div>
              </div>
              ` : ''}
              ${lead.outreach_hook ? `
              <div style="margin-top: 8px; padding: 10px; background: rgba(245,158,11,0.05); border: 1px solid rgba(245,158,11,0.2); border-radius: 8px;">
                <div style="font-size: 0.75rem; font-weight: bold; color: #fbbf24; margin-bottom: 4px;">KİŞİSELLEŞTİRİLMİŞ KANCA (THE HOOK)</div>
                <div style="font-size: 0.8rem; color: var(--text-main); font-style: italic;">"${escapeHtml(lead.outreach_hook)}"</div>
                <div style="margin-top: 6px; display:flex; justify-content:flex-end;">
                  <button class="btn btn-secondary" style="font-size:0.7rem; padding:2px 8px; height:24px;" onclick="copyToClipboard('${escapeHtml(lead.outreach_hook)}')">📋 Kopyala</button>
                </div>
              </div>
              ` : ''}
            </div>
          </div>

          <div class="detail-section">
            <h3>Araştırma Notları &amp; Skor</h3>
            <p style="font-size: 0.9rem; margin-bottom: 8px;"><b>Web Kalite Skoru:</b> ${lead.website_quality_score !== null ? lead.website_quality_score + '/100' : 'Hesaplanmamış'}</p>
            <div style="display: flex; flex-direction: column; gap: 8px;">${notesHtml}</div>
          </div>

          <div class="detail-section">
            <h3>CRM İletişim Günlüğü</h3>
            <div style="display: flex; gap: 8px; margin-bottom: 12px;">
              <input type="text" id="crm-note-input" placeholder="Arama, toplantı veya not ekleyin..." style="flex-grow: 1; padding: 0 10px; border-radius: 6px; background-color: var(--bg-base); border: 1px solid var(--border-subtle); color: var(--text-main); font-size:0.85rem; height:32px;">
              <button class="btn btn-secondary" onclick="addCrmNote(${lead.id})" style="padding: 0 12px; font-size: 0.8rem; height: 32px; flex-shrink: 0;">Ekle</button>
            </div>
            <div id="crm-logs-list" style="display: flex; flex-direction: column; gap: 8px; max-height: 200px; overflow-y: auto; background-color: rgba(255,255,255,0.02); padding: 8px; border-radius: 6px; border: 1px solid var(--border-subtle);">
              <p style="color: var(--text-muted); font-size: 0.8rem;">Yükleniyor...</p>
            </div>
          </div>

          <div class="detail-section">
            <h3>AI Outreach Taslağı</h3>
            <textarea id="edit-draft-box" style="width: 100%; height: 120px; resize: none;" placeholder="Mesaj taslağı oluşturmak için 'Araştır' komutunu çalıştırın.">${escapeHtml(draftMessage)}</textarea>
            <div style="display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap;">
              <button class="btn btn-secondary" onclick="saveDraft(${lead.id})">Taslağı Kaydet</button>
              <button class="btn" onclick="sendAssisted(${lead.id})">Gönder (Assisted A)</button>
              <button class="btn btn-secondary" onclick="sendAutomated(${lead.id})">Gönder (Auto B)</button>
              <button class="btn btn-secondary" style="background-color: #25d366; color: white;" onclick="launchWhatsApp(${lead.id})">🟢 WhatsApp (Manuel)</button>
              <button class="btn btn-secondary" style="background-color: #128c7e; color: white;" onclick="launchWhatsAppAuto(${lead.id})">📲 WhatsApp (Otomatik)</button>
              <button class="btn btn-secondary" style="background-color: #0077b5; color: white;" onclick="launchLinkedInAuto(${lead.id})">🔗 LinkedIn (Otomatik)</button>
              <button class="btn btn-secondary" style="background-color: var(--color-brand); color: white;" onclick="sendSmtpEmail(${lead.id})">📧 E-Posta Gönder</button>
              <button class="btn btn-secondary" style="background-color: #374151; color: var(--text-muted); font-size: 0.75rem;" onclick="loginWhatsApp()">🔑 WhatsApp Giriş</button>
              <button class="btn btn-secondary" style="background-color: #374151; color: var(--text-muted); font-size: 0.75rem;" onclick="loginLinkedIn()">🔑 LinkedIn Giriş</button>
            </div>
          </div>

          <div class="detail-section">
            <h3>Etkinlik & Mesaj Geçmişi</h3>
            <div style="display: flex; flex-direction: column; gap: 8px;">
              ${messagesHtml}
            </div>
          </div>
        `;

        _apiCall(() => window.pywebview.api.get_crm_logs(lead.id), { action: 'CRM loglarını yükle' }).then(cres => {
          const crmDiv = document.getElementById('crm-logs-list');
          if (crmDiv && cres && cres.logs) {
            crmDiv.innerHTML = cres.logs.map(log => `
              <div style="background-color: var(--bg-base); padding: 8px 10px; border-radius: 6px; font-size: 0.8rem; border-left: 3px solid var(--color-brand); text-align: left;">
                <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:var(--text-muted); margin-bottom:4px;">
                  <span>CRM Günlüğü</span>
                  <span>${new Date(log.created_at).toLocaleString()}</span>
                </div>
                <div>${escapeHtml(log.note)}</div>
              </div>
            `).join('') || '<p style="color: var(--text-muted); font-size: 0.8rem;">Henüz CRM notu girilmemiş.</p>';
          }
        });
      });
    }

    // Trigger multi-platform social discovery (YouTube/LinkedIn/TikTok/...)
    function triggerSocialDiscovery(leadId) {
      const btn = document.getElementById('btn-social-' + leadId);
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="loader" style="width: 12px; height: 12px; margin-right: 6px;"></span> Aranıyor...`;
      }
      showToast("Çoklu platform keşfi başlatıldı (YouTube, LinkedIn, TikTok, Facebook, Telegram, X)...", "info");
      _apiCall(
        () => window.pywebview.api.discover_social_profiles(leadId),
        { action: 'Çoklu platform keşfi' }
      ).then(res => {
        if (!res) return;
        if (res.error) {
          if (btn) {
            btn.disabled = false;
            btn.innerHTML = '🌐 Çoklu Platform Keşfi';
          }
          showToast("Hata: " + res.error, "error");
        } else if (res.queued) {
          showToast("Keşif arka planda başlatıldı. Tamamlandığında güncellenecektir.", "info");
        }
      }).catch(err => {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '🌐 Çoklu Platform Keşfi';
        }
        try { console.error('[aegisScout] triggerSocialDiscovery failed', err); } catch (_) {}
      });
    }

    // Callback called from python background thread when social discovery finishes
    function finishSocialDiscovery(leadId, success, errorMsg) {
      const btn = document.getElementById('btn-social-' + leadId);
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '🌐 Çoklu Platform Keşfi';
      }
      if (success) {
        showToast("Çoklu platform keşfi tamamlandı!", "success");
        // Re-render the lead detail panel and the leads table.
        const viewTitle = document.querySelector('#lead-detail-view h2');
        if (viewTitle) selectLead(leadId);
        loadLeads(true);
      } else {
        showToast("Çoklu platform keşfi hatası: " + errorMsg, "error");
      }
    }

    // Trigger AI / Scraper Research — find button by unique ID, not generic querySelector
    function triggerResearch(leadId) {
      const btn = document.getElementById('btn-research-' + leadId);
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="loader" style="width: 14px; height: 14px; margin-right: 6px;"></span> Araştırılıyor...`;
      }
      showToast("Web sitesi taranıyor ve AI analiz mesajı üretiliyor...", "info");
      const promise = _apiCall(
        () => window.pywebview.api.research_lead(leadId),
        { action: 'Araştırma' }
      );
      const wrapped = btn ? _withButtonBusy(btn, promise) : promise;
      wrapped.then(res => {
        if (!res) return;
        if (res.error) {
          if (btn) {
            btn.disabled = false;
            btn.innerHTML = 'Araştır &amp; AI Taslağı Üret';
          }
          showToast("Hata: " + res.error, "error");
        } else if (res.queued) {
          showToast("Araştırma arka planda başlatıldı. Tamamlandığında güncellenecektir.", "info");
        }
      }).catch(err => {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = 'Araştır &amp; AI Taslağı Üret';
        }
        try { console.error('[aegisScout] triggerResearch failed', err); } catch (_) {}
      });
    }

    // Callback called from python background thread when research finishes
    function finishResearch(leadId, success, errorMsg) {
      const btn = document.getElementById('btn-research-' + leadId);
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = 'Araştır &amp; AI Taslağı Üret';
      }
      if (success) {
        showToast("Araştırma ve mesaj taslağı başarıyla oluşturuldu!", "success");
        // Only refresh lead details if this lead is still viewed
        const viewTitle = document.querySelector('#lead-detail-view h2');
        if (viewTitle) {
          selectLead(leadId);
        }
        loadLeads(true);
        loadStats();
        loadHistory();
      } else {
        showToast("Araştırma hatası: " + errorMsg, "error");
      }
    }

    // Mark lead as do_not_contact
    function doNotContactLead(leadId) {
      const promise = _apiCall(
        () => window.pywebview.api.update_lead_status(leadId, 'do_not_contact'),
        { action: 'Aday durum güncelleme' }
      );
      promise.then(res => {
        if (!res) return;
        if (res.success) {
          showToast("İşletme 'İletişim Kurma' olarak işaretlendi.", "info");
          loadLeads(true); loadStats(); loadHistory();
          document.getElementById('lead-detail-view').innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 100px;"><p>Detayları görmek için sol listeden bir işletme seçin.</p></div>';
        } else if (res.error) {
          showToast("Durum güncellenemedi: " + res.error, "error");
        }
      }).catch(() => { /* _apiCall already toasted */ });
    }

    // Client-side CSV export of currently visible leads
    function exportLeadsCSV() {
      const rows = document.querySelectorAll('#leads-table-body tr');
      const visible = Array.from(rows).filter(r => r.style.display !== 'none' && r.cells.length > 2);
      if (visible.length === 0) {
        showToast("Dışa aktarılacak kayıt bulunamadı.", "warning");
        return;
      }
      const header = ['İşletme Adı', 'Sektör', 'Adres', 'Web', 'Durum'];
      const lines = [header.join(',')];
      visible.forEach(r => {
        const cells = Array.from(r.cells).map(c => '"' + c.textContent.replace(/"/g, '""') + '"');
        lines.push(cells.join(','));
      });
      const blob = new Blob([lines.join('\\n')], { type: 'text/csv;charset=utf-8;' });
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href = url;
      a.download = 'aegisScout_leads_' + new Date().toISOString().slice(0,10) + '.csv';
      a.click();
      URL.revokeObjectURL(url);
      showToast(`${visible.length} aday CSV olarak dışa aktarıldı.`, "success");
    }

    // Save modified message draft
    function saveDraft(leadId) {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Mesaj taslağını kaydetme');
        return;
      }
      const content = document.getElementById('edit-draft-box').value;
      _apiCall(() => window.pywebview.api.save_message_draft(leadId, content), { action: 'Mesaj taslağını kaydet' }).then(res => {
        if (!res) return;
        if (res.success) {
          showToast("Mesaj taslağı başarıyla kaydedildi.", "success");
          selectLead(leadId);
        } else {
          showToast("Kaydetme hatası: " + res.error, "error");
        }
      });
    }

    // Mark as pas gec / rejected
    function pasGecLead(leadId) {
      const promise = _apiCall(
        () => window.pywebview.api.update_lead_status(leadId, 'rejected'),
        { action: 'Aday durum güncelleme' }
      );
      promise.then(res => {
        if (!res) return;
        if (res.success) {
          showToast("İşletme pas geçildi.", "info");
          loadLeads(true);
          loadStats();
          loadHistory();
          document.getElementById('lead-detail-view').innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 100px;"><p>Detayları görmek için sol listeden bir işletme seçin.</p></div>';
        } else if (res.error) {
          showToast("Durum güncellenemedi: " + res.error, "error");
        }
      }).catch(() => { /* _apiCall already toasted */ });
    }

    // Outreach Assisted mode dispatch
    function sendAssisted(leadId) {
      showToast("Mesaj panoya kopyalanıyor ve Instagram açılıyor...", "info");
      const promise = _apiCall(
        () => window.pywebview.api.send_assisted(leadId),
        { action: 'Mod A mesaj gönderimi' }
      );
      promise.then(res => {
        if (!res) return;
        if (res.success) {
          showToast("Başarılı! Panodan yapıştırıp gönderebilirsiniz.", "success");
          selectLead(leadId);
          loadLeads(true);
        } else if (res.error) {
          showToast("Hata: " + res.error, "error");
        }
      }).catch(() => { /* _apiCall already toasted */ });
    }

    // Outreach Automated Mod B dispatch
    function sendAutomated(leadId) {
      showToast("Instagram API üzerinden otomatik DM gönderimi başlatıldı...", "info");
      const promise = _apiCall(
        () => window.pywebview.api.send_automated(leadId),
        { action: 'Mod B mesaj gönderimi' }
      );
      promise.then(res => {
        if (!res) return;
        if (res.error) {
          showToast("Otomasyon hatası: " + res.error, "error");
        } else if (res.queued) {
          showToast("Gönderim sıraya alındı, arka planda gönderiliyor...", "info");
        }
      }).catch(err => {
        try { console.error('[aegisScout] sendAutomated failed', err); } catch (_) {}
      });
    }

    // Callback called from python background thread when automated send finishes
    function finishSendAutomated(leadId, success, errorMsg) {
      if (success) {
        showToast("Mesaj otomatik olarak başarıyla gönderildi!", "success");
        const viewTitle = document.querySelector('#lead-detail-view h2');
        if (viewTitle) {
          selectLead(leadId);
        }
        loadLeads(true);
        loadStats();
        loadHistory();
      } else {
        showToast("Otomatik gönderim hatası: " + errorMsg, "error");
      }
    }

    // Toggle automation confirmation checkbox box
    function toggleAutomationAlert() {
      const mode = document.getElementById('cfg-outreach-mode').value;
      const riskBox = document.getElementById('automation-risk-box');
      if (mode === 'full_auto') {
        riskBox.classList.remove('hidden');
      } else {
        riskBox.classList.add('hidden');
      }
    }

    // Load configurations — SANITIZED shape from is_configured().
    // Sensitive fields (api keys, passwords) are NOT returned by the bridge,
    // so their input boxes are left blank and the user must re-type them.
    function loadSettings() {
      if (!_isBridgeReady()) return;
      _apiCall(() => window.pywebview.api.get_settings(), { action: 'Ayarları yükle' }).then(cfg => {
        if (!cfg) return;
        if (cfg.error) {
          showToast("Ayarlar yüklenemedi: " + cfg.error, "error");
          return;
        }

        // Non-sensitive safe values (these are present in the sanitized shape)
        const safe = (id, val, fallback) => {
          const el = document.getElementById(id);
          if (el) el.value = (val !== undefined && val !== null ? val : (fallback || ''));
        };
        safe('cfg-primary-llm', cfg.llm_primary_provider, 'deepseek');
        safe('cfg-fallback-llm', cfg.llm_fallback_provider, '');
        safe('cfg-ollama-url', cfg.ollama_base_url, 'http://localhost:11434');
        safe('cfg-ollama-model', cfg.ollama_model, 'llama3.2:3b');
        safe('cfg-google-search-cx', cfg.google_custom_search_cx, '');
        safe('cfg-ig-username', cfg.instagram_username, '');
        safe('cfg-outreach-mode', cfg.outreach_mode, 'assisted');
        safe('cfg-max-outreach', cfg.max_daily_outreach, 15);
        safe('cfg-smtp-port', cfg.notify_email_smtp_port, 587);
        safe('cfg-imap-port', cfg.notify_email_imap_port, 993);
        safe('cfg-proxy-pool', cfg.proxy_pool, '');
        safe('cfg-show-console', cfg.show_console ? 'true' : 'false', 'true');

        // Sensitive fields: CLEAR (we never get them back). User must re-type to change.
        const sensitiveIds = [
          'cfg-deepseek-key', 'cfg-openai-key', 'cfg-anthropic-key',
          'cfg-openrouter-key', 'cfg-gemini-key', 'cfg-groq-key', 'cfg-mistral-key',
          'cfg-google-places-key', 'cfg-google-search-key',
          'cfg-ig-password', 'cfg-ig-encryption-key',
          'cfg-tg-token', 'cfg-tg-chatid',
          'cfg-smtp-host', 'cfg-smtp-user', 'cfg-smtp-pass',
          'cfg-imap-host', 'cfg-imap-user', 'cfg-imap-pass',
          'cfg-scraper-key', 'cfg-zenrows-key', 'cfg-crawlbase-key',
          'cfg-apify-key', 'cfg-linkedin-cookie',
        ];
        sensitiveIds.forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });

        // Decorate provider sections with a "configured" badge so users see status.
        if (cfg.configured) {
          const decorate = (id, configured) => {
            const el = document.getElementById(id);
            if (!el) return;
            const labelEl = el.closest('.form-group')?.querySelector('label');
            if (labelEl) {
              const existing = labelEl.querySelector('.configured-badge');
              if (existing) existing.remove();
              if (configured) {
                const badge = document.createElement('span');
                badge.className = 'configured-badge';
                badge.style.cssText = 'margin-left:6px;padding:2px 6px;border-radius:4px;background:rgba(16,185,129,0.2);color:#10b981;font-size:0.7rem;font-weight:700;';
                badge.textContent = '✓';
                labelEl.appendChild(badge);
              }
            }
          };
          decorate('cfg-deepseek-key', cfg.configured.deepseek);
          decorate('cfg-openai-key', cfg.configured.openai);
          decorate('cfg-anthropic-key', cfg.configured.anthropic);
          decorate('cfg-openrouter-key', cfg.configured.openrouter);
          decorate('cfg-gemini-key', cfg.configured.gemini);
          decorate('cfg-groq-key', cfg.configured.groq);
          decorate('cfg-mistral-key', cfg.configured.mistral);
          decorate('cfg-google-places-key', cfg.configured.google_places);
          decorate('cfg-google-search-key', cfg.configured.google_custom_search);
          decorate('cfg-ig-username', cfg.configured.instagram_username);
          decorate('cfg-ig-password', cfg.configured.instagram_password);
          decorate('cfg-ig-encryption-key', cfg.configured.instagram_session_encryption_key);
          decorate('cfg-tg-token', cfg.configured.telegram);
          decorate('cfg-smtp-host', cfg.configured.email);
          decorate('cfg-imap-host', cfg.configured.imap);
          decorate('cfg-scraper-key', cfg.configured.scraper);
          decorate('cfg-zenrows-key', cfg.configured.zenrows);
          decorate('cfg-crawlbase-key', cfg.configured.crawlbase);
          decorate('cfg-apify-key', cfg.configured.apify);
          decorate('cfg-linkedin-cookie', cfg.configured.linkedin);
        }

        if (cfg.automation_authorized) {
          document.getElementById('cfg-confirm-risk').checked = true;
        }

        // Sync local storage UI configs
        const localLang = safeLocalStorage.getItem('aegis-lang') || 'tr';
        const langSelect = document.getElementById('cfg-lang');
        if (langSelect) langSelect.value = localLang;

        const localTheme = safeLocalStorage.getItem('aegis-theme') || 'theme-neon';
        const themeSelect = document.getElementById('cfg-theme');
        if (themeSelect) themeSelect.value = localTheme;

        toggleAutomationAlert();
        loadSessions();
        refreshSearchPresetListsLater();
      });
    }

    // Save configurations — split into per-key writes via set_config_value.
    // Sensitive fields use a separate explicit "Update Instagram Login" button
    // (login_instagram Python API) rather than the bulk save.
    async function saveSettings() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Ayarları kaydetme');
        return;
      }
      const mode = document.getElementById('cfg-outreach-mode').value;
      const confirmRisk = document.getElementById('cfg-confirm-risk').checked;

      if (mode === 'full_auto' && !confirmRisk) {
        showToast("Tam otomasyon modunu seçtiğiniz için risk onay kutusunu işaretlemelisiniz.", "error");
        return;
      }

      // Find the "Ayarları Kaydet" button for busy state.
      const saveBtn = Array.from(document.querySelectorAll('button')).find(b =>
        (b.textContent || '').trim() === 'Ayarları Kaydet' ||
        (b.textContent || '').trim() === 'Save Settings'
      );
      if (saveBtn) {
        saveBtn.disabled = true;
        const orig = saveBtn.textContent;
        saveBtn._origText = orig;
        saveBtn.textContent = '⏳ ' + orig;
      }

      // Non-sensitive keys (safe to write via set_config_value)
      const safeKeys = [
        ['llm_primary_provider', 'cfg-primary-llm'],
        ['llm_fallback_provider', 'cfg-fallback-llm'],
        ['ollama_base_url', 'cfg-ollama-url'],
        ['ollama_model', 'cfg-ollama-model'],
        ['google_custom_search_cx', 'cfg-google-search-cx'],
        ['instagram_username', 'cfg-ig-username'],
        ['outreach_mode', 'cfg-outreach-mode'],
        ['max_daily_outreach', 'cfg-max-outreach'],
        ['notify_email_smtp_port', 'cfg-smtp-port'],
        ['notify_email_imap_port', 'cfg-imap-port'],
        ['proxy_pool', 'cfg-proxy-pool'],
      ];

      // Sensitive keys (only persist if user actually typed a new value)
      const sensitiveKeys = [
        ['deepseek_api_key', 'cfg-deepseek-key'],
        ['openai_api_key', 'cfg-openai-key'],
        ['anthropic_api_key', 'cfg-anthropic-key'],
        ['openrouter_api_key', 'cfg-openrouter-key'],
        ['gemini_api_key', 'cfg-gemini-key'],
        ['groq_api_key', 'cfg-groq-key'],
        ['mistral_api_key', 'cfg-mistral-key'],
        ['google_places_api_key', 'cfg-google-places-key'],
        ['google_custom_search_api_key', 'cfg-google-search-key'],
        ['instagram_session_encryption_key', 'cfg-ig-encryption-key'],
        ['telegram_bot_token', 'cfg-tg-token'],
        ['telegram_chat_id', 'cfg-tg-chatid'],
        ['notify_email_smtp_host', 'cfg-smtp-host'],
        ['notify_email_smtp_user', 'cfg-smtp-user'],
        ['notify_email_smtp_pass', 'cfg-smtp-pass'],
        ['notify_email_imap_host', 'cfg-imap-host'],
        ['notify_email_imap_username', 'cfg-imap-user'],
        ['notify_email_imap_password', 'cfg-imap-pass'],
        ['scraper_api_key', 'cfg-scraper-key'],
        ['zenrows_api_key', 'cfg-zenrows-key'],
        ['crawlbase_api_key', 'cfg-crawlbase-key'],
        ['apify_api_key', 'cfg-apify-key'],
        ['linkedin_session_cookie', 'cfg-linkedin-cookie'],
      ];

      let okCount = 0;
      let errCount = 0;
      const errors = [];

      const restore = () => {
        if (saveBtn) {
          saveBtn.disabled = false;
          if (saveBtn._origText) saveBtn.textContent = saveBtn._origText;
        }
      };

      try {
        for (const [envKey, htmlId] of safeKeys) {
          const el = document.getElementById(htmlId);
          if (!el) continue;
          const val = el.value;
          try {
            const res = await window.pywebview.api.set_config_value(envKey, val);
            if (res && res.success) okCount++; else { errCount++; errors.push(`${envKey}: ${res && res.error}`); }
          } catch (e) { errCount++; errors.push(`${envKey}: ${e}`); }
        }

        for (const [envKey, htmlId] of sensitiveKeys) {
          const el = document.getElementById(htmlId);
          if (!el || !el.value) continue;  // skip empty
          try {
            const res = await window.pywebview.api.set_config_value(envKey, el.value);
            if (res && res.success) okCount++; else { errCount++; errors.push(`${envKey}: ${res && res.error}`); }
            el.value = '';  // clear after persistence
          } catch (e) { errCount++; errors.push(`${envKey}: ${e}`); }
        }

        // Mod B acknowledgement (config.toml)
        if (mode === 'full_auto' && confirmRisk) {
          try {
            await window.pywebview.api.set_config_value('outreach.mod_b_acknowledged', true);
          } catch (e) { /* best-effort */ }
        }

        // automation_authorized flag file
        if (mode === 'full_auto' && confirmRisk) {
          try {
            await window.pywebview.api.save_settings({ automation_authorized: true });
          } catch (e) { /* best-effort */ }
        }

        if (errCount === 0) {
          showToast(`Ayarlar başarıyla kaydedildi (${okCount} alan).`, "success");
        } else {
          showToast(`${okCount} alan kaydedildi, ${errCount} hata. ${errors.join('; ')}`, "warning");
        }
      } catch (e) {
        showToast("Ayarlar kaydedilirken beklenmeyen bir hata oluştu: " + e, "error");
        try { console.error('[aegisScout] saveSettings failed', e); } catch (_) {}
      } finally {
        restore();
      }

      // Reload to refresh "configured" badges
      setTimeout(() => loadSettings(), 200);
    }

    // New: explicit Instagram login flow. Sends credentials to the Python
    // bridge via login_instagram(), which keeps them in memory only.
    async function loginInstagram() {
      const usernameEl = document.getElementById('cfg-ig-username');
      const passwordEl = document.getElementById('cfg-ig-password');
      if (!usernameEl || !passwordEl) return;
      const username = usernameEl.value;
      const password = passwordEl.value;
      if (!username || !password) {
        showToast("Instagram kullanıcı adı ve şifre gerekli.", "error");
        return;
      }
      // Find the "Instagram Giriş Yap" button to disable while in flight.
      const loginBtn = Array.from(document.querySelectorAll('button')).find(b =>
        (b.textContent || '').includes('Instagram Giriş Yap')
      );
      try {
        const promise = _apiCall(
          () => window.pywebview.api.login_instagram(username, password),
          { action: 'Instagram girişi' }
        );
        const res = loginBtn ? await _withButtonBusy(loginBtn, promise) : await promise;
        if (res && res.success) {
          showToast("Instagram girişi başarılı. Oturum şifrelenmiş olarak saklandı.", "success");
          passwordEl.value = '';
          loadSettings();
        } else if (res && res.error) {
          showToast("Instagram girişi başarısız: " + res.error, "error");
        }
      } catch (err) {
        // _apiCall already toasted; just keep credential cleared
        try { passwordEl.value = ''; } catch (_) {}
        try { console.error('[aegisScout] loginInstagram failed', err); } catch (_) {}
      }
    }

    async function logoutInstagram() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Instagram çıkışı');
        return;
      }
      try {
        const res = await _apiCall(() => window.pywebview.api.logout_instagram(), { action: 'Instagram çıkışı' });
        if (!res) return;
        if (res.success) {
          showToast("Instagram oturumu silindi.", "info");
          loadSettings();
        } else {
          showToast("Hata: " + res.error, "error");
        }
      } catch (err) {
        // Already toasted by _apiCall
      }
    }

    // -------------------------------------------------------------------
    // Ollama Management
    // -------------------------------------------------------------------
    function checkOllamaStatus() {
      const banner = document.getElementById('ollama-status-banner');
      if (banner) {
        banner.style.display = 'block';
        banner.style.background = 'rgba(255, 255, 255, 0.05)';
        banner.style.color = 'var(--text-main)';
        banner.innerHTML = '⏳ Kontrol ediliyor...';
      }
      _apiCall(() => window.pywebview.api.get_ollama_status(), { action: 'Ollama durumunu sorgula' }).then(res => {
        if (!banner) return;
        if (res && res.status === 'running') {
          banner.style.background = 'rgba(16,185,129,0.1)';
          banner.style.color = '#10b981';
          banner.innerHTML = `✓ Ollama Çalışıyor.<br>Mevcut Modeller: ${res.models.join(', ') || 'Yok'}`;
        } else {
          banner.style.background = 'rgba(239,68,68,0.1)';
          banner.style.color = '#ef4444';
          banner.innerHTML = `✕ Çevrimdışı / Çalışmıyor.<br>Detay: ${res ? res.message : 'Bağlantı hatası'}`;
        }
      });
    }

    function downloadOllamaModel() {
      const modelName = document.getElementById('cfg-ollama-model').value.trim();
      if (!modelName) {
        showToast("Lütfen indirilecek model ismini girin (örn: llama3.2:3b).", "error");
        return;
      }
      showToast(modelName + " indiriliyor (bu işlem arka planda sürer, kapatmayın)...", "info");
      _apiCall(() => window.pywebview.api.pull_ollama_model(modelName), { action: 'Ollama model indir' }).then(res => {
        if (res && res.success) {
          showToast(res.message, "success");
          checkOllamaStatus();
        } else {
          showToast("Hata: " + (res ? res.error : "İndirme başlatılamadı"), "error");
        }
      });
    }

    // -------------------------------------------------------------------
    // CRM Notes
    // -------------------------------------------------------------------
    function addCrmNote(leadId) {
      const input = document.getElementById('crm-note-input');
      if (!input) return;
      const text = input.value.trim();
      if (!text) {
        showToast("Lütfen bir not girin.", "error");
        return;
      }
      _apiCall(() => window.pywebview.api.add_crm_log(leadId, text), { action: 'CRM günlüğü ekle' }).then(res => {
        if (res && res.success) {
          showToast("CRM günlüğü kaydedildi.", "success");
          input.value = '';
          selectLead(leadId);
        } else {
          showToast("Hata: " + (res ? res.error : "Kaydedilemedi"), "error");
        }
      });
    }

    // -------------------------------------------------------------------
    // CRM Kanban Board
    // -------------------------------------------------------------------
    function loadPipeline() {
      if (!_isBridgeReady()) return;
      _apiCall(() => window.pywebview.api.get_leads('all', null), { action: 'Satış hunisi verilerini yükle' }).then(leads => {
        if (!leads || leads.error) return;
        
        const statuses = ['new', 'researched', 'contacted', 'replied', 'meeting_scheduled', 'converted'];
        statuses.forEach(status => {
          const col = document.getElementById('kanban-' + status);
          if (col) col.innerHTML = '';
        });
        
        leads.forEach(lead => {
          const colId = 'kanban-' + (statuses.includes(lead.status) ? lead.status : 'new');
          const col = document.getElementById(colId);
          if (!col) return;
          
          const card = document.createElement('div');
          card.className = 'kanban-card';
          card.draggable = true;
          card.ondragstart = (ev) => {
            ev.dataTransfer.setData("text/plain", lead.id);
          };
          card.onclick = () => {
            switchTab('leads');
            setTimeout(() => selectLead(lead.id), 100);
          };
          
          const scoreBadge = lead.priority_label ? `<div style="font-size:0.7rem; margin-top:4px;"><span style="background:var(--color-brand); color:white; padding:2px 6px; border-radius:4px; font-weight:bold;">${escapeHtml(lead.priority_label)}</span></div>` : '';
          
          card.innerHTML = `
            <div style="font-weight:600; font-size:0.85rem; color:var(--text-main); margin-bottom:4px;">${escapeHtml(lead.business_name)}</div>
            <div style="font-size:0.75rem; color:var(--color-accent);">${escapeHtml(lead.sector || '-')}</div>
            <div style="font-size:0.7rem; color:var(--text-muted); margin-top:2px;">${escapeHtml(lead.address || '-')}</div>
            ${scoreBadge}
          `;
          col.appendChild(card);
        });
      });
    }

    function allowDrop(ev) {
      ev.preventDefault();
    }
    
    function dropLead(ev) {
      ev.preventDefault();
      const leadId = ev.dataTransfer.getData("text/plain");
      let target = ev.target;
      while (target && !target.classList.contains('kanban-column')) {
        target = target.parentElement;
      }
      if (!target) return;
      const newStatus = target.getAttribute('data-status');
      
      _apiCall(() => window.pywebview.api.update_lead_status(leadId, newStatus), { action: 'Aday durumunu güncelle' }).then(res => {
        if (res && res.success) {
          showToast("Aday durumu güncellendi.", "success");
          loadPipeline();
        } else {
          showToast("Hata: " + (res ? res.error : "Bilinmeyen hata"), "error");
        }
      });
    }

    // -------------------------------------------------------------------
    // WhatsApp & Email Outreach
    // -------------------------------------------------------------------
    function launchWhatsApp(leadId) {
      const customText = document.getElementById('edit-draft-box').value;
      showToast("WhatsApp Mod A tetikleniyor...", "info");
      _apiCall(() => window.pywebview.api.launch_whatsapp(leadId, customText), { action: 'WhatsApp link tetikle' }).then(res => {
        if (res && res.success && res.url) {
          window.open(res.url, '_blank');
          showToast("WhatsApp Web açıldı. Mesaj panoya da kopyalanmıştır.", "success");
        } else {
          showToast("Hata: " + (res ? res.error : "WhatsApp başlatılamadı"), "error");
        }
      });
    }

    function sendSmtpEmail(leadId) {
      const customText = document.getElementById('edit-draft-box').value;
      showToast("SMTP üzerinden e-posta gönderiliyor...", "info");
      _apiCall(() => window.pywebview.api.send_email_lead(leadId, customText), { action: 'SMTP e-posta gönder' }).then(res => {
        if (res && res.success) {
          showToast("E-posta başarıyla gönderildi!", "success");
          selectLead(leadId);
        } else {
          showToast("Hata: " + (res ? res.error : "E-posta gönderilemedi"), "error");
        }
      });
    }

    // Load Campaigns List
    function loadCampaigns() {
      if (!_isBridgeReady()) return;
      _apiCall(() => window.pywebview.api.get_campaigns(), { action: 'Kampanyaları yükle' }).then(campaigns => {
        if (!campaigns) return;
        const body = document.getElementById('campaigns-table-body');
        body.innerHTML = '';
        
        if (campaigns.error) {
          showToast("Kampanyalar alınamadı: " + campaigns.error, "error");
          return;
        }
        
        if (campaigns.length === 0) {
          body.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">Kampanya bulunamadı.</td></tr>';
          return;
        }
        
        campaigns.forEach(c => {
          const row = document.createElement('tr');
          row.style.cursor = 'pointer';
          row.onclick = () => selectCampaign(c.id);
          
          let ratioStr = "-";
          if (c.contacted_leads > 0) {
            ratioStr = `%${(c.replied_leads / c.contacted_leads * 100).toFixed(1)} (${c.replied_leads}/${c.contacted_leads})`;
          } else if (c.total_leads > 0) {
            ratioStr = `%0 (0/${c.total_leads})`;
          }
          
          row.innerHTML = `
            <td><b>${c.name}</b><br><small style="color: var(--text-muted);">${c.sector_filter || 'Tümü'} @ ${c.location_filter || 'Tümü'}</small></td>
            <td style="text-align: right;">${c.total_leads}</td>
            <td style="text-align: right; color: var(--color-success); font-weight: 600;">${ratioStr}</td>
            <td style="text-align: right;">
              <button style="border: none; background: transparent; padding: 4px; color: var(--color-danger); cursor: pointer;" onclick="event.stopPropagation(); triggerDeleteCampaign(this)" data-id="${c.id}" data-name="${escapeHtml(c.name)}" title="Kampanyayı Sil">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              </button>
            </td>
          `;
          body.appendChild(row);
        });
      });
    }

    // Select and view Campaign details
    function selectCampaign(campaignId) {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Kampanya detaylarını yükleme');
        return;
      }
      const detailView = document.getElementById('campaign-detail-view');
      detailView.innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 100px;"><span class="loader"></span><p style="margin-top: 12px;">Kampanya yükleniyor...</p></div>';
      
      _apiCall(() => window.pywebview.api.get_campaign_details(campaignId), { action: 'Kampanya detaylarını yükle' }).then(res => {
        if (!res) return;
        if (res.error) {
          showToast("Hata: " + res.error, "error");
          return;
        }
        
        const c = res.campaign;
        const leads = res.leads;
        
        let leadsRows = leads.map(l => `
          <tr>
            <td><b>${l.business_name}</b></td>
            <td>${l.sector || '-'}</td>
            <td><span class="badge badge-${l.status}">${l.status}</span></td>
          </tr>
        `).join('');
        
        if (leads.length === 0) {
          leadsRows = '<tr><td colspan="3" style="text-align: center; color: var(--text-muted);">Kampanyada aday bulunmuyor.</td></tr>';
        }
        
        detailView.innerHTML = `
          <h2 style="font-family: var(--font-display); font-size: 1.4rem;">${c.name}</h2>
          
          <div class="detail-section">
            <p style="font-size: 0.9rem; color: var(--text-muted);"><b>Oluşturulma:</b> ${c.created_at}</p>
            <p style="font-size: 0.9rem; color: var(--text-muted);"><b>Filtreler:</b> Sektör: ${c.sector_filter || 'Tümü'} | Konum: ${c.location_filter || 'Tümü'}</p>
          </div>

          <div class="detail-section" style="background-color: var(--bg-base); padding: 16px; border-radius: 12px; gap: 12px;">
            <h3 style="font-size: 1rem; color: var(--color-accent);">Müşteri Adayı Ekle / Ata</h3>
            
            <div style="display: flex; flex-direction: column; gap: 8px;">
              <button class="btn" style="width: 100%;" onclick="triggerAssignCampaign(${c.id}, true)">
                Kampanya Filtreleriyle Adayları Otomatik Ata
              </button>
              
              <div style="display: flex; gap: 12px; align-items: center; margin-top: 8px;">
                <select id="select-unassigned-lead" style="flex-grow: 1;">
                  <option value="">Aday Seçin...</option>
                </select>
                <button class="btn btn-secondary" onclick="triggerAssignCampaign(${c.id}, false)">
                  Manuel Ata
                </button>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h3>Kampanyadaki Adaylar (${leads.length})</h3>
            <div class="table-container animate-fade-in" style="max-height: 250px; overflow-y: auto;">
              <table>
                <thead>
                  <tr>
                    <th>İşletme Adı</th>
                    <th>Sektör</th>
                    <th>Durum</th>
                  </tr>
                </thead>
                <tbody>
                  ${leadsRows}
                </tbody>
              </table>
            </div>
          </div>
        `;
        
        // Populate unassigned leads in dropdown
        populateUnassignedLeadsDropdown();
      });
    }

    // Populate unassigned leads in the selector dropdown
    function populateUnassignedLeadsDropdown() {
      if (!_isBridgeReady()) return;
      _apiCall(() => window.pywebview.api.get_leads('all'), { action: 'Adayları listele' }).then(leads => {
        if (!leads) return;
        const select = document.getElementById('select-unassigned-lead');
        if (!select) return;
        
        select.innerHTML = '<option value="">Aday Seçin...</option>';
        
        if (leads.error) {
          showToast("Adaylar yüklenemedi: " + leads.error, "error");
          return;
        }
        if (!Array.isArray(leads)) return;
        
        const unassigned = leads.filter(l => l.campaign_id === null);
        if (unassigned.length === 0) {
          const opt = document.createElement('option');
          opt.innerText = "Tüm adaylar kampanyalara atanmış";
          opt.disabled = true;
          select.appendChild(opt);
          return;
        }
        
        unassigned.forEach(l => {
          const opt = document.createElement('option');
          opt.value = l.id;
          opt.innerText = `${l.business_name} (${l.sector || 'Sektörsüz'})`;
          select.appendChild(opt);
        });
      });
    }

    // Trigger Campaign creation
    function triggerCreateCampaign() {
      const name = document.getElementById('camp-name').value;
      const sector = document.getElementById('camp-sector-filter').value;
      const location = document.getElementById('camp-location-filter').value;

      if (!name) {
        showToast("Kampanya adı girmek zorunludur.", "error");
        return;
      }

      // Find the "Kampanya Oluştur" button for busy state.
      const createBtn = Array.from(document.querySelectorAll('button')).find(b =>
        (b.textContent || '').trim() === 'Kampanya Oluştur'
      );
      const promise = _apiCall(
        () => window.pywebview.api.create_campaign(name, sector, location),
        { action: 'Kampanya oluşturma' }
      );
      const wrapped = createBtn ? _withButtonBusy(createBtn, promise) : promise;
      wrapped.then(res => {
        if (!res) return;
        if (res.success) {
          showToast(`Kampanya '${name}' başarıyla oluşturuldu!`, "success");
          document.getElementById('camp-name').value = '';
          document.getElementById('camp-sector-filter').value = '';
          document.getElementById('camp-location-filter').value = '';
          loadCampaigns();
        } else if (res.error) {
          showToast("Hata: " + res.error, "error");
        }
      }).catch(() => { /* _apiCall already toasted */ });
    }

    // Trigger Lead assignment to Campaign
    function triggerAssignCampaign(campaignId, autoFilter) {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Adayı kampanyaya atama');
        return;
      }
      let leadId = null;
      if (!autoFilter) {
        leadId = document.getElementById('select-unassigned-lead').value;
        if (!leadId) {
          showToast("Lütfen atamak için bir aday seçin.", "error");
          return;
        }
      }
      
      showToast("Adaylar atanmaktadır...", "info");
      _apiCall(() => window.pywebview.api.assign_lead_to_campaign(campaignId, leadId ? parseInt(leadId) : null, autoFilter), { action: 'Adayı kampanyaya ata' }).then(res => {
        if (!res) return;
        if (res.success) {
          if (res.assigned > 0) {
            showToast(`${res.assigned} adet aday kampanyaya atandı!`, "success");
          } else {
            showToast(res.message || "Aday atanamadı.", "info");
          }
          selectCampaign(campaignId);
          loadCampaigns();
        } else {
          showToast("Hata: " + res.error, "error");
        }
      });
    }

    // Load History Logs
    function loadHistory() {
      if (!window.pywebview || !window.pywebview.api) return;
      window.pywebview.api.get_activity_logs().then(logs => {
        const body = document.getElementById('history-table-body');
        body.innerHTML = '';
        
        if (logs.error) {
          showToast("Geçmiş yüklenemedi: " + logs.error, "error");
          return;
        }
        
        if (logs.length === 0) {
          body.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">Henüz bir geçmiş kaydı bulunmuyor.</td></tr>';
          return;
        }
        
        logs.forEach(l => {
          const row = document.createElement('tr');
          let badgeClass = "badge-new";
          if (l.action === "research") badgeClass = "badge-researched";
          if (l.action.includes("send")) badgeClass = "badge-contacted";
          if (l.action === "campaign_create" || l.action === "session_start") badgeClass = "badge-replied";
          
          row.innerHTML = `
            <td style="color: var(--text-muted); font-size: 0.8rem;">${l.timestamp}</td>
            <td><span class="badge ${badgeClass}">${l.action}</span></td>
            <td>${l.details || '-'}</td>
            <td style="text-align: right;">
              <button style="border: none; background: transparent; padding: 4px; color: var(--color-danger); cursor: pointer;" onclick="deleteLog(${l.id})" title="Kaydı Sil">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              </button>
            </td>
          `;
          body.appendChild(row);
        });
      });
    }

    // -------------------------------------------------------------------
    // Searches History Tab
    // -------------------------------------------------------------------
    function loadSearchesHistory() {
      if (!window.pywebview || !window.pywebview.api) return;
      window.pywebview.api.get_search_history().then(searches => {
        if (searches.error) {
          showToast("Arama geçmişi yüklenemedi: " + searches.error, "error");
          return;
        }
        allSearches = searches;
        filterSearchesTable();
      });
    }

    function filterSearchesTable() {
      const body = document.getElementById('searches-table-body');
      if (!body) return;
      body.innerHTML = '';

      const sectorInput = document.getElementById('filter-search-sector');
      const locationInput = document.getElementById('filter-search-location');
      const secQ = sectorInput ? sectorInput.value.toLowerCase().trim() : '';
      const locQ = locationInput ? locationInput.value.toLowerCase().trim() : '';

      const filtered = allSearches.filter(s => {
        const sector = (s.sector || '').toLowerCase();
        const location = (s.location || '').toLowerCase();
        return sector.includes(secQ) && location.includes(locQ);
      });

      if (filtered.length === 0) {
        body.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Arama kaydı bulunamadı.</td></tr>';
        return;
      }

      filtered.forEach(s => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td style="color: var(--text-muted); font-size: 0.8rem;">${s.timestamp}</td>
          <td class="bold" style="color: var(--text-main); font-weight: 500;">${escapeHtml(s.sector)}</td>
          <td>${escapeHtml(s.location)}</td>
          <td><span class="badge" style="background: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid var(--border-subtle);">${escapeHtml(s.provider)}</span></td>
          <td style="text-align: center;">
            <span style="color: #10b981; font-weight: bold;">${s.added_count} Yeni</span>
            <span style="color: var(--text-muted); font-size: 0.8rem; margin: 0 4px;">/</span>
            <span style="color: var(--text-muted);">${s.total_candidates} Toplam</span>
          </td>
          <td style="text-align: right;">
            <div style="display: flex; gap: 8px; justify-content: flex-end;">
              <button class="btn btn-secondary" onclick="showLeadsForSearch(${s.id}, '${escapeHtml(s.sector).replace(/'/g, "\\'")}', '${escapeHtml(s.location).replace(/'/g, "\\'")}')" style="padding: 4px 10px; font-size: 0.75rem; height: 28px;">🔍 Göster</button>
              <button class="btn btn-danger" onclick="deleteLeadsForSearch(${s.id}, '${escapeHtml(s.sector).replace(/'/g, "\\'")}', '${escapeHtml(s.location).replace(/'/g, "\\'")}')" style="padding: 4px 10px; font-size: 0.75rem; height: 28px; background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.2); color: #ef4444;">🗑️ Adayları Sil</button>
            </div>
          </td>
        `;
        body.appendChild(row);
      });
    }

    function showLeadsForSearch(searchLogId, sector, location) {
      currentSearchLogId = searchLogId;
      const activeFilterText = document.getElementById('active-filter-text');
      if (activeFilterText) {
        activeFilterText.textContent = `Arama Filtresi Aktif: Sektör: "${sector}", Konum: "${location}"`;
      }
      const activeFilterBadge = document.getElementById('active-leads-filters');
      if (activeFilterBadge) {
        activeFilterBadge.style.display = 'flex';
      }
      
      const leadsTab = Array.from(document.querySelectorAll('.nav-links li')).find(li => {
        return li.getAttribute('onclick') && li.getAttribute('onclick').includes('leads');
      });
      if (leadsTab) {
        switchTab('leads', leadsTab);
      } else {
        loadLeads();
      }
    }

    function clearActiveSearchFilter() {
      currentSearchLogId = null;
      const activeFilterBadge = document.getElementById('active-leads-filters');
      if (activeFilterBadge) {
        activeFilterBadge.style.display = 'none';
      }
      loadLeads();
    }

    function deleteLeadsForSearch(searchLogId, sector, location) {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Aramaya ait adayları silme');
        return;
      }
      _openModal({
        icon: '⚠️',
        iconClass: 'confirm-del',
        title: 'Aramaya Ait Adayları Sil',
        desc: `"${sector}" sektörü ve "${location}" konumu için yapılan bu aramada keşfedilen <b>tüm adaylar ve bunlara ait tüm AI analizleri / mesaj taslakları kalıcı olarak silinecektir.</b><br><br>Bu işlemi onaylıyor musunuz?`,
        confirmText: 'Kalıcı Olarak Sil',
        confirmClass: 'btn-danger',
        cancelText: 'Vazgeç',
        hideCancel: false,
        showInput: false
      }).then(approved => {
        if (approved === true) {
          _apiCall(() => window.pywebview.api.delete_leads_by_search(searchLogId), { action: 'Aramaya ait adayları sil' }).then(res => {
            if (!res) return;
            if (res.success) {
              showToast(`${res.deleted_count} aday başarıyla silindi ve arama kaydı temizlendi.`, "success");
              loadSearchesHistory();
              if (currentSearchLogId === searchLogId) {
                clearActiveSearchFilter();
              } else {
                loadLeads();
              }
            } else {
              showToast("Silme hatası: " + res.error, "error");
            }
          });
        }
      });
    }

    // -------------------------------------------------------------------
    // Export Modal Dialog
    // -------------------------------------------------------------------
    function openExportModal() {
      const modal = document.getElementById('export-modal');
      if (!modal) return;
      
      const xlsxRadio = document.querySelector('.format-select-label input[value=".xlsx"]');
      if (xlsxRadio) {
        xlsxRadio.checked = true;
      }
      
      modal.classList.add('show');
      initExportFormatSelector();
    }

    function closeExportModal() {
      const modal = document.getElementById('export-modal');
      if (modal) modal.classList.remove('show');
    }

    function initExportFormatSelector() {
      const labels = document.querySelectorAll('.format-select-label');
      labels.forEach(lbl => {
        const radio = lbl.querySelector('input');
        if (radio.checked) {
          lbl.style.borderColor = 'var(--color-brand)';
          lbl.style.background = 'rgba(59,130,246,0.1)';
        } else {
          lbl.style.borderColor = 'var(--border-accent)';
          lbl.style.background = 'var(--bg-base)';
        }
        lbl.onclick = () => {
          labels.forEach(l => {
            l.style.borderColor = 'var(--border-accent)';
            l.style.background = 'var(--bg-base)';
            l.querySelector('input').checked = false;
          });
          lbl.style.borderColor = 'var(--color-brand)';
          lbl.style.background = 'rgba(59,130,246,0.1)';
          radio.checked = true;
        };
      });
    }

    function executeExportLeads() {
      const scope = document.getElementById('export-scope').value;
      const formatRadio = document.querySelector('input[name="export-format"]:checked');
      const format = formatRadio ? formatRadio.value : '.xlsx';

      const filters = {
        format: format,
        status: scope === 'filtered' ? document.getElementById('filter-status').value : 'all',
        search_log_id: scope === 'filtered' ? currentSearchLogId : null
      };

      if (scope === 'filtered') {
        const searchInput = document.getElementById('search-leads-input');
        if (searchInput && searchInput.value.trim()) {
          filters.keyword = searchInput.value.trim();
        }
      }

      // Locate the primary action button inside the export modal so the
      // spinner appears next to "Dışa Aktar" while the file dialog is open.
      const exportBtn = document.querySelector('#export-modal .modal-actions .btn:not(.btn-secondary)');
      showToast("Dosya kaydetme penceresi açılıyor...", "info");
      const promise = _apiCall(
        () => window.pywebview.api.export_leads_dialog(filters),
        { action: 'Dışa aktarma' }
      );
      const wrapped = exportBtn ? _withButtonBusy(exportBtn, promise) : promise;
      wrapped.then(res => {
        closeExportModal();
        if (!res) return; // _apiCall already toasted
        if (res.error) {
          showToast("Dışa aktarma başarısız: " + res.error, "error");
        } else if (res.success) {
          const filename = (res.path || '').split('\\\\').pop() || res.path || '';
          showToast(`${res.count} aday başarıyla kaydedildi: ${filename}`, "success");
        } else if (res.cancelled) {
          showToast("İşlem iptal edildi.", "info");
        }
      }).catch(() => { /* _apiCall already toasted */ });
    }

    // -------------------------------------------------------------------
    // Advanced Delete Dialog
    // -------------------------------------------------------------------
    function openAdvancedDeleteModal() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Gelişmiş silme arayüzünü açma');
        return;
      }
      const modal = document.getElementById('advanced-delete-modal');
      if (!modal) return;
      
      document.getElementById('del-filter-keyword').value = '';
      document.getElementById('del-filter-status').value = 'all';
      document.getElementById('del-filter-sector').value = '';
      document.getElementById('del-filter-source').value = 'all';
      document.getElementById('del-filter-website').value = 'all';
      document.getElementById('del-filter-start-date').value = '';
      document.getElementById('del-filter-end-date').value = '';
      
      const searchSelect = document.getElementById('del-filter-search-log');
      searchSelect.innerHTML = '<option value="">Arama seçilmedi</option>';
      
      _apiCall(() => window.pywebview.api.get_search_history(), { action: 'Arama geçmişini yükle' }).then(searches => {
        if (!searches) return;
        if (!searches.error) {
          searches.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = `${s.timestamp.slice(5,16)} - ${s.sector} - ${s.location} (${s.added_count} Yeni)`;
            searchSelect.appendChild(opt);
          });
        }
      });

      document.getElementById('del-calc-summary').innerHTML = 'Eşleşen aday sayısını görmek için "Hesapla" butonuna basın.';
      document.getElementById('del-calc-summary').style.color = 'var(--text-muted)';
      
      const execBtn = document.getElementById('btn-execute-adv-delete');
      execBtn.disabled = true;
      execBtn.style.opacity = '0.6';
      
      modal.classList.add('show');
    }

    function closeAdvancedDeleteModal() {
      const modal = document.getElementById('advanced-delete-modal');
      if (modal) modal.classList.remove('show');
    }

    function getAdvancedDeleteFilters() {
      return {
        keyword: document.getElementById('del-filter-keyword').value,
        status: document.getElementById('del-filter-status').value,
        sector: document.getElementById('del-filter-sector').value,
        source: document.getElementById('del-filter-source').value,
        has_website: document.getElementById('del-filter-website').value,
        search_log_id: document.getElementById('del-filter-search-log').value,
        start_date: document.getElementById('del-filter-start-date').value,
        end_date: document.getElementById('del-filter-end-date').value
      };
    }

    function calculateAdvancedDeleteMatches() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Aday eşleşmesini hesaplama');
        return;
      }
      const filters = getAdvancedDeleteFilters();
      filters.dry_run = true;
      
      const summary = document.getElementById('del-calc-summary');
      summary.textContent = 'Hesaplanıyor...';
      summary.style.color = 'var(--text-muted)';
      
      _apiCall(() => window.pywebview.api.clear_leads_advanced(filters), { action: 'Silinecek aday sayısını hesapla' }).then(res => {
        if (!res) return;
        const execBtn = document.getElementById('btn-execute-adv-delete');
        if (res.error) {
          summary.textContent = "Hata: " + res.error;
          summary.style.color = '#ef4444';
          execBtn.disabled = true;
          execBtn.style.opacity = '0.6';
        } else {
          summary.innerHTML = `Kriterlere uyan <b>${res.count}</b> aday bulundu ve silinecek.`;
          if (res.count > 0) {
            summary.style.color = '#f59e0b';
            execBtn.disabled = false;
            execBtn.style.opacity = '1';
          } else {
            summary.style.color = 'var(--text-muted)';
            execBtn.disabled = true;
            execBtn.style.opacity = '0.6';
          }
        }
      });
    }

    function executeAdvancedDeleteLeads() {
      const filters = getAdvancedDeleteFilters();
      filters.dry_run = false;

      _openModal({
        icon: '🗑️',
        iconClass: 'confirm-del',
        title: 'Kriterlere Uyan Adayları Sil',
        desc: 'Seçtiğiniz kriterlere uyan <b>tüm adaylar ve bunlara ait tüm AI analizleri / mesaj taslakları kalıcı olarak silinecektir.</b><br><br>Bu işlemi onaylıyor musunuz?',
        confirmText: 'Kalıcı Olarak Sil',
        confirmClass: 'btn-danger',
        cancelText: 'Vazgeç',
        hideCancel: false,
        showInput: false
      }).then(approved => {
        if (approved === true) {
          const execBtn = document.getElementById('btn-execute-adv-delete');
          const promise = _apiCall(
            () => window.pywebview.api.clear_leads_advanced(filters),
            { action: 'Aday silme' }
          );
          const wrapped = execBtn ? _withButtonBusy(execBtn, promise) : promise;
          wrapped.then(res => {
            if (!res) return;
            closeAdvancedDeleteModal();
            if (res.error) {
              showToast("Silme hatası: " + res.error, "error");
            } else {
              showToast(`${res.deleted_count} aday başarıyla silindi.`, "success");
              loadLeads();
              loadStats();
              loadHistory();
            }
          }).catch(() => { /* _apiCall already toasted */ });
        }
      });
    }

    // Trigger New Session
    function triggerNewSession() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Yeni oturum');
        return;
      }
      const promise = _apiCall(
        () => window.pywebview.api.create_activity_log("session_start", "Yeni bir çalışma oturumu manuel olarak başlatıldı."),
        { action: 'Yeni oturum' }
      );
      promise.then(res => {
        if (!res) return;
        if (res.success) {
          showToast("Yeni oturum başarıyla başlatıldı ve günlüğe kaydedildi.", "success");
          loadHistory();
        } else if (res.error) {
          showToast("Hata: " + res.error, "error");
        }
      }).catch(() => { /* _apiCall already toasted */ });
    }

    // Trigger Clear History
    function triggerClearHistory() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Geçmişi temizleme');
        return;
      }
      showConfirm('Geçmişi Temizle', 'Tüm işlem geçmişini kalıcı olarak temizlemek istediğinizden emin misiniz?', 'Evet, Temizle', true).then(ok => {
        if (!ok) return;
        _apiCall(() => window.pywebview.api.clear_activity_logs(), { action: 'Geçmişi temizle' }).then(res => {
          if (!res) return;
          if (res.success) {
            showToast('Tüm işlem geçmişi temizlendi.', 'success');
            loadHistory();
          } else {
            showToast('Hata: ' + res.error, 'error');
          }
        });
      });
    }

    // Update step-by-step progress during discovery
    function updateDiscoveryProgress(msg) {
      const box = document.getElementById('discovery-progress-box');
      box.classList.remove('hidden');

      const logArea = document.getElementById('discovery-progress-text');
      const line = document.createElement('div');
      line.innerText = `> ${msg}`;
      logArea.appendChild(line);
      logArea.scrollTop = logArea.scrollHeight;

      // Better keyword matching — covers both Turkish and English messages
      let pct = 10;
      const msgL = msg.toLowerCase();
      if (msgL.includes('geocod') || msgL.includes('konum') || msgL.includes('başlatılıyor')) pct = 20;
      else if (msgL.includes('aranıyor') || msgL.includes('sorgulanıyor') || msgL.includes('searching')) pct = 45;
      else if (msgL.includes('karşılaştırılıyor') || msgL.includes('tekilleştirme') || msgL.includes('dedup')) pct = 75;
      else if (msgL.includes('tamamlandı') || msgL.includes('kaydedildi') || msgL.includes('complete')) pct = 100;

      document.getElementById('discovery-progress-bar').style.width = pct + '%';
      document.getElementById('discovery-percent').innerText = pct + '%';
    }

    // Called by python backend thread when discovery finishes (success or failure)
    function finishDiscovery(success, added, errorMsg, total, duplicates) {
      document.getElementById('btn-start-discovery').disabled = false;
      document.getElementById('discovery-btn-text').innerText = "Keşfi Başlat";
      document.getElementById('discovery-loader').classList.add('hidden');
      
      if (success) {
        if (total !== undefined && duplicates !== undefined) {
          showToast(`Keşif tamamlandı! ${total} aday bulundu: ${added} yeni, ${duplicates} kopya.`, "success");
        } else {
          showToast(`Keşif tamamlandı! ${added} yeni potansiyel müşteri eklendi.`, "success");
        }
        loadStats();
        loadLeads();
        loadHistory();
        setTimeout(() => {
          document.getElementById('discovery-progress-box').classList.add('hidden');
        }, 12000);
      } else {
        showToast("Hata: " + errorMsg, "error");
        updateDiscoveryProgress("Hata oluştu: " + errorMsg);
      }
    }

    // Load Work Sessions List
    function loadSessions() {
      if (!window.pywebview || !window.pywebview.api) return;
      window.pywebview.api.get_sessions().then(sessions => {
        const body = document.getElementById('sessions-table-body');
        body.innerHTML = '';

        if (sessions.error) {
          showToast('Oturumlar yüklenemedi: ' + sessions.error, 'error');
          return;
        }

        if (!sessions.length) {
          body.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--text-muted);padding:32px;">Henüz kayıtlı oturum yok.</td></tr>';
          return;
        }

        sessions.forEach(s => {
          const row = document.createElement('tr');

          let actionBtn;
          if (s.is_active) {
            actionBtn = `
              <div style="display:flex;gap:8px;justify-content:flex-end;align-items:center;">
                <button class="btn btn-secondary" style="padding:6px 14px;font-size:0.8rem;" onclick="renameSession(this)" data-id="${s.id}" data-name="${escapeHtml(s.name)}">
                  ✏️ Yeniden Adlandır
                </button>
                <span class="badge badge-replied" style="padding:6px 14px;background:rgba(16,185,129,0.2);color:#10b981;border:1px solid rgba(16,185,129,0.4);">● Aktif Oturum</span>
              </div>`;
            row.style.backgroundColor = 'rgba(16,185,129,0.03)';
          } else {
            actionBtn = `
              <div style="display:flex;gap:8px;justify-content:flex-end;align-items:center;">
                <button class="btn btn-secondary" style="padding:6px 12px;font-size:0.8rem;" onclick="renameSession(this)" data-id="${s.id}" data-name="${escapeHtml(s.name)}">✏️ Adlandır</button>
                <button class="btn btn-secondary" style="padding:6px 12px;font-size:0.8rem;" onclick="switchSession(${s.id})">Oturuma Geç</button>
                <button class="btn btn-danger"    style="padding:6px 12px;font-size:0.8rem;" onclick="deleteSession(this)" data-id="${s.id}" data-name="${escapeHtml(s.name)}">🗑 Sil</button>
              </div>`;
          }

          row.innerHTML = `
            <td style="font-weight:600;color:var(--text-main);">${s.name}</td>
            <td style="color:var(--text-muted);font-size:0.85rem;">${s.created_at}</td>
            <td>${actionBtn}</td>
          `;
          body.appendChild(row);
        });
      });
    }

    // Create a new session
    function triggerCreateSession() {
      showPrompt('Yeni Çalışma Oturumu', 'Yeni oturum için açıklayıcı bir isim girin:', '', 'ör. Kadıköy Kampanyası — Temmuz 2026').then(name => {
        if (!name) return;
        const promise = _apiCall(
          () => window.pywebview.api.create_session(name),
          { action: 'Yeni oturum oluşturma' }
        );
        promise.then(res => {
          if (!res) return;
          if (res.success) {
            showToast('Yeni çalışma oturumu başarıyla oluşturuldu ve etkinleştirildi.', 'success');
            _updateSidebarSessionName(name);
            loadSessions();
            loadStats(); loadLeads(); loadCampaigns(); loadHistory();
          } else if (res.error) {
            showToast(res.error, 'error');
          }
        }).catch(() => { /* _apiCall already toasted */ });
      });
    }

    // Update sidebar session indicator
    function _updateSidebarSessionName(name) {
      const el = document.getElementById('sidebar-session-name');
      if (el) el.textContent = '● ' + name;
    }

    // Rename Session
    function renameSession(btnOrId, currentName) {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Oturumu yeniden adlandırma');
        return;
      }
      let sessionId = btnOrId;
      if (btnOrId && typeof btnOrId === 'object') {
        sessionId = btnOrId.getAttribute('data-id');
        currentName = btnOrId.getAttribute('data-name');
      }
      showPrompt('Oturumu Yeniden Adlandır', `"<b>${currentName}</b>" oturumu için yeni bir isim girin:`, currentName, 'Yeni oturum adı...').then(newName => {
        if (!newName || newName === currentName) return;
        _apiCall(() => window.pywebview.api.rename_session(sessionId, newName), { action: 'Oturumu yeniden adlandır' }).then(res => {
          if (!res) return;
          if (res.success) {
            showToast(`Oturum "${newName}" olarak yeniden adlandırıldı.`, 'success');
            loadSessions();
          } else {
            showToast(res.error, 'error');
          }
        });
      });
    }

    // Switch to another session
    function switchSession(sessionId) {
      const promise = _apiCall(
        () => window.pywebview.api.switch_session(sessionId),
        { action: 'Oturum değiştirme' }
      );
      promise.then(res => {
        if (!res) return;
        if (res.success) {
          showToast('Çalışma oturumu değiştirildi.', 'success');
          // Update sidebar session name from table
          const rows = document.querySelectorAll('#sessions-table-body tr');
          rows.forEach(r => {
            const btn = r.querySelector('button[onclick^="switchSession"]');
            if (btn && btn.getAttribute('onclick').includes('(' + sessionId + ')')) {
              _updateSidebarSessionName(r.cells[0] ? r.cells[0].textContent.trim() : '');
            }
          });
          loadSessions();
          loadStats(); loadLeads(); loadCampaigns(); loadHistory();
        } else if (res.error) {
          showToast(res.error, 'error');
        }
      }).catch(() => { /* _apiCall already toasted */ });
    }

    // Delete Session Handler
    function deleteSession(btnOrId, name) {
      let sessionId = btnOrId;
      if (btnOrId && typeof btnOrId === 'object') {
        sessionId = btnOrId.getAttribute('data-id');
        name = btnOrId.getAttribute('data-name');
      }
      showConfirm(
        'Oturumu Sil',
        `<b>${name}</b> oturumunu silmek istediğinizden emin misiniz?<br><br><span style="color:#f87171;font-size:0.82rem;">⚠️ Bu oturuma ait tüm adaylar, kampanyalar ve geçmiş günlükleri kalıcı olarak silinecektir!</span>`,
        'Evet, Sil',
        true
      ).then(ok => {
        if (!ok) return;
        const promise = _apiCall(
          () => window.pywebview.api.delete_session(sessionId),
          { action: 'Oturum silme' }
        );
        promise.then(res => {
          if (!res) return;
          if (res.success) {
            showToast(`"${name}" oturumu başarıyla silindi.`, 'success');
            loadSessions();
          } else if (res.error) {
            showToast(res.error, 'error');
          }
        }).catch(() => { /* _apiCall already toasted */ });
      });
    }

    // Delete Lead Handler
    function triggerDeleteLead(btnOrId, name) {
      let leadId = btnOrId;
      if (btnOrId && typeof btnOrId === 'object') {
        leadId = btnOrId.getAttribute('data-id');
        name = btnOrId.getAttribute('data-name');
      }
      showConfirm('Adayı Sil', `<b>${name}</b> adayını kalıcı olarak silmek istediğinizden emin misiniz?`, 'Evet, Sil', true).then(ok => {
        if (!ok) return;
        const promise = _apiCall(
          () => window.pywebview.api.delete_lead(leadId),
          { action: 'Aday silme' }
        );
        promise.then(res => {
          if (!res) return;
          if (res.success) {
            showToast(`"${name}" adayı silindi.`, 'success');
            loadLeads(true); loadStats(); loadHistory();
            document.getElementById('lead-detail-view').innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 100px;"><p>Detayları görmek için sol listeden bir işletme seçin.</p></div>';
          } else if (res.error) {
            showToast(res.error, 'error');
          }
        }).catch(() => { /* _apiCall already toasted */ });
      });
    }

    // Clear all leads in active session
    function triggerClearLeadsAll() {
      showConfirm(
        'Tüm Adayları Sil',
        'Bu çalışma oturumundaki <b>tüm adayları, araştırma notlarını ve mesaj taslaklarını</b> kalıcı olarak silmek istediğinizden emin misiniz?',
        'Evet, Tümünü Sil',
        true
      ).then(ok => {
        if (!ok) return;
        // Find the "Tümünü Sil" button so it shows a busy spinner.
        const clearBtn = Array.from(document.querySelectorAll('button')).find(b =>
          (b.getAttribute('title') || '').includes('tüm aday verilerini kalıcı olarak siler')
        );
        const promise = _apiCall(
          () => window.pywebview.api.clear_all_leads(),
          { action: 'Tüm adayları sil' }
        );
        const wrapped = clearBtn ? _withButtonBusy(clearBtn, promise) : promise;
        wrapped.then(res => {
          if (!res) return;
          if (res.success) {
            showToast('Tüm adaylar başarıyla temizlendi.', 'success');
            loadLeads();
            loadStats();
            loadHistory();
            document.getElementById('lead-detail-view').innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 100px;"><p>Detayları görmek için sol listeden bir işletme seçin.</p></div>';
          } else {
            showToast(res.error, 'error');
          }
        }).catch(() => { /* _apiCall already toasted */ });
      });
    }

    // Clear filtered leads
    function triggerClearLeadsFiltered() {
      if (!_isBridgeReady()) {
        _bridgeUnavailableError('Adayları silme');
        return;
      }
      const status = document.getElementById('filter-status').value;
      const statusText = document.getElementById('filter-status').options[document.getElementById('filter-status').selectedIndex].text;
      
      showPrompt(
        'Filtreli Aday Temizliği',
        `Durumu <b>"${statusText}"</b> olan adaylardan silmek istediğiniz sektörü (kategoriyi) belirtin.<br><span style="color:var(--text-muted);font-size:0.8rem;">(Boş bırakırsanız seçili durumdaki tüm sektörler silinir)</span>`,
        '',
        'ör. kuaför'
      ).then(sector => {
        if (sector === null) return;
        
        const confirmMsg = `Durumu <b>"${statusText}"</b> ${sector ? `ve sektörü <b>"${sector}"</b>` : ''} olan tüm adayları kalıcı olarak silmek istediğinizden emin misiniz?`;
        
        showConfirm('Filtreli Adayları Sil', confirmMsg, 'Evet, Sil', true).then(ok => {
          if (!ok) return;
          _apiCall(() => window.pywebview.api.clear_leads_by_filter(status, sector), { action: 'Filtreli adayları sil' }).then(res => {
            if (!res) return;
            if (res.success) {
              showToast(`${res.deleted_count} adet aday silindi.`, 'success');
              loadLeads();
              loadStats();
              loadHistory();
              document.getElementById('lead-detail-view').innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 100px;"><p>Detayları görmek için sol listeden bir işletme seçin.</p></div>';
            } else {
              showToast(res.error, 'error');
            }
          });
        });
      });
    }

    // Delete Campaign Handler
    function triggerDeleteCampaign(btnOrId, name) {
      let campaignId = btnOrId;
      if (btnOrId && typeof btnOrId === 'object') {
        campaignId = btnOrId.getAttribute('data-id');
        name = btnOrId.getAttribute('data-name');
      }
      showConfirm('Kampanyayı Sil', `<b>${name}</b> kampanyasını silmek istediğinizden emin misiniz?<br><br><span style="color:var(--text-muted);font-size:0.82rem;">Not: Kampanyadaki adaylar silinmez, havuzda serbest bırakılır.</span>`, 'Evet, Sil', true).then(ok => {
        if (!ok) return;
        const promise = _apiCall(
          () => window.pywebview.api.delete_campaign(campaignId),
          { action: 'Kampanya silme' }
        );
        promise.then(res => {
          if (!res) return;
          if (res.success) {
            showToast(`"${name}" kampanyası silindi.`, 'success');
            loadCampaigns(); loadLeads(); loadStats(); loadHistory();
            document.getElementById('campaign-detail-view').innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 100px;"><p>Detayları görmek ve adayları atamak için sol listeden bir kampanya seçin.</p></div>';
          } else if (res.error) {
            showToast(res.error, 'error');
          }
        }).catch(() => { /* _apiCall already toasted */ });
      });
    }

    // Delete Log Handler
    function deleteLog(logId) {
      showConfirm('Kaydı Sil', 'Bu geçmiş kaydını kalıcı olarak silmek istediğinizden emin misiniz?', 'Evet, Sil', true).then(ok => {
        if (!ok) return;
        const promise = _apiCall(
          () => window.pywebview.api.delete_activity_log(logId),
          { action: 'Kayıt silme' }
        );
        promise.then(res => {
          if (!res) return;
          if (res.success) { showToast('Geçmiş kaydı silindi.', 'success'); loadHistory(); }
          else if (res.error) { showToast(res.error, 'error'); }
        }).catch(() => { /* _apiCall already toasted */ });
      });
    }

    // 👁️ Toggle Password Visibility
    function togglePasswordVisibility(inputId, btn) {
      const input = document.getElementById(inputId);
      if (!input) return;
      if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = '🔒';
      } else {
        input.type = 'password';
        btn.textContent = '👁️';
      }
    }

    // 🌐 i18n Translation Dictionary
    const TRANSLATIONS = {
      tr: {
        dashboard: "Dashboard",
        leads: "Adaylar (Leads)",
        campaigns: "Kampanyalar",
        history: "Geçmiş",
        sessions: "Oturumlar",
        settings: "Ayarlar",
        
        dashboard_title: "Dashboard",
        dashboard_subtitle: "Müşteri keşif turları başlatın ve genel durum istatistiklerini takip edin.",
        db_card_new: "YENİ KEŞFEDİLEN",
        db_card_researched: "AI ANALİZİ HAZIR",
        db_card_contacted: "İLETİŞİME GEÇİLDİ",
        db_card_replied: "YANIT ALINDI",
        db_search_sec_title: "İşletme Keşif Radarı",
        db_search_sec_subtitle: "Belirli bölge ve sektörlerdeki yeni adayları otomatik tara.",
        
        lbl_sector: "Sektör Anahtar Kelimesi",
        lbl_location: "Konum / Bölge",
        lbl_radius: "Yarıçap (km)",
        lbl_provider: "Veri Kaynağı",
        btn_start_discovery: "Keşif Turunu Başlat 🚀",
        
        leads_title: "Müşteri Adayları",
        leads_subtitle: "Keşfedilen işletmeleri inceleyin, AI analizi yapın ve iletişime geçin.",
        btn_export_csv: "📥 CSV",
        btn_clear_category: "Kategoriyi Sil 🗑️",
        btn_clear_all: "Tümünü Sil 🗑️",
        
        tbl_col_name: "İşletme Adı",
        tbl_col_sector: "Sektör",
        tbl_col_addr: "Konum",
        tbl_col_web: "Web",
        tbl_col_status: "Durum",
        
        settings_title: "Ayarlar",
        settings_subtitle: "API anahtarlarını, otomasyon ayarlarını ve bildirim kanallarını yapılandırın.",
        settings_sec_env: "Uygulama Yapılandırması (.env)",
        settings_section_llm: "1. LLM / Yapay Zeka Ayarları",
        settings_section_google: "2. Google ve Arama Servisleri",
        settings_section_ig: "3. Instagram Otomasyonu (Mod B)",
        settings_section_notif: "4. Bildirim Kanalları (SMTP / Telegram)",
        settings_section_ui: "5. Arayüz Ayarları",
        btn_save_settings: "Ayarları Kaydet",
        
        lbl_primary_llm: "Birincil LLM Sağlayıcı",
        lbl_fallback_llm: "Yedek (Fallback) Sağlayıcı",
        lbl_deepseek_key: "DeepSeek API Anahtarı",
        lbl_openai_key: "OpenAI API Anahtarı",
        lbl_anthropic_key: "Anthropic API Anahtarı",
        lbl_openrouter_key: "OpenRouter API Anahtarı",
        lbl_gemini_key: "Gemini API Anahtarı",
        lbl_groq_key: "Groq API Anahtarı",
        lbl_mistral_key: "Mistral API Anahtarı",
        lbl_ollama_url: "Ollama Base URL (Yerel)",
        lbl_google_places_key: "Google Places API Anahtarı",
        lbl_google_search_key: "Google Custom Search API Anahtarı",
        lbl_google_search_cx: "Google Custom Search CX (Arama Motoru ID)",
        lbl_ig_username: "Instagram Kullanıcı Adı",
        lbl_ig_password: "Instagram Şifresi",
        lbl_ig_encryption_key: "Oturum Şifreleme Anahtarı",
        lbl_outreach_mode: "Erişim Modu (Outreach Mode)",
        lbl_max_outreach: "Günlük Maksimum Mesaj Limiti",
        lbl_tg_token: "Telegram Bot Token",
        lbl_tg_chatid: "Telegram Chat ID",
        lbl_smtp_host: "SMTP Host",
        lbl_smtp_port: "SMTP Port",
        lbl_smtp_user: "E-posta Kullanıcı Adı (From)",
        lbl_smtp_pass: "E-posta Şifresi",
        lbl_cfg_lang: "Arayüz Dili (Language)",
        lbl_cfg_theme: "Arayüz Teması (Theme)",
        lbl_cfg_show_console: "Geliştirici Konsolu (CMD)",
        info_cfg_show_console_desc: "Uygulama arkasında çalışan CMD terminal penceresinin görünürlüğünü ayarlar. Logları gerçek zamanlı izlemek için 'Açık' tutabilirsiniz.",
        lbl_open_logs: "Log Dosyaları (Logs)",
        btn_open_logs: "Log Klasörünü Aç",
        
        opt_none: "Yok",
        opt_assisted: "Assisted Mod A (Clipboard & Tarayıcı - Güvenli)",
        opt_full_auto: "Mod B (Tam Otomasyon - Riskli)",
        
        automation_risk_text: "⚠️ <b>UYARI:</b> Tam otomasyon modunun etkinleştirilmesi Instagram Kullanım Koşulları'nı (ToS) ihlal eder. Hesabınızın kısıtlanması veya kapatılması riskini anlıyor musunuz?",
        automation_confirm_label: "Riskleri anladım, tam otomasyonu etkinleştirmek istiyorum.",
        
        // Tooltip Descriptions
        info_primary_llm_desc: "Mesaj taslaklarını ve analiz notlarını üretirken kullanılacak birincil yapay zeka model sağlayıcısı.",
        info_fallback_llm_desc: "Birincil LLM hata verirse veya limiti dolarsa otomatik olarak devreye girecek yedek sağlayıcı.",
        info_deepseek_key_desc: "DeepSeek LLM modelini kullanarak akıllı outreach taslakları üretmek için gereklidir.",
        info_openai_key_desc: "OpenAI GPT-4o modellerine erişim için gerekli API anahtarı.",
        info_anthropic_key_desc: "Anthropic Claude (3.5 Haiku, Sonnet vb.) modelleri için gerekli API anahtarı.",
        info_openrouter_key_desc: "Çeşitli açık kaynak ve ticari modellere tek bir API üzerinden erişmek için kullanılır.",
        info_gemini_key_desc: "Google Gemini (2.5 Flash, Pro vb.) modelleri için gerekli API anahtarı.",
        info_groq_key_desc: "Groq Llama 3 modellerine ultra hızlı erişim için gerekli API anahtarı.",
        info_mistral_key_desc: "Mistral AI modellerine erişim için gerekli API anahtarı.",
        info_ollama_url_desc: "Bilgisayarınızda yerel çalışan Ollama servisinin adresi (örn. http://localhost:11434). Tamamen offline çalışmayı sağlar.",
        info_google_places_key_desc: "Google Haritalar üzerinden işletmeleri daha güncel ve zengin aramak için gerekli Places API anahtarı.",
        info_google_search_key_desc: "Google arama motoru üzerinden işletmelerin web site veya Instagram adreslerini bulmak için kullanılan Custom Search API anahtarı.",
        info_google_search_cx_desc: "Google Custom Search Engine (CSE) için oluşturulmuş arama motoru ID'niz (CX).",
        info_ig_username_desc: "Otomasyon modunun DM göndermek ve gelen mesajları kontrol etmek için kullanacağı Instagram kullanıcı adı.",
        info_ig_password_desc: "Instagram hesabınızın şifresi. Şifreniz yerel diskte şifrelenmiş olarak saklanır.",
        info_ig_encryption_key_desc: "Instagram şifrenizin diskte güvenle saklanması için kullanılan Fernet simetrik şifreleme anahtarı.",
        info_outreach_mode_desc: "Assisted Mod A: Güvenlidir. Mesajı panoya kopyalar ve Instagram profilini tarayıcıda açar, siz gönderirsiniz. Mod B: Otomatiktir. Hesabınızdan arka planda mesaj gönderir ancak spam filtresi ve ToS riski barındırır.",
        info_max_outreach_desc: "Instagram hesabınızın spam engeline takılmaması için günlük gönderilecek maksimum mesaj limiti. (Önerilen: 15-20)",
        info_tg_token_desc: "Uygulamadaki yanıtlar veya hata durumları hakkında size mesaj gönderecek olan Telegram bot token'ı.",
        info_tg_chatid_desc: "Telegram botunun bildirim göndereceği chat (kullanıcı veya grup) benzersiz ID'si.",
        info_smtp_host_desc: "E-posta bildirimleri göndermek için kullanılacak posta sunucusu adresi (örn. smtp.gmail.com).",
        info_smtp_port_desc: "SMTP sunucusunun port numarası (genellikle TLS için 587 veya SSL için 465).",
        info_smtp_user_desc: "SMTP sunucusunda oturum açmak için kullanılacak e-posta adresi.",
        info_smtp_pass_desc: "SMTP sunucusu e-posta şifresi (veya Gmail için özel Uygulama Şifresi).",
        info_cfg_lang_desc: "Uygulama dilini Türkçe veya İngilizce olarak değiştirin.",
        info_cfg_theme_desc: "Arayüzün görünümünü ve renk şemasını değiştirin."
      },
      en: {
        dashboard: "Dashboard",
        leads: "Leads",
        campaigns: "Campaigns",
        history: "History",
        sessions: "Sessions",
        settings: "Settings",
        
        dashboard_title: "Dashboard",
        dashboard_subtitle: "Start business discovery scans and track overall status statistics.",
        db_card_new: "NEW DISCOVERED",
        db_card_researched: "AI ANALYSIS READY",
        db_card_contacted: "CONTACTED",
        db_card_replied: "REPLIES RECEIVED",
        db_search_sec_title: "Business Discovery Radar",
        db_search_sec_subtitle: "Automatically scan new leads in specific locations and sectors.",
        
        lbl_sector: "Sector Keyword",
        lbl_location: "Location / Region",
        lbl_radius: "Radius (km)",
        lbl_provider: "Data Source",
        btn_start_discovery: "Launch Scan 🚀",
        
        leads_title: "Leads Manager",
        leads_subtitle: "Analyze discovered businesses, run AI research, and start outreach.",
        btn_export_csv: "📥 CSV",
        btn_clear_category: "Clear Category 🗑️",
        btn_clear_all: "Clear All 🗑️",
        
        tbl_col_name: "Business Name",
        tbl_col_sector: "Sector",
        tbl_col_addr: "Location",
        tbl_col_web: "Web",
        tbl_col_status: "Status",
        
        settings_title: "Settings",
        settings_subtitle: "Configure API keys, automation settings, and notification channels.",
        settings_sec_env: "Application Configuration (.env)",
        settings_section_llm: "1. LLM / AI Engine Settings",
        settings_section_google: "2. Google & Search Services",
        settings_section_ig: "3. Instagram Automation (Mod B)",
        settings_section_notif: "4. Notification Channels (SMTP / Telegram)",
        settings_section_ui: "5. UI Settings",
        btn_save_settings: "Save Settings",
        
        lbl_primary_llm: "Primary LLM Provider",
        lbl_fallback_llm: "Fallback LLM Provider",
        lbl_deepseek_key: "DeepSeek API Key",
        lbl_openai_key: "OpenAI API Key",
        lbl_anthropic_key: "Anthropic API Key",
        lbl_openrouter_key: "OpenRouter API Key",
        lbl_gemini_key: "Gemini API Key",
        lbl_groq_key: "Groq API Key",
        lbl_mistral_key: "Mistral API Key",
        lbl_ollama_url: "Ollama Base URL (Local)",
        lbl_google_places_key: "Google Places API Key",
        lbl_google_search_key: "Google Custom Search API Key",
        lbl_google_search_cx: "Google Custom Search CX (Search Engine ID)",
        lbl_ig_username: "Instagram Username",
        lbl_ig_password: "Instagram Password",
        lbl_ig_encryption_key: "Session Encryption Key",
        lbl_outreach_mode: "Outreach Mode",
        lbl_max_outreach: "Max Daily Outreach Limit",
        lbl_tg_token: "Telegram Bot Token",
        lbl_tg_chatid: "Telegram Chat ID",
        lbl_smtp_host: "SMTP Host",
        lbl_smtp_port: "SMTP Port",
        lbl_smtp_user: "Email Username (From)",
        lbl_smtp_pass: "Email Password",
        lbl_cfg_lang: "Interface Language",
        lbl_cfg_theme: "Interface Theme",
        lbl_cfg_show_console: "Developer Console (CMD)",
        info_cfg_show_console_desc: "Toggles visibility of the background CMD terminal window. Keep it 'Open' to monitor logs in real time.",
        lbl_open_logs: "Logs",
        btn_open_logs: "Open Logs Folder",
        
        opt_none: "None",
        opt_assisted: "Assisted Mode A (Clipboard & Browser - Safe)",
        opt_full_auto: "Mode B (Full Automation - Risky)",
        
        automation_risk_text: "⚠️ <b>WARNING:</b> Enabling full automation mode violates Instagram Terms of Service (ToS). Do you understand the risk of account limitation or suspension?",
        automation_confirm_label: "I understand the risks, activate full automation.",
        
        // Tooltip Descriptions
        info_primary_llm_desc: "The primary AI model provider used to draft messages and analysis notes.",
        info_fallback_llm_desc: "The backup provider that will automatically activate if the primary LLM fails or limits out.",
        info_deepseek_key_desc: "Required to generate smart outreach drafts using DeepSeek LLM models.",
        info_openai_key_desc: "Required API key for accessing OpenAI GPT-4o models.",
        info_anthropic_key_desc: "Required API key for Anthropic Claude (3.5 Haiku, Sonnet, etc.) models.",
        info_openrouter_key_desc: "Enables access to various open source and commercial models via a single API on OpenRouter.",
        info_gemini_key_desc: "Required API key for Google Gemini models.",
        info_groq_key_desc: "Required API key for fast access to Groq Llama 3 models.",
        info_mistral_key_desc: "Required API key for Mistral AI models.",
        info_ollama_url_desc: "Ollama local service address running on your machine (e.g. http://localhost:11434). Enables fully offline runs.",
        info_google_places_key_desc: "Google Places API key required to search map businesses with higher details.",
        info_google_search_key_desc: "Custom Search API key used to find business websites or Instagram profiles on Google.",
        info_google_search_cx_desc: "Your Search Engine ID (CX) created for Google Custom Search Engine.",
        info_ig_username_desc: "Instagram username used by the automation to send DMs and check inbox replies.",
        info_ig_password_desc: "Your Instagram password. Stored encrypted securely on local disk.",
        info_ig_encryption_key_desc: "Fernet symmetric key used to encrypt the Instagram password on disk.",
        info_outreach_mode_desc: "Assisted Mode A: Safe. Copies draft and opens profile, you send. Mode B: Automated. Sends DM in background, carries spam filter and account suspend risk.",
        info_max_outreach_desc: "Daily limit of outbound Instagram DMs to prevent spam block. (Recommended: 15-20)",
        info_tg_token_desc: "Telegram bot token to notify you about inbox replies or app logs.",
        info_tg_chatid_desc: "Unique Telegram user/group ID to receive bot notifications.",
        info_smtp_host_desc: "Mail server address used to send email alerts (e.g. smtp.gmail.com).",
        info_smtp_port_desc: "SMTP server port (typically 587 for TLS or 465 for SSL).",
        info_smtp_user_desc: "Email username used to login to SMTP.",
        info_smtp_pass_desc: "Email password or app-specific password used to authenticate SMTP.",
        info_cfg_lang_desc: "Change the application display language.",
        info_cfg_theme_desc: "Change the visual interface colors and theme."
      },
      ar: {
        dashboard: "لوحة القيادة",
        leads: "العملاء المحتملون",
        campaigns: "الحملات",
        history: "السجل",
        sessions: "الجلسات",
        settings: "الإعدادات",
        dashboard_title: "لوحة القيادة",
        dashboard_subtitle: "ابدأ مسح اكتشاف الأعمال وتتبع إحصاءات الحالة العامة.",
        db_card_new: "تم اكتشافه حديثًا",
        db_card_researched: "تحليل الذكاء الاصطناعي جاهز",
        db_card_contacted: "تم الاتصال به",
        db_card_replied: "الردود المستلمة",
        db_search_sec_title: "رادار اكتشاف الأعمال",
        db_search_sec_subtitle: "امسح العملاء المحتملين تلقائيًا في مواقع وقطاعات محددة.",
        lbl_sector: "الكلمة المفتاحية للقطاع",
        lbl_location: "الموقع / المنطقة",
        lbl_radius: "نصف القطر (كم)",
        lbl_provider: "مصدر البيانات",
        btn_start_discovery: "بدء المسح 🚀",
        leads_title: "إدارة العملاء المحتملين",
        leads_subtitle: "قم بتحليل الأعمال المكتشفة، وتشغيل أبحاث الذكاء الاصطناعي، وبدء التواصل.",
        btn_export_csv: "📥 تصدير",
        btn_clear_category: "حذف الفئة 🗑️",
        btn_clear_all: "حذف الكل 🗑️",
        tbl_col_name: "اسم العمل",
        tbl_col_sector: "القطاع",
        tbl_col_addr: "الموقع",
        tbl_col_web: "موقع الويب",
        tbl_col_status: "الحالة",
        settings_title: "الإعدادات",
        settings_subtitle: "تكوين مفاتيح API، وإعدادات الأتمتة، وقنوات الإشعار.",
        settings_sec_env: "تكوين التطبيق (.env)",
        settings_section_llm: "1. إعدادات محرك الذكاء الاصطناعي / LLM",
        settings_section_google: "2. خدمات جوجل والبحث",
        settings_section_ig: "3. أتمتة إنستغرام (الوضع ب)",
        settings_section_notif: "4. قنوات الإشعار (SMTP / Telegram)",
        settings_section_ui: "5. إعدادات الواجهة",
        btn_save_settings: "حفظ الإعدادات",
        lbl_primary_llm: "مزود LLM الرئيسي",
        lbl_fallback_llm: "المزود الاحتياطي (Fallback)",
        lbl_deepseek_key: "مفتاح DeepSeek API",
        lbl_openai_key: "مفتاح OpenAI API",
        lbl_anthropic_key: "مفتاح Anthropic API",
        lbl_openrouter_key: "مفتاح OpenRouter API",
        lbl_gemini_key: "مفتاح Gemini API",
        lbl_groq_key: "مفتاح Groq API",
        lbl_mistral_key: "مفتاح Mistral API",
        lbl_ollama_url: "عنوان Ollama المحلي",
        lbl_google_places_key: "مفتاح Google Places API",
        lbl_google_search_key: "مفتاح Google Custom Search API",
        lbl_google_search_cx: "معرف محرك البحث Google CX",
        lbl_ig_username: "اسم مستخدم إنستغرام",
        lbl_ig_password: "كلمة مرور إنستغرام",
        lbl_ig_encryption_key: "مفتاح تشفير الجلسة",
        lbl_outreach_mode: "وضع التواصل",
        lbl_max_outreach: "الحد الأقصى للتواصل اليومي",
        lbl_tg_token: "رمز بوت تليجرام",
        lbl_tg_chatid: "معرف دردشة تليجرام",
        lbl_smtp_host: "SMTP Host",
        lbl_smtp_port: "منفذ SMTP",
        lbl_smtp_user: "اسم مستخدم البريد الإلكتروني (من)",
        lbl_smtp_pass: "كلمة مرور البريد الإلكتروني",
        lbl_cfg_lang: "لغة الواجهة",
        lbl_cfg_theme: "مظهر الواجهة",
        lbl_cfg_show_console: "وحدة تحكم المطور (CMD)",
        info_cfg_show_console_desc: "تبديل رؤية نافذة وحدة تحكم CMD الخلفية. أبقها مفتوحة لمراقبة السجلات في الوقت الفعلي.",
        lbl_open_logs: "السجلات",
        btn_open_logs: "فتح مجلد السجلات",
        opt_none: "لا يوجد",
        opt_assisted: "الوضع المساعد أ (الحافظة والمتصفح - آمن)",
        opt_full_auto: "الوضع ب (الأتمتة الكاملة - خطير)",
        automation_risk_text: "⚠️ <b>تحذير:</b> تمكين وضع الأتمتة الكاملة ينتهك شروط خدمة إنستغرام. هل تفهم مخاطر تقييد الحساب أو تعليقه؟",
        automation_confirm_label: "أفهم المخاطر، أريد تنشيط الأتمتة الكاملة.",
        info_primary_llm_desc: "مزود نموذج الذكاء الاصطناعي الأساسي المستخدم لصياغة الرسائل وملاحظات التحليل.",
        info_fallback_llm_desc: "المزود الاحتياطي الذي سيتم تنشيطه تلقائيًا في حالة فشل نموذج الذكاء الاصطناعي الأساسي.",
        info_deepseek_key_desc: "مطلوب لإنشاء مسودات تواصل ذكية باستخدام نماذج DeepSeek.",
        info_openai_key_desc: "مفتاح API مطلوب للوصول إلى نماذج OpenAI GPT-4o.",
        info_anthropic_key_desc: "مفتاح API مطلوب لنماذج Anthropic Claude.",
        info_openrouter_key_desc: "تمكين الوصول إلى نماذج تجارية ومفتوحة المصدر مختلفة عبر واجهة برمجة تطبيقات واحدة.",
        info_gemini_key_desc: "مفتاح API مطلوب لنماذج Google Gemini.",
        info_groq_key_desc: "مفتاح API مطلوب للوصول السريع إلى نماذج Groq Llama 3.",
        info_mistral_key_desc: "مفتاح API مطلوب لنماذج Mistral AI.",
        info_ollama_url_desc: "عنوان خدمة Ollama المحلية التي تعمل على جهازك لتشغيل النماذج دون اتصال بالإنترنت تمامًا.",
        info_google_places_key_desc: "مفتاح Google Places API مطلوب للبحث عن الشركات بمعلومات وتفاصيل أكثر ثراءً.",
        info_google_search_key_desc: "مفتاح Custom Search API المستخدم للعثور على مواقع الشركات أو حسابات إنستغرام على جوجل.",
        info_google_search_cx_desc: "معرف محرك البحث الخاص بك (CX) الذي تم إنشاؤه لـ Google Custom Search.",
        info_ig_username_desc: "اسم مستخدم إنستغرام المستخدم لإرسال الرسائل والتحقق من الردود.",
        info_ig_password_desc: "كلمة مرور إنستغرام الخاصة بك. مخزنة مشفرة على القرص المحلي.",
        info_ig_encryption_key_desc: "مفتاح تشفير يستخدم لتشفير كلمة مرور إنستغرام على القرص.",
        info_outreach_mode_desc: "الوضع أ: آمن. ينسخ المسودة ويفتح الملف الشخصي، وتقوم أنت بالإرسال. الوضع ب: تلقائي. يرسل رسائل في الخلفية، ويحمل مخاطر الحظر.",
        info_max_outreach_desc: "الحد اليومي لإرسال رسائل إنستغرام لتجنب الحظر (موصى به: 15-20).",
        info_tg_token_desc: "رمز بوت تليجرام لإعلامك بالردود الجديدة أو سجلات التطبيق.",
        info_tg_chatid_desc: "معرف دردشة تليجرام لتلقي إشعارات البوت.",
        info_smtp_host_desc: "عنوان خادم البريد المستخدم لإرسال تنبيهات البريد الإلكتروني.",
        info_smtp_port_desc: "منفذ خادم SMTP (عادةً 587 لـ TLS أو 465 لـ SSL).",
        info_smtp_user_desc: "اسم مستخدم البريد الإلكتروني المستخدم لتسجيل الدخول إلى SMTP.",
        info_smtp_pass_desc: "كلمة مرور البريد الإلكتروني أو كلمة مرور التطبيق المستخدمة لـ SMTP.",
        info_cfg_lang_desc: "تغيير لغة عرض التطبيق.",
        info_cfg_theme_desc: "تغيير ألوان مظهر الواجهة والسمة المحددة."
      },
      zh: {
        dashboard: "仪表盘",
        leads: "潜在客户",
        campaigns: "营销活动",
        history: "操作历史",
        sessions: "工作会话",
        settings: "系统设置",
        dashboard_title: "仪表盘",
        dashboard_subtitle: "启动业务搜索扫描并跟踪全局状态统计数据。",
        db_card_new: "新发现商家",
        db_card_researched: "AI分析完成",
        db_card_contacted: "已联系商家",
        db_card_replied: "收到回复数",
        db_search_sec_title: "业务探索雷达",
        db_search_sec_subtitle: "自动在特定区域和行业扫描新的潜在客户。",
        lbl_sector: "行业关键字",
        lbl_location: "位置 / 区域",
        lbl_radius: "搜索半径 (公里)",
        lbl_provider: "数据源",
        btn_start_discovery: "开始扫描 🚀",
        leads_title: "潜在客户管理",
        leads_subtitle: "分析发现的商家，运行AI研究，并启动对接。",
        btn_export_csv: "📥 导出",
        btn_clear_category: "清空当前类 🗑️",
        btn_clear_all: "清空全部 🗑️",
        tbl_col_name: "商家名称",
        tbl_col_sector: "行业类型",
        tbl_col_addr: "地址位置",
        tbl_col_web: "网站",
        tbl_col_status: "对接状态",
        settings_title: "系统设置",
        settings_subtitle: "配置 API 密钥、自动化参数以及通知通道。",
        settings_sec_env: "应用环境变量配置 (.env)",
        settings_section_llm: "1. AI / 大语言模型设置",
        settings_section_google: "2. Google 及搜索服务配置",
        settings_section_ig: "3. Instagram 自动对接设置 (模式 B)",
        settings_section_notif: "4. 系统通知通道 (SMTP / Telegram)",
        settings_section_ui: "5. 界面个性化设置",
        btn_save_settings: "保存设置",
        lbl_primary_llm: "主 AI 模型提供商",
        lbl_fallback_llm: "备用 AI 模型提供商",
        lbl_deepseek_key: "DeepSeek API 密钥",
        lbl_openai_key: "OpenAI API 密钥",
        lbl_anthropic_key: "Anthropic API 密钥",
        lbl_openrouter_key: "OpenRouter API 密钥",
        lbl_gemini_key: "Gemini API 密钥",
        lbl_groq_key: "Groq API 密钥",
        lbl_mistral_key: "Mistral API 密钥",
        lbl_ollama_url: "本地 Ollama API 地址",
        lbl_google_places_key: "Google Places API 密钥",
        lbl_google_search_key: "Google Custom Search API 密钥",
        lbl_google_search_cx: "Google Custom Search CX (引擎 ID)",
        lbl_ig_username: "Instagram 账号用户名",
        lbl_ig_password: "Instagram 账号密码",
        lbl_ig_encryption_key: "会话本地加密密钥",
        lbl_outreach_mode: "客户对接模式 (Outreach Mode)",
        lbl_max_outreach: "每日发送上限数量",
        lbl_tg_token: "Telegram Bot Token",
        lbl_tg_chatid: "Telegram Chat ID",
        lbl_smtp_host: "SMTP 主机地址",
        lbl_smtp_port: "SMTP 端口号",
        lbl_smtp_user: "发件人邮箱用户名 (From)",
        lbl_smtp_pass: "发件人邮箱密码 / 授权码",
        lbl_cfg_lang: "系统界面语言",
        lbl_cfg_theme: "系统界面主题",
        lbl_cfg_show_console: "开发人员控制台 (CMD)",
        info_cfg_show_console_desc: "切换后台 CMD 终端窗口的显示状态。保持开启可实时监控系统日志。",
        lbl_open_logs: "日志文件",
        btn_open_logs: "打开日志文件夹",
        opt_none: "无",
        opt_assisted: "辅助模式 A (剪贴板与浏览器手动 - 安全)",
        opt_full_auto: "全自动模式 B (后台模拟自动发信 - 风险)",
        automation_risk_text: "⚠️ <b>警告：</b>启用全自动模式违反 Instagram 服务条款。您是否完全知晓并愿意承担账号被封禁或受限的风险？",
        automation_confirm_label: "我已知晓上述风险，申请启用全自动模式。",
        info_primary_llm_desc: "用于撰写开发信草稿和分析报告的主要大语言模型提供商。",
        info_fallback_llm_desc: "当主 AI 服务发生报错或达到配额限制时自动切换的备用服务。",
        info_deepseek_key_desc: "使用 DeepSeek 模型生成个性化开发信所需的 API 密钥。",
        info_openai_key_desc: "访问 OpenAI GPT-4o 系列模型所需的 API 密钥。",
        info_anthropic_key_desc: "访问 Anthropic Claude 3.5 系列模型所需的 API 密钥。",
        info_openrouter_key_desc: "通过 OpenRouter 统一访问各类商业或开源模型所需的 API 密钥。",
        info_gemini_key_desc: "访问 Google Gemini 系列模型所需的 API 密钥。",
        info_groq_key_desc: "极速访问 Groq 托管的 Llama 3 等开源模型所需的 API 密钥。",
        info_mistral_key_desc: "访问 Mistral AI 商业模型所需的 API 密钥。",
        info_ollama_url_desc: "运行在本地的 Ollama 服务 API 接口地址 (例如 http://localhost:11434)。开启全离线模式。",
        info_google_places_key_desc: "用于在 Google 地图上更精准、丰富地抓取商家信息所需的 Places 密钥。",
        info_google_search_key_desc: "用于在 Google 上反查商家官网和 Instagram 社交账号的 Custom Search 密钥。",
        info_google_search_cx_desc: "您为 Google 自定义搜索引擎生成的搜索引擎 ID (CX)。",
        info_ig_username_desc: "自动对接模块用于登录并发送私信、检测回复的 Instagram 账号名称。",
        info_ig_password_desc: "Instagram 账号的登录密码。将以高度安全加密的形式存储在本地磁盘上。",
        info_ig_encryption_key_desc: "用于本地加密 Instagram 密码的 Fernet 对称加密密钥。",
        info_outreach_mode_desc: "辅助模式 A: 安全。复制开发信并打开对方主页由您发送。模式 B: 全自动。由后台程序代发，存在封号和反垃圾机制拦截风险。",
        info_max_outreach_desc: "每日发信的上限以避免触发 Instagram 封号机制 (推荐值: 15-20)。",
        info_tg_token_desc: "用于将客户回复或程序运行日志推送到您手机上的 Telegram Bot 密钥。",
        info_tg_chatid_desc: "用于接收通知的 Telegram 个人聊天 ID 或群组 ID。",
        info_smtp_host_desc: "发送邮件通知所需的 SMTP 服务器地址 (如 smtp.gmail.com)。",
        info_smtp_port_desc: "SMTP 服务器端口 (一般 TLS 使用 587，SSL 使用 465)。",
        info_smtp_user_desc: "用于登录 SMTP 服务器的邮箱账号。",
        info_smtp_pass_desc: "SMTP 邮箱登录密码或系统专用的应用程序密码。",
        info_cfg_lang_desc: "更改本软件的整体显示语言。",
        info_cfg_theme_desc: "更换软件界面的主题色调和视觉风格。"
      },
      ru: {
        dashboard: "Панель",
        leads: "Лиды",
        campaigns: "Кампании",
        history: "История",
        sessions: "Сессии",
        settings: "Настройки",
        dashboard_title: "Панель управления",
        dashboard_subtitle: "Запуск сканирования и общая статистика.",
        db_card_new: "НОВЫЕ ЛИДЫ",
        db_card_researched: "AI АНАЛИЗ ГОТОВ",
        db_card_contacted: "СВЯЗАЛИСЬ",
        db_card_replied: "ОТВЕТЫ ПОЛУЧЕНЫ",
        db_search_sec_title: "Радар поиска бизнесов",
        db_search_sec_subtitle: "Автоматический поиск лидов в выбранных локациях и сферах.",
        lbl_sector: "Ключевое слово сферы",
        lbl_location: "Локация / Регион",
        lbl_radius: "Радиус (км)",
        lbl_provider: "Источник данных",
        btn_start_discovery: "Начать поиск 🚀",
        leads_title: "Управление лидами",
        leads_subtitle: "Анализ найденных лидов, запуск AI-исследований и начало охвата.",
        btn_export_csv: "📥 Экспорт",
        btn_clear_category: "Очистить категорию 🗑️",
        btn_clear_all: "Очистить всё 🗑️",
        tbl_col_name: "Название бизнеса",
        tbl_col_sector: "Сфера",
        tbl_col_addr: "Адрес",
        tbl_col_web: "Сайт",
        tbl_col_status: "Статус",
        settings_title: "Настройки",
        settings_subtitle: "Настройка API ключей, параметров автоматизации и каналов уведомлений.",
        settings_sec_env: "Конфигурация приложения (.env)",
        settings_section_llm: "1. Параметры AI / LLM моделей",
        settings_section_google: "2. Службы Google и поиск",
        settings_section_ig: "3. Автоматизация Instagram (Режим B)",
        settings_section_notif: "4. Уведомления (SMTP / Telegram)",
        settings_section_ui: "5. Настройки интерфейса",
        btn_save_settings: "Сохранить настройки",
        lbl_primary_llm: "Основной провайдер LLM",
        lbl_fallback_llm: "Резервный провайдер LLM",
        lbl_deepseek_key: "API Ключ DeepSeek",
        lbl_openai_key: "API Ключ OpenAI",
        lbl_anthropic_key: "API Ключ Anthropic",
        lbl_openrouter_key: "API Ключ OpenRouter",
        lbl_gemini_key: "API Ключ Gemini",
        lbl_groq_key: "API Ключ Groq",
        lbl_mistral_key: "API Ключ Mistral",
        lbl_ollama_url: "Адрес локального Ollama",
        lbl_google_places_key: "API Ключ Google Places",
        lbl_google_search_key: "API Ключ Google Custom Search",
        lbl_google_search_cx: "ID поискового движка Google (CX)",
        lbl_ig_username: "Имя пользователя Instagram",
        lbl_ig_password: "Пароль Instagram",
        lbl_ig_encryption_key: "Ключ шифрования сессии",
        lbl_outreach_mode: "Режим охвата (Outreach Mode)",
        lbl_max_outreach: "Дневной лимит сообщений",
        lbl_tg_token: "Токен бота Telegram",
        lbl_tg_chatid: "Chat ID в Telegram",
        lbl_smtp_host: "SMTP Хост",
        lbl_smtp_port: "SMTP Порт",
        lbl_smtp_user: "Имя пользователя Email (От кого)",
        lbl_smtp_pass: "Пароль от Email",
        lbl_cfg_lang: "Язык интерфейса",
        lbl_cfg_theme: "Тема интерфейса",
        lbl_cfg_show_console: "Консоль разработчика (CMD)",
        info_cfg_show_console_desc: "Показывает или скрывает фоновое окно терминала CMD. Оставьте открытым для отслеживания логов в реальном времени.",
        lbl_open_logs: "Логи",
        btn_open_logs: "Открыть папку с логами",
        opt_none: "Нет",
        opt_assisted: "Ассистент А (Буфер и браузер - Безопасно)",
        opt_full_auto: "Режим B (Полная автоматизация - Рискованно)",
        automation_risk_text: "⚠️ <b>ВНИМАНИЕ:</b> Включение полной автоматизации нарушает правила Instagram. Вы понимаете риск блокировки аккаунта?",
        automation_confirm_label: "Я понимаю риски, включить автоматизацию.",
        info_primary_llm_desc: "Основной провайдер AI для составления черновиков сообщений и анализа.",
        info_fallback_llm_desc: "Резервный провайдер, который включится автоматически при сбое основного.",
        info_deepseek_key_desc: "Требуется для составления умных сообщений через модели DeepSeek.",
        info_openai_key_desc: "Требуется для доступа к моделям OpenAI GPT-4o.",
        info_anthropic_key_desc: "Требуется для доступа к моделям Anthropic Claude.",
        info_openrouter_key_desc: "Дает доступ к различным моделям через одно API OpenRouter.",
        info_gemini_key_desc: "Требуется для моделей Google Gemini.",
        info_groq_key_desc: "Требуется для быстрого доступа к моделям Groq Llama 3.",
        info_mistral_key_desc: "Требуется для доступа к моделям Mistral AI.",
        info_ollama_url_desc: "Адрес локального сервиса Ollama на вашем ПК для полной работы офлайн.",
        info_google_places_key_desc: "API ключ Google Places для поиска детальной информации о бизнесах на картах.",
        info_google_search_key_desc: "Ключ Custom Search для поиска сайтов или профилей Instagram в Google.",
        info_google_search_cx_desc: "Ваш ID поискового движка (CX) в Google Custom Search.",
        info_ig_username_desc: "Логин Instagram для отправки сообщений и проверки ответов.",
        info_ig_password_desc: "Пароль от Instagram. Хранится в зашифрованном виде на диске.",
        info_ig_encryption_key_desc: "Ключ Fernet для шифрования пароля Instagram на диске.",
        info_outreach_mode_desc: "Режим А: Безопасно. Копирует текст и открывает профиль, вы отправляете сами. Режим B: Автоматически отправляет сообщения из фона, есть риск блокировки.",
        info_max_outreach_desc: "Лимит исходящих сообщений в день для защиты от бана (Рекомендуется: 15-20).",
        info_tg_token_desc: "Токен бота Telegram для уведомления вас об ответах клиентов.",
        info_tg_chatid_desc: "Ваш Chat ID для получения уведомлений от бота.",
        info_smtp_host_desc: "Адрес почтового сервера для отправки email-уведомлений.",
        info_smtp_port_desc: "Порт SMTP-сервера (обычно 587 для TLS или 465 для SSL).",
        info_smtp_user_desc: "Почтовый ящик для авторизации на SMTP-сервере.",
        info_smtp_pass_desc: "Пароль от почты или пароль приложения для SMTP.",
        info_cfg_lang_desc: "Смена языка приложения.",
        info_cfg_theme_desc: "Смена цветовой темы оформления интерфейса."
      },
      de: {
        dashboard: "Dashboard",
        leads: "Leads",
        campaigns: "Kampagnen",
        history: "Verlauf",
        sessions: "Sitzungen",
        settings: "Einstellungen",
        dashboard_title: "Dashboard",
        dashboard_subtitle: "Starten Sie Branchen-Suchscans und verfolgen Sie allgemeine Statistiken.",
        db_card_new: "NEU ENTDECKT",
        db_card_researched: "AI-ANALYSE BEREIT",
        db_card_contacted: "KONTAKTIERT",
        db_card_replied: "ANTWORTEN ERHALTEN",
        db_search_sec_title: "Business Discovery Radar",
        db_search_sec_subtitle: "Scannen Sie automatisch neue Leads in bestimmten Standorten und Branchen.",
        lbl_sector: "Branche Stichwort",
        lbl_location: "Standort / Region",
        lbl_radius: "Radius (km)",
        lbl_provider: "Datenquelle",
        btn_start_discovery: "Scan starten 🚀",
        leads_title: "Leads-Manager",
        leads_subtitle: "Analysieren Sie gefundene Unternehmen, starten Sie AI-Recherchen und beginnen Sie Outreach.",
        btn_export_csv: "📥 Export",
        btn_clear_category: "Kategorie leeren 🗑️",
        btn_clear_all: "Alle leeren 🗑️",
        tbl_col_name: "Name des Unternehmens",
        tbl_col_sector: "Branche",
        tbl_col_addr: "Standort",
        tbl_col_web: "Webseite",
        tbl_col_status: "Status",
        settings_title: "Einstellungen",
        settings_subtitle: "Konfigurieren Sie API-Schlüssel, Automatisierungseinstellungen und Benachrichtigungen.",
        settings_sec_env: "Anwendungskonfiguration (.env)",
        settings_section_llm: "1. LLM / AI-Engine Einstellungen",
        settings_section_google: "2. Google & Suchdienste",
        settings_section_ig: "3. Instagram Automatisierung (Mod B)",
        settings_section_notif: "4. Benachrichtigungskanäle (SMTP / Telegram)",
        settings_section_ui: "5. UI-Einstellungen",
        btn_save_settings: "Einstellungen speichern",
        lbl_primary_llm: "Primärer LLM-Anbieter",
        lbl_fallback_llm: "Fallback-LLM-Anbieter",
        lbl_deepseek_key: "DeepSeek API-Schlüssel",
        lbl_openai_key: "OpenAI API-Schlüssel",
        lbl_anthropic_key: "Anthropic API-Schlüssel",
        lbl_openrouter_key: "OpenRouter API-Schlüssel",
        lbl_gemini_key: "Gemini API-Schlüssel",
        lbl_groq_key: "Groq API-Schlüssel",
        lbl_mistral_key: "Mistral API-Schlüssel",
        lbl_ollama_url: "Ollama Basis-URL (Lokal)",
        lbl_google_places_key: "Google Places API-Schlüssel",
        lbl_google_search_key: "Google Custom Search API-Schlüssel",
        lbl_google_search_cx: "Google Custom Search CX (Suchmaschinen-ID)",
        lbl_ig_username: "Instagram Benutzername",
        lbl_ig_password: "Instagram Passwort",
        lbl_ig_encryption_key: "Sitzungs-Verschlüsselungsschlüssel",
        lbl_outreach_mode: "Outreach-Modus",
        lbl_max_outreach: "Max. tägliches Outreach-Limit",
        lbl_tg_token: "Telegram Bot Token",
        lbl_tg_chatid: "Telegram Chat ID",
        lbl_smtp_host: "SMTP Host",
        lbl_smtp_port: "SMTP Port",
        lbl_smtp_user: "E-Mail Benutzername (Von)",
        lbl_smtp_pass: "E-Mail Passwort",
        lbl_cfg_lang: "Oberflächen-Sprache",
        lbl_cfg_theme: "Oberflächen-Design",
        lbl_cfg_show_console: "Entwicklerkonsole (CMD)",
        info_cfg_show_console_desc: "Schaltet die Sichtbarkeit des CMD-Terminalfensters im Hintergrund um. Lassen Sie es geöffnet, um Protokolle in Echtzeit zu sehen.",
        lbl_open_logs: "Protokolle",
        btn_open_logs: "Log-Ordner öffnen",
        opt_none: "Keine",
        opt_assisted: "Unterstützter Modus A (Zwischenablage & Browser - Sicher)",
        opt_full_auto: "Modus B (Vollautomatisierung - Riskant)",
        automation_risk_text: "⚠️ <b>WARNUNG:</b> Das Aktivieren der Vollautomatisierung verstößt gegen die Instagram-Nutzungsbedingungen. Verstehen Sie das Risiko einer Kontosperrung?",
        automation_confirm_label: "Ich verstehe die Risiken, Vollautomatisierung aktivieren.",
        info_primary_llm_desc: "Der primäre KI-Modellanbieter zum Entwerfen von Nachrichten und Analyseberichten.",
        info_fallback_llm_desc: "Der Backup-Anbieter, der automatisch aktiviert wird, wenn der primäre LLM ausfällt.",
        info_deepseek_key_desc: "Erforderlich, um intelligente Outreach-Entwürfe mit DeepSeek LLM-Modellen zu generieren.",
        info_openai_key_desc: "Erforderlicher API-Schlüssel für den Zugriff auf OpenAI GPT-4o Modelle.",
        info_anthropic_key_desc: "Erforderlicher API-Schlüssel für Anthropic Claude Modelle.",
        info_openrouter_key_desc: "Ermöglicht den Zugriff auf verschiedene Modelle über eine einzige API auf OpenRouter.",
        info_gemini_key_desc: "Erforderlicher API-Schlüssel für Google Gemini-Modelle.",
        info_groq_key_desc: "Erforderlicher API-Schlüssel für schnellen Zugriff auf Groq Llama 3 Modelle.",
        info_mistral_key_desc: "Erforderlicher API-Schlüssel für Mistral AI Modelle.",
        info_ollama_url_desc: "Adresse des lokalen Ollama-Dienstes auf Ihrem Rechner für die vollständige Offline-Nutzung.",
        info_google_places_key_desc: "Google Places API-Schlüssel erforderlich, um Kartenunternehmen mit mehr Details zu suchen.",
        info_google_search_key_desc: "Custom Search API-Schlüssel, um Webseiten oder Instagram-Profile auf Google zu finden.",
        info_google_search_cx_desc: "Ihre für Google Custom Search erstellte Suchmaschinen-ID (CX).",
        info_ig_username_desc: "Instagram-Benutzername, der von der Automatisierung verwendet wird, um DMs zu senden.",
        info_ig_password_desc: "Ihr Instagram-Passwort. Wird verschlüsselt auf der lokalen Festplatte gespeichert.",
        info_ig_encryption_key_desc: "Symmetrischer Fernet-Schlüssel zur Verschlüsselung des Instagram-Passworts auf der Festplatte.",
        info_outreach_mode_desc: "Modus A: Sicher. Kopiert Entwurf und öffnet Profil, Sie senden selbst. Modus B: Automatisiert. Sendet DM im Hintergrund, birgt das Risiko von Sperren.",
        info_max_outreach_desc: "Tägliches Limit für Instagram-DMs zur Vermeidung von Spam-Sperren (Empfohlen: 15-20).",
        info_tg_token_desc: "Telegram Bot Token, um Sie über Posteingangs-Antworten oder App-Logs zu benachrichtigen.",
        info_tg_chatid_desc: "Eindeutige Telegram User/Group ID, um Bot-Benachrichtigungen zu erhalten.",
        info_smtp_host_desc: "Mailserver-Adresse zum Senden von E-Mail-Benachrichtigungen.",
        info_smtp_port_desc: "SMTP-Server-Port (normalerweise 587 für TLS oder 465 für SSL).",
        info_smtp_user_desc: "E-Mail-Benutzername zur SMTP-Authentifizierung.",
        info_smtp_pass_desc: "E-Mail-Passwort oder App-Passwort zur SMTP-Authentifizierung.",
        info_cfg_lang_desc: "Ändern Sie die Sprache der Anwendung.",
        info_cfg_theme_desc: "Ändern Sie die Farben und das Design der Benutzeroberfläche."
      },
      hi: {
        dashboard: "डैशबोर्ड",
        leads: "लीड्स",
        campaigns: "अभियान",
        history: "इतिहास",
        sessions: "सत्र",
        settings: "सेटिंग्स",
        dashboard_title: "डैशबोर्ड",
        dashboard_subtitle: "व्यवसाय खोज स्कैन शुरू करें और समग्र सांख्यिकी को ट्रैक करें।",
        db_card_new: "नई खोज",
        db_card_researched: "AI विश्लेषण तैयार",
        db_card_contacted: "संपर्क किया गया",
        db_card_replied: "उत्तर प्राप्त हुए",
        db_search_sec_title: "व्यवसाय खोज राडार",
        db_search_sec_subtitle: "विशिष्ट स्थानों और क्षेत्रों में स्वचालित रूप से नई लीड स्कैन करें।",
        lbl_sector: "श्रेणी कीवर्ड",
        lbl_location: "स्थान / क्षेत्र",
        lbl_radius: "त्रिज्या (किमी)",
        lbl_provider: "डेटा स्रोत",
        btn_start_discovery: "स्कैन शुरू करें 🚀",
        leads_title: "लीड्स प्रबंधक",
        leads_subtitle: "खोजे गए व्यवसायों का विश्लेषण करें, AI अनुसंधान चलाएं, और आउटरीच शुरू करें।",
        btn_export_csv: "📥 निर्यात",
        btn_clear_category: "श्रेणी खाली करें 🗑️",
        btn_clear_all: "सभी साफ़ करें 🗑️",
        tbl_col_name: "व्यवसाय का नाम",
        tbl_col_sector: "क्षेत्र / श्रेणी",
        tbl_col_addr: "स्थान",
        tbl_col_web: "वेबसाइट",
        tbl_col_status: "स्थिति",
        settings_title: "सेटिंग्स",
        settings_subtitle: "API कुंजी, स्वचालन सेटिंग्स और सूचना चैनलों को कॉन्फ़िगर करें।",
        settings_sec_env: "एप्लिकेशन कॉन्फ़िगरेशन (.env)",
        settings_section_llm: "1. LLM / AI इंजन सेटिंग्स",
        settings_section_google: "2. Google और खोज सेवाएँ",
        settings_section_ig: "3. Instagram स्वचालन (मोड B)",
        settings_section_notif: "4. सूचना चैनल (SMTP / Telegram)",
        settings_section_ui: "5. UI सेटिंग्स",
        btn_save_settings: "सेटिंग्स सहेजें",
        lbl_primary_llm: "प्राथमिक LLM प्रदाता",
        lbl_fallback_llm: "फ़ॉलबैक LLM प्रदाता",
        lbl_deepseek_key: "DeepSeek API कुंजी",
        lbl_openai_key: "OpenAI API कुंजी",
        lbl_anthropic_key: "Anthropic API कुंजी",
        lbl_openrouter_key: "OpenRouter API कुंजी",
        lbl_gemini_key: "Gemini API कुंजी",
        lbl_groq_key: "Groq API कुंजी",
        lbl_mistral_key: "Mistral API कुंजी",
        lbl_ollama_url: "ओलामा बेस URL (स्थानीय)",
        lbl_google_places_key: "Google Places API कुंजी",
        lbl_google_search_key: "Google Custom Search API कुंजी",
        lbl_google_search_cx: "Google Custom Search CX ID",
        lbl_ig_username: "Instagram उपयोगकर्ता नाम",
        lbl_ig_password: "Instagram पासवर्ड",
        lbl_ig_encryption_key: "सत्र एन्क्रिप्शन कुंजी",
        lbl_outreach_mode: "आउटरीच मोड",
        lbl_max_outreach: "दैनिक अधिकतम संदेश सीमा",
        lbl_tg_token: "Telegram बॉट टोकन",
        lbl_tg_chatid: "Telegram चैट ID",
        lbl_smtp_host: "SMTP होस्ट",
        lbl_smtp_port: "SMTP पोर्ट",
        lbl_smtp_user: "ईमेल उपयोगकर्ता नाम (From)",
        lbl_smtp_pass: "ईमेल पासवर्ड",
        lbl_cfg_lang: "इंटरफ़ेस भाषा",
        lbl_cfg_theme: "इंटरफ़ेस थीम",
        lbl_cfg_show_console: "डेवलपर कंसोल (CMD)",
        info_cfg_show_console_desc: "बैकग्राउंड CMD टर्मिनल विंडो की दृश्यता को टॉगल करता है। रीयल-टाइम में लॉग देखने के लिए खुला रखें।",
        lbl_open_logs: "लॉग फ़ाइलें",
        btn_open_logs: "लॉग फ़ोल्डर खोलें",
        opt_none: "कोई नहीं",
        opt_assisted: "असिस्टेड मोड A (क्लिपबोर्ड और ब्राउज़र - सुरक्षित)",
        opt_full_auto: "मोड B (पूर्ण स्वचालन - जोखिम भरा)",
        automation_risk_text: "⚠️ <b>चेतावनी:</b> पूर्ण स्वचालन मोड सक्षम करना Instagram नियमों का उल्लंघन करता है। क्या आप खाता प्रतिबंध या निलंबन के जोखिम को समझते हैं?",
        automation_confirm_label: "मैं जोखिमों को समझता हूँ, पूर्ण स्वचालन सक्रिय करें।",
        info_primary_llm_desc: "संदेशों का मसौदा और रिपोर्ट तैयार करने के लिए उपयोग किया जाने वाला प्राथमिक AI प्रदाता।",
        info_fallback_llm_desc: "बैकअप प्रदाता जो प्राथमिक LLM के विफल होने पर स्वचालित रूप से सक्रिय हो जाएगा।",
        info_deepseek_key_desc: "DeepSeek मॉडल का उपयोग करके स्मार्ट आउटरीच ड्राफ्ट उत्पन्न करने के लिए आवश्यक।",
        info_openai_key_desc: "OpenAI GPT-4o मॉडल तक पहुँचने के लिए आवश्यक API कुंजी।",
        info_anthropic_key_desc: "Anthropic Claude मॉडल के लिए आवश्यक API कुंजी।",
        info_openrouter_key_desc: "OpenRouter पर एक ही API के माध्यम से विभिन्न मॉडलों तक पहुंच सक्षम करता है।",
        info_gemini_key_desc: "Google Gemini मॉडल के लिए आवश्यक API कुंजी।",
        info_groq_key_desc: "Groq Llama 3 मॉडल तक त्वरित पहुंच के लिए आवश्यक API कुंजी।",
        info_mistral_key_desc: "Mistral AI मॉडल के लिए आवश्यक API कुंजी।",
        info_ollama_url_desc: "पूर्ण ऑफ़लाइन चलने के लिए आपके मशीन पर चल रहे ओलामा सेवा का पता।",
        info_google_places_key_desc: "अधिक विवरण के साथ मानचित्र व्यवसायों को खोजने के लिए Google Places API कुंजी आवश्यक।",
        info_google_search_key_desc: "Google पर व्यावसायिक वेबसाइट या Instagram प्रोफाइल खोजने के लिए उपयोग की जाने वाली कस्टम खोज API कुंजी।",
        info_google_search_cx_desc: "Google Custom Search Engine के लिए बनाया गया आपका सर्च इंजन ID (CX)।",
        info_ig_username_desc: "Instagram उपयोगकर्ता नाम जिसका उपयोग स्वचालन द्वारा संदेश भेजने के लिए किया जाएगा।",
        info_ig_password_desc: "आपका Instagram पासवर्ड। स्थानीय डिस्क पर सुरक्षित रूप से एन्क्रिप्टेड संग्रहीत।",
        info_ig_encryption_key_desc: "डिस्क पर Instagram पासवर्ड एन्क्रिप्ट करने के लिए उपयोग की जाने वाली सममित कुंजी।",
        info_outreach_mode_desc: "मोड A: सुरक्षित। ड्राफ्ट कॉपी करता है और प्रोफ़ाइल खोलता है, आप स्वयं भेजते हैं। मोड B: स्वचालित। बैकग्राउंड में मैसेज भेजता है, ब्लॉक का खतरा है।",
        info_max_outreach_desc: "ब्लॉक से बचने के लिए आउटबाउंड संदेशों की दैनिक सीमा (अनुशंसित: 15-20)।",
        info_tg_token_desc: "नए संदेशों या त्रुटियों के बारे में सूचित करने के लिए Telegram बॉट टोकन।",
        info_tg_chatid_desc: "बॉट नोटिफिकेशन प्राप्त करने के लिए अद्वितीय Telegram चैट ID।",
        info_smtp_host_desc: "ईमेल सूचनाएं भेजने के लिए उपयोग किए जाने वाले मेल सर्वर का पता।",
        info_smtp_port_desc: "SMTP सर्वर पोर्ट (आमतौर पर TLS के लिए 587 या SSL के लिए 465)।",
        info_smtp_user_desc: "SMTP लॉगिन के लिए उपयोग किया जाने वाला ईमेल उपयोगकर्ता नाम।",
        info_smtp_pass_desc: "SMTP लॉगिन के लिए उपयोग किया जाने वाला ईमेल या ऐप पासवर्ड।",
        info_cfg_lang_desc: "एप्लिकेशन की भाषा बदलें।",
        info_cfg_theme_desc: "इंटरफ़ेस के रंग और थीम बदलें।"
      },
      fr: {
        dashboard: "Tableau",
        leads: "Prospects",
        campaigns: "Campagnes",
        history: "Historique",
        sessions: "Sessions",
        settings: "Paramètres",
        dashboard_title: "Tableau de bord",
        dashboard_subtitle: "Lancez des scans de recherche d'entreprises et suivez les statistiques globales.",
        db_card_new: "NOUVELLES DÉCOUVERTES",
        db_card_researched: "ANALYSE AI PRÊTE",
        db_card_contacted: "CONTACTÉS",
        db_card_replied: "RÉPONSES REÇUES",
        db_search_sec_title: "Radar de découverte d'entreprises",
        db_search_sec_subtitle: "Scannez automatiquement de nouveaux prospects dans des lieux et secteurs spécifiques.",
        lbl_sector: "Mot-clé du secteur",
        lbl_location: "Lieu / Région",
        lbl_radius: "Rayon (km)",
        lbl_provider: "Source de données",
        btn_start_discovery: "Lancer le scan 🚀",
        leads_title: "Gestion des prospects",
        leads_subtitle: "Analysez les entreprises trouvées, lancez des recherches IA et commencez l'outreach.",
        btn_export_csv: "📥 Exporter",
        btn_clear_category: "Vider la catégorie 🗑️",
        btn_clear_all: "Tout vider 🗑️",
        tbl_col_name: "Nom de l'entreprise",
        tbl_col_sector: "Secteur",
        tbl_col_addr: "Adresse",
        tbl_col_web: "Site Web",
        tbl_col_status: "Statut",
        settings_title: "Paramètres",
        settings_subtitle: "Configurez les clés API, les paramètres d'automatisation et les notifications.",
        settings_sec_env: "Configuration de l'application (.env)",
        settings_section_llm: "1. Paramètres du moteur IA / LLM",
        settings_section_google: "2. Google & Services de recherche",
        settings_section_ig: "3. Automatisation Instagram (Mode B)",
        settings_section_notif: "4. Notifications (SMTP / Telegram)",
        settings_section_ui: "5. Paramètres d'interface",
        btn_save_settings: "Enregistrer les paramètres",
        lbl_primary_llm: "Fournisseur LLM principal",
        lbl_fallback_llm: "Fournisseur LLM de secours",
        lbl_deepseek_key: "Clé API DeepSeek",
        lbl_openai_key: "Clé API OpenAI",
        lbl_anthropic_key: "Clé API Anthropic",
        lbl_openrouter_key: "Clé API OpenRouter",
        lbl_gemini_key: "Clé API Gemini",
        lbl_groq_key: "Clé API Groq",
        lbl_mistral_key: "Clé API Mistral",
        lbl_ollama_url: "URL de base Ollama (Local)",
        lbl_google_places_key: "Clé API Google Places",
        lbl_google_search_key: "Clé API Google Custom Search",
        lbl_google_search_cx: "ID du moteur Google (CX)",
        lbl_ig_username: "Nom d'utilisateur Instagram",
        lbl_ig_password: "Mot de passe Instagram",
        lbl_ig_encryption_key: "Clé de chiffrement de session",
        lbl_outreach_mode: "Mode de contact",
        lbl_max_outreach: "Limite de messages quotidienne",
        lbl_tg_token: "Token du bot Telegram",
        lbl_tg_chatid: "Chat ID Telegram",
        lbl_smtp_host: "Hôte SMTP",
        lbl_smtp_port: "Port SMTP",
        lbl_smtp_user: "Utilisateur Email (De)",
        lbl_smtp_pass: "Mot de passe Email",
        lbl_cfg_lang: "Langue de l'interface",
        lbl_cfg_theme: "Thème de l'interface",
        lbl_cfg_show_console: "Console développeur (CMD)",
        info_cfg_show_console_desc: "Active ou désactive l'affichage du terminal CMD en arrière-plan. Utile pour suivre les logs en temps réel.",
        lbl_open_logs: "Logs",
        btn_open_logs: "Ouvrir le dossier logs",
        opt_none: "Aucun",
        opt_assisted: "Mode assisté A (Presse-papiers & Navigateur - Sûr)",
        opt_full_auto: "Mode B (Automatisation complète - Risqué)",
        automation_risk_text: "⚠️ <b>ATTENTION:</b> L'automatisation complète enfreint les conditions d'Instagram. Comprenez-vous le risque de blocage de compte?",
        automation_confirm_label: "Je comprends les risques, activer le mode automatique.",
        info_primary_llm_desc: "Fournisseur principal d'IA pour générer les messages et analyses.",
        info_fallback_llm_desc: "Fournisseur de secours activé automatiquement si le principal échoue.",
        info_deepseek_key_desc: "Requis pour générer des messages intelligents via les modèles DeepSeek.",
        info_openai_key_desc: "Requis pour accéder aux modèles OpenAI GPT-4o.",
        info_anthropic_key_desc: "Requis pour accéder aux modèles Anthropic Claude.",
        info_openrouter_key_desc: "Permet l'accès à divers modèles via une seule API OpenRouter.",
        info_gemini_key_desc: "Requis pour accéder aux modèles Google Gemini.",
        info_groq_key_desc: "Requis pour un accès rapide aux modèles Groq Llama 3.",
        info_mistral_key_desc: "Requis pour accéder aux modèles Mistral AI.",
        info_ollama_url_desc: "Adresse locale de votre service Ollama pour travailler entièrement hors ligne.",
        info_google_places_key_desc: "Clé Google Places API requise pour enrichir les résultats de recherche de lieux.",
        info_google_search_key_desc: "Clé Custom Search API pour trouver des sites web ou profils Instagram sur Google.",
        info_google_search_cx_desc: "ID de votre moteur de recherche Custom Search (CX).",
        info_ig_username_desc: "Nom d'utilisateur utilisé par l'automatisation pour envoyer des messages.",
        info_ig_password_desc: "Votre mot de passe Instagram. Stocké chiffré sur votre disque local.",
        info_ig_encryption_key_desc: "Clé de chiffrement utilisée pour sécuriser le mot de passe Instagram.",
        info_outreach_mode_desc: "Mode A: Sûr. Copie le brouillon et ouvre le profil, vous envoyez. Mode B: Automatique. Envoie le message en arrière-plan, comporte des risques de blocage.",
        info_max_outreach_desc: "Limite quotidienne de messages pour éviter les blocages de spam (Conseillé: 15-20).",
        info_tg_token_desc: "Token du bot Telegram pour vous informer des réponses ou erreurs de l'application.",
        info_tg_chatid_desc: "ID unique de votre chat Telegram pour recevoir les notifications du bot.",
        info_smtp_host_desc: "Adresse du serveur de messagerie pour envoyer les alertes email.",
        info_smtp_port_desc: "Port du serveur SMTP (généralement 587 pour TLS ou 465 pour SSL).",
        info_smtp_user_desc: "Nom d'utilisateur email pour s'authentifier sur le SMTP.",
        info_smtp_pass_desc: "Mot de passe de messagerie ou mot de passe d'application pour le SMTP.",
        info_cfg_lang_desc: "Modifier la langue de l'application.",
        info_cfg_theme_desc: "Modifier le thème et les couleurs de l'interface."
      },
      es: {
        dashboard: "Tablero",
        leads: "Prospectos",
        campaigns: "Campañas",
        history: "Historial",
        sessions: "Sesiones",
        settings: "Ajustes",
        dashboard_title: "Tablero de control",
        dashboard_subtitle: "Inicie escaneos de descubrimiento de empresas y realice un seguimiento estadístico.",
        db_card_new: "NUEVOS DESCUBIERTOS",
        db_card_researched: "ANÁLISIS AI LISTO",
        db_card_contacted: "CONTACTADOS",
        db_card_replied: "RESPUESTAS RECIBIDAS",
        db_search_sec_title: "Radar de descubrimiento de negocios",
        db_search_sec_subtitle: "Escanee automáticamente nuevos prospectos en ubicaciones y sectores específicos.",
        lbl_sector: "Palabra clave del sector",
        lbl_location: "Ubicación / Región",
        lbl_radius: "Radio (km)",
        lbl_provider: "Fuente de datos",
        btn_start_discovery: "Iniciar escaneo 🚀",
        leads_title: "Gestor de prospectos",
        leads_subtitle: "Analice empresas encontradas, ejecute investigaciones IA e inicie el contacto.",
        btn_export_csv: "📥 Exportar",
        btn_clear_category: "Vaciar categoría 🗑️",
        btn_clear_all: "Vaciar todo 🗑️",
        tbl_col_name: "Nombre de la empresa",
        tbl_col_sector: "Sector",
        tbl_col_addr: "Ubicación",
        tbl_col_web: "Sitio web",
        tbl_col_status: "Estado",
        settings_title: "Configuración",
        settings_subtitle: "Configure claves API, automatización y canales de notificación.",
        settings_sec_env: "Configuración de la aplicación (.env)",
        settings_section_llm: "1. Ajustes del motor IA / LLM",
        settings_section_google: "2. Google y servicios de búsqueda",
        settings_section_ig: "3. Automatización de Instagram (Modo B)",
        settings_section_notif: "4. Canales de notificación (SMTP / Telegram)",
        settings_section_ui: "5. Ajustes de interfaz",
        btn_save_settings: "Guardar configuración",
        lbl_primary_llm: "Proveedor LLM principal",
        lbl_fallback_llm: "Proveedor LLM de respaldo",
        lbl_deepseek_key: "Clave API DeepSeek",
        lbl_openai_key: "Clave API OpenAI",
        lbl_anthropic_key: "Clave API Anthropic",
        lbl_openrouter_key: "Clave API OpenRouter",
        lbl_gemini_key: "Clave API Gemini",
        lbl_groq_key: "Clave API Groq",
        lbl_mistral_key: "Clave API Mistral",
        lbl_ollama_url: "URL de base de Ollama (Local)",
        lbl_google_places_key: "Clave API Google Places",
        lbl_google_search_key: "Clave API Google Custom Search",
        lbl_google_search_cx: "ID de motor de Google (CX)",
        lbl_ig_username: "Usuario de Instagram",
        lbl_ig_password: "Contraseña de Instagram",
        lbl_ig_encryption_key: "Clave de cifrado de sesión",
        lbl_outreach_mode: "Modo de contacto",
        lbl_max_outreach: "Límite de mensajes diario",
        lbl_tg_token: "Token de bot Telegram",
        lbl_tg_chatid: "Chat ID de Telegram",
        lbl_smtp_host: "Servidor SMTP",
        lbl_smtp_port: "Puerto SMTP",
        lbl_smtp_user: "Usuario de correo (De)",
        lbl_smtp_pass: "Contraseña de correo",
        lbl_cfg_lang: "Idioma de interfaz",
        lbl_cfg_theme: "Tema de interfaz",
        lbl_cfg_show_console: "Consola de desarrollador (CMD)",
        info_cfg_show_console_desc: "Activa o desactiva la visibilidad del terminal CMD en segundo plano. Útil para seguir los logs en tiempo real.",
        lbl_open_logs: "Registros",
        btn_open_logs: "Abrir carpeta logs",
        opt_none: "Ninguno",
        opt_assisted: "Modo asistido A (Portapapeles y navegador - Seguro)",
        opt_full_auto: "Modo B (Automatización completa - Riesgoso)",
        automation_risk_text: "⚠️ <b>ADVERTENCIA:</b> La automatización total infringe los términos de Instagram. ¿Comprende el riesgo de suspensión de cuenta?",
        automation_confirm_label: "Comprendo los riesgos, activar automatización total.",
        info_primary_llm_desc: "Proveedor de IA principal para redactar los borradores de mensajes y análisis.",
        info_fallback_llm_desc: "Proveedor de respaldo activado automáticamente si el principal falla.",
        info_deepseek_key_desc: "Requerido para generar mensajes inteligentes mediante los modelos DeepSeek.",
        info_openai_key_desc: "Requerido para acceder a los modelos OpenAI GPT-4o.",
        info_anthropic_key_desc: "Requerido para acceder a los modelos Anthropic Claude.",
        info_openrouter_key_desc: "Permite acceder a múltiples modelos mediante una sola API OpenRouter.",
        info_gemini_key_desc: "Requerido para acceder a los modelos Google Gemini.",
        info_groq_key_desc: "Requerido para acceso rápido a los modelos Groq Llama 3.",
        info_mistral_key_desc: "Requerido para acceder a los modelos Mistral AI.",
        info_ollama_url_desc: "Dirección local de su servicio Ollama para trabajar totalmente fuera de línea.",
        info_google_places_key_desc: "Clave API de Google Places requerida para enriquecer las búsquedas de mapas de negocios.",
        info_google_search_key_desc: "Clave API Custom Search para buscar sitios web o perfiles de Instagram en Google.",
        info_google_search_cx_desc: "ID de su motor de búsqueda Custom Search (CX).",
        info_ig_username_desc: "Nombre de usuario de Instagram para el envío automático de mensajes.",
        info_ig_password_desc: "Su contraseña de Instagram. Guardada de forma cifrada en el disco local.",
        info_ig_encryption_key_desc: "Clave Fernet usada para cifrar de forma segura la contraseña de Instagram.",
        info_outreach_mode_desc: "Modo A: Seguro. Copia el borrador y abre el perfil, usted lo envía. Modo B: Automático. Envía mensajes en segundo plano, conlleva riesgo de bloqueo.",
        info_max_outreach_desc: "Límite diario de DMs salientes para evitar bloqueos por spam (Recomendado: 15-20).",
        info_tg_token_desc: "Token de Telegram Bot para notificarle sobre respuestas o errores de la app.",
        info_tg_chatid_desc: "ID único de chat de Telegram para recibir notificaciones del bot.",
        info_smtp_host_desc: "Servidor de correo saliente para el envío de alertas de email.",
        info_smtp_port_desc: "Puerto de servidor SMTP (usualmente 587 para TLS o 465 para SSL).",
        info_smtp_user_desc: "Usuario de correo usado para autenticar en el SMTP.",
        info_smtp_pass_desc: "Contraseña de correo o contraseña específica de aplicación para el SMTP.",
        info_cfg_lang_desc: "Modificar el idioma de la aplicación.",
        info_cfg_theme_desc: "Modificar el tema de colores y moficar la interfaz visual."
      }
    };

    let currentLang = 'tr';

    function getTranslation(key) {
      const lang = TRANSLATIONS[currentLang] || TRANSLATIONS['tr'];
      return lang[key] || key;
    }

    function applyLanguage(langId) {
      currentLang = langId || 'tr';
      const lang = TRANSLATIONS[currentLang];
      if (!lang) return;

      document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (lang[key]) {
          if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            el.placeholder = lang[key];
          } else {
            el.innerHTML = lang[key];
          }
        }
      });

      // Update active language option select in UI
      const selectLang = document.getElementById('cfg-lang');
      if (selectLang) selectLang.value = currentLang;

      safeLocalStorage.setItem('aegis-lang', currentLang);
      saveUiStateDebounced();
    }

    function changeLang(langId) {
      applyLanguage(langId);
      let msg = "Language changed.";
      if (langId === 'tr') msg = "Dil Türkçe olarak değiştirildi.";
      else if (langId === 'en') msg = "Language set to English.";
      else if (langId === 'ar') msg = "تم تغيير اللغة إلى العربية.";
      else if (langId === 'zh') msg = "语言已更改为中文。";
      else if (langId === 'ru') msg = "Язык изменен на русский.";
      else if (langId === 'de') msg = "Sprache auf Deutsch geändert.";
      else if (langId === 'hi') msg = "भाषा बदलकर हिंदी कर दी गई है।";
      else if (langId === 'fr') msg = "Langue modifiée en français.";
      else if (langId === 'es') msg = "Idioma cambiado a español.";
      showToast(msg, 'info');
    }

    // 🎨 Theme Switcher Logic
    function changeTheme(themeId) {
      document.body.className = '';
      document.body.classList.add(themeId);
      
      const selectTheme = document.getElementById('cfg-theme');
      if (selectTheme) selectTheme.value = themeId;

      safeLocalStorage.setItem('aegis-theme', themeId);
      saveUiStateDebounced();
    }

    // Persist UI State
    let uiStateSaveTimeout = null;
    function saveUiStateDebounced() {
      if (uiStateSaveTimeout) clearTimeout(uiStateSaveTimeout);
      uiStateSaveTimeout = setTimeout(() => {
        if (!_isBridgeReady() || !window.pywebview.api.save_ui_state) return;
        
        const activeTabEl = document.querySelector('.nav-item.active');
        const activeTab = activeTabEl ? activeTabEl.getAttribute('data-tab') : 'dashboard';
        
        const state = {
          theme: document.body.className.split(' ').find(c => c.startsWith('theme-')) || 'theme-neon',
          language: currentLang || 'tr',
          sidebar: activeTab,
          last_view: '',
          active_tab: activeTab,
          search_sector: document.getElementById('search-sector') ? document.getElementById('search-sector').value : '',
          search_location: document.getElementById('search-location') ? document.getElementById('search-location').value : '',
          search_radius: document.getElementById('search-radius') ? document.getElementById('search-radius').value : '',
          search_provider: document.getElementById('search-provider') ? document.getElementById('search-provider').value : '',
          leads_filter_status: document.getElementById('filter-status') ? document.getElementById('filter-status').value : '',
          leads_filter_has_website: '',
          leads_filter_has_instagram: ''
        };
        
        window.pywebview.api.save_ui_state(JSON.stringify(state));
      }, 1500);
    }

    // Load and Apply UI State
    function loadAndApplyUiState() {
      if (!_isBridgeReady() || !window.pywebview.api.load_ui_state) return;
      window.pywebview.api.load_ui_state().then(stateStr => {
        try {
          const state = JSON.parse(stateStr || '{}');
          
          if (state.theme) {
            changeTheme(state.theme);
          }
          if (state.language) {
            applyLanguage(state.language);
          }
          const activeTab = state.active_tab || state.sidebar;
          if (activeTab) {
            const tabEl = Array.from(document.querySelectorAll('.nav-links li')).find(li => {
              return li.getAttribute('onclick') && li.getAttribute('onclick').includes(`switchTab('${activeTab}'`);
            }) || Array.from(document.querySelectorAll('.nav-item')).find(el => el.getAttribute('data-tab') === activeTab);
            if (tabEl) {
              switchTab(activeTab, tabEl);
            } else {
              switchTab(activeTab);
            }
          }
          if (state.search_sector) {
            const el = document.getElementById('search-sector');
            if (el) el.value = state.search_sector;
          }
          if (state.search_location) {
            const el = document.getElementById('search-location');
            if (el) el.value = state.search_location;
          }
          if (state.search_radius) {
            const el = document.getElementById('search-radius');
            if (el) el.value = state.search_radius;
          }
          if (state.search_provider) {
            const el = document.getElementById('search-provider');
            if (el) el.value = state.search_provider;
          }
          if (state.leads_filter_status) {
            const el = document.getElementById('filter-status');
            if (el) {
              el.value = state.leads_filter_status;
              loadLeads();
            }
          }
        } catch (e) {
          console.error('[aegisScout] loadAndApplyUiState failed to parse', e);
        }
      });
    }

    // Robust bridge initialization - handles both early and late pywebviewready
    function _initApp() {
      // Apply saved language and theme on startup
      const savedLang = safeLocalStorage.getItem('aegis-lang') || 'tr';
      applyLanguage(savedLang);
      const savedTheme = safeLocalStorage.getItem('aegis-theme') || 'theme-neon';
      changeTheme(savedTheme);

      // 🛡️ Modal safety: clear any stuck .show classes that may have
      // been left over from a previous page load (e.g., after a JS crash).
      try { _forceCloseAllModals(); } catch (_) {}

      // Check if pywebview API is available before calling it
      window.pywebviewReady = _isBridgeReady();
      if (window.pywebviewReady) {
        loadStats();
        loadSessions();
        loadHistory();
        loadCampaigns();
        loadAndApplyUiState();
      } else {
        // Bridge not ready yet — will retry once pywebviewready fires.
        // Show a non-blocking warning toast so user knows UI is in read-only mode.
        setTimeout(() => {
          if (!window.pywebviewReady) {
            try {
              showToast(
                'Python köprüsü henüz hazır değil. Sayfayı yenilemeyi veya uygulamayı yeniden başlatmayı deneyin.',
                'warning',
                'Köprü Bekleniyor',
                5000
              );
            } catch (_) {}
          }
        }, 3000);
      }

      // Add listeners to search inputs and filter select inputs to auto-save UI state
      const idsToListen = [
        'search-sector',
        'search-location',
        'search-radius',
        'search-provider',
        'filter-status'
      ];
      idsToListen.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          el.addEventListener('input', saveUiStateDebounced);
          el.addEventListener('change', saveUiStateDebounced);
        }
      });

      // Scroll event on leads-table-container to load more
      if (!_scrollListenerAdded) {
        const container = document.getElementById('leads-table-container');
        if (container) {
          container.addEventListener('scroll', () => {
            if (container.scrollHeight - container.scrollTop - container.clientHeight < 40) {
              renderMoreLeads();
            }
          });
          _scrollListenerAdded = true;
        }
      }
    }

    // Listen for pywebview bridge ready
    window.addEventListener('pywebviewready', () => {
      window.pywebviewReady = _isBridgeReady();
      // If the initial init already ran but the bridge wasn't ready, run a
      // limited re-init so data loads once the bridge finally appears.
      if (window.pywebviewReady && typeof _initApp === 'function') {
        // Mark as ready and trigger the data loaders that are idempotent.
        try { loadStats(); } catch (_) {}
        try { loadSessions(); } catch (_) {}
        try { loadHistory(); } catch (_) {}
        try { loadCampaigns(); } catch (_) {}
        try { loadAndApplyUiState(); } catch (_) {}
        try {
          _apiCall(() => window.pywebview.api.get_sessions(), { action: 'Oturumları yükle' })
            .then(sessions => {
              if (sessions && !sessions.error) {
                const active = (Array.isArray(sessions) ? sessions : []).find(s => s && s.is_active);
                if (active) _updateSidebarSessionName(active.name);
              }
            })
            .catch(() => {});
        } catch (_) {}
      }
    });
    // Also listen for DOMContentLoaded as fallback
    document.addEventListener('DOMContentLoaded', _initApp);
    // If DOM is already loaded, init immediately
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      // Short delay to ensure pywebview bridge is ready
      setTimeout(_initApp, 500);
    }

    /* ══════════════════════════════════════════════
       ⌨️ Global Keyboard Shortcuts (Escape / Enter)
       ══════════════════════════════════════════════ */
    function _activeModal() {
      // Returns the topmost currently-visible modal element, or null.
      const ids = ['modal-overlay', 'export-modal', 'advanced-delete-modal'];
      for (let i = ids.length - 1; i >= 0; i--) {
        const el = document.getElementById(ids[i]);
        if (el && el.classList.contains('show')) return el;
      }
      return null;
    }

    document.addEventListener('keydown', e => {
      // Escape: close the topmost open modal regardless of which one it is
      if (e.key === 'Escape') {
        const active = _activeModal();
        if (!active) return;
        e.preventDefault();
        if (active.id === 'modal-overlay') {
          _cancelModal();
        } else if (active.id === 'export-modal') {
          closeExportModal();
        } else if (active.id === 'advanced-delete-modal') {
          closeAdvancedDeleteModal();
        } else {
          active.classList.remove('show');
        }
        return;
      }

      // Enter: confirm main modal when no button is focused
      // Enter: confirm main modal when no button is focused
      if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey) {
        const active = _activeModal();
        if (!active) return;
        if (active.id !== 'modal-overlay') return; // only main modal auto-confirms on Enter
        const tag = (e.target && e.target.tagName) || '';
        // Don't auto-confirm when user is typing in a textarea
        if (tag === 'TEXTAREA') return;
        // Don't auto-confirm when the focused element is itself a button
        if (tag === 'BUTTON') return;
        // Only auto-confirm if the modal has the input visible
        const inputEl = document.getElementById('modal-input');
        if (inputEl && inputEl.style.display !== 'none') return;
        e.preventDefault();
        _confirmModal();
      }
    });

    /* ══════════════════════════════════════════════
       🚀 aegisScout B2B Growth Platform V2 - JS LOGIC
       ══════════════════════════════════════════════ */
    let uniboxSelectedLeadId = null;
    let currentWaterfallConfig = [];

    // --- 🛡️ Local Email Verifier Trigger ---
    function triggerEmailVerify(email, leadId) {
      if (!email || email === 'Bulunamadı' || email.trim() === '') {
        showToast("Doğrulanacak geçerli bir e-posta adresi bulunamadı.", "error");
        return;
      }
      showToast("E-posta doğrulama işlemi başlatıldı...", "info");
      const btn = document.getElementById('btn-verify-email-' + leadId);
      _withButtonBusy(btn, _apiCall(() => window.pywebview.api.verify_email_address(email), { action: 'E-postayı doğrula' })).then(res => {
        if (res && res.status) {
          if (res.success) {
            showToast(`E-posta geçerli: ${res.status.toUpperCase()}`, "success");
          } else {
            showToast(`E-posta geçersiz: ${res.status.toUpperCase()}`, "error");
          }
          selectLead(leadId);
        } else {
          showToast("E-posta doğrulama başarısız.", "error");
        }
      });
    }

    // --- 🚀 Website Screen-Audit Trigger ---
    function triggerScreenAudit(leadId) {
      showToast("Web sitesi ekran görüntüsü ve AI analizi başlatıldı. Bu işlem 10-15 saniye sürebilir...", "info");
      const btn = document.getElementById('btn-screen-audit-' + leadId);
      _withButtonBusy(btn, _apiCall(() => window.pywebview.api.run_screen_audit(leadId), { action: 'Screen-Audit çalıştır' })).then(res => {
        if (res && res.success) {
          showToast("Web sitesi görsel analizi başarıyla tamamlandı!", "success");
          selectLead(leadId);
        } else {
          showToast("Analiz hatası: " + (res ? res.error : "Bilinmeyen hata"), "error");
        }
      });
    }

    // --- ⚡ Waterfall Enrichment Trigger ---
    function triggerWaterfall(leadId) {
      showToast("Dinamik şelale zenginleştirme akışı başlatıldı...", "info");
      const btn = document.getElementById('btn-waterfall-' + leadId);
      _withButtonBusy(btn, _apiCall(() => window.pywebview.api.run_waterfall_lead(leadId), { action: 'Şelale akışını çalıştır' })).then(res => {
        if (res && res.success) {
          showToast("Şelale akışı başarıyla tamamlandı!", "success");
          selectLead(leadId);
        } else {
          showToast("Şelale hatası: " + (res ? res.error : "Bilinmeyen hata"), "error");
        }
      });
    }

    // --- 💬 Playwright WhatsApp/LinkedIn Outreach ---
    function launchWhatsAppAuto(leadId) {
      const draftBox = document.getElementById('edit-draft-box');
      const text = draftBox ? draftBox.value : '';
      if (!text) {
        showToast("Gönderilecek taslak mesaj bulunamadı.", "error");
        return;
      }
      showToast("Otomatik WhatsApp mesajı gönderiliyor...", "info");
      _apiCall(() => window.pywebview.api.launch_whatsapp_auto(leadId, text), { action: 'Otomatik WhatsApp mesajı gönder' }).then(res => {
        if (res && res.success) {
          showToast("WhatsApp mesajı otomatik gönderildi.", "success");
          selectLead(leadId);
        } else {
          showToast("Gönderim hatası: " + (res ? res.error : "Bilinmeyen hata"), "error");
        }
      });
    }

    function launchLinkedInAuto(leadId) {
      const draftBox = document.getElementById('edit-draft-box');
      const text = draftBox ? draftBox.value : '';
      if (!text) {
        showToast("Gönderilecek taslak mesaj bulunamadı.", "error");
        return;
      }
      showToast("Otomatik LinkedIn bağlantı isteği/mesajı gönderiliyor...", "info");
      _apiCall(() => window.pywebview.api.launch_linkedin_auto(leadId, text), { action: 'Otomatik LinkedIn işlemi' }).then(res => {
        if (res && res.success) {
          showToast("LinkedIn işlemi otomatik tamamlandı.", "success");
          selectLead(leadId);
        } else {
          showToast("LinkedIn hatası: " + (res ? res.error : "Bilinmeyen hata"), "error");
        }
      });
    }

    function loginWhatsApp() {
      showToast("WhatsApp Web giriş tarayıcısı açılıyor...", "info");
      window.pywebview.api.launch_whatsapp_login().then(res => {
        if (res && res.error) showToast("Hata: " + res.error, "error");
      });
    }

    function loginLinkedIn() {
      showToast("LinkedIn giriş tarayıcısı açılıyor...", "info");
      window.pywebview.api.launch_linkedin_login().then(res => {
        if (res && res.error) showToast("Hata: " + res.error, "error");
      });
    }

    // --- 📥 Unified Inbox Logic ---
    function loadUnibox() {
      if (!_isBridgeReady()) return;
      _apiCall(() => window.pywebview.api.get_unibox_messages(), { action: 'Gelen kutusu mesajlarını yükle' }).then(data => {
        if (!data || data.error) return;
        
        const listDiv = document.getElementById('unibox-leads-list');
        listDiv.innerHTML = '';
        
        if (data.length === 0) {
          listDiv.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center; margin-top: 20px;">Henüz sohbet geçmişi bulunmuyor.</p>';
          document.getElementById('unibox-thread-view').innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 100px;">Mesaj geçmişi yok.</div>';
          document.getElementById('unibox-reply-container').style.display = 'none';
          return;
        }

        data.forEach(item => {
          const itemDiv = document.createElement('div');
          itemDiv.className = 'unibox-lead-item' + (uniboxSelectedLeadId === item.lead_id ? ' active' : '');
          itemDiv.innerHTML = `
            <div style="font-weight:600; font-size:0.85rem; color:var(--text-main);">${escapeHtml(item.lead_name)}</div>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">${escapeHtml(item.lead_email || item.lead_phone || 'İletişim bilgisi yok')}</div>
          `;
          itemDiv.onclick = () => {
            uniboxSelectedLeadId = item.lead_id;
            document.querySelectorAll('.unibox-lead-item').forEach(el => el.classList.remove('active'));
            itemDiv.classList.add('active');
            renderUniboxThread(item);
          };
          listDiv.appendChild(itemDiv);
          
          if (uniboxSelectedLeadId === item.lead_id) {
            renderUniboxThread(item);
          }
        });
      });
    }

    function renderUniboxThread(leadData) {
      const threadDiv = document.getElementById('unibox-thread-view');
      threadDiv.innerHTML = '';
      
      leadData.messages.forEach(m => {
        const bubble = document.createElement('div');
        bubble.className = 'unibox-msg-bubble ' + m.direction;
        bubble.innerHTML = `
          <div style="font-size:0.7rem; opacity:0.8; margin-bottom:4px; font-weight:600;">
            ${escapeHtml(m.channel.toUpperCase())} - ${escapeHtml(m.created_at)}
          </div>
          <div>${escapeHtml(m.content)}</div>
        `;
        threadDiv.appendChild(bubble);
      });
      
      // Auto-scroll to bottom of thread
      threadDiv.scrollTop = threadDiv.scrollHeight;
      
      // Show reply controls
      document.getElementById('unibox-reply-container').style.display = 'flex';
      
      // Auto-select channel based on lead availability
      const selectChannel = document.getElementById('unibox-reply-channel');
      if (selectChannel) {
        if (leadData.lead_email) selectChannel.value = 'email';
        else if (leadData.lead_phone) selectChannel.value = 'whatsapp';
      }
    }

    function sendUniboxReplyMessage() {
      if (!uniboxSelectedLeadId) return;
      const textEl = document.getElementById('unibox-reply-text');
      const text = textEl ? textEl.value.trim() : '';
      const channel = document.getElementById('unibox-reply-channel').value;
      
      if (!text) {
        showToast("Lütfen bir yanıt yazın.", "warning");
        return;
      }

      showToast("Yanıt gönderiliyor...", "info");
      _apiCall(() => window.pywebview.api.send_unibox_reply(uniboxSelectedLeadId, channel, text), { action: 'Yanıt gönder' }).then(res => {
        if (res && (res.success || !res.error)) {
          showToast("Yanıtınız başarıyla gönderildi.", "success");
          textEl.value = '';
          loadUnibox();
        } else {
          showToast("Gönderim hatası: " + (res ? res.error : "Bilinmeyen hata"), "error");
        }
      });
    }

    // --- ⚡ Waterfall enrichment Config Logic ---
    function loadWaterfallConfig() {
      if (!_isBridgeReady()) return;
      _apiCall(() => window.pywebview.api.get_waterfall_config(), { action: 'Şelale ayarlarını yükle' }).then(config => {
        if (!config || config.error) return;
        currentWaterfallConfig = config;
        renderWaterfallConfigUi();
      });
    }

    function renderWaterfallConfigUi() {
      const listDiv = document.getElementById('waterfall-steps-list');
      listDiv.innerHTML = '';
      
      const visualDiv = document.getElementById('waterfall-flow-visual');
      visualDiv.innerHTML = '';

      currentWaterfallConfig.forEach((step, idx) => {
        // Render step config box
        const stepBox = document.createElement('div');
        stepBox.style = "background: var(--bg-base); padding: 12px; border-radius: 8px; border: 1px solid var(--border-subtle); display:flex; flex-direction:column; gap:6px;";
        
        let templateInput = '';
        if (step.step_id === 'search_query') {
          templateInput = `
            <div style="margin-top:6px;">
              <label style="font-size:0.75rem; color:var(--text-muted);">Arama Sorgusu Şablonu:</label>
              <input type="text" id="waterfall-query-template" value="${escapeHtml(step.query_template || '')}" style="width:100%; height:28px; padding:0 8px; border-radius:6px; background:var(--bg-card); border:1px solid var(--border-accent); color:var(--text-main); font-size:0.8rem; margin-top:4px;">
            </div>
          `;
        }

        stepBox.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-weight:600; font-size:0.85rem; color:var(--text-main);">${escapeHtml(step.name)}</div>
            <label class="switch" style="position: relative; display: inline-block; width: 40px; height: 20px;">
              <input type="checkbox" class="waterfall-step-toggle" data-step-id="${step.step_id}" ${step.enabled ? 'checked' : ''} onchange="updateWaterfallVisualFromUi()" style="opacity: 0; width: 0; height: 0;">
              <span class="slider" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--border-accent); transition: .3s; border-radius: 20px;"></span>
            </label>
          </div>
          <div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(step.description)}</div>
          ${templateInput}
        `;
        listDiv.appendChild(stepBox);

        // Render step visual block if enabled
        if (step.enabled) {
          const stepEl = document.createElement('div');
          stepEl.className = 'waterfall-flow-step';
          stepEl.innerText = step.name;
          visualDiv.appendChild(stepEl);
        }
      });
      
      // Ensure the visual flow steps don't have dangling arrows
      updateWaterfallVisualFromUi();
    }

    function updateWaterfallVisualFromUi() {
      const visualDiv = document.getElementById('waterfall-flow-visual');
      visualDiv.innerHTML = '';
      
      const toggles = document.querySelectorAll('.waterfall-step-toggle');
      toggles.forEach(toggle => {
        const stepId = toggle.getAttribute('data-step-id');
        const enabled = toggle.checked;
        const stepObj = currentWaterfallConfig.find(s => s.step_id === stepId);
        
        if (enabled && stepObj) {
          const stepEl = document.createElement('div');
          stepEl.className = 'waterfall-flow-step';
          stepEl.innerText = stepObj.name;
          visualDiv.appendChild(stepEl);
        }
      });
      
      if (visualDiv.children.length === 0) {
        visualDiv.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem;">Aktif adım yok. Lütfen en az bir adım etkinleştirin.</div>';
      }
    }

    function saveWaterfallConfigUi() {
      const configToSave = [];
      const toggles = document.querySelectorAll('.waterfall-step-toggle');
      
      toggles.forEach(toggle => {
        const stepId = toggle.getAttribute('data-step-id');
        const enabled = toggle.checked;
        const stepObj = currentWaterfallConfig.find(s => s.step_id === stepId);
        
        if (stepObj) {
          const copy = {...stepObj, enabled: enabled};
          if (stepId === 'search_query') {
            const tmpl = document.getElementById('waterfall-query-template');
            if (tmpl) copy.query_template = tmpl.value.trim();
          }
          configToSave.push(copy);
        }
      });

      _apiCall(() => window.pywebview.api.save_waterfall_config(configToSave), { action: 'Şelale akışı ayarlarını kaydet' }).then(res => {
        if (res && res.success) {
          showToast("Şelale akış konfigürasyonu kaydedildi.", "success");
          loadWaterfallConfig();
        } else {
          showToast("Hata: " + (res ? res.error : "Bilinmeyen hata"), "error");
        }
      });
    }

    // --- 📈 Email Warmup Control ---
    function loadWarmupStatus() {
      if (!_isBridgeReady()) return;
      _apiCall(() => window.pywebview.api.get_warmup_status(), { action: 'E-posta ısıtma durumunu yükle' }).then(res => {
        if (!res || res.error) return;
        
        const checkbox = document.getElementById('warmup-toggle-checkbox');
        if (checkbox) checkbox.checked = !!res.active;
        
        const stats = res.stats || {};
        document.getElementById('warmup-stat-sent').innerText = stats.sent || 0;
        document.getElementById('warmup-stat-replied').innerText = stats.replied || 0;
        document.getElementById('warmup-stat-spam_rescued').innerText = stats.spam_rescued || 0;
        document.getElementById('warmup-stat-starred').innerText = stats.starred || 0;
        
        // Load active accounts
        window.pywebview.api.get_smtp_accounts().then(accs => {
          const accList = document.getElementById('warmup-accounts-list');
          accList.innerHTML = '';
          if (!accs || accs.length === 0) {
            accList.innerHTML = '<p style="color:var(--text-muted); font-size:0.8rem; text-align:center; padding-top:20px;">Tanımlı e-posta hesabı bulunamadı. Ayarlar panelinden hesap ekleyin.</p>';
            return;
          }
          
          accs.forEach(acc => {
            const accBox = document.createElement('div');
            accBox.style = "background:var(--bg-base); border:1px solid var(--border-subtle); padding:10px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;";
            accBox.innerHTML = `
              <div>
                <div style="font-weight:600; font-size:0.85rem;">${escapeHtml(acc.name)}</div>
                <div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(acc.smtp_user)}</div>
              </div>
              <div style="font-size:0.75rem; font-weight:bold; color:${acc.is_active ? 'var(--color-success)' : 'var(--color-danger)'}">
                ${acc.is_active ? 'Aktif (Isıtılıyor)' : 'Pasif'}
              </div>
            `;
            accList.appendChild(accBox);
          });
        });
      });
    }

    function toggleWarmupState(checked) {
      _apiCall(() => window.pywebview.api.toggle_warmup(checked), { action: 'E-posta ısıtma durumunu güncelle' }).then(res => {
        if (res && res.success) {
          showToast("Isıtma durumu güncellendi: " + (res.active ? "AKTİF" : "PASİF"), "success");
          loadWarmupStatus();
        }
      });
    }

    function runWarmupManual() {
      showToast("Manuel P2P ısıtma döngüsü başlatıldı. SMTP ve IMAP işlemleri gerçekleştiriliyor...", "info");
      const btn = document.getElementById('btn-run-warmup-manual');
      _withButtonBusy(btn, _apiCall(() => window.pywebview.api.run_warmup_cycle_manual(), { action: 'Manuel ısıtma döngüsü çalıştır' })).then(res => {
        if (res && res.success) {
          showToast("Warmup döngüsü başarıyla tamamlandı: " + res.details, "success");
          loadWarmupStatus();
        } else {
          showToast("Isıtma başarısız: " + (res ? res.error : "Bilinmeyen hata"), "error");
        }
      });
    }

    // Clipboard copy helper fallback
    function copyToClipboard(text) {
      try {
        const temp = document.createElement('textarea');
        temp.value = text;
        document.body.appendChild(temp);
        temp.select();
        document.execCommand('copy');
        document.body.removeChild(temp);
        showToast("Metin panoya kopyalandı!", "success");
      } catch (err) {
        showToast("Kopyalama başarısız.", "error");
      }
    }

    function viewFullImage(url) {
      window.open(url, '_blank');
    }

  </script>
</body>
</html>
"""
