import re

with open("web/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Add HTML markup for attachment button and preview bar
old_input_box = """            <div class="input-floating-bar">
              <div class="input-box">
                <textarea id="chatInput" placeholder="Спроси GIGAMOGG о чём угодно..." rows="1"></textarea>"""

new_input_box = """            <div class="input-floating-bar">
              <!-- Панель предпросмотра прикрепленных файлов и фото -->
              <div id="attachmentsPreviewArea" style="display:none; width:100%; max-width:840px; margin:0 auto 8px auto; display:flex; gap:8px; flex-wrap:wrap; padding:4px 6px;"></div>

              <div class="input-box">
                <!-- Кнопка прикрепления файлов/фото -->
                <button class="attach-btn" id="attachBtn" type="button" onclick="$('fileInput').click()" title="Прикрепить фото или файл (Ctrl+V или перетащите)" style="background:transparent; border:none; color:var(--tx-secondary); padding:0 8px; cursor:pointer; display:flex; align-items:center; justify-content:center; transition:color 0.15s ease;">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                  </svg>
                </button>
                <input type="file" id="fileInput" multiple accept="image/*,.txt,.pdf,.csv,.json,.py,.js,.html,.css,.md,.xml,.yaml,.yml,.c,.cpp,.h,.rs,.go,.java,.sql" style="display:none;" onchange="handleFileSelect(event)">

                <textarea id="chatInput" placeholder="Спросите о чём угодно или попросите создать сайт..." rows="1"></textarea>"""

if old_input_box in html:
    html = html.replace(old_input_box, new_input_box)
    print("Injected attachment button and preview bar markup!")
else:
    print("Warning: old_input_box not found")

# 2. Add Attachment JS logic
js_attachments_code = """
    /* ══════════════════════════════════════════════════════════════════════════
       10. ЗАГРУЗКА И ОБРАБОТКА ФАЙЛОВ И ФОТО (ATTACHMENTS & DRAG-AND-DROP)
       ══════════════════════════════════════════════════════════════════════════ */
    let attachedFiles = [];

    function handleFileSelect(e) {
      const files = Array.from(e.target.files || []);
      addFilesToAttachments(files);
      e.target.value = '';
    }

    function addFilesToAttachments(files) {
      files.forEach(file => {
        const isImg = file.type.startsWith('image/');
        const reader = new FileReader();

        if (isImg) {
          reader.onload = (ev) => {
            attachedFiles.push({
              name: file.name,
              type: file.type,
              size: file.size,
              isImage: true,
              dataUrl: ev.target.result,
              textContent: ''
            });
            renderAttachmentsPreview();
            playCyberSound('blip');
          };
          reader.readAsDataURL(file);
        } else {
          // Текстовый файл или код
          reader.onload = (ev) => {
            attachedFiles.push({
              name: file.name,
              type: file.type || 'text/plain',
              size: file.size,
              isImage: false,
              dataUrl: '',
              textContent: ev.target.result
            });
            renderAttachmentsPreview();
            playCyberSound('blip');
          };
          reader.readAsText(file);
        }
      });
    }

    function removeAttachment(idx) {
      attachedFiles.splice(idx, 1);
      renderAttachmentsPreview();
      playCyberSound('step');
    }

    function renderAttachmentsPreview() {
      const bar = $('attachmentsPreviewArea');
      if (!bar) return;

      if (!attachedFiles.length) {
        bar.style.display = 'none';
        bar.innerHTML = '';
        return;
      }

      bar.style.display = 'flex';
      bar.innerHTML = attachedFiles.map((f, idx) => {
        if (f.isImage) {
          return `
            <div style="position:relative; width:58px; height:58px; border-radius:10px; border:1px solid rgba(255,255,255,0.18); overflow:hidden; background:#12151e; box-shadow:0 4px 14px rgba(0,0,0,0.5);">
              <img src="${f.dataUrl}" style="width:100%; height:100%; object-fit:cover;" title="${esc(f.name)}" />
              <button onclick="removeAttachment(${idx})" style="position:absolute; top:2px; right:2px; width:18px; height:18px; border-radius:50%; background:rgba(0,0,0,0.75); border:1px solid rgba(255,255,255,0.3); color:#fff; font-size:11px; line-height:1; cursor:pointer; display:flex; align-items:center; justify-content:center;">✕</button>
            </div>
          `;
        } else {
          const szKb = (f.size / 1024).toFixed(1) + ' KB';
          return `
            <div style="position:relative; display:flex; align-items:center; gap:8px; background:#141722; border:1px solid rgba(255,255,255,0.14); border-radius:8px; padding:6px 12px; font-size:12px; color:#ededed; box-shadow:0 4px 14px rgba(0,0,0,0.4);">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <div style="max-width:130px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-weight:600;">${esc(f.name)}</div>
              <span style="font-size:10px; color:var(--tx-muted);">${szKb}</span>
              <button onclick="removeAttachment(${idx})" style="background:transparent; border:none; color:var(--tx-muted); font-size:13px; cursor:pointer; padding:0 2px;">✕</button>
            </div>
          `;
        }
      }).join('');
    }

    // Drag-and-drop на страницу
    window.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
    });
    window.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
        addFilesToAttachments(Array.from(e.dataTransfer.files));
      }
    });

    // Вставка из буфера обмена (Ctrl+V скриншоты и картинки)
    window.addEventListener('paste', (e) => {
      const items = (e.clipboardData || e.originalEvent.clipboardData).items;
      for (const item of items) {
        if (item.type.indexOf('image') !== -1) {
          const blob = item.getAsFile();
          if (blob) {
            addFilesToAttachments([blob]);
          }
        }
      }
    });
"""

# Insert js_attachments_code right before /* ── Инициализация ── */
init_marker = "/* ── Инициализация ── */"
if init_marker in html:
    html = html.replace(init_marker, js_attachments_code + "\n    " + init_marker, 1)
    print("Inserted attachment JS logic before init!")

# 3. Update sendMessage to send attached files and render them
old_send_chat_call = re.compile(r'const res = await api\(\'/api/chat\', \{\s*text,\s*tier: activeTier,\s*thread: activeThreadId,\s*history: conversationHistory,\s*temperature: 0\.8\s*\}\);', re.DOTALL)
new_send_chat_call = """const filesToSend = [...attachedFiles];
        // Сбрасываем прикрепленные файлы из панели ввода
        attachedFiles = [];
        renderAttachmentsPreview();

        const res = await api('/api/chat', {
          text,
          tier: activeTier,
          thread: activeThreadId,
          history: conversationHistory,
          files: filesToSend,
          temperature: 0.8
        });"""

if old_send_chat_call.search(html):
    html = old_send_chat_call.sub(new_send_chat_call, html)
    print("Updated /api/chat call to pass files!")
else:
    print("Warning: old_send_chat_call not found")

# Also pass files to user's appendMsg in sendMessage:
html = html.replace(
    "appendMsg('user', text);",
    "appendMsg('user', text, { files: [...attachedFiles] });"
)

# 4. Render files in appendMsg if user attached photos or files
old_user_msg = '<div class="msg-text">${formattedContent}</div>'
new_user_msg = """${(meta && meta.files && meta.files.length) ? `
            <div class="user-attached-preview" style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:8px;">
              ${meta.files.map(f => {
                if (f.isImage && f.dataUrl) {
                  return `<a href="${f.dataUrl}" target="_blank" style="display:inline-block; width:120px; height:120px; border-radius:10px; overflow:hidden; border:1px solid rgba(255,255,255,0.2);"><img src="${f.dataUrl}" style="width:100%; height:100%; object-fit:cover;" /></a>`;
                } else {
                  return `<div style="display:inline-flex; align-items:center; gap:6px; background:#181b26; border:1px solid rgba(255,255,255,0.15); border-radius:8px; padding:6px 12px; font-size:12px; color:#fff;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg><span>${esc(f.name)}</span></div>`;
                }
              }).join('')}
            </div>
          ` : ''}
          <div class="msg-text">${formattedContent}</div>"""

html = html.replace(old_user_msg, new_user_msg)
print("Updated appendMsg to render attached photos and files in message bubble!")

with open("web/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved web/index.html successfully!")
