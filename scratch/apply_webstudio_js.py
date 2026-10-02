import re

with open("web/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update formatMarkdown to include the "Предпросмотр сайта" button for HTML blocks
old_cb = """        const highlighted = highlightCode(code.trim(), lang);
        codeBlocks.push({
          id,
          html: `<div class="code-block-wrapper">
            <div class="code-block-header">
              <span class="code-lang-tag">${lName}</span>
              <button class="btn-copy-code" onclick="copyCodeBlock(this)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                <span>Копировать код</span>
              </button>
            </div>
            <pre><code>${highlighted}</code></pre>
          </div>`
        });"""

new_cb = """        const highlighted = highlightCode(code.trim(), lang);
        const isHtml = (lang || '').toLowerCase() === 'html' || code.includes('<!DOCTYPE html') || code.includes('<html');
        const previewBtn = isHtml ? `
              <button class="btn-copy-code" style="background:#151822; border-color:rgba(255,255,255,0.18); color:#ededed; margin-right:6px;" onclick="openCodeInWebStudio(this)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                <span>Предпросмотр сайта</span>
              </button>` : '';
        codeBlocks.push({
          id,
          html: `<div class="code-block-wrapper">
            <div class="code-block-header">
              <span class="code-lang-tag">${lName}</span>
              <div style="display:flex; align-items:center;">
                ${previewBtn}
                <button class="btn-copy-code" onclick="copyCodeBlock(this)">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                  <span>Копировать код</span>
                </button>
              </div>
            </div>
            <pre><code>${highlighted}</code></pre>
          </div>`
        });"""

if old_cb in content:
    content = content.replace(old_cb, new_cb)
    print("Updated formatMarkdown with Web Studio preview button!")
else:
    print("Warning: old code block markup not found verbatim")

# 2. Replace the old training & catalog JS section with Web Studio engine
train_section_pattern = re.compile(
    r'/\* ══════════════════════════════════════════════════════════════════════════\s*3\. ОБУЧЕНИЕ И ГРАФИК LOSS.*?/\* ══════════════════════════════════════════════════════════════════════════\s*5\. ЖЕЛЕЗО',
    re.DOTALL
)

webstudio_js = """/* ══════════════════════════════════════════════════════════════════════════
       3. ВЕБ-СТУДИЯ И ПРЕДПРОСМОТР (LIVE WEB STUDIO)
       ══════════════════════════════════════════════════════════════════════════ */
    let currentStudioHtml = '';

    function loadHtmlIntoStudio(htmlCode, urlTitle) {
      if (!htmlCode) return;
      currentStudioHtml = htmlCode;
      const iframe = $('webStudioIframe');
      const placeholder = $('studioEmptyPlaceholder');
      const urlBar = $('studioUrlBar');
      if (placeholder) placeholder.style.display = 'none';
      if (urlBar) urlBar.textContent = 'https://gigamogg.local/preview/' + (urlTitle || 'index.html');
      if (iframe) {
        iframe.srcdoc = htmlCode;
      }
    }

    function setStudioViewport(width) {
      const iframe = $('webStudioIframe');
      if (iframe) iframe.style.width = width;
      document.querySelectorAll('.vp-btn').forEach(btn => {
        const matches = btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(width);
        btn.classList.toggle('active', matches);
        btn.style.background = matches ? '#1e2230' : 'transparent';
        btn.style.color = matches ? '#fff' : 'var(--tx-secondary)';
      });
      playCyberSound('blip');
    }

    function reloadStudioPreview() {
      if (currentStudioHtml) {
        loadHtmlIntoStudio(currentStudioHtml);
        playCyberSound('step');
      }
    }

    function openStudioInNewTab() {
      if (!currentStudioHtml) return;
      const blob = new Blob([currentStudioHtml], { type: 'text/html;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
    }

    function downloadStudioHtml() {
      if (!currentStudioHtml) return;
      const blob = new Blob([currentStudioHtml], { type: 'text/html;charset=utf-8' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'gigamogg_site.html';
      a.click();
      playCyberSound('success');
    }

    function openCodeInWebStudio(btn) {
      const wrapper = btn.closest('.code-block-wrapper');
      if (!wrapper) return;
      const code = wrapper.querySelector('pre code').innerText;
      loadHtmlIntoStudio(code);
      switchTab('webstudio');
    }

    /* ══════════════════════════════════════════════════════════════════════════
       5. ЖЕЛЕЗО"""

if train_section_pattern.search(content):
    content = train_section_pattern.sub(webstudio_js, content)
    print("Replaced training JS with Web Studio engine!")
else:
    print("Warning: train section pattern not matched")

# 3. In sendMessage(), ensure res.html_preview is automatically loaded into Web Studio
old_send_handle = """      if (res.answer) {
        appendMsg('bot', res.answer, res);
      }"""

new_send_handle = """      if (res.html_preview) {
        loadHtmlIntoStudio(res.html_preview);
      }
      if (res.answer) {
        appendMsg('bot', res.answer, res);
      }"""

if old_send_handle in content:
    content = content.replace(old_send_handle, new_send_handle)
    print("Connected res.html_preview to loadHtmlIntoStudio!")

# 4. Remove any lingering calls to fetchLossHistory
content = re.sub(r'fetchLossHistory\([^)]*\);?', '', content)
content = re.sub(r'renderCatalogTiers\([^)]*\);?', '', content)

with open("web/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Saved final updated web/index.html! Total length:", len(content))
