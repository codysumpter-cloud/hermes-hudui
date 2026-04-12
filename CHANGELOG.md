# Changelog

All notable changes to hermes-hudui are documented here.

## [Unreleased]

### Added
- **Session transcript viewer** — click any session in the Sessions tab to read the full conversation in a modal with markdown rendering and per-message token counts
- **Session search** — search bar searches session titles and full message content (FTS), results show match type and a content snippet

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
