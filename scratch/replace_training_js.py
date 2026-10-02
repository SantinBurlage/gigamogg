with open("web/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find start of section 3 (line 4644) and start of САЙДБАР: ИСТОРИЯ ДИАЛОГОВ (line 4840)
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if "3. ОБУЧЕНИЕ И ГРАФИК LOSS" in line:
        start_idx = i - 1
    if "САЙДБАР: ИСТОРИЯ ДИАЛОГОВ" in line:
        end_idx = i - 1
        break

print(f"Replacing lines {start_idx+1} to {end_idx+1}")

webstudio_code = """    /* ══════════════════════════════════════════════════════════════════════════
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

"""

new_lines = lines[:start_idx] + [webstudio_code] + lines[end_idx:]

with open("web/index.html", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Updated index.html! New total lines:", len(new_lines))
