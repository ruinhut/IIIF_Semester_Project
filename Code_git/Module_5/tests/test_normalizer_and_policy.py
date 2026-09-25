"""Tests for canonical rights mappings and conservative policy decisions."""

from __future__ import annotations

import unittest

from iiif_rights_filter.extractor import ExtractedEvidence
from iiif_rights_filter.models import RightsPolicy
from iiif_rights_filter.normalizer import (
    classify_evidence,
    classify_normalized_value,
    normalize_rights_value,
)
from iiif_rights_filter.policy import assess_rights


def baseline_policy() -> RightsPolicy:
    return RightsPolicy(
        policy_version="test-v1",
        category_decisions={
            "public_domain": "allow",
            "open_license": "allow",
            "noncommercial_or_limited": "review",
            "in_copyright": "deny",
            "no_known_copyright": "review",
            "institutional_terms": "review",
            "unknown": "review",
            "conflicting": "review",
        },
    )


class NormalizerTests(unittest.TestCase):
    def test_canonicalizes_known_uri_variants(self) -> None:
        self.assertEqual(
            "https://creativecommons.org/licenses/by/4.0/",
            normalize_rights_value("http://creativecommons.org/licenses/by/4.0/"),
        )
        self.assertEqual(
            "https://rightsstatements.org/vocab/NKC/1.0/",
            normalize_rights_value(
                "https://rightsstatements.org/page/NKC/1.0/?language=en"
            ),
        )

    def test_classifies_supported_and_restricted_terms(self) -> None:
        cases = {
            "https://creativecommons.org/publicdomain/mark/1.0/": "public_domain",
            "https://creativecommons.org/licenses/by-sa/4.0/": "open_license",
            "https://creativecommons.org/licenses/by-nc/4.0/": "noncommercial_or_limited",
            "https://rightsstatements.org/vocab/InC/1.0/": "in_copyright",
            "https://rightsstatements.org/vocab/NKC/1.0/": "no_known_copyright",
            "No known restrictions on use.": "no_known_copyright",
            "https://example.org/terms": "institutional_terms",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(expected, classify_normalized_value(value)[0])


class PolicyTests(unittest.TestCase):
    def evidence(self, raw: str, decisive: bool = True) -> ExtractedEvidence:
        return ExtractedEvidence("rights", "$.rights", raw, decisive, "Manifest")

    def test_open_license_is_allowed(self) -> None:
        assessment = assess_rights(
            [self.evidence("http://creativecommons.org/licenses/by/4.0/")],
            baseline_policy(),
            "2026-09-25T12:00:00+02:00",
        )
        self.assertEqual("open_license", assessment.category)
        self.assertEqual("allow", assessment.decision)

    def test_in_copyright_is_denied(self) -> None:
        assessment = assess_rights(
            [self.evidence("https://rightsstatements.org/vocab/InC/1.0/")],
            baseline_policy(),
            "2026-09-25T12:00:00+02:00",
        )
        self.assertEqual("deny", assessment.decision)

    def test_conflicting_decisive_evidence_requires_review(self) -> None:
        assessment = assess_rights(
            [
                self.evidence("https://creativecommons.org/licenses/by/4.0/"),
                self.evidence("All rights reserved"),
            ],
            baseline_policy(),
            "2026-09-25T12:00:00+02:00",
        )
        self.assertEqual("conflicting", assessment.category)
        self.assertEqual("review", assessment.decision)

    def test_attribution_alone_does_not_imply_permission(self) -> None:
        assessment = assess_rights(
            [self.evidence("Credit Example Library", decisive=False)],
            baseline_policy(),
            "2026-09-25T12:00:00+02:00",
        )
        self.assertEqual("unknown", assessment.category)
        self.assertEqual("review", assessment.decision)

    def test_policy_rejects_missing_categories(self) -> None:
        with self.assertRaises(ValueError):
            RightsPolicy("broken", {"open_license": "allow"})


if __name__ == "__main__":
    unittest.main()
