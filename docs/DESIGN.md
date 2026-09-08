# Prompt Folio design and information architecture

Prompt Folio is the brand; “a multilingual prompt handbook” is the descriptor. Direct First is a stable entry ID whose visible Chinese name is 先说重点. Categories are user-level, project-level and chat-level (用户级、项目级、对话级). Chat-level entries start a task or game in the current conversation, which may continue over several turns. These scopes do not imply API role priority.

The existing warm off-white / muted green visual system is retained. Rounded geometric icons use the same line weight and grid. The handbook icon identifies the site; sliders denote persistent preferences; the folder denotes a focused project; the document-and-lens icon denotes research reading. A speech bubble identifies chat-level entries, and a twenty-sided die identifies D&D Dungeon Master. Decorative SVGs are hidden from assistive technology; adjacent labels carry their meanings.

Desktop uses three scope cards and a compact rail. Mobile removes redundant scope cards and lays out All plus the three scope filters in a two-column grid. Details expose a “How to use” disclosure before the text and keep copy/download/share actions together. Essential touch targets are at least 44px tall. Long localized headings wrap safely; prompt text is 16px at mobile sizes. Reduced-motion, dark mode and RTL handling remain. Missing translations retain the source text's language, direction and download filename, alongside a notice in the selected interface language.

Source text and readable presentation are separate: headings receive visual emphasis without changing `textContent`. Copy and Markdown downloads use exactly the same source composition. UI labels are never inserted into a single-prompt copy. Combined copies intentionally add localized section headings.

Real static routes exist for languages, scopes, prompt entries and guides. Each page has useful server-rendered content without JavaScript, canonical metadata and alternate language links. JavaScript adds navigation, search and copying without an external runtime dependency. Old hash links remain accepted; a language-only link now opens the library.

See [icon-system.png](icon-system.png) and [the editable social-preview SVG](../assets/social-preview.svg). No third-party font files are distributed.
