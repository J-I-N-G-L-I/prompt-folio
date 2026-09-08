# Verification scope — Prompt Folio 3.1.0

Date: 2026-09-08. Baseline repository revision: `329885c293f2e17d978e67308a7b4c6df06ac758`. This update was built and tested locally; it has not been committed, pushed or deployed by the assistant.

## Content and generated outputs

The library contains three scopes and three prompts. Direct First and Paper Mentor retain their existing 16 versions each, unchanged. D&D Dungeon Master contains the complete user-supplied Chinese original: 10,521 characters, with CRLF normalized to LF. Its game instructions are stored as content; they were not executed or independently evaluated as D&D rules.

All 16 interface locales include chat-level labels and usage guidance. Missing D&D translations display a notice and the Chinese source, including the source language and direction on the text. Canonical metadata points to the Chinese entry, and Markdown filenames identify the actual content language. The README includes the complete original once and links to it from missing-language sections.

The generator produces **130 HTML documents and 33 static Markdown exports**, checking **4,090 local links**. The 14 unit tests and Node routing checks passed, covering source escaping, complete texts, scope routes, partial translations, content extension, service mappings and legacy links. A custom-domain fixture verifies generation and canonical links at an origin root; routing tests also cover root-level custom domains and the existing `/prompt-folio/` prefix. No real domain or DNS configuration was changed.

## Browser and visual checks

Playwright 1.57.0 ran against installed headless Chrome on Windows over a real local HTTP server with the project path prefix. It passed:

- 552 viewport inspections at widths of 1440, 820, 390 and 320 pixels;
- 80 deterministic copy-content checks, plus actual Clipboard API read/write, denial and asynchronous-race cases;
- 48 browser-generated Markdown downloads across the 16 interface locales, including source-text fallback downloads;
- nine JavaScript-disabled documents with source-language text and download links;
- scope navigation, cross-language search, old hashes, deep-link reload, missing-translation metadata, dark Arabic RTL and keyboard skip links.

The actual Windows Clipboard API check normalizes native CRLF line endings before comparison. All other copied content must match the source. Static export counts and browser download checks count different things: a missing translation downloads the existing source version.

Chinese desktop and tablet homepages, the Chinese mobile D&D page, and the Arabic-interface D&D fallback page were visually inspected. Local screenshots are in `.test-output/chat-screenshots/` (not committed). The machine-readable [release report](test-report.json) records this run.

## Reproduce

```bash
python tools/build.py
python tools/build.py --check --repository J-I-N-G-L-I/prompt-folio
python tools/test_unit.py
node --check templates/app.js
node tools/test_routes.cjs
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python tools/test_browser.py --report .test-output/browser.json
```

To use an already-installed compatible browser, pass `--browser` with its executable path. To capture screenshots, add `--screenshots .test-output/screenshots`. The workflow installs Chromium and its Linux dependencies, then runs the default HTTP mode. `--memory` is available for restricted environments; record that mode explicitly if used.

## Limits

Hosted GitHub Pages, actual GitHub README rendering, DNS and certificate provisioning, physical devices, and screen-reader certification were not tested. This update does not claim native-speaker translation review or systematic model-effectiveness testing. See [EVALUATION.md](EVALUATION.md). Platform setup references retain their existing source dates; no claim is made that every AI service was signed into during this update.
