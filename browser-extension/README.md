# DeepTranslateNMT Browser Extension

Offline-capable extension for Chrome, Edge, and Firefox.

## What It Does

- Popup translator UI
- Right-click context menu translation for selected text
- On-page translation bubble with copy button
- Configurable local API URL and defaults

## Offline Mode

This extension can be used without internet after download if:

1. You run the local backend (`python run_api.py`)
2. Models are present locally
3. Extension points to local API URL (default: `http://127.0.0.1:6000`)

Important for Chrome/Edge: port `6000` is blocked (`ERR_UNSAFE_PORT`).
Use port `8000` for extension connectivity.

## Local Development Install

### Chrome / Edge

1. Open extensions page (`chrome://extensions` or `edge://extensions`)
2. Enable Developer mode
3. Click "Load unpacked"
4. Select this folder: `browser-extension`

### Firefox

1. Open `about:debugging`
2. Click "This Firefox"
3. Click "Load Temporary Add-on"
4. Choose `browser-extension/manifest.json`

## User Setup

1. Start backend from project root:
   - PowerShell: `$env:API_PORT=8000; python run_api.py`
2. Open extension options and click "Test Connection"
3. Use popup or right-click selected text on any page

## Package for Distribution

### Chrome / Edge Store Package

Zip the content of `browser-extension` (not parent folder), for example:

```powershell
Compress-Archive -Path browser-extension\* -DestinationPath deeptranslatenmt-extension.zip -Force
```

Upload the generated zip file to Chrome Web Store / Edge Add-ons.

### Firefox Package

Firefox can use the same source with signing via AMO.

## Notes for Publishing

- Add proper PNG icons (16, 32, 48, 128) in `manifest.json` for store listing quality
- Keep permission scope minimal
- For fully offline claims, avoid cloud APIs in backend config
