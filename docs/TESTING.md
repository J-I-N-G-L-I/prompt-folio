# Verification scope — Prompt Folio 3.0.0

Date: 2026-09-08. Baseline repository revision: `bb8ec49acf454a207cb63085b1deffa6f88c6f8b`. The remote repository was read; this release was built locally and has **not** been pushed or deployed by the assistant.

## Completed locally

The dependency-free generator validates identity, repository/Pages consistency, all actual locale fields, stable service mappings, composition references, translation source versions and hashes, generated output consistency, and links among generated HTML pages and assets. The two entries retain 16 complete versions each. All 16 Direct First prompt bodies were compared with the prior release and preserved byte-for-byte; its visible names and composition labels were localized. Paper Mentor adds a focused-follow-up rule and optional starter fields in each locale.

The source produces 98 static HTML documents (including root and 404), 32 independent Markdown prompt exports, a sitemap and localized canonical/alternate metadata. Missing future translations are explicitly labeled and point to the source version; a third-entry fixture exercises this path. Counts describe generated artifacts, not the number of distinct prompts.

Content/generator unit tests and Node routing-VM tests verify source escaping, exact text, new entry counts, service reordering, partial translations, prefix-relative links, old hashes and new routes. See the machine-readable [release report](test-report.json) for actual results.

The release run passed **11 content/generator tests, Node routing checks, 412 viewport inspections, 64 copy-content checks, 32 browser-generated Markdown downloads and six JavaScript-disabled documents**. Counts are recorded in the release report.

The Playwright regression was run in Chromium with **in-memory HTML documents**. It checks all 16 locales at 1440, 820, 390 and 320 pixels, prompt text, localized composition, browser-generated Markdown downloads, search aliases, clearing search on language changes, returning to the full handbook, explicit old hash links, language-only homepage links, clipboard denial and asynchronous permission races, keyboard skip links and dark Arabic RTL. Text is copied through a deterministic mock; Blob downloads are produced by the browser. No generated AI replies are used as evidence of effectiveness.

JavaScript-disabled static documents are also checked where reported. No-JS pages expose real text, guides and Markdown links; one-click copy and optional composition require JavaScript.

## Environment limits

Local HTTP navigation is blocked by the execution environment's browser policy. The test harness therefore uses its explicit `--memory` mode locally, without disabling that policy. Actual local HTTP routing is additionally reasoned about in pure Node route tests, but that is not equivalent to network navigation. The supplied Actions workflow runs the harness in its default **real local HTTP mode** after upload; its result is still pending until the user runs the workflow.

Hosted GitHub Pages, actual GitHub README rendering, physical phones, OS-level clipboard integration across browsers, browser-tab favicon caching, Apple home-screen icons and screen-reader certification were not tested. The interface contains accessibility-oriented features but is not certified as WCAG conformant. Native-speaker review and systematic cross-model prompt effectiveness evaluation remain unperformed; see [EVALUATION.md](EVALUATION.md).

## Reproduce

```bash
python tools/build.py
python tools/build.py --check --repository J-I-N-G-L-I/prompt-folio
python tools/test_unit.py
node --check templates/app.js
node tools/test_routes.cjs
python -m pip install -r requirements-dev.txt
python -m playwright install --with-deps chromium
python tools/test_browser.py --report .test-output/browser.json
```

In a restricted environment use `--memory` explicitly, and retain that limitation in any published report. A simulated clipboard result establishes what text would be sent to the clipboard API; it does not establish clipboard behavior on every device.

## Signed-in app testing versus documentation

Platform instructions reference official documentation and carry separate service check dates. Menu availability, account eligibility and rollout may differ. This release did not sign into every AI service. A general conversation-level method is included when settings are unavailable. Source links are listed in [SOURCES.md](SOURCES.md).
