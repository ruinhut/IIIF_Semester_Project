"""Protocol and discovery integration tests; no paid model calls or real keys.

The fixture LLM proposes recipes, but the actual discovery engine must fetch
and validate the fixture institution's catalogue and native Manifest itself.
"""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

import pytest

from helpers import provider_value
from iiif_resource_discovery import llm
from iiif_resource_discovery.discovery import DiscoveryLimits
from iiif_resource_discovery.fetch import HttpFetcher
from iiif_resource_discovery.models import ProviderDiscoveryResult, ProviderInputRecord
from iiif_resource_discovery.pipeline import run_pipeline


@contextmanager
def fixture_site():
    state = {"calls": [], "actions": [], "requests": [], "status": 200, "response": None,
             "manifest_context": "http://iiif.io/api/presentation/3/context.json", "canvases": True}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send_value(self, value, status=200, content_type="application/json"):
            body = value.encode() if isinstance(value, str) else json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["calls"].append((self.path, payload, self.headers.get("Authorization")))
            if state["status"] != 200:
                self.send_value("error body secret-test-token", state["status"])
                return
            if state["response"] is not None:
                self.send_value(state["response"])
                return
            action = state["actions"].pop(0) if state["actions"] else {"action": "finish"}
            text = json.dumps(action)
            if self.path.endswith("/responses"):
                self.send_value({"output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}],
                                 "usage": {"input_tokens": 100, "output_tokens": 10}})
            else:
                self.send_value({"choices": [{"message": {"content": text}}], "usage": {"total_tokens": 110}})

        def do_GET(self):
            state["requests"].append((self.path, self.headers.get("Authorization")))
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", state["base"] + "/blocked")
                self.end_headers()
            elif self.path.startswith("/api/items"):
                self.send_value([{"o:id": 44}])
            elif self.path == "/iiif/44/manifest":
                self.send_value({"@context": state["manifest_context"], "id": state["base"] + self.path,
                    "type": "Manifest", "items": [{"id": state["base"] + "/canvas/1", "type": "Canvas"}] if state["canvases"] else []})
            elif self.path in {"/", "/home"}:
                self.send_value('<html>Omeka S. <a href="/api/items">Catalogue API</a></html>', content_type="text/html")
            else:
                self.send_value({"error": "no such item"}, 404)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state["base"] = f"http://127.0.0.1:{server.server_port}"
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def config(state, **extra):
    return {"enabled": True, "model": "fixture-model", "base_url": state["base"] + "/v1",
            "request_delay_seconds": 0, **extra}


def recipe(state):
    return {"type": llm.SUPPORTED_SKILL_TYPE, "api_url": state["base"] + "/api/items",
            "records_path": "$", "identifier_path": "o:id",
            "manifest_url_templates": [state["base"] + "/iiif/{identifier}/manifest"],
            "pagination": {"page_parameter": "page", "page_size_parameter": "per_page", "max_pages": 1}}


def unresolved(state):
    provider = ProviderInputRecord.from_mapping(provider_value(state["base"] + "/home", check_result="reachable_non_json"))
    return ProviderDiscoveryResult(provider=provider)


@pytest.fixture
def token(monkeypatch):
    monkeypatch.setenv("IIIF_LLM_API_KEY", "secret-test-token")


@pytest.mark.parametrize("mode", ["responses", "chat_completions"])
def test_client_protocol_and_redaction(mode, token, tmp_path):
    with fixture_site() as state:
        state["actions"] = [{"action": "finish", "reason": "secret-test-token"}]
        client = llm.LLMClient(config(state, api_mode=mode, web_search=mode == "responses"), tmp_path)
        action = client.next_action([{"role": "user", "content": "Investigate"}])
        path, payload, authorization = state["calls"][0]
        assert action["reason"] == "[REDACTED]"
        assert authorization == "Bearer secret-test-token"
        assert payload["model"] == "fixture-model"
        if mode == "responses":
            assert path == "/v1/responses" and payload["store"] is False
            assert payload["tools"] == [{"type": "web_search"}]
        else:
            assert path == "/v1/chat/completions" and "messages" in payload


def test_client_http_error_never_echoes_body(token, tmp_path):
    with fixture_site() as state:
        state["status"] = 401
        with pytest.raises(llm.LLMError, match="HTTP 401") as exc:
            llm.LLMClient(config(state), tmp_path).next_action([])
        assert "secret-test-token" not in str(exc.value)
        agent = llm.LLMInvestigator(config(state), tmp_path, tmp_path / "kb.json", tmp_path / "out", DiscoveryLimits())
        with pytest.raises(llm.LLMError, match="HTTP 401"):
            agent.enhance(unresolved(state))
        assert len(state["calls"]) == 2  # one direct client call and one agent call; no retry


@pytest.mark.parametrize("response", [[], {"output_text": "not JSON"}, {"output_text": "[]"}])
def test_malformed_model_responses_are_reported(response, token, tmp_path):
    with fixture_site() as state:
        state["response"] = response
        with pytest.raises(llm.LLMError):
            llm.LLMClient(config(state), tmp_path).next_action([])


def test_key_file_and_missing_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("IIIF_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="key missing"):
        llm.load_key({}, tmp_path)
    key_file = tmp_path / "token.json"
    key_file.write_text('{"api_key":"file-token"}')
    assert llm.load_key({"api_key_file": str(key_file)}, tmp_path) == "file-token"
    with pytest.raises(ValueError, match="shared config"):
        llm.load_key({"api_key": "unsafe"}, tmp_path)


@pytest.mark.parametrize("url", ["http://127.0.0.1/", "http://192.168.1.1/", "http://169.254.169.254/",
                               "http://localhost/", "http://example.org:9000/", "http://user:password@example.org/"])
def test_investigation_rejects_private_or_credential_urls(url):
    with pytest.raises(ValueError):
        llm.public_url(url)


def test_every_http_redirect_is_checked():
    with fixture_site() as state:
        def policy(url):
            if url.endswith("/blocked"):
                raise ValueError("redirect blocked")
        with pytest.raises(ValueError, match="redirect blocked"):
            HttpFetcher(retries=0, url_validator=policy).fetch(state["base"] + "/redirect")
        assert not any(url == "/blocked" for url, _ in state["requests"])


def test_generated_recipe_whitelist_and_namespace_values(monkeypatch):
    monkeypatch.setattr(llm, "public_url", lambda url: None)
    value = {"type": llm.XML_IDENTIFIER_SKILL_TYPE, "api_url": "https://library.example/oai",
             "xml_namespaces": {"oai": "http://www.openarchives.org/OAI/2.0/"},
             "pagination": {"page_size": 999, "max_pages": 999}}
    safe = llm.validate_recipe(value, "provider", {"library.example"})
    assert safe["pagination"] == {"page_size": 20, "max_pages": 3}
    # A saved normalized recipe remains valid on the next run.
    llm.validate_recipe(safe, "provider", {"library.example"})
    with pytest.raises(ValueError, match="Unsupported recipe fields"):
        llm.validate_recipe({**value, "code": "anything"}, "p", {"library.example"})
    with pytest.raises(ValueError, match="institution-linked"):
        llm.validate_recipe({**value, "api_url": "https://unrelated.example/api"}, "p", {"library.example"})


def test_real_engine_verifies_model_recipe_then_replays_without_model(token, monkeypatch, tmp_path):
    # Only this local fixture bypasses the public-network policy.
    monkeypatch.setattr(llm, "public_url", lambda url: None)
    with fixture_site() as state:
        state["actions"] = [
            {"action": "fetch_url", "url": state["base"] + "/api/items"},
            {"action": "propose_recipe", "evidence_urls": [state["base"] + "/api/items"], "recipe": recipe(state)}]
        learned = tmp_path / "learned.json"
        investigator = llm.LLMInvestigator(config(state), tmp_path, learned, tmp_path / "out", DiscoveryLimits())
        result = investigator.enhance(unresolved(state))
        assert result.status == "manifests_found" and len(result.manifests) == 1
        assert len(state["calls"]) == 2
        assert all(auth is None for _, auth in state["requests"])
        assert "secret-test-token" not in learned.read_text()
        assert "secret-test-token" not in (tmp_path / "out/llm_investigation.jsonl").read_text()
        monkeypatch.delenv("IIIF_LLM_API_KEY")
        replay = llm.LLMInvestigator({"enabled": False, "request_delay_seconds": 0}, tmp_path, learned, tmp_path / "replay", DiscoveryLimits())
        assert replay.enhance(unresolved(state)).manifests
        assert len(state["calls"]) == 2
        assert "verified_recipe_reused" in (tmp_path / "replay/llm_investigation.jsonl").read_text()


@pytest.mark.parametrize("failure", ["no_evidence", "false_context", "empty_manifest"])
def test_invalid_discovery_never_becomes_learned_knowledge(failure, token, monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "public_url", lambda url: None)
    with fixture_site() as state:
        if failure == "false_context":
            state["manifest_context"] = "https://unrelated.example/context"
        if failure == "empty_manifest":
            state["canvases"] = False
        state["actions"] = [{"action": "propose_recipe", "evidence_urls": [] if failure == "no_evidence" else [state["base"] + "/home"],
                             "recipe": recipe(state)}]
        learned = tmp_path / "learned.json"
        investigator = llm.LLMInvestigator(config(state, max_rounds=1), tmp_path, learned, tmp_path / "out", DiscoveryLimits())
        assert not investigator.enhance(unresolved(state)).manifests
        assert not learned.exists()
        assert "recipe_rejected" in (tmp_path / "out/llm_investigation.jsonl").read_text()


def test_provider_budget_and_resolved_baseline_do_not_spend(token, tmp_path):
    with fixture_site() as state:
        agent = llm.LLMInvestigator(config(state, max_providers=1), tmp_path, tmp_path / "kb.json", tmp_path / "out", DiscoveryLimits())
        agent.attempted = 1
        result = agent.enhance(unresolved(state))
        assert result.issues[-1].issue_type == "llm_provider_budget"
        resolved = unresolved(state)
        resolved.manifests.append(object())
        assert agent.enhance(resolved) is resolved
        assert state["calls"] == []


def test_module3_pipeline_keeps_handoff_contract(token, monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "public_url", lambda url: None)
    with fixture_site() as state:
        state["actions"] = [{"action": "propose_recipe", "evidence_urls": [state["base"] + "/home"], "recipe": recipe(state)}]
        source = tmp_path / "input.jsonl"
        source.write_text(json.dumps(provider_value(state["base"] + "/home", check_result="reachable_non_json")) + "\n")
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"input_jsonl": str(source), "output_directory": "output", "log_directory": "log",
            "html_discovery": {"enabled": False}, "platform_discovery": {"omeka_s_probe_enabled": False},
            "llm_discovery": config(state, max_rounds=1), "learned_knowledge_base": "learned.json"}))
        result = run_pipeline(path)
        assert result.unique_manifest_count == 1 and result.knowledge_resolved_provider_count == 1
        row = json.loads(result.manifest_urls_jsonl.read_text().strip())
        assert row["manifest_url"] == state["base"] + "/iiif/44/manifest"
        assert row["providers"][0]["provider_id"] == "provider-example"
        assert row["discovery_evidence"][0]["discovery_method"].startswith("llm_verified_skill:")
