from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


STATE_SCHEMA_VERSION = "daily-ai-brief.run/v1"
GRAPH_VERSION = "daily-ai-brief.graph/v1"
GRAPH_BUDGETS = {
    "research_seconds": 600,
    "discovery_passes": 1,
    "targeted_rounds": 2,
    "targeted_searches": 8,
    "artifact_repairs": 1,
    "publish_retries": 2,
    "live_checks": 3,
}
DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
REASON_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
TERMINAL_STATUS_NODES = {
    "succeeded": "done",
    "blocked": "blocked",
    "publish_failed": "publish_failed",
    "failed": "failed",
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "graph_version",
    "revision",
    "run_id",
    "date",
    "timezone",
    "started_at",
    "finished_at",
    "status",
    "current_node",
    "budgets",
    "history",
    "candidates",
    "selection",
    "artifact",
    "publication",
    "persistence",
    "node_status",
    "trace",
    "errors",
}
CANDIDATE_KEYS = {
    "id",
    "person",
    "role_org",
    "why_it_matters",
    "summary",
    "theme",
    "story_fingerprint",
    "history_overlap_reason",
    "selected_source_url",
    "sources",
    "scores",
    "confirmation_attempts",
    "status",
    "rejection_reason",
}
SOURCE_KEYS = {
    "label",
    "original_url",
    "canonical_url",
    "tier",
    "kind",
    "published_date",
    "checked_at",
    "verified",
}
SCORE_KEYS = {
    "impact",
    "source_quality",
    "freshness",
    "influence",
    "novelty",
    "total",
}
ARTIFACT_KEYS = {
    "path",
    "sha256",
    "content_fingerprint",
    "item_count",
    "validated",
    "validated_at",
}
PUBLICATION_KEYS = {
    "required",
    "mode",
    "authorization_status",
    "target_verified",
    "target_id",
    "target_url",
    "idempotency_key",
    "delivery_status",
    "live_status",
    "attempts",
    "live_checks",
    "receipt_fingerprint",
    "live_fingerprint",
    "live_date",
    "live_item_count",
    "archive_url",
    "archive_status",
    "archive_fingerprint",
    "archive_date",
    "archive_item_count",
    "failure_reason",
}
PERSISTENCE_KEYS = {
    "attempt_state_path",
    "run_log_path",
    "run_log_status",
    "run_log_entry_sha256",
}
TRACE_KEYS = {
    "sequence",
    "at",
    "node",
    "attempt",
    "outcome",
    "route",
    "input_revision",
    "output_revision",
    "duration_ms",
    "counts",
    "reason_code",
    "payload_fingerprint",
    "idempotency_key",
}
TRACE_COUNT_KEYS = {
    "candidates",
    "qualified",
    "selected",
    "sources",
    "articles",
    "live_items",
    "searches",
}
NODE_STATUS_KEYS = {"status", "attempts", "last_error"}
ERROR_KEYS = {"node", "reason_code", "message", "retryable", "at"}
BANNED_TRACE_KEYS = {
    "analysis",
    "authorization",
    "chainofthought",
    "headers",
    "prompt",
    "rawresponse",
    "reasoning",
    "secret",
    "sourcebody",
    "thoughts",
    "token",
}
TRACKING_QUERY_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
RESEARCH_NODES = {
    "parallel_discovery",
    "normalize",
    "verify_sources",
    "score_dedupe",
    "quality_gate",
    "targeted_research",
}
ARTIFACT_REPAIR_REASON_CODES = {"ARTIFACT_REPAIRABLE"}
PUBLICATION_RETRY_REASON_CODES = {
    "NETWORK_TRANSIENT",
    "HTTP_408",
    "HTTP_425",
    "HTTP_429",
    "HTTP_5XX",
}
LIVE_RETRY_REASON_CODES = {"LIVE_READ_TRANSIENT"}
STATIC_HTML_TAGS = {
    "a",
    "abbr",
    "article",
    "aside",
    "b",
    "blockquote",
    "body",
    "br",
    "code",
    "dd",
    "div",
    "dl",
    "dt",
    "em",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "head",
    "header",
    "hr",
    "html",
    "i",
    "li",
    "main",
    "mark",
    "meta",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "small",
    "span",
    "strong",
    "style",
    "time",
    "title",
    "ul",
}
RESOURCE_ATTRIBUTES = {
    "action",
    "background",
    "cite",
    "data",
    "formaction",
    "manifest",
    "ping",
    "poster",
    "src",
    "srcdoc",
    "srcset",
    "xlink:href",
}
UNSAFE_CSS_PATTERN = re.compile(
    r"url\s*\(|image-set\s*\(|@import|expression\s*\(|behavior\s*:|-moz-binding|\\",
    re.IGNORECASE,
)


class ValidationError(Exception):
    pass


class BriefHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_depth = 0
        self.title_count = 0
        self.h1_depth = 0
        self.footer_depth = 0
        self.style_depth = 0
        self.article_depth = 0
        self.title_parts: list[str] = []
        self.h1_values: list[list[str]] = []
        self.footer_values: list[list[str]] = []
        self.style_parts: list[str] = []
        self.document_parts: list[str] = []
        self.articles: list[dict[str, Any]] = []
        self.current_article: dict[str, Any] | None = None
        self.ol_count = 0
        self.ol_depth = 0
        self.hrefs: list[str] = []
        self.external_assets: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        lowered = tag.lower()
        if lowered not in STATIC_HTML_TAGS:
            self.external_assets.append(f"tag:{lowered}")
        for key, value in attributes.items():
            if key.startswith("on"):
                self.external_assets.append(f"event:{key}")
            if key in RESOURCE_ATTRIBUTES:
                self.external_assets.append(f"attribute:{key}")
            if key == "style" and UNSAFE_CSS_PATTERN.search(value):
                self.external_assets.append("unsafe-inline-style")
        if lowered == "meta" and attributes.get("http-equiv", "").strip().casefold() == "refresh":
            self.external_assets.append("meta-refresh")
        if "href" in attributes and lowered != "a":
            self.external_assets.append(f"href:{lowered}")
        if lowered == "title":
            self.title_depth += 1
            self.title_count += 1
        elif lowered == "h1":
            self.h1_depth += 1
            if self.h1_depth == 1:
                self.h1_values.append([])
        elif lowered == "footer":
            self.footer_depth += 1
            if self.footer_depth == 1:
                self.footer_values.append([])
        elif lowered == "style":
            self.style_depth += 1
        elif lowered == "ol":
            self.ol_count += 1
            self.ol_depth += 1
        elif lowered == "article":
            self.article_depth += 1
            if self.article_depth == 1:
                self.current_article = {
                    "text": [],
                    "hrefs": [],
                    "inside_ordered_list": self.ol_depth > 0,
                }
        if self.article_depth and lowered == "a" and self.current_article is not None:
            href = attributes.get("href", "").strip()
            if href:
                self.current_article["hrefs"].append(href)
        if lowered == "a" and attributes.get("href", "").strip():
            self.hrefs.append(attributes["href"].strip())

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "title" and self.title_depth:
            self.title_depth -= 1
        elif lowered == "h1" and self.h1_depth:
            self.h1_depth -= 1
        elif lowered == "footer" and self.footer_depth:
            self.footer_depth -= 1
        elif lowered == "style" and self.style_depth:
            self.style_depth -= 1
        elif lowered == "ol" and self.ol_depth:
            self.ol_depth -= 1
        elif lowered == "article" and self.article_depth:
            if self.article_depth == 1 and self.current_article is not None:
                self.articles.append(self.current_article)
                self.current_article = None
            self.article_depth -= 1

    def handle_data(self, data: str) -> None:
        self.document_parts.append(data)
        if self.title_depth:
            self.title_parts.append(data)
        if self.h1_depth and self.h1_values:
            self.h1_values[-1].append(data)
        if self.footer_depth and self.footer_values:
            self.footer_values[-1].append(data)
        if self.style_depth:
            self.style_parts.append(data)
        if self.article_depth and self.current_article is not None:
            self.current_article["text"].append(data)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be an object")
    actual = set(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    require(not missing, f"{label} is missing keys: {', '.join(missing)}")
    require(not unknown, f"{label} has unknown keys: {', '.join(unknown)}")
    return value


def require_string(value: Any, label: str, allow_empty: bool = False) -> str:
    require(isinstance(value, str), f"{label} must be a string")
    if not allow_empty:
        require(bool(value.strip()), f"{label} must not be empty")
    return value


def require_integer(value: Any, label: str, minimum: int = 0) -> int:
    require(isinstance(value, int) and not isinstance(value, bool), f"{label} must be an integer")
    require(value >= minimum, f"{label} must be at least {minimum}")
    return value


def require_number(value: Any, label: str, minimum: float = 0) -> float:
    require(
        isinstance(value, (int, float)) and not isinstance(value, bool),
        f"{label} must be a number",
    )
    require(value >= minimum, f"{label} must be at least {minimum}")
    return float(value)


def require_boolean(value: Any, label: str) -> bool:
    require(isinstance(value, bool), f"{label} must be a boolean")
    return value


def require_reason_code(value: Any, label: str, allow_empty: bool = False) -> str:
    text = require_string(value, label, allow_empty=allow_empty)
    if not text and allow_empty:
        return text
    require(REASON_CODE_PATTERN.fullmatch(text) is not None, f"{label} is not a reason code")
    return text


def parse_date(value: Any, label: str) -> date:
    text = require_string(value, label)
    require(bool(DATE_PATTERN.fullmatch(text)), f"{label} must use YYYY-MM-DD")
    try:
        return date.fromisoformat(text)
    except ValueError as error:
        raise ValidationError(f"{label} is not a calendar date") from error


def parse_datetime(value: Any, label: str) -> datetime:
    text = require_string(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError(f"{label} must be an RFC3339 timestamp") from error
    require(parsed.tzinfo is not None, f"{label} must include a timezone offset")
    return parsed


def validate_run_clock(run_date: date, timezone: str, started_at: datetime) -> None:
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as error:
        raise ValidationError("timezone must be a valid IANA timezone") from error
    local_started_at = started_at.astimezone(zone)
    require(local_started_at.date() == run_date, "started_at does not resolve to the run date")
    require(
        started_at.utcoffset() == local_started_at.utcoffset(),
        "started_at offset does not match the resolved timezone",
    )


def normalized_text(value: str) -> str:
    return " ".join(value.split()).casefold()


def canonicalize_url(value: Any, label: str) -> str:
    text = require_string(value, label)
    try:
        parsed = urlsplit(text)
        port = parsed.port
    except ValueError as error:
        raise ValidationError(f"{label} is not a valid URL") from error
    require(parsed.scheme.lower() == "https", f"{label} must use HTTPS")
    require(bool(parsed.hostname), f"{label} must include a host")
    require(not parsed.username and not parsed.password, f"{label} must not include credentials")
    host = parsed.hostname.lower()
    netloc = host if port in {None, 443} else f"{host}:{port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"
    query = [
        (key, item)
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_QUERY_KEYS
    ]
    return urlunsplit(("https", netloc, path, urlencode(query, doseq=True), ""))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_workspace_path(workspace: Path, value: Any, label: str) -> Path:
    text = require_string(value, label)
    relative = Path(text)
    require(not relative.is_absolute(), f"{label} must be workspace-relative")
    require(".." not in relative.parts, f"{label} must not traverse outside the workspace")
    resolved_workspace = workspace.resolve()
    resolved = (resolved_workspace / relative).resolve()
    require(
        resolved == resolved_workspace or resolved_workspace in resolved.parents,
        f"{label} must stay inside the workspace",
    )
    return resolved


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValidationError(f"{label} does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise ValidationError(f"{label} is not valid JSON: {error}") from error
    require(isinstance(value, dict), f"{label} must contain an object")
    return value


def validate_schema_contract(schema: dict[str, Any]) -> None:
    require(schema.get("type") == "object", "run-state schema root must be an object")
    require(schema.get("additionalProperties") is False, "run-state schema root must be strict")
    require(set(schema.get("required", [])) == TOP_LEVEL_KEYS, "run-state schema root drifted")
    properties = schema.get("properties", {})
    require(set(properties) == TOP_LEVEL_KEYS, "run-state schema properties drifted")
    definitions = schema.get("$defs", {})
    expected_definitions = {
        "source": SOURCE_KEYS,
        "scores": SCORE_KEYS,
        "candidate": CANDIDATE_KEYS,
        "artifact": ARTIFACT_KEYS,
        "publication": PUBLICATION_KEYS,
        "persistence": PERSISTENCE_KEYS,
        "node_status": NODE_STATUS_KEYS,
        "trace_event": TRACE_KEYS,
        "error": ERROR_KEYS,
    }
    for name, expected_keys in expected_definitions.items():
        definition = definitions.get(name)
        require(isinstance(definition, dict), f"run-state schema is missing $defs.{name}")
        require(
            definition.get("additionalProperties") is False,
            f"run-state schema $defs.{name} must be strict",
        )
        require(
            set(definition.get("required", [])) == expected_keys,
            f"run-state schema $defs.{name} drifted",
        )
        require(
            set(definition.get("properties", {})) == expected_keys,
            f"run-state schema $defs.{name} properties drifted",
        )
    inline_contracts = {
        "history": {"runs_read", "people", "themes", "urls"},
        "selection": {"candidate_ids", "item_count", "shortfall_reason"},
    }
    for name, expected_keys in inline_contracts.items():
        definition = properties.get(name, {})
        require(definition.get("additionalProperties") is False, f"schema {name} must be strict")
        require(set(definition.get("required", [])) == expected_keys, f"schema {name} drifted")
        require(set(definition.get("properties", {})) >= expected_keys, f"schema {name} properties drifted")


def load_contracts(graph_path: Path, schema_path: Path) -> dict[str, Any]:
    graph = load_json(graph_path, "workflow graph")
    schema = load_json(schema_path, "run-state schema")
    require(
        graph.get("graph_version") == GRAPH_VERSION,
        "workflow graph version is unsupported",
    )
    require(
        graph.get("state_schema_version") == STATE_SCHEMA_VERSION,
        "workflow graph and state schema versions disagree",
    )
    require(
        schema.get("properties", {}).get("schema_version", {}).get("const")
        == STATE_SCHEMA_VERSION,
        "run-state schema version is unsupported",
    )
    validate_schema_contract(schema)
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    budgets = graph.get("budgets")
    require(isinstance(nodes, dict) and nodes, "workflow graph must define nodes")
    require(isinstance(edges, list) and edges, "workflow graph must define edges")
    require(isinstance(budgets, dict) and budgets, "workflow graph must define budgets")
    require(budgets == GRAPH_BUDGETS, "workflow graph budget contract drifted")
    node_names = set(nodes)
    for index, edge in enumerate(edges):
        require(isinstance(edge, dict), f"edge {index} must be an object")
        require(edge.get("from") in node_names, f"edge {index} has an unknown source")
        require(edge.get("to") in node_names, f"edge {index} has an unknown target")
        require_string(edge.get("condition"), f"edge {index} condition")
    require(graph.get("start_node") in node_names, "workflow start node is unknown")
    terminals = graph.get("terminal_nodes")
    require(isinstance(terminals, list), "workflow terminal_nodes must be an array")
    require(set(terminals) <= node_names, "workflow has unknown terminal nodes")
    exclusions = graph.get("global_failure_exclusions")
    require(isinstance(exclusions, list), "workflow failure exclusions must be an array")
    require(set(exclusions) <= node_names, "workflow has unknown failure exclusions")
    loops = graph.get("loops")
    require(isinstance(loops, list), "workflow loops must be an array")
    expected_loops = {
        "targeted_fill": ("targeted_research", "normalize", "targeted_rounds"),
        "artifact_repair": ("validate", "render", "artifact_repairs"),
        "publication_retry": ("publish_update", "publish_update", "publish_retries"),
        "live_verification_retry": ("live_verify", "live_verify", "live_checks"),
    }
    require(
        {loop.get("name") for loop in loops if isinstance(loop, dict)} == set(expected_loops),
        "workflow loop contract drifted",
    )
    edge_pairs = {(edge["from"], edge["to"]) for edge in edges}
    for loop in loops:
        name = loop["name"]
        source, target, budget_name = expected_loops[name]
        require(loop.get("backedge_from") == source, f"workflow loop {name} source drifted")
        require(loop.get("backedge_to") == target, f"workflow loop {name} target drifted")
        require(loop.get("budget") == budget_name, f"workflow loop {name} budget drifted")
        require((source, target) in edge_pairs, f"workflow loop {name} has no edge")
        if name == "live_verification_retry":
            require(
                loop.get("maximum_total_checks") == budgets[budget_name],
                f"workflow loop {name} maximum drifted",
            )
            require(
                loop.get("maximum_backedges") == budgets[budget_name] - 1,
                f"workflow loop {name} backedge maximum drifted",
            )
        else:
            require(
                loop.get("maximum") == budgets[budget_name],
                f"workflow loop {name} maximum drifted",
            )
    return graph


def validate_history(history: Any) -> None:
    values = exact_keys(history, {"runs_read", "people", "themes", "urls"}, "history")
    runs_read = require_integer(values["runs_read"], "history.runs_read")
    require(runs_read <= 2, "history.runs_read exceeds two runs")
    for key in ("people", "themes", "urls"):
        items = values[key]
        require(isinstance(items, list), f"history.{key} must be an array")
        normalized: list[str] = []
        for index, item in enumerate(items):
            text = require_string(item, f"history.{key}[{index}]")
            if key == "urls":
                canonical = canonicalize_url(text, f"history.{key}[{index}]")
                require(text == canonical, f"history.{key}[{index}] is not normalized")
                normalized.append(canonical)
            else:
                normalized.append(normalized_text(text))
        require(len(normalized) == len(set(normalized)), f"history.{key} contains duplicates")


def validate_scores(scores: Any, label: str) -> None:
    values = exact_keys(scores, SCORE_KEYS, label)
    for key in SCORE_KEYS - {"total"}:
        score = require_integer(values[key], f"{label}.{key}")
        require(score <= 5, f"{label}.{key} exceeds 5")
    total = require_integer(values["total"], f"{label}.total")
    expected = (
        6 * values["impact"]
        + 5 * values["source_quality"]
        + 4 * values["freshness"]
        + 3 * values["influence"]
        + 2 * values["novelty"]
    )
    require(total == expected, f"{label}.total does not match the scoring formula")


def validate_source(
    source: Any,
    label: str,
    terminal: bool,
    run_date: date,
    timezone: str,
) -> str | None:
    values = exact_keys(source, SOURCE_KEYS, label)
    require_string(values["label"], f"{label}.label")
    original = canonicalize_url(values["original_url"], f"{label}.original_url")
    canonical = values["canonical_url"]
    if canonical is None:
        require(not terminal, f"{label}.canonical_url is required in terminal state")
    else:
        canonical_raw = require_string(canonical, f"{label}.canonical_url")
        canonical_text = canonicalize_url(canonical_raw, f"{label}.canonical_url")
        require(canonical_raw == canonical_text, f"{label}.canonical_url is not normalized")
        require(canonical_text == original, f"{label}.canonical_url is not canonical")
    tier = require_integer(values["tier"], f"{label}.tier")
    require(tier <= 3, f"{label}.tier exceeds 3")
    kinds = ["primary", "independent", "specialist", "fallback"]
    require(values["kind"] == kinds[tier], f"{label}.kind does not match its tier")
    published_date = parse_date(values["published_date"], f"{label}.published_date")
    require(published_date <= run_date, f"{label}.published_date is after the run date")
    checked_at = parse_datetime(values["checked_at"], f"{label}.checked_at")
    require(
        checked_at.astimezone(ZoneInfo(timezone)).date() == run_date,
        f"{label}.checked_at does not resolve to the run date",
    )
    require_boolean(values["verified"], f"{label}.verified")
    return original if canonical is not None else None


def validate_candidates(
    candidates: Any,
    selection: Any,
    complete_selection: bool,
    run_date: date,
    timezone: str,
) -> list[dict[str, Any]]:
    require(isinstance(candidates, list), "candidates must be an array")
    selection_values = exact_keys(
        selection,
        {"candidate_ids", "item_count", "shortfall_reason"},
        "selection",
    )
    selected_ids = selection_values["candidate_ids"]
    require(isinstance(selected_ids, list), "selection.candidate_ids must be an array")
    for index, candidate_id in enumerate(selected_ids):
        require_string(candidate_id, f"selection.candidate_ids[{index}]")
    require(len(selected_ids) == len(set(selected_ids)), "selection.candidate_ids contains duplicates")
    item_count = require_integer(selection_values["item_count"], "selection.item_count")
    require(item_count == len(selected_ids), "selection.item_count does not match candidate_ids")
    require(item_count <= 10, "selection.item_count exceeds 10")
    shortfall_reason = require_string(
        selection_values["shortfall_reason"],
        "selection.shortfall_reason",
        allow_empty=True,
    )
    if complete_selection:
        require(item_count >= 1, "terminal artifact states require at least one selected item")
        require(len(candidates) >= 14, "terminal artifact states require at least 14 candidates")
    if item_count == 10:
        require(not shortfall_reason, "a ten-item selection must not declare a shortfall")
    elif item_count > 0:
        require(bool(shortfall_reason.strip()), "a short selection must explain its shortfall")
    candidate_ids: list[str] = []
    candidates_by_id: dict[str, dict[str, Any]] = {}
    for index, candidate in enumerate(candidates):
        label = f"candidates[{index}]"
        values = exact_keys(candidate, CANDIDATE_KEYS, label)
        candidate_id = require_string(values["id"], f"{label}.id")
        candidate_ids.append(candidate_id)
        candidates_by_id[candidate_id] = values
        for key in ("person", "role_org", "why_it_matters", "summary", "theme"):
            require_string(values[key], f"{label}.{key}")
        require(len(values["summary"]) <= 500, f"{label}.summary exceeds 500 characters")
        confirmation_attempts = require_integer(
            values["confirmation_attempts"], f"{label}.confirmation_attempts"
        )
        require(confirmation_attempts <= 1, f"{label}.confirmation_attempts exceeds 1")
        status = values["status"]
        require(
            status in {"discovered", "verified", "selected", "rejected"},
            f"{label}.status is invalid",
        )
        rejection_reason = require_reason_code(
            values["rejection_reason"], f"{label}.rejection_reason", allow_empty=True
        )
        if status == "rejected":
            require(bool(rejection_reason.strip()), f"{label} must explain its rejection")
        else:
            require(not rejection_reason, f"{label} has a rejection reason without rejection")
        fingerprint = values["story_fingerprint"]
        if fingerprint is not None:
            fingerprint_text = require_string(fingerprint, f"{label}.story_fingerprint")
            require(
                fingerprint_text == normalized_text(fingerprint_text),
                f"{label}.story_fingerprint is not normalized",
            )
        history_overlap_reason = require_reason_code(
            values["history_overlap_reason"],
            f"{label}.history_overlap_reason",
            allow_empty=True,
        )
        require(
            history_overlap_reason in {"", "MATERIAL_NEW_DEVELOPMENT"},
            f"{label}.history_overlap_reason is unsupported",
        )
        scores = values["scores"]
        if scores is not None:
            validate_scores(scores, f"{label}.scores")
        sources = values["sources"]
        require(isinstance(sources, list) and sources, f"{label}.sources must not be empty")
        canonical_sources: list[str] = []
        verified_sources: set[str] = set()
        for source_index, source in enumerate(sources):
            source_label = f"{label}.sources[{source_index}]"
            canonical = validate_source(
                source,
                source_label,
                complete_selection,
                run_date,
                timezone,
            )
            if canonical is not None:
                canonical_sources.append(canonical)
                if source["verified"]:
                    verified_sources.add(canonical)
        require(
            len(canonical_sources) == len(set(canonical_sources)),
            f"{label}.sources contains duplicate URLs",
        )
        selected_source = values["selected_source_url"]
        if selected_source is not None:
            selected_canonical = canonicalize_url(selected_source, f"{label}.selected_source_url")
            require(
                selected_source == selected_canonical,
                f"{label}.selected_source_url is not normalized",
            )
            require(
                selected_canonical in verified_sources,
                f"{label}.selected_source_url is not a verified source",
            )
        if complete_selection:
            require(status in {"selected", "rejected"}, f"{label} is not terminally classified")
            require(fingerprint is not None, f"{label}.story_fingerprint is required")
            require(scores is not None, f"{label}.scores are required")
        if status == "selected":
            require(fingerprint is not None, f"{label}.story_fingerprint is required")
            require(scores is not None, f"{label}.scores are required")
    require(len(candidate_ids) == len(set(candidate_ids)), "candidate IDs must be unique")
    require(set(selected_ids) <= set(candidate_ids), "selection contains an unknown candidate ID")
    require(
        {item["id"] for item in candidates if item["status"] == "selected"} == set(selected_ids),
        "selected candidate statuses do not match selection.candidate_ids",
    )
    selected = [candidates_by_id[candidate_id] for candidate_id in selected_ids]
    selected_totals = [candidate["scores"]["total"] for candidate in selected]
    require(
        selected_totals == sorted(selected_totals, reverse=True),
        "selected candidates are not ranked by descending score",
    )
    if selected_totals:
        weakest_selected = selected_totals[-1]
        for candidate in candidates:
            if (
                candidate["status"] == "rejected"
                and candidate["rejection_reason"] == "LOWER_COMPOSITE_SCORE"
                and candidate["scores"] is not None
            ):
                require(
                    candidate["scores"]["total"] < weakest_selected,
                    "a lower-score rejection outranks a selected candidate",
                )
    unique_fields = {
        "people": [normalized_text(item["person"]) for item in selected],
        "themes": [normalized_text(item["theme"]) for item in selected],
        "story fingerprints": [normalized_text(item["story_fingerprint"]) for item in selected],
        "source URLs": [
            canonicalize_url(item["selected_source_url"], "selected source URL")
            for item in selected
        ],
    }
    for label, values in unique_fields.items():
        require(len(values) == len(set(values)), f"selected {label} must be unique")
    return selected


def content_fingerprint(selected: list[dict[str, Any]]) -> str:
    payload = [
        {
            "person": item["person"],
            "role_org": item["role_org"],
            "why_it_matters": item["why_it_matters"],
            "source_label": selected_source_label(item),
            "source_url": canonicalize_url(item["selected_source_url"], "selected source URL"),
            "summary": item["summary"],
        }
        for item in selected
    ]
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return sha256_bytes(encoded.encode("utf-8"))


def selected_source_label(candidate: dict[str, Any]) -> str:
    selected_url = canonicalize_url(candidate["selected_source_url"], "selected source URL")
    matching_sources = [
        source
        for source in candidate["sources"]
        if source["canonical_url"] is not None
        and canonicalize_url(source["canonical_url"], "selected source record URL") == selected_url
    ]
    require(len(matching_sources) == 1, "selected source must match exactly one source record")
    return require_string(matching_sources[0]["label"], "selected source label")


def validate_recent_dedupe(selected: list[dict[str, Any]], history: dict[str, Any]) -> None:
    prior_people = {normalized_text(person) for person in history["people"]}
    prior_themes = {normalized_text(theme) for theme in history["themes"]}
    prior_urls = set(history["urls"])
    for index, candidate in enumerate(selected):
        label = f"selected candidate {index + 1}"
        require(
            normalized_text(candidate["theme"]) not in prior_themes,
            f"{label} repeats a recent theme",
        )
        require(
            candidate["selected_source_url"] not in prior_urls,
            f"{label} repeats a recent source URL",
        )
        repeats_person = normalized_text(candidate["person"]) in prior_people
        if repeats_person:
            require(
                candidate["history_overlap_reason"] == "MATERIAL_NEW_DEVELOPMENT",
                f"{label} repeats a recent person without a material-development reason",
            )
            require(
                candidate["scores"]["novelty"] >= 4,
                f"{label} repeats a recent person without sufficient novelty",
            )
        else:
            require(
                not candidate["history_overlap_reason"],
                f"{label} declares a history overlap that does not exist",
            )


def validate_html(path: Path, state: dict[str, Any], selected: list[dict[str, Any]]) -> None:
    try:
        html_bytes = path.read_bytes()
        html_text = html_bytes.decode("utf-8")
    except FileNotFoundError as error:
        raise ValidationError(f"HTML artifact does not exist: {path}") from error
    except UnicodeDecodeError as error:
        raise ValidationError("HTML artifact must use UTF-8") from error
    parser = BriefHTMLParser()
    parser.feed(html_text)
    parser.close()
    artifact = state["artifact"]
    require(sha256_bytes(html_bytes) == artifact["sha256"], "artifact SHA-256 does not match HTML")
    require(parser.ol_count == 1, "HTML must contain exactly one ordered list")
    require(len(parser.h1_values) == 1, "HTML must contain exactly one h1")
    require(len(parser.footer_values) == 1, "HTML must contain exactly one footer")
    require(parser.title_count == 1 and bool(parser.title_parts), "HTML must contain exactly one title")
    run_date = state["date"]
    title = normalized_text(" ".join(parser.title_parts))
    heading = normalized_text(" ".join(parser.h1_values[0]))
    footer_text = " ".join(parser.footer_values[0])
    footer = normalized_text(footer_text)
    require(run_date in title, "HTML title does not contain the run date")
    require(run_date in heading, "HTML h1 does not contain the run date")
    require(run_date in footer, "HTML footer does not contain the run date")
    require("generated" in footer, "HTML footer does not identify a generated timestamp")
    require(
        state["timezone"].casefold() in footer_text.casefold(),
        "HTML footer does not contain the resolved timezone",
    )
    timestamp_match = re.search(
        rf"\b{re.escape(run_date)}[ T][0-9]{{2}}:[0-9]{{2}}(?::[0-9]{{2}})?\b",
        footer_text,
    )
    require(timestamp_match is not None, "HTML footer lacks a parseable generated timestamp")
    try:
        generated_at = datetime.fromisoformat(timestamp_match.group(0).replace(" ", "T"))
    except ValueError as error:
        raise ValidationError("HTML footer generated timestamp is invalid") from error
    require(generated_at.date().isoformat() == run_date, "HTML footer timestamp date mismatches")
    require(not parser.external_assets, "HTML must not contain executable or external-resource markup")
    for index, href in enumerate(parser.hrefs):
        canonicalize_url(href, f"HTML link {index + 1}")
    styles = " ".join(parser.style_parts)
    require(not UNSAFE_CSS_PATTERN.search(styles), "HTML CSS must not execute code or load assets")
    require(len(parser.articles) == len(selected), "HTML article count does not match selection")
    require(
        all(article["inside_ordered_list"] for article in parser.articles),
        "every HTML article must be inside the ordered list",
    )
    require(artifact["item_count"] == len(selected), "artifact item count does not match selection")
    for index, (article, candidate) in enumerate(zip(parser.articles, selected)):
        article_text = normalized_text(" ".join(article["text"]))
        expected_article_text = normalized_text(
            " ".join(
                [
                    candidate["person"],
                    candidate["role_org"],
                    "Why it matters:",
                    candidate["why_it_matters"],
                    candidate["summary"],
                    selected_source_label(candidate),
                ]
            )
        )
        require(
            article_text == expected_article_text,
            f"article {index + 1} public text does not exactly match selected fields",
        )
        hrefs = article["hrefs"]
        require(len(hrefs) == 1, f"article {index + 1} must contain one source link")
        require(
            canonicalize_url(hrefs[0], f"article {index + 1} source link")
            == canonicalize_url(candidate["selected_source_url"], "selected source URL"),
            f"article {index + 1} source link does not match state",
        )
    shortfall_reason = state["selection"]["shortfall_reason"]
    if shortfall_reason:
        document_text = normalized_text(" ".join(parser.document_parts))
        require(
            normalized_text(shortfall_reason) in document_text,
            "HTML does not contain the declared shortfall reason",
        )


def validate_artifact(
    artifact: Any,
    workspace: Path,
    state: dict[str, Any],
    selected: list[dict[str, Any]],
) -> None:
    values = exact_keys(artifact, ARTIFACT_KEYS, "artifact")
    artifact_path = safe_workspace_path(workspace, values["path"], "artifact.path")
    require(re.fullmatch(r"[a-f0-9]{64}", values["sha256"] or "") is not None, "artifact.sha256 is invalid")
    expected_fingerprint = content_fingerprint(selected)
    require(
        values["content_fingerprint"] == expected_fingerprint,
        "artifact content fingerprint does not match selected items",
    )
    item_count = require_integer(values["item_count"], "artifact.item_count", minimum=1)
    require(item_count <= 10, "artifact.item_count exceeds 10")
    validated = require_boolean(values["validated"], "artifact.validated")
    if validated:
        parse_datetime(values["validated_at"], "artifact.validated_at")
    else:
        require(
            state["status"] == "running" and state["current_node"] == "validate",
            "only the validate node may hold an unvalidated artifact",
        )
        require(values["validated_at"] is None, "unvalidated artifact must not have validated_at")
    validate_html(artifact_path, state, selected)


def validate_budgets(budgets: Any, graph: dict[str, Any]) -> None:
    expected = graph["budgets"]
    values = exact_keys(budgets, set(expected), "budgets")
    for name, maximum in expected.items():
        budget = exact_keys(values[name], {"used", "max"}, f"budgets.{name}")
        used = require_number(budget["used"], f"budgets.{name}.used")
        declared_max = require_number(budget["max"], f"budgets.{name}.max")
        require(declared_max == maximum, f"budgets.{name}.max does not match graph")
        require(used <= declared_max, f"budgets.{name} is exhausted beyond its limit")
        if name != "research_seconds":
            require(float(used).is_integer(), f"budgets.{name}.used must be an integer")


def reject_unsafe_trace_fields(value: Any, path: str = "trace") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = re.sub(r"[^a-z0-9]", "", key.casefold())
            require(
                all(fragment not in normalized_key for fragment in BANNED_TRACE_KEYS),
                f"{path} contains forbidden field {key}",
            )
            reject_unsafe_trace_fields(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_unsafe_trace_fields(item, f"{path}[{index}]")


def validate_trace(state: dict[str, Any], graph: dict[str, Any]) -> Counter[str]:
    trace = state["trace"]
    require(isinstance(trace, list) and trace, "trace must not be empty")
    reject_unsafe_trace_fields(trace)
    nodes = set(graph["nodes"])
    terminals = set(graph["terminal_nodes"])
    allowed_edges = {(edge["from"], edge["to"]) for edge in graph["edges"]}
    failure_target = graph["global_failure_target"]
    failure_exclusions = set(graph.get("global_failure_exclusions", []))
    attempts: Counter[str] = Counter()
    prior_revision = 0
    run_started_at = parse_datetime(state["started_at"], "started_at")
    run_finished_at = (
        parse_datetime(state["finished_at"], "finished_at")
        if state["finished_at"] is not None
        else None
    )
    prior_event_at = run_started_at
    research_duration_ms = 0
    targeted_searches = 0
    confirmation_searches = 0
    for index, event in enumerate(trace):
        label = f"trace[{index}]"
        values = exact_keys(event, TRACE_KEYS, label)
        sequence = require_integer(values["sequence"], f"{label}.sequence", minimum=1)
        require(sequence == index + 1, f"{label}.sequence is not contiguous")
        event_at = parse_datetime(values["at"], f"{label}.at")
        require(event_at >= run_started_at, f"{label}.at precedes the run")
        require(event_at >= prior_event_at, f"{label}.at is not chronological")
        if run_finished_at is not None:
            require(event_at <= run_finished_at, f"{label}.at follows the finished run")
        prior_event_at = event_at
        node = require_string(values["node"], f"{label}.node")
        require(node in nodes, f"{label}.node is unknown")
        attempts[node] += 1
        attempt = require_integer(values["attempt"], f"{label}.attempt", minimum=1)
        require(attempt == attempts[node], f"{label}.attempt is not contiguous")
        require(
            values["outcome"] in {"completed", "failed", "blocked", "retrying"},
            f"{label}.outcome is invalid",
        )
        route = require_string(values["route"], f"{label}.route", allow_empty=True)
        input_revision = require_integer(values["input_revision"], f"{label}.input_revision")
        output_revision = require_integer(values["output_revision"], f"{label}.output_revision", minimum=1)
        require(input_revision == prior_revision, f"{label}.input_revision breaks the revision chain")
        require(output_revision == input_revision + 1, f"{label} must increment revision once")
        prior_revision = output_revision
        require_integer(values["duration_ms"], f"{label}.duration_ms")
        if node in RESEARCH_NODES:
            research_duration_ms += values["duration_ms"]
        counts = values["counts"]
        require(isinstance(counts, dict), f"{label}.counts must be an object")
        require(set(counts) <= TRACE_COUNT_KEYS, f"{label}.counts has unknown keys")
        for key, count in counts.items():
            require_integer(count, f"{label}.counts.{key}")
        searches = counts.get("searches", 0)
        if node == "targeted_research":
            require("searches" in counts, f"{label}.counts must record targeted searches")
            targeted_searches += searches
        elif node == "verify_sources":
            require("searches" in counts, f"{label}.counts must record confirmation searches")
            confirmation_searches += searches
        else:
            require(searches == 0, f"{label}.counts.searches is only valid for research nodes")
        require_reason_code(values["reason_code"], f"{label}.reason_code")
        payload_fingerprint = values["payload_fingerprint"]
        idempotency_key = values["idempotency_key"]
        if node == "publish_update":
            require(
                isinstance(payload_fingerprint, str)
                and re.fullmatch(r"[a-f0-9]{64}", payload_fingerprint) is not None,
                f"{label}.payload_fingerprint is invalid",
            )
            require_string(idempotency_key, f"{label}.idempotency_key")
            require(state["artifact"] is not None, f"{label} requires an artifact")
            require(
                payload_fingerprint == state["artifact"]["content_fingerprint"],
                f"{label}.payload_fingerprint changed across publication attempts",
            )
            require(
                idempotency_key == state["publication"]["idempotency_key"],
                f"{label}.idempotency_key changed across publication attempts",
            )
        else:
            require(payload_fingerprint is None, f"{label}.payload_fingerprint must be null")
            require(idempotency_key is None, f"{label}.idempotency_key must be null")
        if index + 1 < len(trace):
            next_node = trace[index + 1].get("node")
            require(route == next_node, f"{label}.route does not match the next node")
            valid_failure = (
                next_node == failure_target
                and node not in terminals
                and node not in failure_exclusions
            )
            require(
                (node, next_node) in allowed_edges or valid_failure,
                f"invalid graph transition: {node} -> {next_node}",
            )
            if node == "quality_gate" and next_node == "targeted_research":
                require("selected" in counts, f"{label}.counts must record selected items")
                require(counts["selected"] < 10, "targeted research requires an unmet item target")
                require(
                    attempts["targeted_research"] < state["budgets"]["targeted_rounds"]["max"],
                    "targeted research requires remaining round budget",
                )
                require(
                    targeted_searches < state["budgets"]["targeted_searches"]["max"],
                    "targeted research requires remaining search budget",
                )
            if node == "quality_gate" and next_node == "render":
                require("selected" in counts, f"{label}.counts must record selected items")
                require(
                    counts["selected"] == state["selection"]["item_count"],
                    "final quality-gate count does not match selection",
                )
                if counts["selected"] < 10:
                    rounds = state["budgets"]["targeted_rounds"]
                    searches_budget = state["budgets"]["targeted_searches"]
                    require(
                        rounds["used"] == rounds["max"]
                        or searches_budget["used"] == searches_budget["max"],
                        "shortfall route requires an exhausted targeted-research budget",
                    )
            retry_reason_contracts = {
                ("validate", "render"): ARTIFACT_REPAIR_REASON_CODES,
                ("publish_update", "publish_update"): PUBLICATION_RETRY_REASON_CODES,
                ("live_verify", "live_verify"): LIVE_RETRY_REASON_CODES,
            }
            allowed_reason_codes = retry_reason_contracts.get((node, next_node))
            if allowed_reason_codes is not None:
                require(
                    values["reason_code"] in allowed_reason_codes,
                    f"{label}.reason_code is not retryable for this backedge",
                )
                if (node, next_node) == ("validate", "render"):
                    require(
                        attempts["render"] - 1 < state["budgets"]["artifact_repairs"]["max"],
                        "artifact repair requires remaining budget",
                    )
                elif (node, next_node) == ("publish_update", "publish_update"):
                    require(
                        attempts["publish_update"] - 1
                        < state["budgets"]["publish_retries"]["max"],
                        "publication retry requires remaining budget",
                    )
                elif (node, next_node) == ("live_verify", "live_verify"):
                    require(
                        attempts["live_verify"] < state["budgets"]["live_checks"]["max"],
                        "live verification retry requires remaining budget",
                    )
            expected_outcome = "retrying" if allowed_reason_codes is not None else "completed"
            require(
                values["outcome"] == expected_outcome,
                f"{label}.outcome does not match its route",
            )
        else:
            require(not route, f"{label}.route must be empty at the current node")
    require(trace[0]["node"] == graph["start_node"], "trace does not start at load_state")
    require(state["revision"] == prior_revision, "state revision does not match trace")
    require(state["current_node"] == trace[-1]["node"], "current_node does not match trace")
    run_status = state["status"]
    if run_status in TERMINAL_STATUS_NODES:
        require(
            trace[-1]["node"] == TERMINAL_STATUS_NODES[run_status],
            "terminal status does not match the final graph node",
        )
        expected_terminal_outcome = {
            "succeeded": "completed",
            "blocked": "blocked",
            "publish_failed": "failed",
            "failed": "failed",
        }[run_status]
        require(
            trace[-1]["outcome"] == expected_terminal_outcome,
            "terminal trace outcome does not match status",
        )
    else:
        require(trace[-1]["node"] not in terminals, "running state cannot end at a terminal node")
        require(trace[-1]["outcome"] == "completed", "running checkpoint outcome must be completed")
    node_status = state["node_status"]
    require(isinstance(node_status, dict), "node_status must be an object")
    require(set(node_status) <= nodes, "node_status contains an unknown node")
    for node, status_value in node_status.items():
        status = exact_keys(status_value, NODE_STATUS_KEYS, f"node_status.{node}")
        require_integer(status["attempts"], f"node_status.{node}.attempts")
        require(
            status["attempts"] == attempts[node],
            f"node_status.{node}.attempts does not match trace",
        )
        require(
            status["status"] in {"pending", "running", "completed", "failed", "blocked", "skipped"},
            f"node_status.{node}.status is invalid",
        )
        require_reason_code(
            status["last_error"],
            f"node_status.{node}.last_error",
            allow_empty=True,
        )
        if attempts[node] == 0:
            require(
                status["status"] in {"pending", "skipped"},
                f"node_status.{node}.status is invalid for an unvisited node",
            )
    for node, count in attempts.items():
        require(node in node_status, f"node_status is missing {node}")
        status = node_status[node]["status"]
        if node == state["current_node"]:
            expected_status = (
                {
                    "succeeded": "completed",
                    "blocked": "blocked",
                    "publish_failed": "failed",
                    "failed": "failed",
                }[run_status]
                if run_status in TERMINAL_STATUS_NODES
                else "running"
            )
        else:
            expected_status = "completed"
        require(status == expected_status, f"node_status.{node}.status does not match graph state")
        if node == state["current_node"] and run_status in {"blocked", "publish_failed", "failed"}:
            require(
                bool(node_status[node]["last_error"]),
                f"node_status.{node}.last_error must record the terminal reason",
            )
    budgets = state["budgets"]
    derived_usage = {
        "discovery_passes": attempts["parallel_discovery"],
        "targeted_rounds": attempts["targeted_research"],
        "artifact_repairs": max(0, attempts["render"] - 1),
        "publish_retries": max(0, attempts["publish_update"] - 1),
        "live_checks": attempts["live_verify"],
        "targeted_searches": targeted_searches,
    }
    for name, used in derived_usage.items():
        require(budgets[name]["used"] == used, f"budgets.{name}.used does not match trace")
    expected_research_seconds = research_duration_ms / 1000
    require(
        abs(budgets["research_seconds"]["used"] - expected_research_seconds) < 1e-9,
        "budgets.research_seconds.used does not match trace durations",
    )
    expected_confirmation_searches = sum(
        candidate["confirmation_attempts"] for candidate in state["candidates"]
    )
    require(
        confirmation_searches == expected_confirmation_searches,
        "confirmation search counts do not match candidates",
    )
    return attempts


def validate_errors(errors: Any, graph: dict[str, Any]) -> None:
    require(isinstance(errors, list), "errors must be an array")
    for index, error in enumerate(errors):
        label = f"errors[{index}]"
        values = exact_keys(error, ERROR_KEYS, label)
        require(values["node"] in graph["nodes"], f"{label}.node is unknown")
        require_reason_code(values["reason_code"], f"{label}.reason_code")
        message = require_string(values["message"], f"{label}.message")
        require(len(message) <= 500, f"{label}.message exceeds 500 characters")
        require_boolean(values["retryable"], f"{label}.retryable")
        parse_datetime(values["at"], f"{label}.at")


def validate_publication(
    publication: Any,
    state: dict[str, Any],
    fingerprint: str | None,
    attempts: Counter[str],
) -> None:
    values = exact_keys(publication, PUBLICATION_KEYS, "publication")
    require_boolean(values["required"], "publication.required")
    require(values["required"], "publication is required for a successful run")
    require(
        values["mode"] in {"content_refresh", "full_deployment"},
        "publication.mode is invalid",
    )
    require(
        values["authorization_status"] in {"not_required", "required"},
        "publication.authorization_status is invalid",
    )
    require_boolean(values["target_verified"], "publication.target_verified")
    require(
        values["delivery_status"] in {"not_attempted", "updated", "unchanged", "failed", "conflict"},
        "publication.delivery_status is invalid",
    )
    require(
        values["live_status"] in {"not_checked", "verified", "mismatch", "failed"},
        "publication.live_status is invalid",
    )
    require(
        values["archive_status"] in {"not_checked", "verified", "mismatch", "failed"},
        "publication.archive_status is invalid",
    )
    publication_attempts = require_integer(values["attempts"], "publication.attempts")
    live_checks = require_integer(values["live_checks"], "publication.live_checks")
    require(publication_attempts == attempts["publish_update"], "publication.attempts does not match trace")
    require(live_checks == attempts["live_verify"], "publication.live_checks does not match trace")
    require(
        publication_attempts <= state["budgets"]["publish_retries"]["max"] + 1,
        "publication attempts exceed the retry budget",
    )
    require(live_checks <= state["budgets"]["live_checks"]["max"], "live checks exceed their budget")
    for key in (
        "target_id",
        "target_url",
        "idempotency_key",
        "receipt_fingerprint",
        "live_fingerprint",
        "live_date",
        "archive_url",
        "archive_fingerprint",
        "archive_date",
    ):
        if values[key] is not None:
            require_string(values[key], f"publication.{key}")
    for key in ("receipt_fingerprint", "live_fingerprint", "archive_fingerprint"):
        if values[key] is not None:
            require(
                re.fullmatch(r"[a-f0-9]{64}", values[key]) is not None,
                f"publication.{key} is invalid",
            )
    for key in ("live_date", "archive_date"):
        if values[key] is not None:
            parse_date(values[key], f"publication.{key}")
    if values["live_item_count"] is not None:
        live_item_count = require_integer(
            values["live_item_count"],
            "publication.live_item_count",
            minimum=1,
        )
        require(live_item_count <= 10, "publication.live_item_count exceeds 10")
    if values["archive_item_count"] is not None:
        archive_item_count = require_integer(
            values["archive_item_count"],
            "publication.archive_item_count",
            minimum=1,
        )
        require(archive_item_count <= 10, "publication.archive_item_count exceeds 10")
    require_reason_code(
        values["failure_reason"],
        "publication.failure_reason",
        allow_empty=True,
    )
    if values["target_url"] is not None:
        canonicalize_url(values["target_url"], "publication.target_url")
    if values["target_verified"]:
        require_string(values["target_id"], "publication.target_id")
        require_string(values["target_url"], "publication.target_url")
    if values["archive_url"] is not None:
        canonicalize_url(values["archive_url"], "publication.archive_url")
    status = state["status"]
    if values["mode"] == "full_deployment":
        require(status == "blocked", "full_deployment must stop blocked for separate approval")
        require(
            values["authorization_status"] == "required",
            "full_deployment must record required approval",
        )
    else:
        require(
            values["authorization_status"] == "not_required",
            "content_refresh must use its preconfigured authorization boundary",
        )
        if fingerprint is not None:
            expected_key = f"daily-ai-brief/{state['date']}/{fingerprint}"
            require(
                values["idempotency_key"] == expected_key,
                "content_refresh idempotency key is invalid",
            )
    if publication_attempts > 0:
        require(values["mode"] == "content_refresh", "publication attempts require content_refresh")
        require(values["target_verified"], "publication attempts require a verified target")
        require(fingerprint is not None, "publication attempts require a validated artifact")
        require(state["artifact"]["validated"], "publication attempts require artifact validation")
        expected_key = f"daily-ai-brief/{state['date']}/{fingerprint}"
        require(values["idempotency_key"] == expected_key, "publication idempotency key is invalid")
    if values["delivery_status"] in {"updated", "unchanged"}:
        require(publication_attempts > 0, "delivered publication requires an attempt")
        require(fingerprint is not None, "delivered publication requires an artifact fingerprint")
        require(
            values["receipt_fingerprint"] == fingerprint,
            "publication receipt fingerprint mismatches",
        )
    if values["delivery_status"] != "not_attempted":
        require(publication_attempts > 0, "publication status requires an attempt")
    if live_checks > 0:
        require(
            values["delivery_status"] in {"updated", "unchanged"},
            "live verification requires successful delivery",
        )
    if values["live_status"] != "not_checked":
        require(live_checks > 0, "live status requires a live verification check")
    if values["archive_status"] != "not_checked":
        require(live_checks > 0, "archive status requires a live verification check")
    if values["live_status"] == "not_checked":
        require(
            all(
                values[key] is None
                for key in ("live_fingerprint", "live_date", "live_item_count")
            ),
            "unchecked live proof must be null",
        )
    if values["archive_status"] == "not_checked":
        require(
            all(
                values[key] is None
                for key in (
                    "archive_url",
                    "archive_fingerprint",
                    "archive_date",
                    "archive_item_count",
                )
            ),
            "unchecked archive proof must be null",
        )
    if values["live_status"] == "verified":
        require(fingerprint is not None, "live verification requires an artifact fingerprint")
        require(values["live_fingerprint"] == fingerprint, "live fingerprint mismatches")
        require(values["live_date"] == state["date"], "live date mismatches the run date")
        require(
            values["live_item_count"] == state["selection"]["item_count"],
            "live item count mismatches the selection",
        )
    if values["archive_status"] == "verified":
        require(fingerprint is not None, "archive verification requires an artifact fingerprint")
        require_string(values["archive_url"], "publication.archive_url")
        archive_url = canonicalize_url(values["archive_url"], "publication.archive_url")
        require(
            archive_url != canonicalize_url(values["target_url"], "publication.target_url"),
            "archive URL must be distinct from the mutable live target",
        )
        parsed_archive_url = urlsplit(archive_url)
        require(
            state["date"] in f"{parsed_archive_url.path}?{parsed_archive_url.query}",
            "archive URL must identify the run date",
        )
        require(
            values["archive_fingerprint"] == fingerprint,
            "archive fingerprint mismatches",
        )
        require(values["archive_date"] == state["date"], "archive date mismatches the run date")
        require(
            values["archive_item_count"] == state["selection"]["item_count"],
            "archive item count mismatches the selection",
        )
    success_proof_required = status == "succeeded" or (
        status == "running" and state["current_node"] == "persist_success"
    )
    if success_proof_required:
        require(values["target_verified"], "success requires a verified publication target")
        require(values["delivery_status"] in {"updated", "unchanged"}, "success requires delivery")
        require(values["live_status"] == "verified", "success requires live verification")
        require(values["archive_status"] == "verified", "success requires archive verification")
        require(fingerprint is not None, "success requires an artifact fingerprint")
        require(values["receipt_fingerprint"] == fingerprint, "publication receipt fingerprint mismatches")
        require(values["live_fingerprint"] == fingerprint, "live fingerprint mismatches")
        require(values["live_date"] == state["date"], "live date mismatches the run date")
        require(
            values["live_item_count"] == state["selection"]["item_count"],
            "live item count mismatches the selection",
        )
        expected_key = f"daily-ai-brief/{state['date']}/{fingerprint}"
        require(values["idempotency_key"] == expected_key, "publication idempotency key is invalid")
        require(not values["failure_reason"], "verified publication has a failure reason")
    elif status == "blocked":
        require(
            values["mode"] == "full_deployment" or not values["target_verified"],
            "blocked content_refresh requires an unverified target or adapter",
        )
        require(values["delivery_status"] == "not_attempted", "blocked state must not publish")
        require(values["live_status"] == "not_checked", "blocked state must not claim live checks")
        require(values["archive_status"] == "not_checked", "blocked state must not claim archive checks")
        require(publication_attempts == 0 and live_checks == 0, "blocked state must stop before mutation")
        require(bool(values["failure_reason"].strip()), "blocked state must record its blocker")
    elif status == "publish_failed":
        require(values["target_verified"], "publish_failed requires a verified target")
        failed_delivery = values["delivery_status"] in {"failed", "conflict"}
        failed_live = values["live_status"] in {"mismatch", "failed"}
        failed_archive = values["archive_status"] in {"mismatch", "failed"}
        require(
            failed_delivery or failed_live or failed_archive,
            "publish_failed lacks a publication failure",
        )
        require(bool(values["failure_reason"].strip()), "publish_failed must record a reason")


def split_run_log_blocks(text: str) -> list[str]:
    matches = list(re.finditer(r"(?m)^## .+$", text))
    blocks: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append(match.string[match.start() : end].strip() + "\n")
    return blocks


def hash_log_block(block: str) -> str:
    return sha256_bytes((block.strip() + "\n").encode("utf-8"))


def log_field(block: str, label: str) -> str | None:
    match = re.search(rf"(?m)^- {re.escape(label)}:\s*(.*)$", block)
    return match.group(1).strip() if match else None


def unique_history_values(values: list[str], urls: bool = False) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = canonicalize_url(value, "run log history URL") if urls else normalized_text(value)
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized if urls else value.strip())
    return result


def validate_history_against_run_log(text: str, state: dict[str, Any]) -> None:
    prior_blocks: list[str] = []
    for block in split_run_log_blocks(text):
        run_id_field = log_field(block, "Run ID")
        run_id = run_id_field.strip("`") if run_id_field is not None else None
        if run_id == state["run_id"]:
            continue
        people_field = log_field(block, "Selected people")
        themes_field = log_field(block, "Main themes")
        v1_fields = (
            "Source URLs",
            "Graph version",
            "Run state",
            "Publication",
            "Live edition",
            "Archive edition",
            "Run ID",
        )
        is_v1 = any(log_field(block, field) is not None for field in v1_fields)
        if is_v1:
            require(run_id is not None and bool(run_id), "v1 history entry is missing Run ID")
            require(people_field is not None, "v1 history entry is missing Selected people")
            require(themes_field is not None, "v1 history entry is missing Main themes")
            require(log_field(block, "Source URLs") is not None, "v1 history entry is missing Source URLs")
            publication_field = log_field(block, "Publication")
            require(
                publication_field is not None and "verified" in publication_field.casefold(),
                "v1 history entry is not a verified success",
            )
        if people_field is None or themes_field is None:
            continue
        prior_blocks.append(block)
    recent_blocks = prior_blocks[-2:]
    people: list[str] = []
    themes: list[str] = []
    urls: list[str] = []
    for block in recent_blocks:
        people.extend(item.strip() for item in log_field(block, "Selected people").split(",") if item.strip())
        themes.extend(item.strip() for item in log_field(block, "Main themes").split(",") if item.strip())
        urls_field = log_field(block, "Source URLs")
        if urls_field is not None:
            try:
                block_urls = json.loads(urls_field)
            except json.JSONDecodeError as error:
                raise ValidationError("run log history Source URLs must be JSON") from error
            require(isinstance(block_urls, list), "run log history Source URLs must be an array")
            urls.extend(
                canonicalize_url(url, "run log history source URL") for url in block_urls
            )
    expected_people = unique_history_values(people)
    expected_themes = unique_history_values(themes)
    expected_urls = unique_history_values(urls, urls=True)
    history = state["history"]
    require(history["runs_read"] == len(recent_blocks), "history.runs_read does not match run log")
    require(
        [normalized_text(value) for value in history["people"]]
        == [normalized_text(value) for value in expected_people],
        "history.people does not match the last two run-log entries",
    )
    require(
        [normalized_text(value) for value in history["themes"]]
        == [normalized_text(value) for value in expected_themes],
        "history.themes does not match the last two run-log entries",
    )
    require(history["urls"] == expected_urls, "history.urls does not match the last two run-log entries")


def validate_run_log_block(
    block: str,
    state: dict[str, Any],
    persistence: dict[str, Any],
    selected: list[dict[str, Any]],
) -> None:
    require(
        hash_log_block(block) == persistence["run_log_entry_sha256"],
        "run log entry digest mismatches",
    )
    required_fields = {
        "Produced/updated",
        "Selected people",
        "Main themes",
        "Source URLs",
        "Source-quality notes",
        "Resolved date/timezone",
        "Output file",
        "Shortfall reason",
        "Graph version",
        "Run state",
        "Publication",
        "Live edition",
        "Archive edition",
        "Run ID",
        "Runtime/workflow notes",
    }
    for field in required_fields:
        require(log_field(block, field) is not None, f"run log entry is missing {field}")
    require(block.startswith(f"## {state['date']} "), "run log heading date mismatches")
    source_urls_field = log_field(block, "Source URLs")
    try:
        source_urls = json.loads(source_urls_field)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValidationError("run log Source URLs must be a JSON array") from error
    require(isinstance(source_urls, list), "run log Source URLs must be a JSON array")
    canonical_log_urls = [
        canonicalize_url(url, f"run log Source URLs[{index}]")
        for index, url in enumerate(source_urls)
    ]
    expected_urls = [candidate["selected_source_url"] for candidate in selected]
    require(canonical_log_urls == expected_urls, "run log Source URLs do not match selection")
    require(source_urls == canonical_log_urls, "run log Source URLs are not normalized")
    expected_people = ", ".join(candidate["person"] for candidate in selected)
    expected_themes = ", ".join(candidate["theme"] for candidate in selected)
    require(log_field(block, "Selected people") == expected_people, "run log Selected people mismatches")
    require(log_field(block, "Main themes") == expected_themes, "run log Main themes mismatches")
    started_at = parse_datetime(state["started_at"], "started_at")
    local_started_at = started_at.astimezone(ZoneInfo(state["timezone"]))
    expected_resolved = (
        f"{state['date']}, {state['timezone']}, {local_started_at.strftime('%H:%M %Z')}"
    )
    require(
        log_field(block, "Resolved date/timezone") == expected_resolved,
        "run log resolved date/timezone mismatches",
    )
    require(state["artifact"]["path"] in log_field(block, "Output file"), "run log output path mismatches")
    require(state["graph_version"] in log_field(block, "Graph version"), "run log graph version mismatches")
    require(
        persistence["attempt_state_path"] in log_field(block, "Run state"),
        "run log state path mismatches",
    )
    publication_field = log_field(block, "Publication")
    require(state["publication"]["mode"] in publication_field, "run log publication mode mismatches")
    require("verified" in publication_field.casefold(), "run log publication is not verified")
    require(state["publication"]["target_url"] in log_field(block, "Live edition"), "run log live URL mismatches")
    require(
        state["publication"]["archive_url"] in log_field(block, "Archive edition"),
        "run log archive URL mismatches",
    )
    if state["selection"]["shortfall_reason"]:
        require(
            state["selection"]["shortfall_reason"] in log_field(block, "Shortfall reason"),
            "run log shortfall reason mismatches",
        )


def validate_persistence(
    persistence: Any,
    workspace: Path,
    state_path: Path,
    state: dict[str, Any],
    selected: list[dict[str, Any]],
) -> None:
    values = exact_keys(persistence, PERSISTENCE_KEYS, "persistence")
    declared_state_path = safe_workspace_path(
        workspace, values["attempt_state_path"], "persistence.attempt_state_path"
    )
    require(declared_state_path == state_path.resolve(), "attempt state path does not match the validated file")
    run_log_path = safe_workspace_path(workspace, values["run_log_path"], "persistence.run_log_path")
    require(
        values["run_log_status"] in {"not_written", "pending_append", "written"},
        "run_log_status is invalid",
    )
    if values["run_log_entry_sha256"] is not None:
        require(
            re.fullmatch(r"[a-f0-9]{64}", values["run_log_entry_sha256"]) is not None,
            "run_log_entry_sha256 is invalid",
        )
    text = run_log_path.read_text(encoding="utf-8") if run_log_path.exists() else ""
    validate_history_against_run_log(text, state)
    blocks = [
        block
        for block in split_run_log_blocks(text)
        if log_field(block, "Run ID") is not None
        and log_field(block, "Run ID").strip("`") == state["run_id"]
    ]
    if values["run_log_status"] == "not_written":
        require(state["status"] != "succeeded", "succeeded state must write the success run log")
        require(not blocks, "unsuccessful run must not appear in the success run log")
        require(values["run_log_entry_sha256"] is None, "unwritten run log entry has a digest")
        return
    if values["run_log_status"] == "pending_append":
        require(
            state["status"] == "running" and state["current_node"] == "persist_success",
            "pending_append is only valid at persist_success",
        )
        require(values["run_log_entry_sha256"] is not None, "pending_append requires a digest")
        require(len(blocks) <= 1, "pending_append found duplicate matching Run IDs")
        if blocks:
            validate_run_log_block(blocks[0], state, values, selected)
        return
    require(state["status"] == "succeeded", "only succeeded state may write the success run log")
    require(len(blocks) == 1, "success run log must contain exactly one matching Run ID")
    validate_run_log_block(blocks[0], state, values, selected)


def validate_run(
    state_path: Path,
    workspace: Path,
    graph_path: Path | None = None,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    skill_root = Path(__file__).resolve().parents[1]
    resolved_graph_path = graph_path or skill_root / "references" / "workflow-graph.json"
    resolved_schema_path = schema_path or skill_root / "references" / "run-state.schema.json"
    graph = load_contracts(resolved_graph_path, resolved_schema_path)
    state = exact_keys(load_json(state_path, "run state"), TOP_LEVEL_KEYS, "run state")
    require(state["schema_version"] == STATE_SCHEMA_VERSION, "run state schema version is unsupported")
    require(state["graph_version"] == graph["graph_version"], "run state graph version is unsupported")
    require_integer(state["revision"], "revision", minimum=1)
    require_string(state["run_id"], "run_id")
    run_date = parse_date(state["date"], "date")
    timezone = require_string(state["timezone"], "timezone")
    started_at = parse_datetime(state["started_at"], "started_at")
    validate_run_clock(run_date, timezone, started_at)
    require(
        state["status"] in {"running", "blocked", "publish_failed", "failed", "succeeded"},
        "status is invalid",
    )
    if state["status"] == "running":
        require(state["finished_at"] is None, "running state must not have finished_at")
    else:
        parse_datetime(state["finished_at"], "finished_at")
    validate_history(state["history"])
    validate_budgets(state["budgets"], graph)
    selected = validate_candidates(
        state["candidates"],
        state["selection"],
        state["artifact"] is not None
        or state["status"] in {"succeeded", "blocked", "publish_failed"},
        run_date,
        timezone,
    )
    validate_recent_dedupe(selected, state["history"])
    attempts = validate_trace(state, graph)
    if state["artifact"] is not None and 0 < state["selection"]["item_count"] < 10:
        rounds = state["budgets"]["targeted_rounds"]
        searches = state["budgets"]["targeted_searches"]
        require(
            rounds["used"] == rounds["max"] or searches["used"] == searches["max"],
            "shortfall requires an exhausted targeted-research budget",
        )
    validate_errors(state["errors"], graph)
    if state["status"] in {"blocked", "publish_failed", "failed"}:
        terminal_reason = state["trace"][-1]["reason_code"]
        require(
            any(
                error["node"] == state["current_node"]
                and error["reason_code"] == terminal_reason
                for error in state["errors"]
            ),
            "terminal reason does not match recorded error",
        )
        require(
            state["node_status"][state["current_node"]]["last_error"] == terminal_reason,
            "terminal reason does not match node status",
        )
        if state["status"] in {"blocked", "publish_failed"}:
            require(
                state["publication"]["failure_reason"] == terminal_reason,
                "publication failure reason does not match terminal reason",
            )
    artifact_fingerprint = None
    if state["artifact"] is not None:
        validate_artifact(state["artifact"], workspace, state, selected)
        artifact_fingerprint = state["artifact"]["content_fingerprint"]
    elif state["status"] in {"succeeded", "blocked", "publish_failed"}:
        raise ValidationError("terminal artifact state is missing its artifact")
    validate_publication(state["publication"], state, artifact_fingerprint, attempts)
    if state["status"] == "succeeded":
        require(not state["errors"], "succeeded state must not contain errors")
    elif state["status"] in {"blocked", "publish_failed", "failed"}:
        require(bool(state["errors"]), f"{state['status']} state must record an error")
    validate_persistence(state["persistence"], workspace, state_path, state, selected)
    return {
        "run_id": state["run_id"],
        "status": state["status"],
        "items": state["selection"]["item_count"],
        "graph_version": state["graph_version"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--workspace", default=Path.cwd(), type=Path)
    parser.add_argument("--graph", type=Path)
    parser.add_argument("--schema", type=Path)
    arguments = parser.parse_args()
    try:
        result = validate_run(
            state_path=arguments.state.resolve(),
            workspace=arguments.workspace.resolve(),
            graph_path=arguments.graph.resolve() if arguments.graph else None,
            schema_path=arguments.schema.resolve() if arguments.schema else None,
        )
    except ValidationError as error:
        print(f"validation failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
