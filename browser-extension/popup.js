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
  status.textContent = message || '';
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
  document.getElementById('sourceLanguage').value = settings.sourceLanguage;
  document.getElementById('targetLanguage').value = settings.targetLanguage;
  document.getElementById('style').value = settings.style;
  document.getElementById('audience').value = settings.audience;
  return settings;
}

async function translate() {
  const inputText = document.getElementById('inputText').value.trim();
  if (!inputText) {
    setStatus('Enter text to translate.', 'error');
    return;
  }

  setStatus('Translating...');

  const settings = await ext.storage.sync.get(DEFAULT_SETTINGS);
  const sourceLanguage = document.getElementById('sourceLanguage').value;
  const targetLanguage = document.getElementById('targetLanguage').value;
  const style = document.getElementById('style').value;
  const audience = document.getElementById('audience').value;

  try {
    const payload = {
      text: inputText,
      source_language: sourceLanguage === 'auto' ? null : sourceLanguage,
      target_language: targetLanguage,
      style,
      audience,
      use_translation_memory: Boolean(settings.useTranslationMemory),
      return_alternatives: false,
      enable_deep_checks: false
    };

    const response = await ext.runtime.sendMessage({
      type: 'translateInBackground',
      payload: {
        text: inputText,
        overrides: {
          apiBaseUrl: settings.apiBaseUrl,
          sourceLanguage,
          targetLanguage,
          style,
          audience,
          useTranslationMemory: Boolean(settings.useTranslationMemory)
        }
      }
    });

    if (!response?.ok) {
      throw new Error(response?.error || 'Unknown translation error');
    }

    const data = response.result;
    const usedBaseUrl = response.settings?.apiBaseUrl || settings.apiBaseUrl;

    document.getElementById('outputText').value = data.translated_text || '';
    setStatus(`Done | Provider: ${data.provider || 'unknown'} | Quality: ${Math.round((data.quality_score || 0) * 100)}%`, 'success');

    await ext.storage.sync.set({
      apiBaseUrl: usedBaseUrl,
      sourceLanguage,
      targetLanguage,
      style,
      audience
    });
  } catch (error) {
    setStatus(`Could not reach local API. Start backend and verify URL in options. (${error.message})`, 'error');
  }
}

function swapLanguages() {
  const src = document.getElementById('sourceLanguage');
  const tgt = document.getElementById('targetLanguage');
  if (src.value === 'auto') {
    setStatus('Cannot swap when source is Auto Detect.', 'error');
    return;
  }
  const tmp = src.value;
  src.value = tgt.value;
  tgt.value = tmp;
}

async function copyOutput() {
  const output = document.getElementById('outputText').value;
  if (!output) return;
  await navigator.clipboard.writeText(output);
  setStatus('Copied to clipboard.', 'success');
}

function openOptions() {
  ext.runtime.openOptionsPage();
}

window.addEventListener('DOMContentLoaded', async () => {
  fillLanguageSelect('sourceLanguage', true);
  fillLanguageSelect('targetLanguage', false);
  await loadSettings();

  document.getElementById('translateBtn').addEventListener('click', translate);
  document.getElementById('swapBtn').addEventListener('click', swapLanguages);
  document.getElementById('copyBtn').addEventListener('click', copyOutput);
  document.getElementById('openOptionsBtn').addEventListener('click', openOptions);
});
