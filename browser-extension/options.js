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

const LANGUAGES = [
  { code: 'auto', label: 'Auto Detect' },
  { code: 'en', label: 'English' },
  { code: 'ta', label: 'Tamil' },
  { code: 'te', label: 'Telugu' },
  { code: 'kn', label: 'Kannada' },
  { code: 'ml', label: 'Malayalam' },
  { code: 'hi', label: 'Hindi' }
];

function setStatus(message, type = '') {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = type ? `status ${type}` : 'status';
}

function fillLanguageSelect(id, includeAuto) {
  const select = document.getElementById(id);
  select.innerHTML = '';
  LANGUAGES.forEach((lang) => {
    if (!includeAuto && lang.code === 'auto') return;
    const option = document.createElement('option');
    option.value = lang.code;
    option.textContent = lang.label;
    select.appendChild(option);
  });
}

async function loadSettings() {
  const settings = await ext.storage.sync.get(DEFAULT_SETTINGS);
  document.getElementById('apiBaseUrl').value = settings.apiBaseUrl;
  document.getElementById('sourceLanguage').value = settings.sourceLanguage;
  document.getElementById('targetLanguage').value = settings.targetLanguage;
  document.getElementById('style').value = settings.style;
  document.getElementById('audience').value = settings.audience;
  document.getElementById('useTranslationMemory').checked = Boolean(settings.useTranslationMemory);
}

async function saveSettings() {
  const normalizedApiBaseUrl = normalizeBaseUrl(document.getElementById('apiBaseUrl').value.trim());
  const settings = {
    apiBaseUrl: normalizedApiBaseUrl,
    sourceLanguage: document.getElementById('sourceLanguage').value,
    targetLanguage: document.getElementById('targetLanguage').value,
    style: document.getElementById('style').value,
    audience: document.getElementById('audience').value,
    useTranslationMemory: document.getElementById('useTranslationMemory').checked
  };

  document.getElementById('apiBaseUrl').value = normalizedApiBaseUrl;
  await ext.storage.sync.set(settings);
  setStatus('Settings saved.', 'success');
}

async function testConnection() {
  const apiBaseUrl = normalizeBaseUrl(document.getElementById('apiBaseUrl').value.trim());
  document.getElementById('apiBaseUrl').value = apiBaseUrl;
  setStatus('Testing connection...');

  try {
    const response = await ext.runtime.sendMessage({
      type: 'testConnectionInBackground',
      payload: { apiBaseUrl }
    });

    if (response?.ok) {
      const workingBaseUrl = response.baseUrl || apiBaseUrl;
      if (workingBaseUrl !== apiBaseUrl) {
        document.getElementById('apiBaseUrl').value = workingBaseUrl;
      }
      await ext.storage.sync.set({ apiBaseUrl: workingBaseUrl });
      setStatus(`Connected: ${response.health?.status || 'healthy'} via ${workingBaseUrl}.`, 'success');
      return;
    }

    // If background returned an error, try direct fetch fallback.
    const candidates = buildCandidateBaseUrls(apiBaseUrl);
    for (const baseUrl of candidates) {
      try {
        const directResponse = await fetch(`${baseUrl}/health`, { cache: 'no-store' });
        if (!directResponse.ok) {
          throw new Error(`HTTP ${directResponse.status}`);
        }
        const health = await directResponse.json();
        document.getElementById('apiBaseUrl').value = baseUrl;
        await ext.storage.sync.set({ apiBaseUrl: baseUrl });
        setStatus(`Connected: ${health.status || 'healthy'} via ${baseUrl} (direct fallback).`, 'success');
        return;
      } catch (_) {
        // Try next candidate.
      }
    }

    setStatus(`Connection failed: ${response?.error || 'Unknown error'}`, 'error');
  } catch (error) {
    // Runtime messaging failure fallback.
    const candidates = buildCandidateBaseUrls(apiBaseUrl);
    for (const baseUrl of candidates) {
      try {
        const directResponse = await fetch(`${baseUrl}/health`, { cache: 'no-store' });
        if (!directResponse.ok) {
          throw new Error(`HTTP ${directResponse.status}`);
        }
        const health = await directResponse.json();
        document.getElementById('apiBaseUrl').value = baseUrl;
        await ext.storage.sync.set({ apiBaseUrl: baseUrl });
        setStatus(`Connected: ${health.status || 'healthy'} via ${baseUrl} (direct fallback).`, 'success');
        return;
      } catch (_) {
        // Try next candidate.
      }
    }

    setStatus(`Connection failed: ${error.message}`, 'error');
  }
}

window.addEventListener('DOMContentLoaded', async () => {
  fillLanguageSelect('sourceLanguage', true);
  fillLanguageSelect('targetLanguage', false);
  await loadSettings();

  document.getElementById('saveBtn').addEventListener('click', saveSettings);
  document.getElementById('testBtn').addEventListener('click', testConnection);
});
