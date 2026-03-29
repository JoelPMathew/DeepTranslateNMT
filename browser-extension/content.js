function removeExistingBubble() {
  const existing = document.getElementById('deeptranslatenmt-bubble');
  if (existing) {
    existing.remove();
  }
}

function createBubble({ originalText, translatedText, sourceLanguage, targetLanguage, qualityScore }) {
  removeExistingBubble();

  const bubble = document.createElement('div');
  bubble.id = 'deeptranslatenmt-bubble';
  bubble.style.position = 'fixed';
  bubble.style.right = '16px';
  bubble.style.bottom = '16px';
  bubble.style.maxWidth = '420px';
  bubble.style.zIndex = '2147483647';
  bubble.style.background = '#0f172a';
  bubble.style.color = '#f8fafc';
  bubble.style.border = '1px solid #334155';
  bubble.style.borderRadius = '12px';
  bubble.style.boxShadow = '0 16px 38px rgba(2, 6, 23, 0.5)';
  bubble.style.padding = '12px';
  bubble.style.fontFamily = "'Segoe UI', sans-serif";

  const quality = typeof qualityScore === 'number' ? `${Math.round(qualityScore * 100)}%` : 'N/A';
  const source = sourceLanguage || 'auto';
  const target = targetLanguage || 'en';

  bubble.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px;">
      <strong style="font-size:13px;">DeepTranslateNMT</strong>
      <button id="deeptranslatenmt-close" style="border:0;background:#1e293b;color:#e2e8f0;border-radius:6px;padding:4px 8px;cursor:pointer;">Close</button>
    </div>
    <div style="font-size:11px;color:#94a3b8;margin-bottom:6px;">${source} -> ${target} | Quality ${quality}</div>
    <div style="font-size:12px;color:#cbd5e1;margin-bottom:6px;white-space:pre-wrap;max-height:80px;overflow:auto;"><em>${originalText}</em></div>
    <div style="font-size:14px;line-height:1.45;white-space:pre-wrap;max-height:180px;overflow:auto;">${translatedText || '(No translation returned)'}</div>
    <div style="display:flex;gap:8px;margin-top:10px;">
      <button id="deeptranslatenmt-copy" style="border:0;background:#2563eb;color:white;border-radius:8px;padding:6px 10px;cursor:pointer;">Copy</button>
    </div>
  `;

  document.body.appendChild(bubble);

  const closeBtn = document.getElementById('deeptranslatenmt-close');
  const copyBtn = document.getElementById('deeptranslatenmt-copy');

  if (closeBtn) {
    closeBtn.addEventListener('click', () => bubble.remove());
  }

  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(translatedText || '');
        copyBtn.textContent = 'Copied';
      } catch (_) {
        copyBtn.textContent = 'Copy failed';
      }
    });
  }

  setTimeout(() => {
    if (bubble.isConnected) {
      bubble.remove();
    }
  }, 20000);
}

const ext = typeof browser !== 'undefined' ? browser : chrome;
ext.runtime.onMessage.addListener((message) => {
  if (message?.type === 'showTranslationBubble' && message.payload) {
    createBubble(message.payload);
  }
});
