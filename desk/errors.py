class DeskError(Exception):
    """Base error."""


class AuthRequired(DeskError):
    """Fanding session is missing or expired; the user must log in again."""


class SessionUnavailable(DeskError):
    """No usable session state (missing file or decryption key)."""


class PageTimeout(DeskError):
    """A page did not render in time (transient)."""


class DomChanged(DeskError):
    """Expected elements are missing; Fanding markup probably changed."""


class LockedPost(DeskError):
    """The account has no access to this post; it is skipped, never bypassed."""
