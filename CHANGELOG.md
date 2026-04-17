# Changelog

All notable changes to hermes-hudui are documented here.

## [Unreleased]

---

## [0.5.0] — 2026-04-17

### Added
- **Sudo tab** — surfaces sudo governance and command history from existing data. Shows approval mode, timeout, command allowlist, and security settings (from `config.yaml`); usage statistics broken down by approved/failed/blocked with a daily sparkline and subcommand type breakdown; scrollable command history extracted from `state.db` tool-output messages via FTS. Closes #14.
- **Regenerate button** — re-run the last message in chat using the AI SDK's regenerate helper; button appears after each completed assistant response.
- **Vercel AI SDK Data Stream Protocol** — replaced the custom SSE chat implementation with the AI SDK's data stream protocol for more robust streaming and future-proofing.

### Fixed
- **WebSocket / StaticFiles mount crash** — WebSocket upgrade scopes no longer fall through to the `StaticFiles` catch-all, preventing a startup crash on certain deployment configurations.
- **Vite dev proxy for `/ws`** — WebSocket connections are now correctly proxied through the Vite dev server to the backend (`:3001`), so live-reload and HUD updates work in dev mode.
- **macOS MallocStackLogging warning** — suppressed the noisy `MallocStackLogging` warning emitted on macOS when spawning subprocesses. Closes #15.
- **zsh extras install hint** — `[tui]` and `[chat]` extras are now quoted in install instructions and error messages to prevent zsh glob expansion.
- **ChatNotAvailableError message** — tightened to a single clear line.

### Performance
- **Chat streaming** — switched to `read1()` for chunked reads and tightened the frontend render throttle, reducing perceived latency on long responses.

---

## [0.4.0] — 2026-04-14

### Added
- **i18n — English + Chinese language support** — every UI string across all 13 tabs is translated. A language toggle button in the header bar switches instantly; choice persists to localStorage.
- **Chat responds in selected language** — when the UI is set to Chinese, chat messages include a language hint so the agent responds in Chinese.
- **Language toggle** — bordered button after the clock in the header, always visible regardless of tab overflow.

### Changed
- Default host binding changed from `0.0.0.0` to `127.0.0.1` for security (contributed by @shivanraptor).

---

## [0.3.1] — 2026-04-12

### Added
- **Chat history persistence** — messages and sessions survive page refresh via localStorage. On server restart, backend sessions are re-created and message history migrated automatically.

### Fixed
- **Corrections tab — session corrections were always empty** — a dead REGEXP loop in the collector fired a `cursor.execute()` that SQLite can't handle (no built-in REGEXP support), throwing an `OperationalError` that silently aborted the function before the LIKE-based queries could run. Fixed by removing the dead loop, collapsing the 8 individual LIKE queries into one OR query, and moving `conn.close()` into a `finally` block.

---

## [0.3.0] — 2026-04-12

### Added
- **Tool call visibility** — chat responses now show tool call cards (web_search, terminal, etc.) with arguments after the response finishes
- **Reasoning display** — agent thinking/reasoning blocks appear as collapsible "Thinking" sections in chat
- **Memory editing** — inline edit, delete, and add entries directly in the Memory tab (both Agent Memory and User Profile)
- **Session transcript viewer** — click any session in the Sessions tab to read the full conversation in a modal with markdown rendering and per-message token counts
- **Session search** — search bar searches session titles and full message content (FTS), results show match type and a content snippet

### Fixed
- HUD-generated chat sessions (`--source tool`) no longer appear in the Sessions tab or search results

---

## [0.2.0] — Chat + New Tabs

### Added
- **Chat tab** — Live chat with your Hermes agent
  - Multiple sessions, each with independent message history
  - Responses stream in real time (SSE)
  - Markdown rendering — headers, lists, tables, code blocks
  - Syntax-highlighted code with a copy button on hover
  - Stop button cancels a response mid-stream
  - Tool call cards and reasoning display (when agent uses tools)
- **Corrections tab** — View corrections grouped by severity (critical / major / minor)
- **Patterns tab** — Task clusters, hourly activity heatmap, repeated prompts

### Fixed
- Chat system warnings (context compression notices) no longer appear in responses
- Chat sessions are fully independent — switching sessions no longer shows the same messages
- Chat output preserves formatting and line breaks

---

## [0.1.0] — Initial Release

### Added
- **Dashboard** — Identity, stats, memory bars, service health, skills, projects, cron jobs, tool usage, daily sparkline
- **Memory** — Agent memory and user profile with capacity bars
- **Skills** — Category chart, skill details, custom skill badges
- **Sessions** — Session history with message/token counts and sparklines
- **Cron** — Scheduled jobs with schedule, status, and prompt preview
- **Projects** — Repos grouped by activity, branch info, language detection
- **Health** — API key status, service health with PIDs
- **Agents** — Live processes, operator alerts, recent session history
- **Profiles** — Full profile cards with model, provider, soul summary, toolsets
- **Costs** — Per-model USD estimates, daily trend, token breakdown
- **Real-time updates** — WebSocket broadcasts changes instantly, no manual refresh
- **Smart caching** — Automatic cache invalidation when agent files change
- **Four themes** — Neural Awakening, Blade Runner, fsociety, Anime
- **CRT scanlines** — Optional overlay
- **Command palette** — `Ctrl+K` to jump anywhere
- **Boot screen** — One-time animated startup sequence
- **Keyboard shortcuts** — `1`–`9`, `0` for tabs; `t` for themes
