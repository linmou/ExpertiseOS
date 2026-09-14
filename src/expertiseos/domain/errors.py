#!/usr/bin/env python3
# Purpose: Define typed failures for consent validation and guarded mutations.


class ConsentError(Exception):
    """Base class for consent-core failures."""


class DomainValidationError(ConsentError, ValueError):
    """Raised when a consent domain value is malformed."""


class CandidateNotFoundError(ConsentError, LookupError):
    """Raised when a proposal is missing or belongs to another interaction."""


class CandidateTransitionError(ConsentError):
    """Raised when a proposal lifecycle transition is illegal."""


class ApprovalRejectedError(ConsentError):
    """Raised when a proposal and actual-user decision do not match exactly."""


class StaleVersionError(ConsentError):
    """Raised when current knowledge versions differ from the approved proposal."""


class ReceiptConflictError(ConsentError):
    """Raised when an operation_id already has a different approval receipt."""


class ReadBackMismatchError(ConsentError):
    """Raised when canonical storage does not match the approved operation."""
