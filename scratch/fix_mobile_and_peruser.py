"""Fix mobile layout and per-user chat isolation in web/index.html"""
import re

with open("web/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# =============================================================================
# 1. MOBILE: Replace the minimal @media block with comprehensive mobile styles
# =============================================================================
old_mobile = """@media(max-width: 860px) {
      .app-shell {
        grid-template-columns: 1fr;
      }

      aside {
        display: none;
      }

      .input-floating-bar {
        left: 50%;
        width: calc(100vw - 32px);
      }

      .quick-cards {
        grid-template-columns: 1fr;
      }

      .train-grid {
        grid-template-columns: 1fr;
      }

      .hw-cards {
        grid-template-columns: 1fr;
      }
    }"""

new_mobile = """/* ── Mobile hamburger button (hidden on desktop) ── */
    .mobile-menu-btn {
      display: none;
      position: fixed;
      top: 12px;
      left: 12px;
      z-index: 1100;
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: rgba(17, 19, 24, 0.92);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255,255,255,0.12);
      color: #ededed;
      cursor: pointer;
      align-items: center;
      justify-content: center;
    }

    .mobile-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.6);
      backdrop-filter: blur(4px);
      z-index: 999;
    }
    .mobile-overlay.open { display: block; }

    @media(max-width: 860px) {
      .mobile-menu-btn { display: flex; }

      .app-shell {
        grid-template-columns: 1fr;
        gap: 0;
      }

      aside {
        position: fixed;
        top: 0; left: -280px;
        width: 270px;
        height: 100dvh;
        z-index: 1000;
        transition: left 0.28s cubic-bezier(.4, 0, .2, 1);
        box-shadow: 8px 0 32px rgba(0,0,0,0.6);
      }
      aside.open { left: 0; }

      .aside-right {
        display: none !important;
      }

      .main-content {
        padding-top: 56px;
      }

      .input-floating-bar {
        left: 50%;
        width: calc(100vw - 20px);
        bottom: 10px;
        border-radius: 14px;
      }

      .chat-input-wrap textarea {
        font-size: 16px; /* prevents iOS zoom */
      }

      .quick-cards {
        grid-template-columns: 1fr;
        gap: 8px;
        padding: 0 8px;
      }

      .train-grid {
        grid-template-columns: 1fr;
      }

      .hw-cards {
        grid-template-columns: 1fr 1fr;
      }

      .hero-title {
        font-size: 28px !important;
      }

      .hero-sub {
        font-size: 13px !important;
      }

      .code-block-wrapper pre {
        font-size: 12px;
        overflow-x: auto;
      }

      .msg-item {
        padding: 10px 8px;
      }

      .tab-panel {
        padding: 12px 8px;
      }

      .bench-grid {
        grid-template-columns: 1fr 1fr !important;
      }

      #authModal > div {
        width: 92vw !important;
        padding: 20px !important;
      }

      .top-bar {
        padding-left: 52px;
      }
    }

    @media(max-width: 480px) {
      .hw-cards {
        grid-template-columns: 1fr;
      }
      .bench-grid {
        grid-template-columns: 1fr !important;
      }
      .quick-cards {
        grid-template-columns: 1fr;
      }
    }"""

html = html.replace(old_mobile, new_mobile)

# =============================================================================
# 2. Add mobile hamburger button + overlay right after <body>
# =============================================================================
old_body_start = """<body>

  <div class="app-shell">"""

new_body_start = """<body>

  <!-- Mobile hamburger button -->
  <button class="mobile-menu-btn" id="mobileMenuBtn" onclick="toggleMobileSidebar()">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
      <line x1="3" y1="6" x2="21" y2="6"/>
      <line x1="3" y1="12" x2="21" y2="12"/>
      <line x1="3" y1="18" x2="21" y2="18"/>
    </svg>
  </button>
  <div class="mobile-overlay" id="mobileOverlay" onclick="closeMobileSidebar()"></div>

  <div class="app-shell">"""

html = html.replace(old_body_start, new_body_start)

# =============================================================================
# 3. Add mobile sidebar toggle JS before init
# =============================================================================
old_init = """    /* ── Инициализация ── */
    (async function init() {"""

new_init = """    /* ── Мобильный сайдбар ── */
    function toggleMobileSidebar() {
      const aside = document.querySelector('aside');
      const overlay = $('mobileOverlay');
      if (aside) aside.classList.toggle('open');
      if (overlay) overlay.classList.toggle('open');
    }
    function closeMobileSidebar() {
      const aside = document.querySelector('aside');
      const overlay = $('mobileOverlay');
      if (aside) aside.classList.remove('open');
      if (overlay) overlay.classList.remove('open');
    }
    // Close sidebar when tab is selected on mobile
    const origSwitchTab = typeof switchTab === 'function' ? switchTab : null;

    /* ── Инициализация ── */
    (async function init() {"""

html = html.replace(old_init, new_init)

# =============================================================================
# 4. Patch switchTab to close mobile sidebar
# =============================================================================
# Find the switchTab function and add closeMobileSidebar call
old_switch = "function switchTab(name) {"
# We need to find the actual function body
idx = html.find(old_switch)
if idx >= 0:
    # Insert closeMobileSidebar() call right after the opening brace
    insert_at = html.find("{", idx) + 1
    html = html[:insert_at] + "\n      closeMobileSidebar();" + html[insert_at:]
    print("Patched switchTab with closeMobileSidebar()")
else:
    print("WARNING: switchTab not found")

# =============================================================================
# 5. Per-user chat key in localStorage
# =============================================================================
# The conversationHistory and thread loading should use username-scoped keys
# We'll add a function to get per-user storage key

old_conversation_history = "let conversationHistory = [];"
new_conversation_history = """let conversationHistory = [];

    function getUserStorageKey(key) {
      const u = currentUser ? currentUser.username : '__anon__';
      return 'giga_' + u + '_' + key;
    }"""

html = html.replace(old_conversation_history, new_conversation_history)

# =============================================================================
# 6. Make loadThread close mobile sidebar
# =============================================================================
old_load_thread = "async function loadThread(id) {"
new_load_thread = "async function loadThread(id) {\n      closeMobileSidebar();"
html = html.replace(old_load_thread, new_load_thread)

# =============================================================================
# 7. Use per-user key for Web Studio preview storage
# =============================================================================
old_preview_save = "localStorage.setItem('giga_latest_preview_html', res.html_preview);"
new_preview_save = "localStorage.setItem(getUserStorageKey('latest_preview_html'), res.html_preview);"
html = html.replace(old_preview_save, new_preview_save)

old_preview_load = "const savedHtml = localStorage.getItem('giga_latest_preview_html');"
new_preview_load = "const savedHtml = localStorage.getItem(getUserStorageKey('latest_preview_html'));"
html = html.replace(old_preview_load, new_preview_load)

# =============================================================================
# 8. Reset conversationHistory on new chat and auth changes
# =============================================================================
old_logout = """    async function logoutUser() {
      await api('/api/auth/logout', {});
      localStorage.removeItem('giga_session_token');
      currentUser = null;
      applyRolePermissions(null);
      updateUserProfileUI();
      playCyberSound('blip');
    }"""

new_logout = """    async function logoutUser() {
      await api('/api/auth/logout', {});
      localStorage.removeItem('giga_session_token');
      currentUser = null;
      conversationHistory = [];
      activeThreadId = null;
      messagesList.innerHTML = '';
      welcomeHero.style.display = 'flex';
      messagesList.style.display = 'none';
      applyRolePermissions(null);
      updateUserProfileUI();
      loadSidebarThreads();
      playCyberSound('blip');
    }"""

html = html.replace(old_logout, new_logout)

# After login - reload threads for the new user
old_after_login = """      currentUser = res.user;
      closeAuthModal();
      applyRolePermissions(currentUser);
      updateUserProfileUI();
      playCyberSound('success');
    }"""

new_after_login = """      currentUser = res.user;
      closeAuthModal();
      conversationHistory = [];
      activeThreadId = null;
      messagesList.innerHTML = '';
      welcomeHero.style.display = 'flex';
      messagesList.style.display = 'none';
      applyRolePermissions(currentUser);
      updateUserProfileUI();
      loadSidebarThreads();
      playCyberSound('success');
    }"""

html = html.replace(old_after_login, new_after_login)

with open("web/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Done! Mobile layout + per-user chat isolation applied.")
