# Contributing to Prompt Folio

Small, specific improvements are welcome: clearer translations, reproducible failure cases, more accurate service setup instructions, and well-scoped prompts. Keep the handbook easy to read and copy.

## Where to edit

`content/library.json` contains site identity, UI strings and setup guides. Each prompt has its own file under `content/prompts/`. Add a new file to `promptFiles` in `content/library.json`. Keep stable IDs in English slugs; translate visible titles. `README.md` and the root `index.html` are generated.

Use a branch and pull request. Changes to prompt text should include a version bump, a source-language revision, and translation status updates. Preserve the original copyright notice in `LICENSE`.

## Translations

Current prompts have 16 locale versions. New entries may start with fewer translations; the site explicitly identifies a source-language fallback. Missing translations are never silently labeled complete. A translated title is part of the localized text.

Every translation records `sourceVersion`, a SHA-256 `sourceHash`, and a status. A source edit automatically marks unmatched translations as stale. Use `python tools/translation.py --help` to stamp only translations you have actually updated. Mark a translation `reviewed` only after a named human has checked it, with their permission for public attribution. AI-generated text remains `ai-assisted`.

## Prompt changes

State the scope, required input, intended behavior and limits. Prefer minimal, justified changes. Do not describe a user-supplied prompt as having elevated system privileges. Keep necessary uncertainty and evidence safeguards. Include a follow-up behavior when a large workflow may otherwise overwhelm narrow questions.

## Reproducible feedback

Provide prompt ID, content version, language, service, displayed model name, date, user input, relevant output and other active instructions. Remove confidential information and sensitive personal or medical data. Distinguish a single example from systematic evaluation. See [the evaluation protocol](docs/EVALUATION.md).

## Local checks

```bash
python tools/build.py
python tools/build.py --check
python tools/test_unit.py
node --check templates/app.js
node tools/test_routes.cjs
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python tools/test_browser.py
```

The default test mode starts a local HTTP server under the same project-path prefix as Pages. `--memory --browser /path/to/chromium` is an explicitly limited mode for restricted environments. Do not describe memory-mode tests as a live deployment test.

## Automation and review

Pull requests build and test without write or deploy permissions. Successful `main` runs synchronize only the three generated files, then deploy the tested `_site/` artifact. No personal token is required. The workflow never force-pushes. Protected branches can use locally generated outputs in a reviewed PR; see the deployment guide.
