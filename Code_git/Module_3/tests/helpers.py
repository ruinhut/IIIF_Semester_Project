"""Shared Module 2-style input fixtures for Module 3 tests."""

from typing import Any


def provider_value(
    endpoint: str,
    *,
    provider_id: str = "provider-example",
    name: str = "Example Library",
    check_result: str = "reachable_json",
    json_type: str | None = None,
) -> dict[str, Any]:
    return {
        "provider_id": provider_id,
        "name": name,
        "institution_url": endpoint,
        "discovery_endpoint": endpoint,
        "discovery_type": json_type or "InstitutionWebsite",
        "record_status": "active",
        "rights_status": "unknown",
        "rights_values": [],
        "source": {"source_type": "test", "source_url": endpoint},
        "raw_source_record": {"fixture": True},
        "schema_version": "1.0",
        "module_2_schema_version": "1.0",
        "endpoint_check": {
            "requested_url": endpoint,
            "final_url": endpoint,
            "checked_at": "2026-09-19T10:00:00+02:00",
            "check_result": check_result,
            "status_code": 200,
            "content_type": "application/json" if check_result == "reachable_json" else "text/html",
            "json_parseable": check_result == "reachable_json",
            "json_resource_type": json_type,
            "redirect_chain": [],
            "response_time_ms": 1,
            "response_bytes": 10,
            "body_truncated": False,
            "attempt_count": 1,
            "error_type": None,
            "error_message": None,
        },
    }
