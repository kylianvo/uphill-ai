import base64
import hashlib
import hmac
import json
import math
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest
from google import genai
from google.genai import types
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import Event, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExportResult
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.util.instrumentation import InstrumentationScope
from opentelemetry.trace import Link, NonRecordingSpan, SpanContext, TraceFlags, TraceState, get_current_span
from opentelemetry.trace.propagation import set_span_in_context
from opentelemetry.trace.status import Status, StatusCode

from config import settings
from services import observability as obs
from services import observability_policy as policy

CANARY = "canary-health-injury-left-knee"
SAFE_ID = "0123456789abcdef0123456789abcdef"


@pytest.fixture
def recording_http_server():
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def _record_request(self):
            body = self.rfile.read(int(self.headers.get("content-length", "0")))
            requests.append(
                {
                    "method": self.command,
                    "path": self.path,
                    "headers": {key.lower(): value for key, value in self.headers.items()},
                    "body": body,
                }
            )
            return body

        def do_POST(self):
            body = self._record_request()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            if self.path == "/api/public/media":
                payload = json.loads(body)
                media_id = payload["sha256Hash"].replace("+", "-").replace("/", "_")[:22]
                upload_url = f"http://{self.headers['host']}/media-upload"
                self.wfile.write(json.dumps({"uploadUrl": upload_url, "mediaId": media_id}).encode())
            else:
                self.wfile.write(b"{}")

        def do_PUT(self):
            self._record_request()
            self.send_response(200)
            self.end_headers()

        def do_PATCH(self):
            self._record_request()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _context(*, trace_state=TraceState()):
    return SpanContext(
        trace_id=1,
        span_id=2,
        is_remote=False,
        trace_flags=TraceFlags(1),
        trace_state=trace_state,
    )


def _unsafe_span():
    linked = SpanContext(
        trace_id=3,
        span_id=4,
        is_remote=True,
        trace_flags=TraceFlags(1),
        trace_state=TraceState([("link", CANARY)]),
    )
    return ReadableSpan(
        name=CANARY,
        context=_context(trace_state=TraceState([("vendor", CANARY)])),
        parent=_context(trace_state=TraceState([("parent", CANARY)])),
        resource=Resource({"service.name": CANARY, "note": CANARY}, schema_url=f"https://{CANARY}"),
        attributes={
            "user.id": SAFE_ID,
            "llm.model_name": CANARY,
            "gen_ai.usage.input_tokens": CANARY,
        },
        events=[Event(CANARY, {"exception.message": CANARY}, timestamp=10)],
        links=[Link(linked, {"note": CANARY})],
        status=Status(StatusCode.ERROR, CANARY),
        start_time=1,
        end_time=2,
        instrumentation_scope=InstrumentationScope(
            CANARY,
            CANARY,
            schema_url=f"https://{CANARY}",
            attributes={"public_key": CANARY},
        ),
    )


def _serialized_span(span):
    return json.dumps(
        {
            "name": span.name,
            "attributes": dict(span.attributes or {}),
            "events": [(event.name, dict(event.attributes or {})) for event in span.events],
            "status": {"code": span.status.status_code.name, "description": span.status.description},
            "resource": {
                "attributes": dict(span.resource.attributes),
                "schema_url": span.resource.schema_url,
            },
            "links": [
                {"attributes": dict(link.attributes or {}), "trace_state": str(link.context.trace_state)}
                for link in span.links
            ],
            "scope": {
                "name": span.instrumentation_scope.name,
                "version": span.instrumentation_scope.version,
                "schema_url": span.instrumentation_scope.schema_url,
                "attributes": dict(span.instrumentation_scope.attributes or {}),
            },
            "trace_state": str(span.context.trace_state),
            "parent_trace_state": str(span.parent.trace_state) if span.parent else "",
        },
        sort_keys=True,
    )


def test_final_exporter_clones_and_sanitizes_every_envelope_surface():
    delegate = InMemorySpanExporter()
    exporter = obs._final_span_exporter(
        delegate,
        resource_attributes={
            "service.name": "uphill-ai-backend",
            "deployment.environment.name": "test",
        },
    )
    original = _unsafe_span()

    assert exporter.export((original,)) is SpanExportResult.SUCCESS

    assert CANARY in _serialized_span(original), "test setup must leave the shared source span untouched"
    [exported] = delegate.get_finished_spans()
    assert CANARY not in _serialized_span(exported)
    assert exported.name == "operation"
    assert dict(exported.attributes or {}) == {}, "identifier shape alone is not trusted provenance"
    assert exported.events == ()
    assert exported.status.status_code is StatusCode.ERROR
    assert exported.status.description is None
    assert dict(exported.resource.attributes) == {
        "service.name": "uphill-ai-backend",
        "deployment.environment.name": "test",
    }
    assert not exported.resource.schema_url
    assert len(exported.links) == 1
    assert dict(exported.links[0].attributes or {}) == {}
    assert len(exported.links[0].context.trace_state) == 0
    assert exported.instrumentation_scope.name == "uphill-ai.observability"
    assert exported.instrumentation_scope.version is None
    assert not exported.instrumentation_scope.schema_url
    assert dict(exported.instrumentation_scope.attributes or {}) == {}
    assert len(exported.context.trace_state) == 0
    assert len(exported.parent.trace_state) == 0


def test_final_exporter_drops_item_when_policy_raises(monkeypatch):
    delegate = InMemorySpanExporter()
    exporter = obs._final_span_exporter(delegate, resource_attributes={"service.name": "uphill-ai-backend"})

    def fail(_envelope):
        raise RuntimeError("policy failed")

    monkeypatch.setattr(policy, "sanitize_span_envelope", fail)

    assert exporter.export((_unsafe_span(),)) is SpanExportResult.SUCCESS
    assert delegate.get_finished_spans() == ()


def test_final_exporter_failure_is_isolated_from_caller():
    class ExplodingExporter:
        def export(self, spans):
            raise RuntimeError("transport failed")

        def force_flush(self, timeout_millis=30000):
            raise RuntimeError("flush failed")

        def shutdown(self):
            raise RuntimeError("shutdown failed")

    exporter = obs._final_span_exporter(ExplodingExporter(), resource_attributes={"service.name": "uphill-ai-backend"})

    assert exporter.export((_unsafe_span(),)) is SpanExportResult.FAILURE
    assert exporter.force_flush() is False
    assert exporter.shutdown() is None


def test_injected_exporter_is_behind_the_final_boundary(langfuse_spans):
    with obs._client.start_as_current_observation(
        as_type="span",
        name=CANARY,
        metadata={"feature": "coach_chat", "notes": CANARY},
    ):
        span = get_current_span()
        span.set_attribute("llm.model_name", CANARY)
        span.add_event(CANARY, {"exception.message": CANARY})
        span.set_status(Status(StatusCode.ERROR, CANARY))

    obs.flush()
    [exported] = langfuse_spans.get_finished_spans()
    assert CANARY not in _serialized_span(exported)
    assert exported.name == "operation"
    assert exported.status.status_code is StatusCode.ERROR


def test_score_allows_only_enumerated_metadata_and_finite_feedback_values():
    class RecordingClient:
        def __init__(self):
            self.calls = []

        def create_score(self, **kwargs):
            self.calls.append(kwargs)

    client = RecordingClient()
    previous, obs._client = obs._client, client
    try:
        obs.score(trace_id=SAFE_ID, name="thumbs", value=-1.0, category="incorrect")
        obs.score(trace_id=CANARY, name="thumbs", value=1.0)
        obs.score(trace_id=SAFE_ID, name=CANARY, value=1.0)
        obs.score(trace_id=SAFE_ID, name="thumbs", value=math.nan)
        obs.score(trace_id=SAFE_ID, name="thumbs", value=True)
        obs.score(trace_id=SAFE_ID, name="thumbs", value=10**1000)
        obs.score(trace_id=SAFE_ID, name="thumbs", value=1.0, category=CANARY)
        obs.score(trace_id=SAFE_ID, name=[], value=1.0, category={})  # type: ignore[arg-type]
    finally:
        obs._client = previous

    assert client.calls == [
        {
            "trace_id": SAFE_ID,
            "name": "thumbs",
            "value": -1.0,
            "data_type": "NUMERIC",
            "metadata": {"category": "incorrect"},
        }
    ]


def test_real_otlp_transport_serializes_only_sanitized_metadata(monkeypatch, recording_http_server):
    base_url, requests = recording_http_server
    public_key = f"pk-lf-boundary-{uuid.uuid4().hex}"
    secret_key = "sk-lf-boundary"
    monkeypatch.setattr(settings, "LANGFUSE_PUBLIC_KEY", public_key)
    monkeypatch.setattr(settings, "LANGFUSE_SECRET_KEY", secret_key)
    monkeypatch.setattr(settings, "OBSERVABILITY_ID_SALT", "boundary-salt")
    monkeypatch.setattr(settings, "LANGFUSE_BASE_URL", base_url)
    monkeypatch.setattr(settings, "LANGFUSE_ENVIRONMENT", "test")
    monkeypatch.setattr(settings, "LANGFUSE_TIMEOUT", 1)
    monkeypatch.setattr(settings, "LANGFUSE_EXPORT_CONTENT", True)

    def gemini_handler(request):
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"role": "model", "parts": [{"text": CANARY}]},
                        "finishReason": "STOP",
                        "index": 0,
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 12,
                    "candidatesTokenCount": 3,
                    "totalTokenCount": 15,
                },
                "modelVersion": "gemini-3.8-flash",
            },
        )

    obs._client = None
    obs.init()
    assert obs.enabled()
    assert obs._client._resources._media_upload_enabled is False
    assert obs._client._resources._media_manager._enabled is False
    try:
        client = genai.Client(
            api_key="test-key",
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1),
                httpx_client=httpx.Client(transport=httpx.MockTransport(gemini_handler)),
            ),
        )
        with obs.trace(CANARY, feature="coach_chat", user_id=42, thread_id=7):
            with obs.span(CANARY):
                current = get_current_span()
                current.add_event(CANARY, {"exception.message": CANARY})
                current.set_status(Status(StatusCode.ERROR, CANARY))
                client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=CANARY,
                    config=types.GenerateContentConfig(
                        system_instruction=CANARY,
                        tools=[
                            types.Tool(
                                function_declarations=[
                                    types.FunctionDeclaration(name="lookup_training", description=CANARY)
                                ]
                            )
                        ],
                    ),
                )
        unsafe_context = SpanContext(
            trace_id=11,
            span_id=12,
            is_remote=True,
            trace_flags=TraceFlags(1),
            trace_state=TraceState([("vendor", CANARY)]),
        )
        unsafe_tracer = obs._client._resources.tracer_provider.get_tracer(
            f"openinference.{CANARY}",
            CANARY,
            schema_url=f"https://{CANARY}",
            attributes={"note": CANARY},
        )
        with unsafe_tracer.start_as_current_span(
            CANARY,
            context=set_span_in_context(NonRecordingSpan(unsafe_context)),
            links=[Link(unsafe_context, {"note": CANARY})],
        ) as unsafe_span:
            unsafe_span.set_attribute("gen_ai.request.model", "gemini-3.8-flash")
            unsafe_span.set_attribute("user.id", SAFE_ID)
            unsafe_span.set_attribute(
                "input.value",
                f"data:text/plain;base64,{base64.b64encode(CANARY.encode()).decode()}",
            )
        obs.score(trace_id=CANARY, name=CANARY, value=1.0, category=CANARY)
        obs.score(trace_id=SAFE_ID, name="thumbs", value=-1.0, category="incorrect")
        obs.flush()
    finally:
        from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
        from openinference.instrumentation.langchain import LangChainInstrumentor

        GoogleGenAIInstrumentor().uninstrument()
        LangChainInstrumentor().uninstrument()
        client_instance, obs._client = obs._client, None
        client_instance.shutdown()

    trace_requests = [request for request in requests if request["path"] == "/api/public/otel/v1/traces"]
    assert trace_requests, f"no OTLP request captured; paths were {[request['path'] for request in requests]}"
    auxiliary_requests = [request for request in requests if request not in trace_requests]
    assert auxiliary_requests, "the valid score must exercise the non-OTLP auxiliary boundary"
    assert not [
        request for request in requests if request["method"] == "PUT"
    ], "metadata-only mode must prevent media bytes from being queued for auxiliary upload"
    assert not [request for request in requests if request["path"] == "/api/public/media"]
    score_requests = [request for request in requests if request["path"] == "/api/public/ingestion"]
    score_events = [
        event
        for request in score_requests
        for event in json.loads(request["body"])["batch"]
        if event["type"] == "score-create"
    ]
    assert len(score_events) == 1
    score_body = score_events[0]["body"]
    assert score_body["name"] == "thumbs"
    assert score_body["value"] == -1.0
    assert score_body["dataType"] == "NUMERIC"
    assert score_body["traceId"] == SAFE_ID
    assert score_body["metadata"] == {"category": "incorrect"}

    all_bodies = b"".join(request["body"] for request in requests)
    assert CANARY.encode() not in all_bodies
    expected_user = hmac.new(b"boundary-salt", b"42", hashlib.sha256).hexdigest()[:32]
    expected_session = hmac.new(b"boundary-salt", b"7", hashlib.sha256).hexdigest()[:32]

    decoded = []
    for request in trace_requests:
        payload = ExportTraceServiceRequest()
        payload.ParseFromString(request["body"])
        decoded.append(MessageToDict(payload, preserving_proto_field_name=True))
        expected_auth = "Basic " + base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        assert request["headers"]["authorization"] == expected_auth
    serialized = json.dumps(decoded, sort_keys=True)
    assert CANARY not in serialized
    assert SAFE_ID not in serialized
    assert expected_user in serialized
    assert expected_session in serialized
    assert "GenerateContent" in serialized
    assert "gemini-3.8-flash" in serialized
    assert "uphill-ai-backend" in serialized
    assert '"deployment.environment.name"' in serialized
    assert "uphill-ai.observability" in serialized


def test_partial_initialization_failure_shuts_down_export_and_instrumentation(monkeypatch):
    import langfuse
    from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from opentelemetry.sdk.trace import TracerProvider

    class TrackingExporter(InMemorySpanExporter):
        def __init__(self):
            super().__init__()
            self.was_shutdown = False

        def shutdown(self):
            self.was_shutdown = True
            return super().shutdown()

    exporter = TrackingExporter()
    replacement = TrackingExporter()
    monkeypatch.setattr(settings, "LANGFUSE_PUBLIC_KEY", f"pk-lf-partial-{uuid.uuid4().hex}")
    monkeypatch.setattr(settings, "LANGFUSE_SECRET_KEY", "sk-lf-partial")
    monkeypatch.setattr(settings, "OBSERVABILITY_ID_SALT", "partial-salt")
    monkeypatch.setattr(settings, "LANGFUSE_TIMEOUT", 0.05)

    def fail(*args, **kwargs):
        raise RuntimeError("instrumentation failed")

    monkeypatch.setattr(LangChainInstrumentor, "instrument", fail)
    original_shutdown = langfuse.Langfuse.shutdown
    allow_shutdown = threading.Event()
    provider_shutdown_attempted = threading.Event()
    shutdown_clients = []

    def slow_shutdown(self):
        shutdown_clients.append(self)
        allow_shutdown.wait(timeout=5)
        return original_shutdown(self)

    def track_provider_shutdown(self):
        provider_shutdown_attempted.set()

    monkeypatch.setattr(langfuse.Langfuse, "shutdown", slow_shutdown)
    monkeypatch.setattr(TracerProvider, "shutdown", track_provider_shutdown)
    obs._client = None
    obs._init_failed = False
    try:
        started = time.monotonic()
        obs.init(span_exporter=exporter)
        elapsed = time.monotonic() - started

        assert obs.enabled() is False
        assert elapsed < 0.75, "failed initialization cleanup must have a deadline"
        assert GoogleGenAIInstrumentor().is_instrumented_by_opentelemetry is False
        assert shutdown_clients[0]._resources.tracer_provider is None
        assert provider_shutdown_attempted.is_set(), "provider cleanup must not wait for client shutdown"
        assert exporter.was_shutdown is True, "exporter cleanup must not wait for client or provider shutdown"

        obs.init(span_exporter=replacement)

        assert obs.enabled() is False, "a failed SDK singleton must not be reused"
        assert replacement.was_shutdown is True, "an exporter rejected after failure remains caller-safe"
    finally:
        allow_shutdown.set()
        time.sleep(0.2)
        obs._init_failed = False
        GoogleGenAIInstrumentor().uninstrument()
        if obs._client is not None:
            client, obs._client = obs._client, None
            client.shutdown()


def test_client_construction_failure_shuts_down_unowned_exporter(monkeypatch):
    import langfuse

    class TrackingExporter(InMemorySpanExporter):
        def __init__(self):
            super().__init__()
            self.was_shutdown = False

        def shutdown(self):
            self.was_shutdown = True
            return super().shutdown()

    exporter = TrackingExporter()
    monkeypatch.setattr(settings, "LANGFUSE_PUBLIC_KEY", f"pk-lf-construction-{uuid.uuid4().hex}")
    monkeypatch.setattr(settings, "LANGFUSE_SECRET_KEY", "sk-lf-construction")
    monkeypatch.setattr(settings, "OBSERVABILITY_ID_SALT", "construction-salt")
    monkeypatch.setattr(
        langfuse,
        "Langfuse",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("client construction failed")),
    )
    obs._client = None
    previous_init_failed, obs._init_failed = obs._init_failed, False
    try:
        obs.init(span_exporter=exporter)

        assert obs.enabled() is False
        assert exporter.was_shutdown is True
    finally:
        obs._init_failed = previous_init_failed


def test_missing_keys_do_not_construct_a_transport(monkeypatch):
    monkeypatch.setattr(settings, "LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setattr(settings, "LANGFUSE_SECRET_KEY", "")
    monkeypatch.setattr(settings, "OBSERVABILITY_ID_SALT", "")
    monkeypatch.setattr(
        obs,
        "_real_otlp_exporter",
        lambda: (_ for _ in ()).throw(AssertionError("transport must not be constructed")),
    )
    obs._client = None

    obs.init()

    assert obs.enabled() is False


def test_unapproved_content_switch_cannot_weaken_runtime_mask(monkeypatch):
    monkeypatch.setattr(settings, "LANGFUSE_EXPORT_CONTENT", True)

    assert obs._mask(data=CANARY) is None
