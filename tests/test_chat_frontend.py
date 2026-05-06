from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_chat_panel_refreshes_backend_composer_state() -> None:
    panel = (ROOT / "frontend/src/components/ChatPanel.tsx").read_text()

    assert "loadComposerState" in panel
    assert "loadComposerState()" in panel
    assert "window.setInterval(loadComposerState, 1000)" in panel
    assert "[activeSessionId, isStreaming, loadComposerState]" in panel
    assert "status={composerState.status}" in panel
    assert "firstTokenMs={composerState.firstTokenMs}" in panel


def test_chat_composer_shows_stage_and_latency() -> None:
    composer = (ROOT / "frontend/src/components/chat/Composer.tsx").read_text()
    hook = (ROOT / "frontend/src/hooks/useChat.ts").read_text()

    assert "starting Hermes" in composer
    assert "connecting model" in composer
    assert "first token" in composer
    assert "status: state.status" in hook
    assert "firstTokenMs: state.first_token_ms" in hook
