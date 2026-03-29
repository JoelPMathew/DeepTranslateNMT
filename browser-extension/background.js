const ext = typeof browser !== 'undefined' ? browser : chrome;

const DEFAULT_SETTINGS = {
  apiBaseUrl: 'http://127.0.0.1:8000',
  sourceLanguage: 'auto',
  targetLanguage: 'en',
  style: 'formal',
  audience: 'general',
  useTranslationMemory: true
};

function normalizeBaseUrl(rawBaseUrl) {
  let value = (rawBaseUrl || '').trim();
  if (!value) {
    value = DEFAULT_SETTINGS.apiBaseUrl;
  }

  if (!/^https?:\/\//i.test(value)) {
    value = `http://${value}`;
  }

  try {
    const parsed = new URL(value);
    const protocol = parsed.protocol === 'https:' ? 'https:' : 'http:';
    const host = parsed.hostname;
    const port = parsed.port ? `:${parsed.port}` : '';
    return `${protocol}//${host}${port}`;
  } catch (_) {
    return DEFAULT_SETTINGS.apiBaseUrl;
  }
}

function buildCandidateBaseUrls(rawBaseUrl) {
  const normalized = normalizeBaseUrl(rawBaseUrl).replace(/\/$/, '');
  const candidates = [normalized];

  if (normalized.includes('127.0.0.1')) {
    candidates.push(normalized.replace('127.0.0.1', 'localhost'));
  } else if (normalized.includes('localhost')) {
    candidates.push(normalized.replace('localhost', '127.0.0.1'));
  }

  return [...new Set(candidates)];
}

async function getSettings() {
  const stored = await ext.storage.sync.get(DEFAULT_SETTINGS);
  return { ...DEFAULT_SETTINGS, ...stored };
}

async function probeHealth(rawBaseUrl) {
  const candidates = buildCandidateBaseUrls(rawBaseUrl || DEFAULT_SETTINGS.apiBaseUrl);
  let lastError = 'Unknown network error';

  for (const baseUrl of candidates) {
    try {
      const response = await fetch(`${baseUrl}/health`, { cache: 'no-store' });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const health = await response.json();
      return { ok: true, baseUrl, health };
    } catch (error) {
      lastError = error?.message || String(error);
    }
  }

  return { ok: false, error: lastError };
}

async function translateText(text, settings) {
  const payload = {
    text,
    source_language: settings.sourceLanguage === 'auto' ? null : settings.sourceLanguage,
    target_language: settings.targetLanguage,
    style: settings.style,
    audience: settings.audience,
    use_translation_memory: Boolean(settings.useTranslationMemory),
    return_alternatives: false,
    enable_deep_checks: false
  };

  const candidates = buildCandidateBaseUrls(settings.apiBaseUrl);
  let lastError = 'Unknown network error';

  for (const baseUrl of candidates) {
    try {
      const response = await fetch(`${baseUrl}/api/v2/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(`Translation failed (${response.status}): ${body.slice(0, 160)}`);
      }

      return response.json();
    } catch (error) {
      lastError = error?.message || String(error);
    }
  }

  throw new Error(`Local API unreachable on 127.0.0.1/localhost. Last error: ${lastError}`);
}

async function showErrorNotification(message) {
  try {
    await ext.notifications.create({
      type: 'basic',
      iconUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAuMB9oNby2wAAAAASUVORK5CYII=',
      title: 'DeepTranslateNMT',
      message
    });
  } catch (_) {
    // Ignore notification failures silently.
  }
}

ext.runtime.onInstalled.addListener(() => {
  ext.contextMenus.create({
    id: 'deeptranslatenmt-translate-selection',
    title: 'Translate with DeepTranslateNMT',
    contexts: ['selection']
  });
});

ext.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== 'deeptranslatenmt-translate-selection' || !info.selectionText) {
    return;
  }

  const originalText = info.selectionText.trim();
  if (!originalText) {
    return;
  }

  try {
    const settings = await getSettings();
    const result = await translateText(originalText, settings);

    if (tab && typeof tab.id === 'number') {
      await ext.tabs.sendMessage(tab.id, {
        type: 'showTranslationBubble',
        payload: {
          originalText,
          translatedText: result.translated_text || '',
          sourceLanguage: result.source_language || settings.sourceLanguage,
          targetLanguage: result.target_language || settings.targetLanguage,
          qualityScore: result.quality_score
        }
      });
    }
  } catch (error) {
    await showErrorNotification(
      `Could not reach local backend. Start DeepTranslateNMT API and verify URL in options. (${error.message})`
    );
  }
});

ext.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== 'translateInBackground' && message?.type !== 'testConnectionInBackground') {
    return false;
  }

  (async () => {
    try {
      if (message?.type === 'testConnectionInBackground') {
        const probe = await probeHealth(message?.payload?.apiBaseUrl);
        if (probe.ok) {
          sendResponse({ ok: true, baseUrl: probe.baseUrl, health: probe.health });
        } else {
          sendResponse({ ok: false, error: probe.error });
        }
        return;
      }

      const settings = await getSettings();
      const overrides = message?.payload?.overrides || {};
      const mergedSettings = { ...settings, ...overrides };
      const result = await translateText(message?.payload?.text || '', mergedSettings);
      sendResponse({ ok: true, result, settings: mergedSettings });
    } catch (error) {
      sendResponse({ ok: false, error: error.message });
    }
  })();

  return true;
});
