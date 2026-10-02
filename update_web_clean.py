import re

with open("web/index.html", "r", encoding="utf-8") as f:
    html = f.read()

print("Original length:", len(html))

# 1. Remove meta-pill-apex and the critic badge in the welcome hero
# In welcome hero:
badge_pattern = re.compile(
    r'<div style="display:flex; justify-content:center; gap:8px; margin-top:10px; margin-bottom:18px;">\s*<span class="meta-pill meta-pill-apex".*?</div>',
    re.DOTALL
)
if badge_pattern.search(html):
    html = badge_pattern.sub('', html)
    print("Removed welcome hero apex & critic badges!")
else:
    print("Warning: welcome hero badge pattern not matched")

# Also remove any remaining .meta-pill-apex occurrences
html = re.sub(r'<span class="meta-pill meta-pill-apex"[^>]*>.*?</span>', '', html)

# 2. Replace any text "GIGAMOGG Apex" with "GIGAMOGG"
html = html.replace("GIGAMOGG Apex", "GIGAMOGG")
html = html.replace("GIGAMOGG • Apex (Флагманская архитектура)", "GIGAMOGG • Cloud Neural Core")
html = html.replace("GIGAMOGG Apex:", "GIGAMOGG:")
html = html.replace("Я автономная нейросеть GIGAMOGG Apex", "Я автономный искусственный интеллект GIGAMOGG")

# 3. Update Sidebar Navigation tabs:
# Remove data-tab="train", "catalog", "hw", replace with "webstudio", "cloud"
old_nav_tabs = re.compile(r'<button class="nav-tab" data-tab="train">.*?</button>\s*<button class="nav-tab" data-tab="catalog">.*?</button>\s*<button class="nav-tab" data-tab="hw">.*?</button>', re.DOTALL)

new_nav_tabs = """<button class="nav-tab" data-tab="webstudio">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
          Веб-Студия (Сайты)
        </button>
        <button class="nav-tab" data-tab="cloud">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>
          </svg>
          Облачный Кластер
        </button>"""

if old_nav_tabs.search(html):
    html = old_nav_tabs.sub(new_nav_tabs, html)
    print("Replaced sidebar navigation tabs!")
else:
    print("Warning: old nav tabs not found by regex")

# 4. Update Sidebar Footer (replace local GPU 8.0 ГБ with Cloud Core Status)
old_footer = re.compile(r'<div class="sidebar-footer">.*?</div>\s*</aside>', re.DOTALL)
new_footer = """<div class="sidebar-footer">
        <div class="gpu-card" style="background:#0e1017; border-color:rgba(255,255,255,0.08);">
          <div>
            <span class="gpu-status-dot" style="background:#10b981;"></span>
            <span id="sideGpuName">GIGAMOGG Cloud</span>
          </div>
          <b style="color:#10b981;">В сети</b>
        </div>
      </div>
    </aside>"""

if old_footer.search(html):
    html = old_footer.sub(new_footer, html)
    print("Updated sidebar footer!")

# 5. Remove panels p-train, p-catalog, p-hw and replace with p-webstudio and p-cloud
old_panels = re.compile(r'<!-- ════════ ВКЛАДКА 3: ОБУЧЕНИЕ И ГРАФИК LOSS ════════ -->.*?<!-- ════════ ВКЛАДКА 6: API КЛЮЧИ', re.DOTALL)

new_panels = """<!-- ════════ ВКЛАДКА 2: ВЕБ-СТУДИЯ И ПРЕДПРОСМОТР САЙТОВ ════════ -->
      <div class="view-panel" id="p-webstudio">
        <div class="webstudio-container" style="display:flex; flex-direction:column; height:calc(100vh - 65px); padding:16px 20px; box-sizing:border-box;">
          <div class="webstudio-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; gap:12px; flex-wrap:wrap;">
            <div style="display:flex; align-items:center; gap:10px;">
              <span style="font-weight:700; font-size:16px; color:#fff;">Веб-Студия GIGAMOGG</span>
              <span class="meta-pill ready" style="font-size:11px; padding:3px 10px;">Интерактивный рендеринг</span>
            </div>
            
            <div class="viewport-switcher" style="display:flex; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:3px; gap:4px;">
              <button class="vp-btn active" id="vpDesktop" onclick="setStudioViewport('100%')" style="background:#1e2230; border:0; color:#fff; padding:5px 12px; border-radius:6px; font-size:12px; cursor:pointer; font-weight:600;">Десктоп</button>
              <button class="vp-btn" id="vpTablet" onclick="setStudioViewport('768px')" style="background:transparent; border:0; color:var(--tx-secondary); padding:5px 12px; border-radius:6px; font-size:12px; cursor:pointer;">Планшет (768px)</button>
              <button class="vp-btn" id="vpMobile" onclick="setStudioViewport('375px')" style="background:transparent; border:0; color:var(--tx-secondary); padding:5px 12px; border-radius:6px; font-size:12px; cursor:pointer;">Мобильный (375px)</button>
            </div>

            <div style="display:flex; gap:8px;">
              <button class="btn-new-chat" style="width:auto; margin:0; padding:7px 14px; font-size:12.5px;" onclick="reloadStudioPreview()">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                <span>Обновить</span>
              </button>
              <button class="btn-new-chat" style="width:auto; margin:0; padding:7px 14px; font-size:12.5px;" onclick="openStudioInNewTab()">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                <span>В новой вкладке</span>
              </button>
              <button class="btn-new-chat" style="width:auto; margin:0; padding:7px 14px; font-size:12.5px; background:#1c202d; border-color:rgba(255,255,255,0.2); color:#fff;" onclick="downloadStudioHtml()">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                <span>Скачать index.html</span>
              </button>
            </div>
          </div>

          <div style="background:#090b10; border:1px solid rgba(255,255,255,0.08); border-bottom:0; border-radius:10px 10px 0 0; padding:7px 14px; display:flex; align-items:center; gap:10px;">
            <div style="display:flex; gap:6px;">
              <span style="width:9px; height:9px; border-radius:50%; background:#ef4444; display:inline-block;"></span>
              <span style="width:9px; height:9px; border-radius:50%; background:#eab308; display:inline-block;"></span>
              <span style="width:9px; height:9px; border-radius:50%; background:#22c55e; display:inline-block;"></span>
            </div>
            <div style="flex:1; background:#12151e; border:1px solid rgba(255,255,255,0.06); border-radius:6px; padding:4px 12px; font-size:11.5px; color:#8892a4; font-family:'JetBrains Mono',monospace; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" id="studioUrlBar">
              https://gigamogg.local/preview/index.html
            </div>
          </div>

          <div style="flex:1; background:#06070a; border:1px solid rgba(255,255,255,0.08); border-radius:0 0 10px 10px; overflow:hidden; display:flex; justify-content:center; align-items:stretch; position:relative;">
            <iframe id="webStudioIframe" style="width:100%; height:100%; border:0; background:#fff; transition:width 0.25s ease;" sandbox="allow-scripts allow-modals allow-forms allow-same-origin"></iframe>
            <div id="studioEmptyPlaceholder" style="position:absolute; inset:0; background:#090a0f; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:12px; color:var(--tx-muted);">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
              <p style="font-size:13.5px; color:#9da3af;">Попросите GIGAMOGG создать сайт (например «Создай сайт для кофейни»), и он появится здесь в реальном времени.</p>
              <button class="btn-new-chat" style="width:auto; margin:0;" onclick="sendPrompt('Создай стильный современный сайт для кофейни с темной темой, меню напитков и контактами')">
                Создать сайт кофейни
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ════════ ВКЛАДКА 3: ОБЛАЧНЫЙ КЛАСТЕР ════════ -->
      <div class="view-panel" id="p-cloud">
        <div class="apikeys-container" style="max-width:900px; margin:0 auto; padding:24px 20px;">
          <div class="ml-header">
            <h2>Облачный Нейросетевой Кластер GIGAMOGG</h2>
            <p>GIGAMOGG подключена к распределенному высокоинтеллектуальному облачному серверу. Никаких локальных ограничений по видеопамяти и весам.</p>
          </div>
          <div class="hw-cards" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:14px; margin-top:20px;">
            <div class="hw-card" style="background:#111318; border:1px solid rgba(255,255,255,0.08); padding:16px; border-radius:10px;"><small style="color:var(--tx-muted); display:block; margin-bottom:4px;">Статус ядра</small><b style="color:var(--accent-green); font-size:16px;">В сети (Online)</b></div>
            <div class="hw-card" style="background:#111318; border:1px solid rgba(255,255,255,0.08); padding:16px; border-radius:10px;"><small style="color:var(--tx-muted); display:block; margin-bottom:4px;">Основной кластер</small><b style="font-size:15px; color:#fff;">Cohere Command R+ (128k)</b></div>
            <div class="hw-card" style="background:#111318; border:1px solid rgba(255,255,255,0.08); padding:16px; border-radius:10px;"><small style="color:var(--tx-muted); display:block; margin-bottom:4px;">Резервный кластер</small><b style="font-size:15px; color:#fff;">THUDM GLM-4</b></div>
            <div class="hw-card" style="background:#111318; border:1px solid rgba(255,255,255,0.08); padding:16px; border-radius:10px;"><small style="color:var(--tx-muted); display:block; margin-bottom:4px;">Web-Architect</small><b style="color:var(--accent-green); font-size:15px;">Активен (HTML5/CSS3/JS)</b></div>
            <div class="hw-card" style="background:#111318; border:1px solid rgba(255,255,255,0.08); padding:16px; border-radius:10px;"><small style="color:var(--tx-muted); display:block; margin-bottom:4px;">Критик-Ко-пайлот</small><b style="color:var(--accent-green); font-size:15px;">Активен (Валидация кода)</b></div>
            <div class="hw-card" style="background:#111318; border:1px solid rgba(255,255,255,0.08); padding:16px; border-radius:10px;"><small style="color:var(--tx-muted); display:block; margin-bottom:4px;">Режим генерации</small><b style="font-size:15px; color:#fff;">Динамический (Zero Canned)</b></div>
          </div>
        </div>
      </div>

      <!-- ════════ ВКЛАДКА 6: API КЛЮЧИ"""

if old_panels.search(html):
    html = old_panels.sub(new_panels, html)
    print("Replaced panels with Web Studio and Cloud Cluster!")
else:
    print("Warning: old panels not found by regex")

with open("web/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved updated web/index.html! New length:", len(html))
