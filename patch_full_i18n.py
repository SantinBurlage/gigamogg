import re

with open("web/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update any remaining old bottom-disclaimer
html = html.replace(
    '<div class="bottom-disclaimer">GIGAMOGG • Локальные веса bfloat16 на NVIDIA GPU + онлайн-интеграция для актуальных данных.</div>',
    '<div class="bottom-disclaimer">GIGAMOGG • Облачный интеллект • Создатель: Кирилл Бакунин (Santin)</div>'
)

# 2. Add IDs to Welcome Hero elements if not present
old_welcome = re.compile(r'<h1>Чем могу помочь сегодня\?</h1>\s*<p>Я автономная нейросеть GIGAMOGG:.*?</p>', re.DOTALL)
new_welcome = """<h1 id="welcomeHeroTitle">Чем могу помочь сегодня?</h1>
                <p id="welcomeHeroDesc">Я автономная нейросеть GIGAMOGG: пишу чистый код, объясняю своими словами, поддерживаю API-ключи, OpenCode и живой интернет.</p>"""

if old_welcome.search(html):
    html = old_welcome.sub(new_welcome, html)
    print("Added IDs to welcomeHeroTitle and welcomeHeroDesc!")

# 3. Add IDs to Quick Cards
old_quick_cards = re.compile(r'<div class="quick-cards">.*?</div>\s*</div>\s*<!-- Список сообщений -->', re.DOTALL)
new_quick_cards = """<div class="quick-cards">
                  <div class="quick-card" onclick="sendPrompt(currentLanguage==='ru'?'Напиши игру «Змейка» на Python с библиотекой Pygame, управлением, очками и экраном проигрыша':'Write a Snake game in Python with Pygame, controls, score and game over screen')">
                    <span class="quick-card-icon" style="color:#38bdf8;">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" /></svg>
                    </span>
                    <div><b id="qc1Title">Напиши Змейку</b>
                      <div id="qc1Desc" style="font-size:12px; color:var(--tx-muted);">Готовая игра на Python с Pygame и очками</div>
                    </div>
                  </div>
                  <div class="quick-card" onclick="sendPrompt(currentLanguage==='ru'?'Объясни квантовые вычисления и суперпозицию простыми словами, на пальцах':'Explain quantum computing and superposition in simple terms')">
                    <span class="quick-card-icon" style="color:#c084fc;">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3" /><path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M4.93 19.07l14.14-14.14" /></svg>
                    </span>
                    <div><b id="qc2Title">Квантовые вычисления</b>
                      <div id="qc2Desc" style="font-size:12px; color:var(--tx-muted);">Суперпозиция и кубиты простыми словами</div>
                    </div>
                  </div>
                  <div class="quick-card" onclick="sendPrompt(currentLanguage==='ru'?'Создай красивый неоновый веб-калькулятор на HTML, CSS и JavaScript':'Create a stylish neon web calculator with HTML, CSS and JavaScript')">
                    <span class="quick-card-icon" style="color:#34d399;">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="3" /><line x1="8" y1="6" x2="16" y2="6" /><line x1="8" y1="11" x2="10" y2="11" /><line x1="14" y1="11" x2="16" y2="11" /><line x1="8" y1="15" x2="10" y2="15" /><line x1="14" y1="15" x2="16" y2="15" /></svg>
                    </span>
                    <div><b id="qc3Title">Веб-калькулятор на JS</b>
                      <div id="qc3Desc" style="font-size:12px; color:var(--tx-muted);">HTML5 + CSS Glassmorphism + JavaScript</div>
                    </div>
                  </div>
                  <div class="quick-card" onclick="sendPrompt(currentLanguage==='ru'?'В чём суть парадокса Ферми: если во Вселенной триллионы звёзд, то где все инопланетяне?':'What is the Fermi paradox: if there are trillions of stars, where is everybody?')">
                    <span class="quick-card-icon" style="color:#fbbf24;">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></svg>
                    </span>
                    <div><b id="qc4Title">Парадокс Ферми</b>
                      <div id="qc4Desc" style="font-size:12px; color:var(--tx-muted);">Где все инопланетяне и почему молчит космос?</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Список сообщений -->"""

if old_quick_cards.search(html):
    html = old_quick_cards.sub(new_quick_cards, html)
    print("Added IDs to quick cards!")

# 4. Add IDs to Right Neural Column
html = html.replace('<span>Нейронные нити и мысли</span>', '<span id="neuralPanelTitle">Нейронные нити и мысли</span>')
html = html.replace('<span>Текущее действие</span>', '<span id="titleCurrentAction">Текущее действие</span>')
html = html.replace('<span>Журнал действий в реальном времени</span>', '<span id="titleActionLog">Журнал действий в реальном времени</span>')
html = html.replace('<span>Хронология рассуждений</span>', '<span id="titleReasoning">Хронология рассуждений</span>')
html = html.replace('<span>Активные синапсы</span>', '<span id="titleSynapses">Активные синапсы</span>')
html = html.replace('<span>В сети</span>', '<span id="sideStatusOnline">В сети</span>')
html = html.replace('<span>Локальный кластер</span>', '<span id="sideClusterLabel">Локальный кластер</span>')
html = html.replace('+ Новый чат', '<span id="btnNewChatText">+ Новый чат</span>')

# 5. Add IDs to Web Studio
html = html.replace('<span style="font-weight:700; font-size:16px; color:#fff;">Веб-Студия GIGAMOGG</span>', '<span id="studioHeaderTitle" style="font-weight:700; font-size:16px; color:#fff;">Веб-Студия GIGAMOGG</span>')
html = html.replace('<span class="meta-pill ready" style="font-size:11px; padding:3px 10px;">Интерактивный рендеринг</span>', '<span id="studioHeaderSub" class="meta-pill ready" style="font-size:11px; padding:3px 10px;">Интерактивный рендеринг</span>')
html = html.replace('<p style="font-size:13.5px; color:#9da3af;">Попросите GIGAMOGG создать сайт (например «Создай сайт для кофейни»), и он появится здесь в реальном времени.</p>', '<p id="studioPlaceholderText" style="font-size:13.5px; color:#9da3af;">Попросите GIGAMOGG создать сайт (например «Создай сайт для кофейни»), и он появится здесь в реальном времени.</p>')
html = html.replace('Создать сайт кофейни\n              </button>', '<span id="studioPlaceholderBtn">Создать сайт кофейни</span>\n              </button>')

# 6. Update loadSidebarThreads to use language
old_empty_thread = '<div style="font-size:12px; color:var(--tx-muted); padding:6px 8px;">Нет сохранённых нитей</div>'
new_empty_thread = '<div style="font-size:12px; color:var(--tx-muted); padding:6px 8px;">\' + (currentLanguage === \'ru\' ? \'Нет сохранённых нитей\' : \'No saved chats\') + \'</div>'
html = html.replace(old_empty_thread, new_empty_thread)

# 7. Comprehensive applyLanguage function
new_apply_language_fn = """function applyLanguage(lang) {
      currentLanguage = lang;
      const isRu = lang === 'ru';

      const btn = $('langToggleBtn');
      if (btn) btn.textContent = lang.toUpperCase();

      // Сайдбар: табы и кнопки
      const tabChat = document.querySelector('.i18n-tab-chat');
      if (tabChat) tabChat.textContent = isRu ? 'Чат и Код' : 'Chat & Code';
      const tabStudio = document.querySelector('.i18n-tab-webstudio');
      if (tabStudio) tabStudio.textContent = isRu ? 'Веб-Студия (Сайты)' : 'Web Studio';
      const tabBench = document.querySelector('.i18n-tab-bench');
      if (tabBench) tabBench.textContent = isRu ? 'Бенчмарки' : 'Benchmarks';
      const tabDialogs = document.querySelector('.i18n-dialogs');
      if (tabDialogs) tabDialogs.textContent = isRu ? 'История диалогов' : 'Chat History';

      const btnNewChatEl = $('btnNewChatText');
      if (btnNewChatEl) btnNewChatEl.textContent = isRu ? '+ Новый чат' : '+ New Chat';

      // Нижний дисклеймер
      document.querySelectorAll('.bottom-disclaimer').forEach(disc => {
        disc.textContent = isRu
          ? 'GIGAMOGG • Облачный интеллект • Создатель: Кирилл Бакунин (Santin)'
          : 'GIGAMOGG • Cloud Intelligence • Creator: Kirill Bakunin (Santin)';
      });

      // Верхняя панель
      const soundLbl = $('soundLabel');
      if (soundLbl) soundLbl.textContent = isRu ? 'Звук' : 'Sound';

      // Поле ввода
      if (chatInput) {
        chatInput.placeholder = isRu
          ? 'Спросите о чём угодно или попросите создать сайт...'
          : 'Ask anything or request to generate a website...';
      }

      // Центральное приветствие (Welcome Hero)
      const wTitle = $('welcomeHeroTitle');
      if (wTitle) wTitle.textContent = isRu ? 'Чем могу помочь сегодня?' : 'How can I help you today?';
      const wDesc = $('welcomeHeroDesc');
      if (wDesc) {
        wDesc.textContent = isRu
          ? 'Я автономная нейросеть GIGAMOGG: пишу чистый код, объясняю своими словами, поддерживаю API-ключи, OpenCode и живой интернет.'
          : 'Autonomous GIGAMOGG intelligence: writing clean code, explaining concepts clearly, supporting API keys, OpenCode, and live internet.';
      }

      // Карточки быстрых запросов (Quick Cards)
      if ($('qc1Title')) $('qc1Title').textContent = isRu ? 'Напиши Змейку' : 'Build Snake Game';
      if ($('qc1Desc')) $('qc1Desc').textContent = isRu ? 'Готовая игра на Python с Pygame и очками' : 'Complete Python Pygame with scoring';
      if ($('qc2Title')) $('qc2Title').textContent = isRu ? 'Квантовые вычисления' : 'Quantum Computing';
      if ($('qc2Desc')) $('qc2Desc').textContent = isRu ? 'Суперпозиция и кубиты простыми словами' : 'Superposition & qubits explained simply';
      if ($('qc3Title')) $('qc3Title').textContent = isRu ? 'Веб-калькулятор на JS' : 'JS Web Calculator';
      if ($('qc3Desc')) $('qc3Desc').textContent = isRu ? 'HTML5 + CSS Glassmorphism + JavaScript' : 'HTML5 + CSS Glassmorphism + JavaScript';
      if ($('qc4Title')) $('qc4Title').textContent = isRu ? 'Парадокс Ферми' : 'Fermi Paradox';
      if ($('qc4Desc')) $('qc4Desc').textContent = isRu ? 'Где все инопланетяне и почему молчит космос?' : 'Where are the aliens and why is space silent?';

      // Правая колонка (Нейронные нити и мысли)
      if ($('neuralPanelTitle')) $('neuralPanelTitle').textContent = isRu ? 'Нейронные нити и мысли' : 'Neural Threads & Thoughts';
      if ($('neuralStatusText')) {
        const cur = $('neuralStatusText').textContent.trim();
        if (cur === 'В покое' || cur === 'Idle') {
          $('neuralStatusText').textContent = isRu ? 'В покое' : 'Idle';
        }
      }
      if ($('titleCurrentAction')) $('titleCurrentAction').textContent = isRu ? 'Текущее действие' : 'Current Action';
      if ($('actionPhaseLabel') && ($('actionPhaseLabel').textContent === 'Ожидание вопроса' || $('actionPhaseLabel').textContent === 'Awaiting query')) {
        $('actionPhaseLabel').textContent = isRu ? 'Ожидание вопроса' : 'Awaiting query';
      }
      if ($('actionPhaseDesc') && ($('actionPhaseDesc').textContent.includes('обработке') || $('actionPhaseDesc').textContent.includes('Ready'))) {
        $('actionPhaseDesc').textContent = isRu ? 'Готов к обработке и поиску данных' : 'Ready to process tasks & data';
      }
      if ($('titleActionLog')) $('titleActionLog').textContent = isRu ? 'Журнал действий в реальном времени' : 'Real-time Action Log';
      if ($('titleReasoning')) $('titleReasoning').textContent = isRu ? 'Хронология рассуждений' : 'Reasoning Timeline';
      if ($('titleSynapses')) $('titleSynapses').textContent = isRu ? 'Активные синапсы' : 'Active Synapses';

      // Статус внизу сайдбара
      if ($('sideStatusOnline')) $('sideStatusOnline').textContent = isRu ? 'В сети' : 'Online';
      if ($('sideClusterLabel')) $('sideClusterLabel').textContent = isRu ? 'Локальный кластер' : 'Local Cluster';

      // Веб-Студия
      if ($('studioHeaderTitle')) $('studioHeaderTitle').textContent = isRu ? 'Веб-Студия GIGAMOGG' : 'GIGAMOGG Web Studio';
      if ($('studioHeaderSub')) $('studioHeaderSub').textContent = isRu ? 'Интерактивный рендеринг' : 'Interactive Rendering';
      if ($('vpDesktop')) $('vpDesktop').textContent = isRu ? 'Десктоп' : 'Desktop';
      if ($('vpTablet')) $('vpTablet').textContent = isRu ? 'Планшет (768px)' : 'Tablet (768px)';
      if ($('vpMobile')) $('vpMobile').textContent = isRu ? 'Мобильный (375px)' : 'Mobile (375px)';
      if ($('studioPlaceholderText')) {
        $('studioPlaceholderText').textContent = isRu
          ? 'Попросите GIGAMOGG создать сайт (например «Создай сайт для кофейни»), и он появится здесь в реальном времени.'
          : 'Ask GIGAMOGG to create a website (e.g. "Build a coffee shop website"), and it will appear here in real time.';
      }
      if ($('studioPlaceholderBtn')) $('studioPlaceholderBtn').textContent = isRu ? 'Создать сайт кофейни' : 'Build coffee shop website';

      // Бенчмарки
      const bBtn = $('btnRunBenchmark');
      if (bBtn) bBtn.textContent = isRu ? 'Запустить бенчмарк' : 'Run Benchmark';

      // Профиль и модальное окно авторизации
      updateUserProfileUI();
      loadSidebarThreads();
    }"""

old_apply_language_pattern = re.compile(r'function applyLanguage\(lang\) \{.*?\n    \}', re.DOTALL)
if old_apply_language_pattern.search(html):
    html = old_apply_language_pattern.sub(new_apply_language_fn, html)
    print("Replaced applyLanguage with comprehensive full-page translator!")

with open("web/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved web/index.html!")
