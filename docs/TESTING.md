# Verification scope — Prompt Folio 3.1.2

Checked locally on 2026-09-08 against commit `d5ef4e046a9c2da63e4df69b6d8181ddf8efcb8b`. These checks do not certify the hosted GitHub Pages deployment.

The library contains three scopes and three prompts. Direct First and Paper Mentor retain their existing 16 versions each, unchanged. D&D Dungeon Master now includes all 16 locale versions: the unchanged Simplified Chinese original and 15 complete AI translations. No Google Translate or external translation service was used. Translations have not received independent native-speaker review.

Each D&D version contains all 11 numbered chapters, 18 subsections and required save fields. The review covered edition boundaries, natural-roll exceptions, death saves, rest recovery, concentration, player intervention windows and private-state recovery. Identified terminology ambiguities were corrected. The Chinese source remains 10,521 characters, with SHA-256 `b1a42f89dd0c81fb0b1b4aae5dbe52320c8d28bf30fa27462fb1fa297e0fd76f`. Game instructions remain stored content; gameplay effectiveness was not evaluated.

Release 3.1.2 corrects 28 length-guidance paragraphs across all 14 non-Chinese versions. The narrative range remains 400–900 and the first-response limit remains approximately 300, counted directly in local words, Japanese 字 or Korean 자. Chinese-character comparisons were removed. A paragraph-by-paragraph comparison verified that both Chinese versions and all other prompt content remain unchanged; all 16 Markdown exports match the current source exactly.

The generator produces **130 HTML documents and 48 complete Markdown exports**, checking **4,330 local links**. All **16 unit tests**, JavaScript syntax checks and Node routing tests passed. Coverage includes full locale availability, source integrity, text preservation, export bytes, missing-translation fixtures, source escaping, scope routes, content extension and custom-domain roots.

Long prompts over 8,000 characters link to complete localized Markdown exports from the README. The README is checked against GitHub's [500 KiB display limit](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes). Website readers, copying and downloads retain full text; the root HTML also embeds all translations for offline use.

Real local HTTP testing used headless Chromium with the existing project URL prefix:

- **604 viewport checks** at 1440, 820, 390 and 320 pixels, including dark RTL and static pages.
- **80 clipboard checks** for exact content, starters and combinations; denial and asynchronous-race handling were also checked. These use a controlled Clipboard API mock, plus one separate actual Clipboard API round-trip with native Windows CRLF normalization.
- **48 browser-generated Markdown downloads**, checked for exact text and localized filenames.
- All **16 D&D language switches**, with matching text, language attributes, canonical URLs and no fallback notices.
- **22 JavaScript-disabled documents**, including every D&D locale, with complete text, correct direction and static downloads.
- Search, navigation, legacy links, deep-link reloads, sharing and keyboard skip links.

English, Japanese, Hindi and Arabic D&D mobile screenshots were visually inspected for release 3.1.1. Release 3.1.2 changes only text guidance and reruns the complete browser checks above. Local images are in `.test-output/dnd-translation-screenshots/` and are not committed. The machine-readable [release report](test-report.json) records locale lengths, hashes and the browser run.

No remote GitHub workflow, production deployment, DNS change, physical-device certification, screen-reader certification or systematic model-effectiveness evaluation was performed in this session.
