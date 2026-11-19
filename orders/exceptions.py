from django.core.exceptions import ValidationError


class CheckoutConflict(Exception):
    """The same checkout key was reused with different content."""


class InsufficientStock(ValidationError):
    """Requested inventory is no longer available."""
