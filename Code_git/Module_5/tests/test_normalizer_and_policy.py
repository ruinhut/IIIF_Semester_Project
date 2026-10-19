"""Tests for canonical rights mappings and public-reuse decisions."""

from __future__ import annotations

import unittest

from iiif_rights_filter.extractor import ExtractedEvidence
from iiif_rights_filter.models import RightsPolicy
from iiif_rights_filter.normalizer import (
    classify_normalized_value,
    normalize_rights_value,
)
from iiif_rights_filter.policy import assess_rights


def automatic_policy() -> RightsPolicy:
    return RightsPolicy(
        policy_version="test-v2",
        category_decisions={
            "public_domain": "allow",
            "open_license": "allow",
            "noncommercial_or_limited": "exclude",
            "in_copyright": "exclude",
            "no_known_copyright": "exclude",
            "institutional_terms": "exclude",
            "unknown": "exclude",
            "conflicting": "exclude",
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

    def test_open_license_is_public_reuse_eligible(self) -> None:
        assessment = assess_rights(
            [self.evidence("http://creativecommons.org/licenses/by/4.0/")],
            automatic_policy(),
            "2026-09-29T12:00:00+02:00",
        ).to_dict()
        self.assertEqual("open_license", assessment["category"])
        self.assertEqual("allow", assessment["decision"])
        self.assertTrue(assessment["public_reuse_eligible"])
        self.assertTrue(assessment["usage_permissions"]["commercial_use"])

    def test_in_copyright_is_research_only(self) -> None:
        assessment = assess_rights(
            [self.evidence("https://rightsstatements.org/vocab/InC/1.0/")],
            automatic_policy(),
            "2026-09-29T12:00:00+02:00",
        ).to_dict()
        self.assertEqual("exclude", assessment["decision"])
        self.assertEqual("retained", assessment["research_status"])
        self.assertTrue(assessment["usage_permissions"]["academic_analysis"])
        self.assertFalse(assessment["usage_permissions"]["public_distribution"])

    def test_conflicting_evidence_is_research_only(self) -> None:
        assessment = assess_rights(
            [
                self.evidence("https://creativecommons.org/licenses/by/4.0/"),
                self.evidence("All rights reserved"),
            ],
            automatic_policy(),
            "2026-09-29T12:00:00+02:00",
        ).to_dict()
        self.assertEqual("conflicting", assessment["category"])
        self.assertEqual("exclude", assessment["decision"])
        self.assertEqual("retained", assessment["research_status"])

    def test_attribution_alone_produces_retained_unknown(self) -> None:
        assessment = assess_rights(
            [self.evidence("Credit Example Library", decisive=False)],
            automatic_policy(),
            "2026-09-29T12:00:00+02:00",
        ).to_dict()
        self.assertEqual("unknown", assessment["category"])
        self.assertEqual("exclude", assessment["decision"])
        self.assertEqual("未知版权", assessment["display_label"]["zh"])
        self.assertTrue(assessment["usage_permissions"]["retain_url_and_metadata"])

    def test_policy_rejects_missing_categories(self) -> None:
        with self.assertRaises(ValueError):
            RightsPolicy("broken", {"open_license": "allow"})


if __name__ == "__main__":
    unittest.main()
