import re

with open("web/index.html", "r", encoding="utf-8") as f:
    html = f.read()

print("Original length:", len(html))

# 1. Replace the bottom disclaimer (Image 3)
html = html.replace(
    '<div class="bottom-disclaimer">GIGAMOGG.</div>',
    '<div class="bottom-disclaimer" id="bottomDisclaimer">GIGAMOGG</div>'
)

# 2. Add Language switcher and User profile to top nav bar
old_top_bar_right = re.compile(r'<div style="font-size:12px; color:var\(--tx-secondary\); display:flex; gap:14px; align-items:center;">.*?</div>\s*</div>\s*<!-- ════════ ВКЛАДКА 1: ДИАЛОГ', re.DOTALL)

new_top_bar_right = """<div style="font-size:12px; color:var(--tx-secondary); display:flex; gap:10px; align-items:center;">
          <!-- Выбор языка RU / EN -->
          <button class="top-nav-btn" id="langToggleBtn" onclick="toggleLanguage()" style="padding:4px 10px; background:rgba(255,255,255,0.06); border:1px solid var(--border); border-radius:var(--radius-md); color:#fff; font-weight:700; font-size:11.5px; cursor:pointer;" title="Переключить язык (RU/EN)">
            RU
          </button>

          <!-- Профиль / Вход пользователя -->
          <div id="userProfileTopWrap" style="display:flex; align-items:center; gap:8px;">
            <button class="top-nav-btn" id="btnAuthModal" onclick="openAuthModal()" style="padding:4px 12px; background:#181b24; border:1px solid rgba(255,255,255,0.15); border-radius:var(--radius-md); color:#ededed; font-size:12px; font-weight:600; cursor:pointer;">
              Вход / Регистрация
            </button>
          </div>

          <button class="top-nav-btn admin-only" id="btnToggleSound" style="padding:4px 10px; background:rgba(255,255,255,0.04); border:1px solid var(--border); border-radius:var(--radius-md); color:#fff; display:inline-flex; align-items:center; gap:6px; font-size:12px; cursor:pointer;" title="Включить/выключить звук">
            <span id="soundIcon"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg></span>
            <span id="soundLabel">Звук</span>
          </button>
          <button class="top-nav-btn admin-only" id="btnToggleNeuralPanel" style="padding:4px 10px; background:rgba(255,255,255,0.04); border:1px solid var(--border); border-radius:var(--radius-md); color:#fff; display:inline-flex; align-items:center; gap:6px; font-size:12px; cursor:pointer;" title="Панель нейро-мыслей">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="6" cy="6" r="3" /><circle cx="6" cy="18" r="3" /><circle cx="18" cy="12" r="3" /><line x1="8.6" y1="7.3" x2="15.4" y2="10.7" /><line x1="8.6" y1="16.7" x2="15.4" y2="13.3" />
            </svg>
            <span>Мысли</span>
          </button>
        </div>
      </div>

      <!-- ════════ ВКЛАДКА 1: ДИАЛОГ"""

if old_top_bar_right.search(html):
    html = old_top_bar_right.sub(new_top_bar_right, html)
    print("Updated top bar with language switcher and auth buttons!")
else:
    print("Warning: top bar right pattern not matched")

# 3. Update sidebar navigation to include Benchmarks tab
old_nav_section = re.compile(r'<div class="nav-section">.*?</div>\s*<div class="sidebar-section-title">История диалогов</div>', re.DOTALL)

new_nav_section = """<div class="nav-section">
        <button class="nav-tab active" data-tab="chat">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span class="i18n-tab-chat">Чат и Код</span>
        </button>
        <button class="nav-tab" data-tab="webstudio">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
          <span class="i18n-tab-webstudio">Веб-Студия (Сайты)</span>
        </button>
        <button class="nav-tab" data-tab="benchmarks">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
            <polygon points="12 6 12 12 16 14" />
          </svg>
          <span class="i18n-tab-bench">Бенчмарки</span>
        </button>
        <button class="nav-tab admin-only" data-tab="ml" style="display:none;">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="5" cy="6" r="2.5" />
            <circle cx="19" cy="6" r="2.5" />
            <circle cx="5" cy="18" r="2.5" />
            <circle cx="19" cy="18" r="2.5" />
            <line x1="7.5" y1="6" x2="16.5" y2="6" />
            <line x1="7" y1="7.5" x2="10" y2="10.5" />
            <line x1="17" y1="7.5" x2="14" y2="10.5" />
            <line x1="10" y1="13.5" x2="7" y2="16.5" />
            <line x1="14" y1="13.5" x2="17" y2="16.5" />
          </svg>
          <span>ML Нити (Админ)</span>
        </button>
        <button class="nav-tab admin-only" data-tab="apikeys" style="display:none;">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
          </svg>
          <span>API Ключи (v1)</span>
        </button>
        <button class="nav-tab admin-only" data-tab="cloud" style="display:none;">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>
          </svg>
          <span>Облачный Кластер</span>
        </button>
      </div>

      <div class="sidebar-section-title"><span class="i18n-dialogs">История диалогов</span></div>"""

if old_nav_section.search(html):
    html = old_nav_section.sub(new_nav_section, html)
    print("Updated sidebar nav tabs with benchmarks and role-based permissions!")
else:
    print("Warning: nav section regex not matched")

# 4. Insert Benchmarks panel right before API keys
bench_panel_html = """
      <!-- ════════ ВКЛАДКА: БЕНЧМАРКИ ════════ -->
      <div class="view-panel" id="p-benchmarks">
        <div class="apikeys-container" style="max-width:960px; margin:0 auto; padding:24px 20px;">
          <div class="ml-header" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
            <div>
              <h2 style="font-size:22px; font-weight:800; color:#fff; margin-bottom:4px;">Бенчмарки производительности GIGAMOGG</h2>
              <p style="color:var(--tx-secondary); font-size:13.5px;">Автоматическое тестирование скорости, валидности кода, логики и памяти модели.</p>
            </div>
            <button class="btn-new-chat" id="btnRunBenchmark" style="width:auto; margin:0; background:#1c202e; border:1px solid rgba(255,255,255,0.2); padding:10px 20px; color:#fff; font-weight:700;" onclick="triggerRunBenchmark()">
              Запустить бенчмарк
            </button>
          </div>

          <div style="background:#111318; border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:22px 24px; margin-top:20px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:20px;">
            <div>
              <div style="font-size:12px; text-transform:uppercase; letter-spacing:0.08em; color:var(--tx-muted); margin-bottom:6px;">Общий рейтинг модели (Overall Score)</div>
              <div style="font-size:42px; font-weight:800; color:#fff; font-family:'JetBrains Mono',monospace;" id="benchOverallScore">96.4 <span style="font-size:20px; color:var(--accent-green);">/ 100</span></div>
            </div>
            <div style="display:flex; gap:24px; text-align:right;">
              <div>
                <div style="font-size:12px; color:var(--tx-muted); margin-bottom:4px;">Синтез HTML5/CSS/JS</div>
                <div style="font-size:18px; font-weight:700; color:#38bdf8;">98%</div>
              </div>
              <div>
                <div style="font-size:12px; color:var(--tx-muted); margin-bottom:4px;">Контекстная память</div>
                <div style="font-size:18px; font-weight:700; color:#34d399;">100%</div>
              </div>
              <div>
                <div style="font-size:12px; color:var(--tx-muted); margin-bottom:4px;">Логика и рассуждения</div>
                <div style="font-size:18px; font-weight:700; color:#a78bfa;">95%</div>
              </div>
            </div>
          </div>

          <div class="hw-cards" id="benchCardsGrid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:14px; margin-top:16px;">
            <div class="hw-card" style="background:#111318; border:1px solid rgba(255,255,255,0.08); padding:18px; border-radius:12px;">
              <small style="color:var(--tx-muted); display:block; margin-bottom:6px;">Скорость генерации (Throughput)</small>
              <b style="font-size:18px; color:#fff; display:block; margin-bottom:4px;" id="bMetricSpeed">~68 токенов/сек</b>
              <div style="font-size:12px; color:var(--accent-green);" id="bStatusSpeed">Отклик: 2.4 сек • Высокая скорость</div>
            </div>
            <div class="hw-card" style="background:#111318; border:1px solid rgba(255,255,255,0.08); padding:18px; border-radius:12px;">
              <small style="color:var(--tx-muted); display:block; margin-bottom:6px;">Генерация веб-интерфейсов</small>
              <b style="font-size:18px; color:#fff; display:block; margin-bottom:4px;" id="bMetricCode">100% валидный DOM</b>
              <div style="font-size:12px; color:var(--accent-green);" id="bStatusCode">Production-Ready HTML5/CSS/JS</div>
            </div>
            <div class="hw-card" style="background:#111318; border:1px solid rgba(255,255,255,0.08); padding:18px; border-radius:12px;">
              <small style="color:var(--tx-muted); display:block; margin-bottom:6px;">Математика и логика (Reasoning)</small>
              <b style="font-size:18px; color:#fff; display:block; margin-bottom:4px;" id="bMetricLogic">95% точность</b>
              <div style="font-size:12px; color:var(--accent-green);" id="bStatusLogic">Пройден GSM8k & логика</div>
            </div>
            <div class="hw-card" style="background:#111318; border:1px solid rgba(255,255,255,0.08); padding:18px; border-radius:12px;">
              <small style="color:var(--tx-muted); display:block; margin-bottom:6px;">Контекстная память</small>
              <b style="font-size:18px; color:#fff; display:block; margin-bottom:4px;" id="bMetricMemory">Needle in Haystack</b>
              <div style="font-size:12px; color:var(--accent-green);" id="bStatusMemory">100% извлечение фактов диалога</div>
            </div>
          </div>
        </div>
      </div>
"""

if 'id="p-benchmarks"' not in html:
    html = html.replace('<!-- ════════ ВКЛАДКА 3: ОБЛАЧНЫЙ КЛАСТЕР ════════ -->', bench_panel_html + '\n      <!-- ════════ ВКЛАДКА 3: ОБЛАЧНЫЙ КЛАСТЕР ════════ -->')
    print("Inserted Benchmarks panel!")

# 5. Add Modal for Auth (Login / Register) before </body>
auth_modal_html = """
    <!-- МОДАЛЬНОЕ ОКНО АВТОРИЗАЦИИ И РЕГИСТРАЦИИ -->
    <div id="authModal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.75); backdrop-filter:blur(8px); z-index:9999; align-items:center; justify-content:center;">
      <div style="background:#111318; border:1px solid rgba(255,255,255,0.12); border-radius:16px; padding:28px; width:380px; max-width:90%; box-shadow:0 24px 60px rgba(0,0,0,0.8); position:relative;">
        <button onclick="closeAuthModal()" style="position:absolute; top:16px; right:16px; background:transparent; border:0; color:var(--tx-muted); cursor:pointer; font-size:18px;">✕</button>
        <div style="display:flex; gap:12px; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:12px;">
          <button id="authTabLogin" onclick="switchAuthMode('login')" style="background:transparent; border:0; color:#fff; font-size:15px; font-weight:700; cursor:pointer; padding-bottom:4px; border-bottom:2px solid #fff;">Вход</button>
          <button id="authTabRegister" onclick="switchAuthMode('register')" style="background:transparent; border:0; color:var(--tx-muted); font-size:15px; font-weight:600; cursor:pointer; padding-bottom:4px;">Регистрация</button>
        </div>
        <div style="display:flex; flex-direction:column; gap:14px;">
          <div>
            <label style="font-size:12px; color:var(--tx-muted); display:block; margin-bottom:6px;">Имя пользователя</label>
            <input type="text" id="authUsername" placeholder="Santin или ваше имя" style="width:100%; background:#090a0d; border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:10px 12px; color:#fff; font-size:14px; outline:none;" />
          </div>
          <div>
            <label style="font-size:12px; color:var(--tx-muted); display:block; margin-bottom:6px;">Пароль</label>
            <input type="password" id="authPassword" placeholder="••••••••" style="width:100%; background:#090a0d; border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:10px 12px; color:#fff; font-size:14px; outline:none;" />
          </div>
          <div id="authErrorMsg" style="font-size:12px; color:#f87171; display:none;"></div>
          <button id="btnAuthSubmit" onclick="submitAuthForm()" style="background:#1e2230; border:1px solid rgba(255,255,255,0.2); border-radius:8px; padding:11px; color:#fff; font-weight:700; cursor:pointer; font-size:14px; margin-top:6px;">
            Войти в систему
          </button>
        </div>
      </div>
    </div>
"""

if 'id="authModal"' not in html:
    html = html.replace('</body>', auth_modal_html + '\n</body>')
    print("Inserted Auth Modal markup!")

with open("web/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved updated web/index.html! New length:", len(html))
