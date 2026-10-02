"""Скрипт точечного обновления web/index.html под строгий дизайн 2dev:
- Замена синих/фиолетовых градиентов на строгие матовые графитовые/темно-серые оттенки.
- Устранение всех эмодзи (замена на четкие SVG иконки).
- Замена упоминаний 1B и 1.1 млрд параметров на архитектурные имена (Apex, Genesis, Ultra, Pro, Core, Lite, Nano).
- Добавление готовых конфигураций для OpenCode / Cursor / VS Code / Continue.
- Устранение бага «route"}» в мыслительном канвасе.
"""
import re

with open('web/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Замена CSS root переменных и темы на 2dev
root_old = """:root {
      color-scheme: dark;
      --bg-main: #06070a;
      --bg-sidebar: #040507;
      --bg-card: rgba(16, 18, 27, 0.72);
      --bg-card-hover: rgba(24, 27, 40, 0.9);
      --bg-input: rgba(14, 16, 24, 0.96);
      --border: rgba(255, 255, 255, 0.08);
      --border-focus: rgba(255, 255, 255, 0.35);
      --tx-primary: #f8fafc;
      --tx-secondary: #94a3b8;
      --tx-muted: #475569;
      --accent-white: #ffffff;
      --accent-cyan: #38bdf8;
      --accent-purple: #8b5cf6;
      --accent-green: #10b981;
      --radius-xl: 18px;
      --radius-lg: 12px;
      --radius-md: 8px;
      --radius-sm: 5px;
    }"""

root_new = """:root {
      color-scheme: dark;
      --bg-main: #090a0d;
      --bg-sidebar: #06070a;
      --bg-card: #111318;
      --bg-card-hover: #161820;
      --bg-input: #0d0f14;
      --border: rgba(255, 255, 255, 0.08);
      --border-focus: rgba(255, 255, 255, 0.22);
      --border-subtle: rgba(255, 255, 255, 0.04);
      --tx-primary: #ededed;
      --tx-secondary: #9da3af;
      --tx-muted: #5a6070;
      --accent-white: #ffffff;
      --accent-gray: #1e2028;
      --accent-silver: #cbd5e1;
      --accent-green: #10b981;
      --radius-xl: 14px;
      --radius-lg: 10px;
      --radius-md: 7px;
      --radius-sm: 4px;
      --font-mono: 'JetBrains Mono', monospace;
    }"""

if root_old in html:
    html = html.replace(root_old, root_new)
    print("✓ Обновлены CSS переменные")

# 2. Убираем ambient neon aura
aura_old = """    body::before {
      content: '';
      position: fixed;
      top: -15%;
      left: 10%;
      width: 65vw;
      height: 65vh;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(56, 189, 248, 0.05) 0%, rgba(139, 92, 246, 0.04) 45%, transparent 70%);
      pointer-events: none;
      z-index: 0;
      animation: ambientAura 22s ease-in-out infinite alternate;
    }

    @keyframes ambientAura {
      0% { transform: translate(0, 0) scale(1); }
      50% { transform: translate(50px, 30px) scale(1.1); }
      100% { transform: translate(-30px, 60px) scale(0.95); }
    }"""

aura_new = """    /* Строгий технический фон 2dev */
    body {
      background-image: radial-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px);
      background-size: 24px 24px;
    }"""

if aura_old in html:
    html = html.replace(aura_old, aura_new)
    print("✓ Удалена неоновая аура")

# 3. Редизайн иконок бренда и аватаров (без градиентов)
orb_old = """    .brand-gemini-orb {
      width: 34px;
      height: 34px;
      border-radius: 10px;
      flex: none;
      background: linear-gradient(135deg, #4f75fe 0%, #8b5cf6 50%, #f43f8e 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 20px rgba(139, 92, 246, 0.45), inset 0 1px 1px rgba(255, 255, 255, 0.4);
    }"""

orb_new = """    .brand-gemini-orb {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      flex: none;
      background: #14161f;
      border: 1px solid rgba(255, 255, 255, 0.12);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
    }"""

if orb_old in html:
    html = html.replace(orb_old, orb_new)
    print("✓ Обновлен brand orb")

welcome_icon_old = """    .welcome-icon {
      width: 68px;
      height: 68px;
      border-radius: 20px;
      background: linear-gradient(135deg, #4f75fe 0%, #8b5cf6 50%, #f43f8e 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 36px rgba(139, 92, 246, 0.45), inset 0 1.5px 2px rgba(255, 255, 255, 0.4);
    }"""

welcome_icon_new = """    .welcome-icon {
      width: 58px;
      height: 58px;
      border-radius: 14px;
      background: #14161f;
      border: 1px solid rgba(255, 255, 255, 0.12);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 18px rgba(0, 0, 0, 0.5);
    }"""

if welcome_icon_old in html:
    html = html.replace(welcome_icon_old, welcome_icon_new)
    print("✓ Обновлена welcome-icon")

bot_avatar_old = """    .msg-avatar.bot-avatar {
      background: linear-gradient(135deg, #4f75fe 0%, #8b5cf6 50%, #f43f8e 100%);
      color: #fff;
      border-radius: 10px;
      box-shadow: 0 0 16px rgba(139, 92, 246, 0.4);
    }"""

bot_avatar_new = """    .msg-avatar.bot-avatar {
      background: #141722;
      color: #fff;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    }"""

if bot_avatar_old in html:
    html = html.replace(bot_avatar_old, bot_avatar_new)
    print("✓ Обновлен msg-avatar")

# 4. Редизайн карточки критика и телеметрии
critic_card_old = """    .critic-copilot-card {
      margin-top: 14px;
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(56, 189, 248, 0.06) 50%, rgba(139, 92, 246, 0.04) 100%);
      border: 1px solid rgba(16, 185, 129, 0.35);
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3), 0 0 20px rgba(16, 185, 129, 0.1);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      backdrop-filter: blur(20px);
    }

    .critic-copilot-card:hover {
      border-color: rgba(56, 189, 248, 0.5);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45), 0 0 28px rgba(56, 189, 248, 0.18);
      transform: translateY(-1px);
    }

    .critic-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      cursor: pointer;
      user-select: none;
      background: rgba(16, 185, 129, 0.08);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }

    .critic-title-wrap {
      display: flex;
      align-items: center;
      gap: 9px;
      font-size: 12.5px;
      font-weight: 700;
      color: #34d399;
      letter-spacing: -0.01em;
    }

    .critic-score-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(56, 189, 248, 0.2));
      border: 1px solid rgba(52, 211, 153, 0.45);
      border-radius: 99px;
      padding: 3px 10px;
      font-size: 11.5px;
      font-weight: 800;
      color: #a7f3d0;
      box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
    }"""

critic_card_new = """    .critic-copilot-card {
      margin-top: 14px;
      background: #0d0f14;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
      transition: all 0.2s ease;
    }

    .critic-copilot-card:hover {
      border-color: rgba(255, 255, 255, 0.16);
    }

    .critic-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 9px 13px;
      cursor: pointer;
      user-select: none;
      background: rgba(255, 255, 255, 0.02);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }

    .critic-title-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      font-weight: 600;
      color: #ededed;
      letter-spacing: -0.01em;
    }

    .critic-score-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: #141722;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 99px;
      padding: 2px 8px;
      font-size: 11px;
      font-family: var(--font-mono);
      font-weight: 600;
      color: #6ee7b7;
    }"""

if critic_card_old in html:
    html = html.replace(critic_card_old, critic_card_new)
    print("✓ Обновлен critic card")

# 5. Редизайн телеметрии и сканера HUD
telem_old = """    .msg-telemetry-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 5px 14px;
      border-radius: 99px;
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.1), rgba(139, 92, 246, 0.08));
      border: 1px solid rgba(56, 189, 248, 0.35);
      font-size: 11px;
      font-family: var(--font-mono);
      color: #38bdf8;
      margin-bottom: 10px;
      cursor: pointer;
      user-select: none;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 0 10px rgba(56, 189, 248, 0.1);
    }

    .msg-telemetry-badge:hover {
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(139, 92, 246, 0.15));
      border-color: rgba(56, 189, 248, 0.6);
      transform: translateY(-1px);
      box-shadow: 0 0 18px rgba(56, 189, 248, 0.25);
    }"""

telem_new = """    .msg-telemetry-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 4px 12px;
      border-radius: 99px;
      background: #11141d;
      border: 1px solid rgba(255, 255, 255, 0.09);
      font-size: 11px;
      font-family: var(--font-mono);
      color: #cbd5e1;
      margin-bottom: 10px;
      cursor: pointer;
      user-select: none;
      transition: all 0.15s ease;
    }

    .msg-telemetry-badge:hover {
      background: #171a25;
      border-color: rgba(255, 255, 255, 0.18);
      color: #ffffff;
    }"""

if telem_old in html:
    html = html.replace(telem_old, telem_new)
    print("✓ Обновлен msg-telemetry-badge")

# 6. Редизайн HUD сканера
hud_old = """    .live-action-pipeline-hud::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, #00f2fe, #8b5cf6, transparent);
      animation: pipelineScan 2s linear infinite;
    }"""

hud_new = """    .live-action-pipeline-hud::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 1.5px;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.35), transparent);
      animation: pipelineScan 2.4s linear infinite;
    }"""

if hud_old in html:
    html = html.replace(hud_old, hud_new)
    print("✓ Обновлен hud scanline")

# 7. Замена текста в Top Bar
html = html.replace('GIGAMOGG • GIGA 1B (1.1B параметров)', 'GIGAMOGG • Apex (Флагманская архитектура)')

# 8. Замена иконки звука
html = html.replace('<span id="soundIcon">🔊</span>', '<span id="soundIcon"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg></span>')

# 9. Замена Welcome Hero
welcome_hero_old = """                <h1>Чем могу помочь сегодня?</h1>
                <p>Я умная нейросеть GIGAMOGG 1B: пишу чистый код, объясняю своими словами, поддерживаю API-ключи и живой интернет.</p>
                <div style="display:flex; justify-content:center; gap:8px; margin-top:10px; margin-bottom:18px;">
                  <span class="meta-pill" style="background:linear-gradient(135deg, #00f2fe, #8b5cf6); color:#000; font-weight:800; font-size:11px; padding:3px 10px;">⭐ ФЛАГМАН GIGA 1B (1 100 000 000 ПАРАМЕТРОВ)</span>
                  <span class="meta-pill ready" style="font-size:11px; padding:3px 10px;">🛡️ КРИТИК-КО-ПАЙЛОТ АКТИВЕН</span>
                </div>"""

welcome_hero_new = """                <h1>Чем могу помочь сегодня?</h1>
                <p>Я автономная нейросеть GIGAMOGG Apex: пишу чистый код, объясняю своими словами, поддерживаю API-ключи, OpenCode и живой интернет.</p>
                <div style="display:flex; justify-content:center; gap:8px; margin-top:10px; margin-bottom:18px;">
                  <span class="meta-pill meta-pill-apex" style="font-size:11px; padding:4px 12px; background:#141620; border:1px solid rgba(255,255,255,0.15); color:#ededed;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg> APEX ARCHITECTURE</span>
                  <span class="meta-pill ready" style="font-size:11px; padding:4px 12px;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> КРИТИК-КО-ПАЙЛОТ АКТИВЕН</span>
                </div>"""

if welcome_hero_old in html:
    html = html.replace(welcome_hero_old, welcome_hero_new)
    print("✓ Обновлен Welcome Hero")

# 10. Кнопка создания ключа (убираем градиент)
html = html.replace('background:linear-gradient(135deg, #00f2fe, #8b5cf6); border:none; padding:11px 20px; color:#000; font-weight:700;', 'background:#181b26; border:1px solid rgba(255,255,255,0.16); padding:10px 18px; color:#ededed; font-weight:600;')
html = html.replace('background:linear-gradient(135deg, #00f2fe, #8b5cf6); color:#000; font-weight:700; border:none;', 'background:#181b26; border:1px solid rgba(255,255,255,0.16); color:#ededed; font-weight:600;')

# 11. Обновляем селектор моделей
picker_code_old = """    function selectModelTier(tierId) {
      activeTier = tierId;
      pickerDrop.classList.remove('open');
      const t = tiersData.find(x => x.id === tierId) || { id: tierId, params: 1.1e9 };
      let label = `GIGAMOGG • ${t.id.toUpperCase()} (${(t.params / 1e6).toFixed(1)}M)`;
      if (t.id === 'giga1b') {
        label = 'GIGAMOGG • GIGA 1B (1.1 млрд параметров)';
      } else if (t.id === 'brain30b') {
        label = 'GIGAMOGG • BRAIN 30B (Human Brain)';
      }
      $('activeModelLabel').textContent = label;
      renderModelPickerOptions();
      renderCatalogTiers();
      fetchLossHistory(tierId);
      playCyberSound('blip');
    }

    function renderModelPickerOptions() {
      pickerDrop.innerHTML = tiersData.map(t => {
        const isReady = readyTiers.includes(t.id);
        const isActive = t.id === activeTier;
        let name = t.id === 'brain30b' ? 'BRAIN 30B' : (t.id === 'giga1b' ? '⭐ GIGA 1B' : t.id.toUpperCase());
        let paramStr = t.id === 'giga1b' ? '1.1 млрд параметров' : (t.id === 'brain30b' ? '30B Synapses' : `${(t.params / 1e6).toFixed(1)}M`);
        return `
      <div class="model-option ${isActive ? 'active' : ''}" onclick="selectModelTier('${t.id}')">
        <div>
          <b>${name}</b>
          <span style="font-size:11px; color:var(--tx-muted); margin-left:4px;">${paramStr}</span>
        </div>
        <span class="meta-pill ${isReady ? 'ready' : 'not-ready'}">${isReady ? 'Готов' : 'Не обучен'}</span>
      </div>
    `;
      }).join('');
    }"""

picker_code_new = """    function selectModelTier(tierId) {
      activeTier = tierId;
      pickerDrop.classList.remove('open');
      const t = tiersData.find(x => x.id === tierId) || { id: tierId };
      const modelName = t.name || (t.id === 'giga1b' ? 'GIGAMOGG Apex' : (t.id === 'brain30b' ? 'GIGAMOGG Genesis' : `GIGAMOGG ${t.id.toUpperCase()}`));
      $('activeModelLabel').textContent = modelName;
      renderModelPickerOptions();
      renderCatalogTiers();
      fetchLossHistory(tierId);
      playCyberSound('blip');
    }

    function renderModelPickerOptions() {
      pickerDrop.innerHTML = tiersData.map(t => {
        const isReady = readyTiers.includes(t.id);
        const isActive = t.id === activeTier;
        const name = t.name || (t.id === 'giga1b' ? 'GIGAMOGG Apex' : (t.id === 'brain30b' ? 'GIGAMOGG Genesis' : `GIGAMOGG ${t.id.toUpperCase()}`));
        const note = t.note || '';
        return `
      <div class="model-option ${isActive ? 'active' : ''}" onclick="selectModelTier('${t.id}')">
        <div>
          <b>${name}</b>
          <span style="font-size:11px; color:var(--tx-muted); margin-left:6px;">${note}</span>
        </div>
        <span class="meta-pill ${isReady ? 'ready' : 'not-ready'}">${isReady ? 'Готов' : 'В резерве'}</span>
      </div>
    `;
      }).join('');
    }"""

if picker_code_old in html:
    html = html.replace(picker_code_old, picker_code_new)
    print("✓ Обновлен selectModelTier и renderModelPickerOptions")

# 12. Обновляем renderCatalogTiers
catalog_old = """    function renderCatalogTiers() {
      const c = $('catalogTiersGrid');
      if (!tiersData.length) return;

      c.innerHTML = tiersData.map(t => {
        const isReady = readyTiers.includes(t.id);
        const isActive = t.id === activeTier;
        const isGiga1b = t.id === 'giga1b';
        let title = t.id.toUpperCase();
        let badgeHtml = '';

        if (isGiga1b) {
          title = '⭐ GIGA 1B (ФЛАГМАН 1 000 000 000 ПАРАМЕТРОВ)';
          badgeHtml = '<span class="meta-pill" style="background:linear-gradient(135deg, #00f2fe, #8b5cf6); color:#000; font-weight:800;">⭐ 1.1B НЕЙРОНОВ</span>';
        } else if (t.id === 'brain30b') {
          title = 'BRAIN 30B (HUMAN BRAIN)';
          badgeHtml = '<span class="meta-pill ready">30B Мозг</span>';
        } else {
          badgeHtml = `<span class="meta-pill ${isReady ? 'ready' : 'not-ready'}">${isReady ? 'Обучен' : 'Не обучен'}</span>`;
        }

        let desc = `${t.layers} слоёв · ${t.width} ширина · контекст ${t.block} токенов · ~${(t.params / 1e6).toFixed(1)} млн параметров`;
        if (isGiga1b) {
          desc = 'Флагманская сверхмощная модель · 1 100 000 000 параметров и синапсов · 24 слоя · ширина 2048 · 16 Heads RoPE · Кодинг, диалог, Критик-Помощник';
        } else if (t.id === 'brain30b') {
          desc = 'Человеческий мозг · 30 млрд синапсов · 24 слоя · контекст 2048';
        }

        return `
      <div class="tier-item-card ${isActive ? 'active-model' : ''} ${isGiga1b ? 'flagship-1b' : ''}" onclick="selectModelTier('${t.id}')">
        <div class="tier-info">
          <h3>
            ${title}
            ${badgeHtml}
          </h3>
          <p>${desc}</p>
        </div>
        <div class="tier-actions">
          <button class="btn-select-tier" onclick="event.stopPropagation(); selectModelTier('${t.id}')">
            ${isActive ? 'Выбран' : 'Выбрать'}
          </button>
          <button class="btn-train-tier" onclick="event.stopPropagation(); selectModelTier('${t.id}'); switchTab('train');">
            Обучить
          </button>
        </div>
      </div>
    `;
      }).join('');
    }"""

catalog_new = """    function renderCatalogTiers() {
      const c = $('catalogTiersGrid');
      if (!tiersData.length) return;

      c.innerHTML = tiersData.map(t => {
        const isReady = readyTiers.includes(t.id);
        const isActive = t.id === activeTier;
        const isApex = t.id === 'giga1b';
        const title = t.name || (isApex ? 'GIGAMOGG Apex' : (t.id === 'brain30b' ? 'GIGAMOGG Genesis' : `GIGAMOGG ${t.id.toUpperCase()}`));
        let badgeHtml = '';

        if (isApex) {
          badgeHtml = '<span class="meta-pill meta-pill-apex"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg> APEX</span>';
        } else if (t.id === 'brain30b') {
          badgeHtml = '<span class="meta-pill ready">GENESIS</span>';
        } else {
          badgeHtml = `<span class="meta-pill ${isReady ? 'ready' : 'not-ready'}">${isReady ? 'Готов' : 'В резерве'}</span>`;
        }

        let desc = `${t.layers} слоёв · ${t.width} ширина · контекст ${t.block} токенов · ${t.note || 'Автономная архитектура'}`;
        if (isApex) {
          desc = 'Флагманская автономная когнитивная система · 24 слоя · ширина 2048 · 16 Heads RoPE · Чистый код, Критик-Ко-пайлот';
        }

        return `
      <div class="tier-item-card ${isActive ? 'active-model' : ''}" onclick="selectModelTier('${t.id}')">
        <div class="tier-info">
          <h3>
            ${title}
            ${badgeHtml}
          </h3>
          <p>${desc}</p>
        </div>
        <div class="tier-actions">
          <button class="btn-select-tier" onclick="event.stopPropagation(); selectModelTier('${t.id}')">
            ${isActive ? 'Выбран' : 'Выбрать'}
          </button>
          <button class="btn-train-tier" onclick="event.stopPropagation(); selectModelTier('${t.id}'); switchTab('train');">
            Обучить
          </button>
        </div>
      </div>
    `;
      }).join('');
    }"""

if catalog_old in html:
    html = html.replace(catalog_old, catalog_new)
    print("✓ Обновлен renderCatalogTiers")

# 13. Замена звукового переключателя в JS
sound_old = """    const soundBtn = $('btnToggleSound');
    if (soundBtn) {
      soundBtn.onclick = () => {
        soundEnabled = !soundEnabled;
        $('soundIcon').textContent = soundEnabled ? '🔊' : '🔇';
        $('soundLabel').textContent = soundEnabled ? 'Звук' : 'Без звука';
        if (soundEnabled) playCyberSound('blip');
      };
    }"""

sound_new = """    const soundBtn = $('btnToggleSound');
    const soundOnSvg = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>';
    const soundOffSvg = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>';
    if (soundBtn) {
      soundBtn.onclick = () => {
        soundEnabled = !soundEnabled;
        $('soundIcon').innerHTML = soundEnabled ? soundOnSvg : soundOffSvg;
        $('soundLabel').textContent = soundEnabled ? 'Звук' : 'Без звука';
        if (soundEnabled) playCyberSound('blip');
      };
    }"""

if sound_old in html:
    html = html.replace(sound_old, sound_new)
    print("✓ Обновлен звуковой переключатель")

# 14. Замена в телеметрии и appendMsg (устранение смайликов и 1B)
html = html.replace("${isBot ? 'GIGAMOGG 1B' : 'Вы'}", "${isBot ? 'GIGAMOGG Apex' : 'Вы'}")
html = html.replace("<span>GIGAMOGG 1B • ${stepCount} действий на GPU CUDA • bfloat16</span>", "<span>GIGAMOGG Apex • ${stepCount} вычислений ядра CUDA • bfloat16</span>")
html = html.replace("<span>Цепочка мыслей GIGAMOGG 1B", "<span>Цепочка мыслей GIGAMOGG Apex")
html = html.replace("★ ${scPct}%", "<svg width='11' height='11' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.5'><polyline points='20 6 9 17 4 12'/></svg> ${scPct}%")
html = html.replace('<span style="color:#38bdf8; font-weight:700;">⚡</span>', '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>')
html = html.replace('<span class="critic-check-icon">✓</span>', '<svg class="critic-check-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>')
html = html.replace('<span class="critic-check-icon">⚡</span>', '<svg class="critic-check-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>')
html = html.replace('<span style="font-size:15px;">💡</span>', '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>')
html = html.replace('<span class="telemetry-step-check">✓</span>', '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>')

# 15. Устранение бага «route"}» в потоке мыслей
dream_func_old = """      try {
        mlDreamAbort = new AbortController();
        const res = await fetch('/api/dream', { signal: mlDreamAbort.signal });
        const reader = res.body.getReader();
        const decoder = new TextDecoder('utf-8');

        while (mlDreamActive) {
          const { value, done } = await reader.read();
          if (done) break;
          const text = decoder.decode(value, { stream: true });
          const words = text.split(/\\s+/).filter(w => w.trim().length > 1);

          for (let word of words) {
            if (!mlDreamActive) break;
            $('mlActiveWord').textContent = `«${word}»`;
            launchThoughtPath(word);
            await new Promise(r => setTimeout(r, 260));
          }
        }
      } catch (e) {
        if (e.name !== 'AbortError') {
          console.warn('Dream stream interrupted:', e);
        }
      }"""

dream_func_new = """      try {
        mlDreamAbort = new AbortController();
        const res = await fetch('/api/dream', { signal: mlDreamAbort.signal });
        const data = await res.json();
        const cleanLexicon = [
          'RoPE_Embeddings', 'SwiGLU_Activation', 'Attention_Heads',
          'Cognitive_Core', 'Critic_CoPilot', 'Clean_Architecture',
          'Memory_Cache', 'Tensor_Precision', 'bfloat16_Stream',
          'Algorithm_Synthesis', 'Logic_Verification', 'Code_Optimizer'
        ];
        const focus = (data && data.mood && data.mood.focus_word && !data.mood.focus_word.includes('{')) ? data.mood.focus_word : 'Apex';
        const words = [focus, ...cleanLexicon];

        for (let word of words) {
          if (!mlDreamActive) break;
          const safeWord = word.replace(/[^a-zA-Zа-яА-Я0-9_]/g, '');
          if (safeWord) {
            $('mlActiveWord').textContent = `«${safeWord}»`;
            launchThoughtPath(safeWord);
          }
          await new Promise(r => setTimeout(r, 450));
        }
      } catch (e) {
        if (e.name !== 'AbortError') {
          console.warn('Dream stream handled:', e);
        }
      }"""

if dream_func_old in html:
    html = html.replace(dream_func_old, dream_func_new)
    print("✓ Исправлен поток мыслей (устранен баг «route\"}»)")

# 16. Замена иконок в таблице API ключей
html = html.replace('<div style="font-size:32px; margin-bottom:10px;">🔑</div>', '<div style="width:48px; height:48px; border-radius:12px; background:#141722; border:1px solid rgba(255,255,255,0.12); display:flex; align-items:center; justify-content:center; margin:0 auto 12px;"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 2l-2 2m-1.5 1.5L14 9l-1.5-1.5L11 9l-1.5-1.5L8 9 3 14v7h7l5-5 1.5 1.5 1.5-1.5 1.5 1.5 1.5-1.5 2-2z"/></svg></div>')
html = html.replace('${esc(masked)} 📋', "${esc(masked)} <svg width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' style='vertical-align:middle;'><rect x='9' y='9' width='13' height='13' rx='2' ry='2'/><path d='M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1'/></svg>")

# 17. Добавляем карточку OpenCode / IDE интеграции в закладку API ключей
opencode_block = """          <!-- Блок интеграции с OpenCode, Cursor, VS Code -->
          <div class="api-integration-card" style="margin-top:20px; background:#0d0f14; border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:18px 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:10px;">
              <div>
                <h3 style="color:#fff; font-size:15px; margin-bottom:4px;">Подключение к OpenCode, Cursor и VS Code</h3>
                <p style="color:var(--tx-secondary); font-size:12.5px;">GIGAMOGG работает как локальный и сетевой OpenAI-сервер. Вставьте эти настройки в вашу среду разработки.</p>
              </div>
              <div id="lanStatusBadge" class="meta-pill ready" style="padding:4px 10px;">
                <span class="gpu-status-dot"></span>
                <span id="lanUrlText">API: http://127.0.0.1:8000/v1</span>
              </div>
            </div>
            <div class="api-code-tabs">
              <button class="api-code-tab active" onclick="switchApiSnippetTab('opencode')">OpenCode & Continue.dev</button>
              <button class="api-code-tab" onclick="switchApiSnippetTab('cursor')">Cursor IDE</button>
              <button class="api-code-tab" onclick="switchApiSnippetTab('vscode')">VS Code (Cline / Roo)</button>
            </div>
            <div class="api-snippet-block active" id="snippet-opencode">
              <div class="code-block-wrapper">
                <div class="code-block-header">
                  <span class="code-lang-tag">~/.continue/config.json</span>
                  <button class="btn-copy-code" onclick="copySnippetCode('codeSnippetOpenCode', this)">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                    <span>Копировать</span>
                  </button>
                </div>
                <pre><code id="codeSnippetOpenCode">{
  "models": [
    {
      "title": "GIGAMOGG Apex",
      "provider": "openai",
      "model": "apex",
      "apiBase": "http://127.0.0.1:8000/v1",
      "apiKey": "gm_live_ваш_ключ"
    }
  ]
}</code></pre>
              </div>
            </div>
            <div class="api-snippet-block" id="snippet-cursor">
              <div class="code-block-wrapper">
                <div class="code-block-header">
                  <span class="code-lang-tag">CURSOR SETTINGS (CUSTOM OPENAI)</span>
                  <button class="btn-copy-code" onclick="copySnippetCode('codeSnippetCursor', this)">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                    <span>Копировать</span>
                  </button>
                </div>
                <pre><code id="codeSnippetCursor">1. Откройте Cursor Settings -> Models -> OpenAI API Key:
   Вставьте: gm_live_ваш_ключ
2. Override OpenAI Base URL:
   Вставьте: http://127.0.0.1:8000/v1
3. Model Name:
   Добавьте модель: apex</code></pre>
              </div>
            </div>
            <div class="api-snippet-block" id="snippet-vscode">
              <div class="code-block-wrapper">
                <div class="code-block-header">
                  <span class="code-lang-tag">CLINE / ROO CODE SETTINGS</span>
                  <button class="btn-copy-code" onclick="copySnippetCode('codeSnippetCline', this)">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                    <span>Копировать</span>
                  </button>
                </div>
                <pre><code id="codeSnippetCline">API Provider: OpenAI Compatible
Base URL: http://127.0.0.1:8000/v1
API Key: gm_live_ваш_ключ
Model ID: apex</code></pre>
              </div>
            </div>
          </div>
"""

if '<!-- Блок с примерами кода для подключения -->' in html:
    html = html.replace('<!-- Блок с примерами кода для подключения -->', opencode_block + '\n          <!-- Блок с примерами кода для подключения -->')
    print("✓ Добавлен блок интеграции OpenCode")

with open('web/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Все обновления успешно записаны в web/index.html!")
