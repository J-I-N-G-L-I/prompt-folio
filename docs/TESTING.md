# Verification scope / 核验范围

Date: 2026-09-08 · Build: 2.0.0

## Content and build

The source and generated outputs pass `python tools/build.py --check`. Both entries contain complete bodies in all 16 locales; all 32 bodies occur exactly once in the generated README. Direct First was compared with the prior user-approved version; its bodies are unchanged. The Chinese Paper Mentor export is generated from the same content source.

JavaScript syntax was checked with `node --check templates/app.js`. Node.js is only used for this optional syntax check; it is not a build or deployment requirement.

## Browser tests

The optional Playwright suite completed in Chromium with the self-contained HTML loaded into an **in-memory document**. It checks 16 locales, 2 prompts and 192 combinations of page/viewport inspection at widths 1440, 390 and 320 pixels. It found no horizontal page overflow or duplicate IDs in those checks, and no uncaught JavaScript page errors.

80 copy-content checks compare complete prompt bodies, optional combined text, project starter text and share URLs. **The clipboard transport is simulated**, and the content checks dispatch click events programmatically; selected navigation and fallback tests additionally use browser click actions. This does not verify a physical OS clipboard or all browser permission behaviours.

Search, scoped navigation, browser history, language retention, legacy links, invalid IDs, optional combination, clipboard-denial fallback and late asynchronous clipboard results were checked. **The language storage adapter is simulated** in persistence tests.

Two browser-generated Blob downloads were verified byte-for-byte: an English Paper Mentor and a Chinese combination. Dark-mode Arabic RTL was checked at mobile width. Desktop and mobile screenshots are actual renders of the supplied HTML, not AI-generated interface mockups.

See [machine-readable report](test-report.json) for the completed run. The screenshots delivered alongside the package are representative views, not an exhaustive visual audit of every translated screen.

## Environment limits

The environment blocked localhost HTTP navigation. Testing therefore used in-memory HTML rendering, without bypassing that restriction. No actual GitHub Pages deployment, GitHub README rendering, network resource loading, favicon display in a real browser tab, Apple home-screen behaviour or system clipboard was verified. Complete these checks after publishing.

The interface has access-oriented features but has not undergone a formal accessibility audit or a comprehensive multi-browser / assistive-technology test. Translation text was AI-assisted and has not been independently reviewed by native speakers. No systematic benchmark of prompt effectiveness across models, tasks, disciplines or languages was conducted.

中文要点：程序检查验证了网页逻辑和正文一致性，不能据此声称提示词已经在全部模型中有效，也不能替代上线后的实际设备检查。

## Official setup sources

Routes were checked against the following documentation on the date above. Account eligibility, interface labels and available settings may change; each translated guide retains a primary source link and a general conversation-level fallback.

- [ChatGPT custom instructions](https://help.openai.com/en/articles/8096356)
- [ChatGPT Projects](https://help.openai.com/en/articles/10169521)
- [Claude personalization](https://support.claude.com/en/articles/10185728-understanding-claude-s-personalization-features)
- [Claude project instructions](https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects)
- [Gemini personal instructions](https://support.google.com/gemini/answer/16598625)
- [Gemini Gems](https://support.google.com/gemini/answer/15146780)
- [Microsoft 365 Copilot custom instructions](https://support.microsoft.com/en-us/microsoft-365-copilot/customize-how-microsoft-365-copilot-responds-to-you)
- [Perplexity account settings](https://www.perplexity.ai/help-center/en/articles/10352990-account-settings)
- [Perplexity Projects](https://www.perplexity.ai/help-center/en/articles/10352961-what-are-spaces)

Important distinctions: ChatGPT project instructions override global custom instructions; Gemini personal instructions are not available in Gems. These are reflected in the optional combination guidance. Menu verification came from documentation, not hands-on testing of signed-in accounts on every service.
