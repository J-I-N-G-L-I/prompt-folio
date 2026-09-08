# Changelog

## 3.1.0 — 2026-09-08

- Added chat-level tasks and games (对话级), with labels and usage guidance in all 16 interface locales, dedicated routes and matching icons.
- Added D&D Dungeon Master 1.0.0 with the complete user-supplied Chinese prompt. Only line endings are normalized; other interface languages explicitly fall back to Chinese.
- Updated desktop scope cards and mobile filters for three scopes. Source-language labels, direction, canonical links and Markdown filenames remain accurate when translations are absent.
- Kept a single complete original in the README for entries without translations, with links from missing-language sections. Existing translated prompt bodies are unchanged.
- Added chat-route, fallback-content and custom-domain-root regression checks, and documented Pages publishing-source and domain configuration.

## 3.0.0 — 2026-09-08

- Completed the Prompt Folio brand and repository/Pages-address migration.
- Localized the Direct First display title in all 16 locales, including 先说重点 and 先說重點; stable IDs and explicit prompt hash links remain compatible.
- Preserved all Direct First prompt bodies. Paper Mentor 1.1.0 adds focused follow-up behavior and optional background/goal/focus/language starters in every locale.
- Shortened mobile navigation; placed usage instructions before the prompt; increased readability and touch targets; moved sharing into the reader toolbar.
- Added cross-language aliases and whitespace/hyphen normalization; switching language clears search; “Back to the handbook” returns all entries.
- Introduced real static paths, localized server-rendered content, canonical/alternate metadata, a sitemap, no-JavaScript content and Markdown exports.
- Split each prompt into an editable source file. Guide references use stable IDs; counts and composition references are data-driven. Missing and stale translations are explicitly labeled.
- Added CI for source identity, local links, routing, content extension and browser regressions. Successful main runs sync generated README/HTML before Pages deployment.
- Added contributor instructions, feedback/translation Issue forms and a clearly labeled evaluation protocol. Human translation review, model-effectiveness experiments and physical-device testing are not claimed.

## Earlier releases

2.0.0 introduced the two-scope handbook. Direct First 1.1.0 preserved the user's revised Chinese writing preference. The original MIT copyright notice remains unchanged.
