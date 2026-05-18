from __future__ import annotations


class SessionExpiredError(RuntimeError):
    """Raised when the browser session is not authenticated.

    Signals that the bot reached a login page or the vocabulary page
    did not render expected elements. The run must abort — no word
    processing should happen in this state.
    """


class WordPersistenceError(RuntimeError):
    """Raised when a word cannot be confirmed in the vocabulary list after submission.

    Signals that the submit action appeared to succeed (form closed) but the word
    was not found when re-checking the vocabulary page. The run continues with the
    next word; the failure is logged and screenshotted.
    """
