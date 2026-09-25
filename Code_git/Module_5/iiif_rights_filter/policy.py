"""Combine classified rights evidence and apply a versioned project policy."""

from __future__ import annotations

from typing import Iterable

from .extractor import ExtractedEvidence
from .models import RightsAssessment, RightsEvidence, RightsPolicy
from .normalizer import classify_evidence


def assess_rights(
    extracted: Iterable[ExtractedEvidence],
    policy: RightsPolicy,
    assessed_at: str,
) -> RightsAssessment:
    """Classify all evidence and produce one conservative Manifest decision."""

    evidence = [classify_evidence(item) for item in extracted]
    effective_categories = sorted(
        {item.category for item in evidence if item.decisive}
    )

    reason_codes: list[str] = []
    if not effective_categories:
        category = "unknown"
        reason_codes.append("no_decisive_rights_evidence")
    elif len(effective_categories) == 1:
        category = effective_categories[0]
        reason_codes.append("single_effective_category")
    else:
        category = "conflicting"
        reason_codes.append("multiple_effective_categories")

    decision = policy.category_decisions[category]
    reason_codes.append(f"policy_decision_{decision}")
    return RightsAssessment(
        category=category,
        decision=decision,
        policy_version=policy.policy_version,
        policy_rule=f"category_decisions.{category}",
        assessed_at=assessed_at,
        evidence=evidence,
        effective_categories=effective_categories,
        reason_codes=reason_codes,
    )


def assessment_error(
    policy: RightsPolicy,
    assessed_at: str,
    reason_code: str,
) -> RightsAssessment:
    """Create a review result when raw Manifest evidence cannot be trusted."""

    return RightsAssessment(
        category="unknown",
        decision="review",
        policy_version=policy.policy_version,
        policy_rule="operational_guard.review",
        assessed_at=assessed_at,
        evidence=[],
        effective_categories=[],
        reason_codes=[reason_code, "operational_guard_review"],
    )
