# Repository Guidelines

## Project Structure & Module Organization
- docs/: Primary knowledge base. Start at docs/README.md; add topic docs under existing folders (e.g., 04-implementation/mt4-system/).
- MetaQuotes_*/MQL4/: MT4 sources (ignored in git by default). Use Experts/, Indicators/, Scripts/, Presets/ for EA, indicators, scripts, and tester presets.
- 取得データ/, レポート/, メモ/: Data snapshots, reports, and working notes. Avoid committing large binaries unless essential.
- Root .bas files: Excel/VBA helper modules archived alongside research.

## Build, Test, and Development Commands
- MQL4 compile: Open sources (.mq4) in MetaEditor and build to .ex4 (git-ignored). Place code in MetaQuotes_*/MQL4/{Experts|Indicators|Scripts}/.
- Strategy testing: Use MT4 Strategy Tester; store presets in MetaQuotes_*/MQL4/Presets/ and include tester reports/screenshots in PRs when logic changes.
- Docs authoring: Edit Markdown under docs/. No build step required; keep files small and focused.

## Coding Style & Naming Conventions
- Indentation: 4 spaces; no tabs. Max line ~120 chars.
- MQL4: CamelCase for functions (CalculateSignal), ALL_CAPS for constants (MAX_TRADES), snake_case for locals where clearer.
- Filenames: Experts: EA_Name.mq4, Indicators: Indicator_Name.mq4, Scripts: Script_Name.mq4.
- Comments: Brief header with purpose/inputs/side effects. Keep comments bilingual if helpful; prefer concise Japanese for docs.

## Testing Guidelines
- Unit level: Not used; prefer deterministic Strategy Tester runs with fixed symbol/timeframe (e.g., USDJPY H1) and seed.
- Artifacts: Attach tester report (HTML/PNG) and parameter preset (.set). Summarize entry/exit logic verified and edge cases.
- Naming: tests/YYYYMMDD_symbol_timeframe_scenario.*

## Commit & Pull Request Guidelines
- Commit style: Conventional Commits (e.g., docs:, feat:, fix:, refactor:, chore:). Use imperative, present tense.
- Scope examples: docs(04-implementation):, feat(EA_TopFilter):.
- PRs must include: purpose and scope, affected paths, before/after notes, tester evidence for trading logic, and linked issues.

## Security & Configuration Tips
- Do not commit credentials, account numbers, compiled .ex4, logs, or MetaQuotes*/. Respect .gitignore.
- Keep large datasets and tester outputs local; include minimal samples only when necessary.
