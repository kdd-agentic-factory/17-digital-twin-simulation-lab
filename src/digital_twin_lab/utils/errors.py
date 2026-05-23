"""Common application errors."""

from __future__ import annotations


class DigitalTwinLabError(Exception):
    """Base application error."""


class ResourceNotFoundError(DigitalTwinLabError):
    """Raised when static catalog data cannot be found."""


class ValidationError(DigitalTwinLabError):
    """Raised when the input is semantically invalid."""
