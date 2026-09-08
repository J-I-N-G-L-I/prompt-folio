# Prompt Folio design and information architecture

Prompt Folio is the brand; “a multilingual prompt handbook” is the descriptor. Direct First is a stable entry ID whose visible Chinese name is 先说重点. Main categories remain user-level and project-level; they describe intended scope and do not imply API role priority.

The existing warm off-white / muted green visual system is retained. Rounded geometric icons use the same line weight and grid. The handbook icon identifies the site; sliders denote persistent preferences; the folder denotes a focused project; the document-and-lens icon denotes research reading. Decorative SVGs are hidden from assistive technology; adjacent labels carry their meanings.

Desktop retains scope cards and a compact rail. Mobile removes redundant scope cards while preserving the scope navigation. The first actual prompt appears substantially earlier than in version 2. Details expose a “How to use” disclosure before the text and keep copy/download/share actions together. Essential touch targets are at least 44px tall. Long localized headings wrap safely; prompt text is 16px at mobile sizes. Reduced-motion, dark mode and RTL handling remain.

Source text and readable presentation are separate: headings receive visual emphasis without changing `textContent`. Copy and Markdown downloads use exactly the same source composition. UI labels are never inserted into a single-prompt copy. Combined copies intentionally add localized section headings.

Real static routes exist for languages, scopes, prompt entries and guides. Each page has useful server-rendered content without JavaScript, canonical metadata and alternate language links. JavaScript adds navigation, search and copying without an external runtime dependency. Old hash links remain accepted; a language-only link now opens the library.

See [icon-system.png](icon-system.png) and [the editable social-preview SVG](../assets/social-preview.svg). No third-party font files are distributed.
