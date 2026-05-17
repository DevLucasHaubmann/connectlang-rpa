from __future__ import annotations


class SessionExpiredError(RuntimeError):
    """Raised when the browser session is not authenticated.

    Signals that the bot reached a login page or the vocabulary page
    did not render expected elements. The run must abort — no word
    processing should happen in this state.
    """
