import React, { useState, useRef, useEffect } from 'react';
import './App.css';

const API_BASE = '/api/v2';

// Main Translation Component
export const TranslationEditor = () => {
  const [sourceText, setSourceText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [sourceLanguage, setSourceLanguage] = useState('ta');
  const [targetLanguage, setTargetLanguage] = useState('en');
  const [style, setStyle] = useState('formal');
  const [audience, setAudience] = useState('general');
  const [glossaryText, setGlossaryText] = useState('');
  const [loading, setLoading] = useState(false);
  const [confidence, setConfidence] = useState(0);
  const [qualityScore, setQualityScore] = useState(0);
  const [alternatives, setAlternatives] = useState([]);
  const [rationale, setRationale] = useState('');
  const [recoverySuggestions, setRecoverySuggestions] = useState([]);
  const [flags, setFlags] = useState([]);
  const [backTranslation, setBackTranslation] = useState('');
  const [errorText, setErrorText] = useState('');
  const [useTranslationMemory, setUseTranslationMemory] = useState(true);
  const [recoveryStatus, setRecoveryStatus] = useState('');

  const parseGlossary = (input) => {
    const entries = {};
    input
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .forEach((line) => {
        const separator = line.includes('=') ? '=' : line.includes(':') ? ':' : null;
        if (!separator) return;
        const [source, target] = line.split(separator).map((part) => part.trim());
        if (source && target) {
          entries[source] = target;
        }
      });
    return entries;
  };

  const buildFallbackRecoverySuggestions = ({
    text,
    quality,
    selectedAudience,
    selectedStyle,
    cacheEnabled,
    glossary,
    translated,
  }) => {
    const suggestions = [];
    const lowerText = (text || '').toLowerCase();

    if (!translated || !translated.trim()) {
      suggestions.push('No translation text returned. Retry once and switch target language to verify provider health.');
    }

    if ((quality ?? 0) < 0.65) {
      suggestions.push('Low quality detected. Use shorter sentences and avoid idioms, then retry.');
    }

    if (cacheEnabled) {
      suggestions.push('Disable translation memory cache and retry to force a fresh translation.');
    }

    if (selectedAudience !== 'technical' && /(bank|charge|lead|light|right|fair|bat)\b/.test(lowerText)) {
      suggestions.push('Ambiguous term detected. Switch Audience Mode to Technical and add context.');
    }

    if (!glossary.trim()) {
      suggestions.push('Add glossary lock terms for business/domain words before retrying.');
    }

    if (selectedStyle === 'casual') {
      suggestions.push('If tone feels off, switch style to Neutral or Formal and retry.');
    }

    if (!suggestions.length) {
      suggestions.push('Retry with Technical audience and glossary lock to improve consistency.');
    }

    return suggestions;
  };

  const submitTranslation = async (overrides = {}) => {
    const text = (overrides.sourceText ?? sourceText).trim();
    if (!text) return;
    setLoading(true);
    setErrorText('');
    setRecoveryStatus('');
    try {
      const response = await fetch(`${API_BASE}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          source_language: overrides.sourceLanguage ?? sourceLanguage,
          target_language: overrides.targetLanguage ?? targetLanguage,
          style: overrides.style ?? style,
          audience: overrides.audience ?? audience,
          glossary_terms: parseGlossary(overrides.glossaryText ?? glossaryText),
          return_alternatives: false,
          enable_deep_checks: false,
          use_translation_memory: overrides.useTranslationMemory ?? useTranslationMemory,
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Translation failed');
      }

      const data = await response.json();
      setTranslatedText(data.translated_text || '');
      setConfidence(data.confidence || 0);
      setQualityScore(data.quality_score || 0);
      setAlternatives(data.alternatives || []);
      setRationale(data.rationale || '');
      const backendSuggestions = Array.isArray(data.recovery_suggestions) ? data.recovery_suggestions : [];
      const fallbackSuggestions = buildFallbackRecoverySuggestions({
        text,
        quality: data.quality_score,
        selectedAudience: overrides.audience ?? audience,
        selectedStyle: overrides.style ?? style,
        cacheEnabled: overrides.useTranslationMemory ?? useTranslationMemory,
        glossary: overrides.glossaryText ?? glossaryText,
        translated: data.translated_text,
      });
      setRecoverySuggestions(backendSuggestions.length ? backendSuggestions : fallbackSuggestions);
      setFlags(data.flags || []);
      setBackTranslation(data.back_translation || '');
    } catch (error) {
      console.error('Translation error:', error);
      setErrorText(error.message || 'Translation error.');
      setRecoverySuggestions([
        'Translation request failed. Check backend service status and retry.',
        'Try disabling cache and switching style to Neutral for a clean attempt.',
      ]);
    }
    setLoading(false);
  };

  const handleTranslate = async () => {
    await submitTranslation();
  };

  const applyRecoverySuggestion = async (tip) => {
    const lower = tip.toLowerCase();
    const overrides = {};
    let message = 'Applied suggestion and retried translation.';

    if (lower.includes('disable cache') || lower.includes('fresh translation')) {
      setUseTranslationMemory(false);
      overrides.useTranslationMemory = false;
      message = 'Cache disabled for a fresh translation.';
    }

    if (lower.includes('shorter sentences')) {
      const chunks = sourceText
        .split(/[;,.!?]/)
        .map((s) => s.trim())
        .filter(Boolean);
      if (chunks.length > 1) {
        const shortened = chunks.slice(0, 2).join('. ') + '.';
        setSourceText(shortened);
        overrides.sourceText = shortened;
        message = 'Source text shortened and retried.';
      } else {
        setStyle('neutral');
        overrides.style = 'neutral';
        message = 'Switched to neutral style to reduce phrasing risk.';
      }
    }

    if (lower.includes('add context') || lower.includes('ambiguous term')) {
      setAudience('technical');
      overrides.audience = 'technical';
      message = 'Audience changed to technical for clearer disambiguation.';
    }

    if (lower.includes('glossary')) {
      if (!glossaryText.trim()) {
        const starter = 'bank = financial institution';
        setGlossaryText(starter);
        overrides.glossaryText = starter;
      }
      message = 'Glossary guidance applied. Edit terms if needed and retry executed.';
    }

    setRecoveryStatus(message);
    await submitTranslation(overrides);
  };

  return (
    <div className="translation-editor">
      <div className="editor-section source-section">
        <div className="advanced-controls">
          <label>
            Audience Mode
            <select value={audience} onChange={(e) => setAudience(e.target.value)}>
              <option value="general">General</option>
              <option value="student">Student</option>
              <option value="professional">Professional</option>
              <option value="marketing">Marketing</option>
              <option value="technical">Technical</option>
            </select>
          </label>

          <label>
            Style
            <select value={style} onChange={(e) => setStyle(e.target.value)}>
              <option value="formal">Formal</option>
              <option value="neutral">Neutral</option>
              <option value="casual">Casual</option>
            </select>
          </label>
        </div>

        <select value={sourceLanguage} onChange={(e) => setSourceLanguage(e.target.value)}>
          <option value="ta">Tamil (தமிழ்)</option>
          <option value="te">Telugu (తెలుగు)</option>
          <option value="kn">Kannada (ಕನ್ನಡ)</option>
          <option value="ml">Malayalam (മലയാളം)</option>
          <option value="hi">Hindi (हिन्दी)</option>
          <option value="en">English</option>
        </select>
        <textarea
          className="main-input"
          value={sourceText}
          onChange={(e) => setSourceText(e.target.value)}
          placeholder="Enter text to translate..."
        />

        <textarea
          className="glossary-input"
          value={glossaryText}
          onChange={(e) => setGlossaryText(e.target.value)}
          placeholder="Glossary lock (one per line):\nAzure = Azure\nService Bus = Service Bus"
        />

        <label className="memory-toggle">
          <input
            type="checkbox"
            checked={useTranslationMemory}
            onChange={(e) => setUseTranslationMemory(e.target.checked)}
          />
          Use translation memory (cache)
        </label>
      </div>

      <button onClick={handleTranslate} disabled={loading} className="translate-btn">
        {loading ? 'Translating...' : 'Translate'}
      </button>

      <div className="editor-section target-section">
        <select value={targetLanguage} onChange={(e) => setTargetLanguage(e.target.value)}>
          <option value="en">English</option>
          <option value="ta">Tamil (தமிழ்)</option>
          <option value="te">Telugu (తెలుగు)</option>
          <option value="kn">Kannada (ಕನ್ನಡ)</option>
          <option value="ml">Malayalam (മലയാളം)</option>
          <option value="hi">Hindi (हिन्दी)</option>
        </select>
        <textarea
          className="main-output"
          value={translatedText}
          readOnly
          placeholder="Translation will appear here..."
        />
        <div className="confidence">Confidence: {(confidence * 100).toFixed(1)}%</div>
        <div className="confidence quality">Quality Score: {(qualityScore * 100).toFixed(1)}%</div>
      </div>

      <div className="insights-panel">
        {rationale && <p><strong>Rationale:</strong> {rationale}</p>}
        {backTranslation && <p><strong>Back-Translation Check:</strong> {backTranslation}</p>}

        {flags.length > 0 && (
          <div className="flags-box">
            <h4>Quality Flags</h4>
            <ul>
              {flags.map((flag, idx) => (
                <li key={`${flag}-${idx}`}>{flag}</li>
              ))}
            </ul>
          </div>
        )}

        {alternatives.length > 0 && (
          <div className="alternatives-box">
            <h4>Alternative Renderings</h4>
            <ul>
              {alternatives.map((alt, idx) => (
                <li key={`${alt}-${idx}`}>{alt}</li>
              ))}
            </ul>
          </div>
        )}

        {recoverySuggestions.length > 0 && (
          <div className="recovery-box">
            <h4>Error Recovery Suggestions</h4>
            <ul>
              {recoverySuggestions.map((tip, idx) => (
                <li className="recovery-item" key={`${tip}-${idx}`}>
                  <span>{tip}</span>
                  <button
                    type="button"
                    className="apply-suggestion-btn"
                    onClick={() => applyRecoverySuggestion(tip)}
                    disabled={loading}
                  >
                    Apply
                  </button>
                </li>
              ))}
            </ul>
            <p className="recovery-hint">
              Example implementation: clicking Apply adjusts settings from this suggestion and retries automatically.
            </p>
          </div>
        )}

        {recoveryStatus && <div className="recovery-status">{recoveryStatus}</div>}

        {errorText && <div className="error-box">{errorText}</div>}
      </div>
    </div>
  );
};

// Document Translation Component
export const DocumentTranslator = () => {
  const [file, setFile] = useState(null);
  const [sourceLanguage, setSourceLanguage] = useState('ta');
  const [targetLanguage, setTargetLanguage] = useState('en');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef();

  const handleFileSelect = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_language', sourceLanguage);
    formData.append('target_language', targetLanguage);

    try {
      const response = await fetch(`${API_BASE}/translate/document`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Upload error:', error);
    }
    setUploading(false);
  };

  return (
    <div className="document-translator">
      <h2>📄 Document Translation</h2>
      
      <div className="upload-section">
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept=".pdf,.docx,.txt,.md,.json"
          style={{ display: 'none' }}
        />
        <button onClick={() => fileInputRef.current.click()} className="upload-btn">
          Choose File
        </button>
        {file && <span>{file.name}</span>}
      </div>

      <div className="language-select">
        <select value={sourceLanguage} onChange={(e) => setSourceLanguage(e.target.value)}>
          <option value="ta">Tamil</option>
          <option value="te">Telugu</option>
          <option value="en">English</option>
        </select>
        <span>→</span>
        <select value={targetLanguage} onChange={(e) => setTargetLanguage(e.target.value)}>
          <option value="en">English</option>
          <option value="ta">Tamil</option>
          <option value="te">Telugu</option>
        </select>
      </div>

      <button onClick={handleUpload} disabled={!file || uploading} className="translate-btn">
        {uploading ? 'Translating...' : 'Translate Document'}
      </button>

      {result && (
        <div className="result">
          <h3>✅ Translation Complete</h3>
          <p>Segments: {result.segments_count}</p>
          <a href={result.download_url || `${API_BASE}/outputs/${result.output_file}`} download>
            Download Translated File
          </a>
        </div>
      )}
    </div>
  );
};

// Speech Translation Component
export const SpeechTranslator = () => {
  const [file, setFile] = useState(null);
  const [sourceLanguage, setSourceLanguage] = useState('en-US');
  const [targetLanguage, setTargetLanguage] = useState('ta-IN');
  const [translating, setTranslating] = useState(false);
  const [recognizedText, setRecognizedText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [liveTranslation, setLiveTranslation] = useState('');
  const [liveStatus, setLiveStatus] = useState('Idle');
  const fileInputRef = useRef();
  const recognitionRef = useRef(null);

  const toTextLanguageCode = (speechCode) => {
    if (!speechCode) return 'en';
    return speechCode.split('-')[0].toLowerCase();
  };

  const translateLiveSegment = async (segment) => {
    const clean = segment.trim();
    if (!clean) return;

    try {
      const response = await fetch(`${API_BASE}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: clean,
          source_language: toTextLanguageCode(sourceLanguage),
          target_language: toTextLanguageCode(targetLanguage),
          style: 'neutral',
          audience: 'general',
          glossary_terms: {},
          return_alternatives: false,
          enable_deep_checks: false,
          use_translation_memory: true,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Live translation failed');
      }

      const translated = (data.translated_text || '').trim();
      if (!translated) return;

      setLiveTranslation((prev) => (prev ? `${prev} ${translated}` : translated));
      setTranslatedText((prev) => (prev ? `${prev} ${translated}` : translated));
    } catch (err) {
      setError(err.message || 'Live translation failed');
    }
  };

  const stopLiveTranslation = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
    setLiveStatus('Stopped');
  };

  const startLiveTranslation = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError('Live speech is not supported in this browser. Try Chrome or Edge.');
      return;
    }

    setError('');
    setLiveStatus('Listening...');

    if (!recognitionRef.current) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = async (event) => {
        let interim = '';
        let finalized = '';

        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          const chunk = event.results[i][0]?.transcript || '';
          if (event.results[i].isFinal) {
            finalized += `${chunk} `;
          } else {
            interim += chunk;
          }
        }

        if (finalized.trim()) {
          setLiveTranscript((prev) => `${prev}${prev ? ' ' : ''}${finalized.trim()}`);
          setRecognizedText((prev) => `${prev}${prev ? ' ' : ''}${finalized.trim()}`);
          await translateLiveSegment(finalized);
        } else {
          setLiveStatus(`Listening... ${interim}`);
        }
      };

      recognition.onerror = (event) => {
        setError(`Live speech error: ${event.error}`);
        setIsListening(false);
        setLiveStatus('Error');
      };

      recognition.onend = () => {
        setIsListening(false);
        setLiveStatus((prev) => (prev === 'Error' ? prev : 'Stopped'));
      };

      recognitionRef.current = recognition;
    }

    recognitionRef.current.lang = sourceLanguage;
    recognitionRef.current.start();
    setIsListening(true);
  };

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const handleFileSelect = (e) => {
    const selected = e.target.files?.[0] || null;
    setFile(selected);
    setRecognizedText('');
    setTranslatedText('');
    setConfidence(0);
    setError('');
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl('');
    }
  };

  const handleSpeechTranslate = async () => {
    if (!file) return;
    setTranslating(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const params = new URLSearchParams({
        source_language: sourceLanguage,
        target_language: targetLanguage,
      });

      const response = await fetch(`${API_BASE}/speech/translate?${params.toString()}`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Speech translation failed');
      }

      setRecognizedText(data.original_text || '');
      setTranslatedText(data.translated_text || '');
      setConfidence(data.confidence || 0);
    } catch (err) {
      setError(err.message || 'Speech translation failed');
    } finally {
      setTranslating(false);
    }
  };

  const handleGenerateAudio = async () => {
    if (!translatedText.trim()) return;
    setError('');

    try {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
        setAudioUrl('');
      }

      const ttsLanguage = targetLanguage.split('-')[0] || 'en';
      const params = new URLSearchParams({
        text: translatedText,
        language: ttsLanguage,
      });

      const response = await fetch(`${API_BASE}/speech/synthesize?${params.toString()}`, {
        method: 'POST',
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Speech synthesis failed');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
    } catch (err) {
      setError(err.message || 'Speech synthesis failed');
    }
  };

  return (
    <div className="document-translator speech-translator">
      <h2>🎤 Speech Translation</h2>

      <div className="upload-section">
        <input
          ref={fileInputRef}
          type="file"
          accept=".wav,.mp3,.flac,.ogg,.m4a"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        <button type="button" onClick={() => fileInputRef.current?.click()} className="upload-btn">
          Choose Audio
        </button>
        {file && <span>{file.name}</span>}
      </div>

      <div className="live-card">
        <div className="live-header">
          <h3>Live Microphone Translation</h3>
          <span className={`live-pill ${isListening ? 'on' : 'off'}`}>{liveStatus}</span>
        </div>
        <div className="live-actions">
          <button
            type="button"
            className="upload-btn"
            onClick={startLiveTranslation}
            disabled={isListening}
          >
            Start Live
          </button>
          <button
            type="button"
            className="upload-btn"
            onClick={stopLiveTranslation}
            disabled={!isListening}
          >
            Stop Live
          </button>
        </div>
        <p className="live-note">Speak continuously. Finalized phrases are translated automatically in near real-time.</p>
      </div>

      <div className="language-select">
        <select value={sourceLanguage} onChange={(e) => setSourceLanguage(e.target.value)}>
          <option value="en-US">English (US)</option>
          <option value="ta-IN">Tamil (IN)</option>
          <option value="te-IN">Telugu (IN)</option>
          <option value="hi-IN">Hindi (IN)</option>
        </select>
        <span>→</span>
        <select value={targetLanguage} onChange={(e) => setTargetLanguage(e.target.value)}>
          <option value="en-US">English (US)</option>
          <option value="ta-IN">Tamil (IN)</option>
          <option value="te-IN">Telugu (IN)</option>
          <option value="hi-IN">Hindi (IN)</option>
        </select>
      </div>

      <button type="button" onClick={handleSpeechTranslate} disabled={!file || translating} className="translate-btn">
        {translating ? 'Translating Audio...' : 'Translate Speech'}
      </button>

      <div className="speech-results">
        <div className="speech-result-block">
          <h3>Recognized Text</h3>
          <p>{liveTranscript || recognizedText || 'Recognized speech will appear here...'}</p>
        </div>
        <div className="speech-result-block">
          <h3>Translated Text</h3>
          <p>{liveTranslation || translatedText || 'Translated text will appear here...'}</p>
        </div>
      </div>

      <div className="confidence">Confidence: {(confidence * 100).toFixed(1)}%</div>

      <div className="speech-actions">
        <button
          type="button"
          className="upload-btn"
          onClick={handleGenerateAudio}
          disabled={!translatedText.trim()}
        >
          Generate Audio
        </button>
        {audioUrl && <audio controls src={audioUrl} className="speech-audio-player" />}
      </div>

      {error && <div className="error-box">{error}</div>}
    </div>
  );
};

// Main App Component
export default function App() {
  const [activeTab, setActiveTab] = useState('translate');

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-brand">
          <h1>🧠 DeepTranslateNMT</h1>
          <p className="tagline">Neural Machine Translation • Real-Time Speech • Advanced Quality Assurance</p>
        </div>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'translate' ? 'active' : ''}
          onClick={() => setActiveTab('translate')}
        >
          📝 Translate
        </button>
        <button
          className={activeTab === 'documents' ? 'active' : ''}
          onClick={() => setActiveTab('documents')}
        >
          📄 Documents
        </button>
        <button
          className={activeTab === 'speech' ? 'active' : ''}
          onClick={() => setActiveTab('speech')}
        >
          🎤 Speech
        </button>
      </nav>

      <main className="content">
        {activeTab === 'translate' && <TranslationEditor />}
        {activeTab === 'documents' && <DocumentTranslator />}
        {activeTab === 'speech' && <SpeechTranslator />}
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <p>© 2026 DeepTranslateNMT • Cutting-Edge Neural Machine Translation Platform</p>
          <p className="footer-features">Speech Translation • Document Processing • Real-Time Collaboration • Quality Guardrails</p>
        </div>
      </footer>
    </div>
  );
}
