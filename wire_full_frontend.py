import re

with open("web/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update api() function to send Authorization Bearer header
old_api_fn = """async function api(path, body) {
      try {
        const res = await fetch(path, {
          method: body === undefined ? 'GET' : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: body === undefined ? undefined : JSON.stringify(body || {})
        });
        return await res.json();
      } catch (e) {
        return { error: 'Связь с сервером потеряна: ' + e.message };
      }
    }"""

new_api_fn = """let conversationHistory = [];
    let currentUser = null;
    let currentLanguage = localStorage.getItem('giga_lang') || 'ru';

    async function api(path, body) {
      try {
        const token = localStorage.getItem('giga_session_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
          headers['Authorization'] = 'Bearer ' + token;
        }
        const res = await fetch(path, {
          method: body === undefined ? 'GET' : 'POST',
          headers: headers,
          body: body === undefined ? undefined : JSON.stringify(body || {})
        });
        return await res.json();
      } catch (e) {
        return { error: 'Связь с сервером потеряна: ' + e.message };
      }
    }"""

if old_api_fn in html:
    html = html.replace(old_api_fn, new_api_fn)
    print("Replaced api() with auth-aware api()!")
else:
    print("Warning: old_api_fn not found exactly, using regex")
    api_pattern = re.compile(r'async function api\(path, body\) \{.*?return \{ error: \'Связь с сервером потеряна: \' \+ e\.message \};\s*\}\s*\}', re.DOTALL)
    if api_pattern.search(html):
        html = api_pattern.sub(new_api_fn, html)
        print("Replaced api() via regex!")

# 2. Update sendMessage to send history and handle html_preview
old_send_pattern = re.compile(r'const res = await api\(\'/api/chat\', \{\s*text,\s*tier: activeTier,\s*thread: activeThreadId,\s*temperature: 0\.8\s*\}\);', re.DOTALL)
new_send_call = """// Запоминаем вопрос пользователя в локальную память диалога
        conversationHistory.push({ role: 'user', content: text });

        const res = await api('/api/chat', {
          text,
          tier: activeTier,
          thread: activeThreadId,
          history: conversationHistory,
          temperature: 0.8
        });"""

if old_send_pattern.search(html):
    html = old_send_pattern.sub(new_send_call, html)
    print("Updated /api/chat call to pass history!")
else:
    print("Warning: old_send_pattern not found")

# 3. In sendMessage on response, handle conversationHistory, html_preview and Web Studio
old_res_handling = re.compile(r'appendMsg\(\'bot\', res\.answer, \{\s*thoughts,\s*actions,\s*thought_words: words,\s*critique: res\.critique,\s*corrected: res\.corrected,\s*correction_note: res\.correction_note,\s*perplexity: res\.perplexity\s*\}\);', re.DOTALL)
new_res_handling = """// Запоминаем ответ модели в локальную память диалога
        conversationHistory.push({ role: 'assistant', content: res.answer });

        // Если сгенерирован сайт - автоматически передаем в интерактивную Веб-Студию
        if (res.html_preview) {
          loadHtmlIntoStudio(res.html_preview, 'site.html');
          try {
            localStorage.setItem('giga_latest_preview_html', res.html_preview);
          } catch(e) {}
        }

        appendMsg('bot', res.answer, {
          thoughts,
          actions,
          thought_words: words,
          critique: res.critique,
          corrected: res.corrected,
          correction_note: res.correction_note,
          perplexity: res.perplexity,
          html_preview: res.html_preview
        });"""

if old_res_handling.search(html):
    html = old_res_handling.sub(new_res_handling, html)
    print("Updated response handling with html_preview and memory recording!")
else:
    print("Warning: old_res_handling not found")

# 4. In loadThread, set conversationHistory
old_load_thread = re.compile(r'\(res\.turns \|\| \[\]\)\.forEach\(t => \{\s*appendMsg\(t\.role === \'user\' \? \'user\' : \'bot\', t\.text, t\.score !== undefined \? \{ score: t\.score, verdict: \'нормально\' \} : null, t\.corrected\);\s*\}\);', re.DOTALL)
new_load_thread = """conversationHistory = (res.turns || []).map(t => ({
        role: t.role === 'user' ? 'user' : 'assistant',
        content: t.text
      }));

      (res.turns || []).forEach(t => {
        appendMsg(t.role === 'user' ? 'user' : 'bot', t.text, t.score !== undefined ? { score: t.score, verdict: 'нормально' } : null, t.corrected);
      });"""

if old_load_thread.search(html):
    html = old_load_thread.sub(new_load_thread, html)
    print("Updated loadThread to restore conversationHistory!")

# 5. In btnNewChat handler, clear conversationHistory
old_new_chat = "$('btnNewChat').onclick = () => {"
new_new_chat = """$('btnNewChat').onclick = () => {
      conversationHistory = [];"""

if old_new_chat in html:
    html = html.replace(old_new_chat, new_new_chat, 1)
    print("Updated btnNewChat to reset conversationHistory!")

# 6. In appendMsg, add website interactive banner if meta.html_preview exists
old_msg_bot = re.compile(r'div\.innerHTML = `.*?<div class="msg-bubble-bot">.*?`;', re.DOTALL)
# Let's inspect appendMsg bubble construction to cleanly insert preview badge

with open("web/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved intermediate updates to web/index.html")
