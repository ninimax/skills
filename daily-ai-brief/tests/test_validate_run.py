from __future__ import annotations

import copy
import html
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_run import (
    RESEARCH_NODES,
    ValidationError,
    content_fingerprint,
    hash_log_block,
    sha256_bytes,
    validate_run,
)


RUN_DATE = "2026-08-03"
TIMESTAMP = "2026-08-03T09:00:00+02:00"
GRAPH_VERSION = "daily-ai-brief.graph/v1"
SCHEMA_VERSION = "daily-ai-brief.run/v1"


class RunFixture:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def candidate(self, index: int, selected_count: int, summary: str | None = None) -> dict:
        selected = index < selected_count
        score = 5 if selected else 4
        source_url = f"https://example.com/story-{index + 1}"
        return {
            "id": f"candidate-{index + 1}",
            "person": f"Person {index + 1}",
            "role_org": f"Role {index + 1}, Organization {index + 1}",
            "why_it_matters": f"Why story {index + 1} matters for agent engineering.",
            "summary": summary or f"Verified summary for consequential AI story {index + 1}.",
            "theme": f"Theme {index + 1}",
            "story_fingerprint": f"story-{index + 1}",
            "history_overlap_reason": "",
            "selected_source_url": source_url if selected else None,
            "sources": [
                {
                    "label": f"Primary source {index + 1}",
                    "original_url": source_url,
                    "canonical_url": source_url,
                    "tier": 0,
                    "kind": "primary",
                    "published_date": RUN_DATE,
                    "checked_at": TIMESTAMP,
                    "verified": selected,
                }
            ],
            "scores": {
                "impact": score,
                "source_quality": score,
                "freshness": score,
                "influence": score,
                "novelty": score,
                "total": 100 if selected else 80,
            },
            "confirmation_attempts": 0,
            "status": "selected" if selected else "rejected",
            "rejection_reason": "" if selected else "LOWER_COMPOSITE_SCORE",
        }

    def html_document(self, candidates: list[dict], shortfall_reason: str) -> str:
        shortfall = f"<p>{html.escape(shortfall_reason)}</p>" if shortfall_reason else ""
        articles = []
        for candidate in candidates:
            articles.append(
                "".join(
                    [
                        "<li><article>",
                        f"<h2>{html.escape(candidate['person'])}</h2>",
                        f"<p>{html.escape(candidate['role_org'])}</p>",
                        f"<p><strong>Why it matters:</strong> {html.escape(candidate['why_it_matters'])}</p>",
                        f"<p>{html.escape(candidate['summary'])}</p>",
                        f"<a href=\"{html.escape(candidate['selected_source_url'])}\">{html.escape(candidate['sources'][0]['label'])}</a>",
                        "</article></li>",
                    ]
                )
            )
        return "".join(
            [
                "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">",
                f"<title>Daily AI Brief - {RUN_DATE}</title>",
                "<style>body{font-family:system-ui}article{padding:1rem}</style></head><body><main>",
                f"<header><h1>Daily AI Brief - {RUN_DATE}</h1>{shortfall}</header><ol>",
                "".join(articles),
                f"</ol><footer>Generated {RUN_DATE} 09:00 CEST · Europe/Stockholm</footer>",
                "</main></body></html>",
            ]
        )

    def trace(
        self,
        nodes: list[str],
        candidate_count: int,
        selected_count: int,
        fingerprint: str,
        idempotency_key: str | None,
    ) -> tuple[list[dict], dict]:
        attempts: Counter[str] = Counter()
        events = []
        for index, node in enumerate(nodes):
            attempts[node] += 1
            final = index + 1 == len(nodes)
            outcome = "completed"
            if final and node == "blocked":
                outcome = "blocked"
            elif final and node in {"publish_failed", "failed"}:
                outcome = "failed"
            elif not final and nodes[index + 1] == node:
                outcome = "retrying"
            elif not final and (node, nodes[index + 1]) == ("validate", "render"):
                outcome = "retrying"
            reason_code = node.upper()
            if not final and nodes[index + 1] == node:
                reason_code = (
                    "NETWORK_TRANSIENT"
                    if node == "publish_update"
                    else "LIVE_READ_TRANSIENT"
                )
            elif not final and (node, nodes[index + 1]) == ("validate", "render"):
                reason_code = "ARTIFACT_REPAIRABLE"
            counts = {
                "candidates": candidate_count,
                "selected": selected_count,
            }
            if node == "targeted_research":
                counts["searches"] = 2
            elif node == "verify_sources":
                counts["searches"] = 0
            events.append(
                {
                    "sequence": index + 1,
                    "at": TIMESTAMP,
                    "node": node,
                    "attempt": attempts[node],
                    "outcome": outcome,
                    "route": "" if final else nodes[index + 1],
                    "input_revision": index,
                    "output_revision": index + 1,
                    "duration_ms": 10,
                    "counts": counts,
                    "reason_code": reason_code,
                    "payload_fingerprint": fingerprint if node == "publish_update" else None,
                    "idempotency_key": idempotency_key if node == "publish_update" else None,
                }
            )
        statuses = {}
        for node, count in attempts.items():
            status = "completed"
            if node == "blocked":
                status = "blocked"
            elif node in {"publish_failed", "failed"}:
                status = "failed"
            statuses[node] = {"status": status, "attempts": count, "last_error": ""}
        return events, statuses

    def log_block(self, state: dict, selected: list[dict]) -> str:
        people = ", ".join(candidate["person"] for candidate in selected)
        themes = ", ".join(candidate["theme"] for candidate in selected)
        urls = json.dumps([candidate["selected_source_url"] for candidate in selected])
        shortfall = state["selection"]["shortfall_reason"] or "None; 10 sourced items produced."
        return f"""## {RUN_DATE} 09:00 CEST

- Produced/updated: `{state['artifact']['path']}`
- Selected people: {people}
- Main themes: {themes}
- Source URLs: {urls}
- Source-quality notes: Verified primary sources selected.
- Resolved date/timezone: {RUN_DATE}, Europe/Stockholm, 09:00 CEST
- Output file: `{state['artifact']['path']}`
- Shortfall reason: {shortfall}
- Graph version: `{GRAPH_VERSION}`
- Run state: `{state['persistence']['attempt_state_path']}`
- Publication: content_refresh, verified
- Live edition: {state['publication']['target_url']}
- Archive edition: {state['publication']['archive_url']}
- Run ID: `{state['run_id']}`
- Runtime/workflow notes: Bounded graph completed with live verification.
"""

    def prior_log(self) -> str:
        return """## 2026-08-01 09:00 CEST

- Produced/updated: `daily-ai-brief-2026-08-01.html`
- Selected people: Legacy Person
- Main themes: Legacy Theme
- Source-quality notes: Legacy entry without v1 fields.
- Resolved date/timezone: 2026-08-01, Europe/Stockholm, 09:00 CEST
- Output file: `daily-ai-brief-2026-08-01.html`
- Shortfall reason: None
- Runtime/workflow notes: Legacy success entry.

## 2026-08-02 09:00 CEST

- Produced/updated: `daily-ai-brief-2026-08-02.html`
- Selected people: Previous Person 1
- Main themes: Previous Theme 1
- Source URLs: ["https://example.com/previous-1"]
- Source-quality notes: Verified primary source.
- Resolved date/timezone: 2026-08-02, Europe/Stockholm, 09:00 CEST
- Output file: `daily-ai-brief-2026-08-02.html`
- Shortfall reason: None
- Graph version: `daily-ai-brief.graph/v1`
- Run state: `.daily-ai-brief/runs/prior.json`
- Publication: content_refresh, verified
- Live edition: https://daily.example.test/edition/2026-08-02
- Archive edition: https://daily.example.test/archive/2026-08-02
- Run ID: `prior-run`
- Runtime/workflow notes: Prior v1 success entry.

"""

    def build(
        self,
        status: str = "succeeded",
        selected_count: int = 10,
        targeted_rounds: int = 0,
        publish_attempts: int = 1,
        artifact_repairs: int = 0,
        live_check_attempts: int = 1,
        publish_failure_stage: str = "delivery",
        summary_overrides: dict[int, str] | None = None,
    ) -> tuple[Path, dict]:
        summaries = summary_overrides or {}
        candidates = [
            self.candidate(index, selected_count, summaries.get(index)) for index in range(14)
        ]
        selected = candidates[:selected_count]
        shortfall_reason = (
            "8/10 - two candidates failed source-quality checks."
            if selected_count < 10
            else ""
        )
        artifact_relative = f"daily-ai-brief-{RUN_DATE}.html"
        artifact_path = self.workspace / artifact_relative
        artifact_html = self.html_document(selected, shortfall_reason)
        artifact_path.write_text(artifact_html, encoding="utf-8")
        fingerprint = content_fingerprint(selected)
        run_id = f"{RUN_DATE}T090000+0200-test-{status}-{selected_count}-{targeted_rounds}-{publish_attempts}"
        state_relative = f".daily-ai-brief/runs/{run_id}.json"
        state_path = self.workspace / state_relative
        state_path.parent.mkdir(parents=True, exist_ok=True)
        run_log_relative = ".daily-ai-brief/run-log.md"
        run_log_path = self.workspace / run_log_relative
        base_nodes = [
            "load_state",
            "parallel_discovery",
            "normalize",
            "verify_sources",
            "score_dedupe",
            "quality_gate",
        ]
        for _ in range(targeted_rounds):
            base_nodes.extend(
                [
                    "targeted_research",
                    "normalize",
                    "verify_sources",
                    "score_dedupe",
                    "quality_gate",
                ]
            )
        base_nodes.extend(["render", "validate"])
        for _ in range(artifact_repairs):
            base_nodes.extend(["render", "validate"])
        if status == "succeeded":
            nodes = base_nodes + ["publish_update"] * publish_attempts + [
                *(["live_verify"] * live_check_attempts),
                "persist_success",
                "done",
            ]
        elif status == "blocked":
            nodes = base_nodes + ["blocked"]
        elif status == "publish_failed":
            nodes = base_nodes + ["publish_update"] * publish_attempts
            if publish_failure_stage in {"live", "archive"}:
                nodes += ["live_verify"] * live_check_attempts
            nodes += ["publish_failed"]
        else:
            nodes = base_nodes + ["failed"]
        publication_key = f"daily-ai-brief/{RUN_DATE}/{fingerprint}"
        trace, node_status = self.trace(
            nodes,
            len(candidates),
            selected_count,
            fingerprint,
            publication_key,
        )
        live_checks = nodes.count("live_verify")
        publication = {
            "required": True,
            "mode": "content_refresh",
            "authorization_status": "not_required",
            "target_verified": status in {"succeeded", "publish_failed"},
            "target_id": "existing-daily-brief" if status in {"succeeded", "publish_failed"} else None,
            "target_url": (
                f"https://daily.example.test/edition/{RUN_DATE}"
                if status in {"succeeded", "publish_failed"}
                else None
            ),
            "idempotency_key": publication_key,
            "delivery_status": (
                "updated"
                if status == "succeeded"
                or (status == "publish_failed" and publish_failure_stage in {"live", "archive"})
                else "failed"
                if status == "publish_failed"
                else "not_attempted"
            ),
            "live_status": (
                "verified"
                if status == "succeeded"
                or (status == "publish_failed" and publish_failure_stage == "archive")
                else "mismatch"
                if status == "publish_failed" and publish_failure_stage == "live"
                else "not_checked"
            ),
            "attempts": nodes.count("publish_update"),
            "live_checks": live_checks,
            "receipt_fingerprint": (
                fingerprint
                if status == "succeeded"
                or (status == "publish_failed" and publish_failure_stage in {"live", "archive"})
                else None
            ),
            "live_fingerprint": (
                fingerprint
                if status == "succeeded"
                or (status == "publish_failed" and publish_failure_stage == "archive")
                else "0" * 64
                if status == "publish_failed" and publish_failure_stage == "live"
                else None
            ),
            "live_date": (
                RUN_DATE
                if status == "succeeded"
                or (status == "publish_failed" and publish_failure_stage in {"live", "archive"})
                else None
            ),
            "live_item_count": (
                selected_count
                if status == "succeeded"
                or (status == "publish_failed" and publish_failure_stage in {"live", "archive"})
                else None
            ),
            "archive_url": (
                f"https://daily.example.test/archive/{RUN_DATE}"
                if status == "succeeded"
                or (status == "publish_failed" and publish_failure_stage == "archive")
                else None
            ),
            "archive_status": (
                "verified"
                if status == "succeeded"
                else "mismatch"
                if status == "publish_failed" and publish_failure_stage == "archive"
                else "not_checked"
            ),
            "archive_fingerprint": (
                fingerprint
                if status == "succeeded"
                else "0" * 64
                if status == "publish_failed" and publish_failure_stage == "archive"
                else None
            ),
            "archive_date": (
                RUN_DATE
                if status == "succeeded"
                or (status == "publish_failed" and publish_failure_stage == "archive")
                else None
            ),
            "archive_item_count": (
                selected_count
                if status == "succeeded"
                or (status == "publish_failed" and publish_failure_stage == "archive")
                else None
            ),
            "failure_reason": (
                "SITES_TARGET_UNVERIFIED"
                if status == "blocked"
                else "ARCHIVE_MISMATCH"
                if status == "publish_failed" and publish_failure_stage == "archive"
                else "LIVE_MISMATCH"
                if status == "publish_failed" and publish_failure_stage == "live"
                else "DELIVERY_RETRIES_EXHAUSTED"
                if status == "publish_failed"
                else ""
            ),
        }
        errors = []
        if status in {"blocked", "publish_failed", "failed"}:
            errors.append(
                {
                    "node": status,
                    "reason_code": publication["failure_reason"] or "RUN_FAILED",
                    "message": publication["failure_reason"] or "The run failed validation.",
                    "retryable": False,
                    "at": TIMESTAMP,
                }
            )
            trace[-1]["reason_code"] = errors[0]["reason_code"]
            node_status[nodes[-1]]["last_error"] = errors[0]["reason_code"]
        state = {
            "schema_version": SCHEMA_VERSION,
            "graph_version": GRAPH_VERSION,
            "revision": len(trace),
            "run_id": run_id,
            "date": RUN_DATE,
            "timezone": "Europe/Stockholm",
            "started_at": TIMESTAMP,
            "finished_at": TIMESTAMP,
            "status": status,
            "current_node": nodes[-1],
            "budgets": {
                "research_seconds": {
                    "used": sum(
                        event["duration_ms"]
                        for event in trace
                        if event["node"] in RESEARCH_NODES
                    )
                    / 1000,
                    "max": 600,
                },
                "discovery_passes": {"used": nodes.count("parallel_discovery"), "max": 1},
                "targeted_rounds": {"used": nodes.count("targeted_research"), "max": 2},
                "targeted_searches": {
                    "used": sum(
                        event["counts"].get("searches", 0)
                        for event in trace
                        if event["node"] == "targeted_research"
                    ),
                    "max": 8,
                },
                "artifact_repairs": {"used": max(0, nodes.count("render") - 1), "max": 1},
                "publish_retries": {"used": max(0, nodes.count("publish_update") - 1), "max": 2},
                "live_checks": {"used": live_checks, "max": 3},
            },
            "history": {
                "runs_read": 2,
                "people": ["Legacy Person", "Previous Person 1"],
                "themes": ["Legacy Theme", "Previous Theme 1"],
                "urls": ["https://example.com/previous-1"],
            },
            "candidates": candidates,
            "selection": {
                "candidate_ids": [candidate["id"] for candidate in selected],
                "item_count": selected_count,
                "shortfall_reason": shortfall_reason,
            },
            "artifact": {
                "path": artifact_relative,
                "sha256": sha256_bytes(artifact_html.encode("utf-8")),
                "content_fingerprint": fingerprint,
                "item_count": selected_count,
                "validated": True,
                "validated_at": TIMESTAMP,
            },
            "publication": publication,
            "persistence": {
                "attempt_state_path": state_relative,
                "run_log_path": run_log_relative,
                "run_log_status": "written" if status == "succeeded" else "not_written",
                "run_log_entry_sha256": None,
            },
            "node_status": node_status,
            "trace": trace,
            "errors": errors,
        }
        if status == "succeeded":
            block = self.log_block(state, selected)
            run_log_path.write_text(self.prior_log() + block, encoding="utf-8")
            state["persistence"]["run_log_entry_sha256"] = hash_log_block(block)
        else:
            run_log_path.write_text(self.prior_log(), encoding="utf-8")
        self.write_state(state_path, state)
        return state_path, state

    def write_state(self, state_path: Path, state: dict) -> None:
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    def write_artifact(self, state: dict, artifact_html: str) -> None:
        artifact_path = self.workspace / state["artifact"]["path"]
        artifact_path.write_text(artifact_html, encoding="utf-8")
        state["artifact"]["sha256"] = sha256_bytes(artifact_html.encode("utf-8"))

    def refresh_log_hash(self, state: dict) -> None:
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        blocks = run_log_path.read_text(encoding="utf-8").split(f"## {RUN_DATE} 09:00 CEST", 1)
        current = f"## {RUN_DATE} 09:00 CEST" + blocks[1]
        state["persistence"]["run_log_entry_sha256"] = hash_log_block(current)


class ValidateRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary_directory.name)
        self.fixture = RunFixture(self.workspace)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def assert_valid(self, state_path: Path) -> dict:
        return validate_run(state_path, self.workspace)

    def assert_invalid(self, state_path: Path, message: str | None = None) -> None:
        with self.assertRaises(ValidationError) as context:
            self.assert_valid(state_path)
        if message:
            self.assertIn(message, str(context.exception))

    def test_valid_success_with_legacy_log_history(self) -> None:
        state_path, _ = self.fixture.build()
        result = self.assert_valid(state_path)
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["items"], 10)

    def test_rejects_history_omitted_from_state(self) -> None:
        state_path, state = self.fixture.build()
        state["history"] = {"runs_read": 0, "people": [], "themes": [], "urls": []}
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "history.runs_read does not match run log")

    def test_rejects_v1_history_entry_without_urls(self) -> None:
        state_path, state = self.fixture.build()
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        run_log_path.write_text(
            run_log_path.read_text(encoding="utf-8").replace(
                '- Source URLs: ["https://example.com/previous-1"]\n',
                "",
            ),
            encoding="utf-8",
        )
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "v1 history entry is missing Source URLs")

    def test_rejects_incomplete_recent_v1_history_entry(self) -> None:
        state_path, state = self.fixture.build()
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        run_log_path.write_text(
            run_log_path.read_text(encoding="utf-8").replace(
                "- Selected people: Previous Person 1\n",
                "",
            ),
            encoding="utf-8",
        )
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "v1 history entry is missing Selected people")

    def test_v1_history_cannot_be_demoted_to_legacy(self) -> None:
        state_path, state = self.fixture.build()
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        heading = f"## {RUN_DATE} 09:00 CEST"
        prior, current = run_log_path.read_text(encoding="utf-8").split(heading, 1)
        for label in ("Source URLs", "Graph version", "Run state", "Run ID"):
            prior = re_sub_line(prior, label)
        run_log_path.write_text(prior + heading + current, encoding="utf-8")
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "v1 history entry is missing Run ID")

    def test_cli_validates_a_successful_run(self) -> None:
        state_path, _ = self.fixture.build()
        completed = subprocess.run(
            [
                sys.executable,
                str(SKILL_ROOT / "scripts" / "validate_run.py"),
                "--workspace",
                str(self.workspace),
                "--state",
                str(state_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "succeeded")

    def test_valid_shortfall_after_targeted_fill(self) -> None:
        state_path, _ = self.fixture.build(selected_count=8, targeted_rounds=2)
        result = self.assert_valid(state_path)
        self.assertEqual(result["items"], 8)

    def test_rejects_shortfall_before_targeted_budget_exhaustion(self) -> None:
        state_path, _ = self.fixture.build(selected_count=8, targeted_rounds=1)
        self.assert_invalid(state_path, "shortfall route requires")

    def test_rejects_targeted_research_when_item_target_is_met(self) -> None:
        state_path, _ = self.fixture.build(selected_count=10, targeted_rounds=1)
        self.assert_invalid(state_path, "unmet item target")

    def test_local_validation_gate_accepts_unmarked_artifact(self) -> None:
        state_path, state = self.fixture.build(status="blocked")
        state["status"] = "running"
        state["current_node"] = "validate"
        state["finished_at"] = None
        state["artifact"]["validated"] = False
        state["artifact"]["validated_at"] = None
        state["trace"] = state["trace"][:-1]
        state["trace"][-1]["route"] = ""
        state["revision"] = len(state["trace"])
        state["node_status"].pop("blocked")
        state["node_status"]["validate"]["status"] = "running"
        state["errors"] = []
        self.fixture.write_state(state_path, state)
        result = self.assert_valid(state_path)
        self.assertEqual(result["status"], "running")

    def test_pre_persistence_gate_requires_live_proof(self) -> None:
        state_path, state = self.fixture.build()
        state["status"] = "running"
        state["current_node"] = "persist_success"
        state["finished_at"] = None
        state["trace"] = state["trace"][:-1]
        state["trace"][-1]["route"] = ""
        state["revision"] = len(state["trace"])
        state["node_status"].pop("done")
        state["node_status"]["persist_success"]["status"] = "running"
        state["persistence"]["run_log_status"] = "not_written"
        state["persistence"]["run_log_entry_sha256"] = None
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        run_log_path.write_text(self.fixture.prior_log(), encoding="utf-8")
        self.fixture.write_state(state_path, state)
        self.assert_valid(state_path)
        state["publication"]["live_fingerprint"] = "0" * 64
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "live fingerprint")

    def test_pending_append_recovers_exact_existing_log_entry(self) -> None:
        state_path, state = self.fixture.build()
        state["status"] = "running"
        state["current_node"] = "persist_success"
        state["finished_at"] = None
        state["trace"] = state["trace"][:-1]
        state["trace"][-1]["route"] = ""
        state["revision"] = len(state["trace"])
        state["node_status"].pop("done")
        state["node_status"]["persist_success"]["status"] = "running"
        state["persistence"]["run_log_status"] = "pending_append"
        self.fixture.write_state(state_path, state)
        result = self.assert_valid(state_path)
        self.assertEqual(result["status"], "running")

    def test_pending_append_allows_preappend_checkpoint(self) -> None:
        state_path, state = self.fixture.build()
        state["status"] = "running"
        state["current_node"] = "persist_success"
        state["finished_at"] = None
        state["trace"] = state["trace"][:-1]
        state["trace"][-1]["route"] = ""
        state["revision"] = len(state["trace"])
        state["node_status"].pop("done")
        state["node_status"]["persist_success"]["status"] = "running"
        state["persistence"]["run_log_status"] = "pending_append"
        (self.workspace / state["persistence"]["run_log_path"]).write_text(
            self.fixture.prior_log(),
            encoding="utf-8",
        )
        self.fixture.write_state(state_path, state)
        self.assert_valid(state_path)

    def test_pending_append_rejects_mismatched_existing_entry(self) -> None:
        state_path, state = self.fixture.build()
        state["status"] = "running"
        state["current_node"] = "persist_success"
        state["finished_at"] = None
        state["trace"] = state["trace"][:-1]
        state["trace"][-1]["route"] = ""
        state["revision"] = len(state["trace"])
        state["node_status"].pop("done")
        state["node_status"]["persist_success"]["status"] = "running"
        state["persistence"]["run_log_status"] = "pending_append"
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        run_log_path.write_text(
            run_log_path.read_text(encoding="utf-8").replace(
                "Verified primary sources selected.",
                "Changed after digest creation.",
            ),
            encoding="utf-8",
        )
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "digest mismatches")

    def test_succeeded_state_cannot_skip_success_log(self) -> None:
        state_path, state = self.fixture.build()
        state["persistence"]["run_log_status"] = "not_written"
        state["persistence"]["run_log_entry_sha256"] = None
        (self.workspace / state["persistence"]["run_log_path"]).write_text(
            self.fixture.prior_log(),
            encoding="utf-8",
        )
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "must write the success run log")

    def test_accepts_exactly_500_character_summary(self) -> None:
        state_path, _ = self.fixture.build(summary_overrides={0: "x" * 500})
        self.assert_valid(state_path)

    def test_rejects_501_character_summary(self) -> None:
        state_path, _ = self.fixture.build(summary_overrides={0: "x" * 501})
        self.assert_invalid(state_path, "exceeds 500")

    def test_rejects_artifact_digest_mismatch(self) -> None:
        state_path, state = self.fixture.build()
        state["artifact"]["sha256"] = "0" * 64
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "SHA-256")

    def test_rejects_inline_event_handler(self) -> None:
        state_path, state = self.fixture.build()
        artifact_path = self.workspace / state["artifact"]["path"]
        artifact_html = artifact_path.read_text(encoding="utf-8").replace(
            "<body>",
            "<body onload=\"alert(1)\">",
        )
        self.fixture.write_artifact(state, artifact_html)
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "executable or external-resource")

    def test_rejects_external_resource_markup(self) -> None:
        state_path, state = self.fixture.build()
        artifact_path = self.workspace / state["artifact"]["path"]
        artifact_html = artifact_path.read_text(encoding="utf-8").replace(
            "<footer>",
            "<embed src=\"https://example.com/payload\"><footer>",
        )
        self.fixture.write_artifact(state, artifact_html)
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "executable or external-resource")

    def test_rejects_external_css_load(self) -> None:
        state_path, state = self.fixture.build()
        artifact_path = self.workspace / state["artifact"]["path"]
        artifact_html = artifact_path.read_text(encoding="utf-8").replace(
            "body{font-family:system-ui}",
            "body{background:url(https://example.com/pixel)}",
        )
        self.fixture.write_artifact(state, artifact_html)
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "CSS must not")

    def test_rejects_html_date_mismatch(self) -> None:
        state_path, state = self.fixture.build()
        artifact_path = self.workspace / state["artifact"]["path"]
        artifact_html = artifact_path.read_text(encoding="utf-8").replace(
            f"<title>Daily AI Brief - {RUN_DATE}</title>",
            "<title>Daily AI Brief - 2026-08-04</title>",
        )
        artifact_path.write_text(artifact_html, encoding="utf-8")
        state["artifact"]["sha256"] = sha256_bytes(artifact_html.encode("utf-8"))
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "title")

    def test_rejects_footer_without_generated_timestamp(self) -> None:
        state_path, state = self.fixture.build()
        artifact_path = self.workspace / state["artifact"]["path"]
        artifact_html = artifact_path.read_text(encoding="utf-8").replace(
            f"Generated {RUN_DATE} 09:00 CEST · Europe/Stockholm",
            RUN_DATE,
        )
        self.fixture.write_artifact(state, artifact_html)
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "generated timestamp")

    def test_rejects_footer_without_resolved_timezone(self) -> None:
        state_path, state = self.fixture.build()
        artifact_path = self.workspace / state["artifact"]["path"]
        artifact_html = artifact_path.read_text(encoding="utf-8").replace(
            " · Europe/Stockholm",
            "",
        )
        self.fixture.write_artifact(state, artifact_html)
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "resolved timezone")

    def test_rejects_source_published_after_run_date(self) -> None:
        state_path, state = self.fixture.build()
        state["candidates"][0]["sources"][0]["published_date"] = "2026-08-04"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "after the run date")

    def test_rejects_timezone_offset_mismatch(self) -> None:
        state_path, state = self.fixture.build()
        state["started_at"] = "2026-08-03T09:00:00+01:00"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "offset")

    def test_rejects_zero_item_terminal_selection(self) -> None:
        state_path, state = self.fixture.build()
        state["selection"] = {"candidate_ids": [], "item_count": 0, "shortfall_reason": "No items."}
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "at least one")

    def test_rejects_duplicate_selected_fields(self) -> None:
        for field in ("person", "theme", "story_fingerprint"):
            with self.subTest(field=field):
                state_path, state = self.fixture.build()
                state["candidates"][1][field] = state["candidates"][0][field]
                self.fixture.write_state(state_path, state)
                self.assert_invalid(state_path, "must be unique")

    def test_rejects_noncanonical_story_fingerprint(self) -> None:
        state_path, state = self.fixture.build()
        state["candidates"][1]["story_fingerprint"] = "  STORY-1  "
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "story_fingerprint is not normalized")

    def test_rejects_prose_rejection_reason(self) -> None:
        state_path, state = self.fixture.build()
        state["candidates"][-1]["rejection_reason"] = "Long private reasoning about rejection"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "not a reason code")

    def test_rejects_unsupported_history_overlap_reason(self) -> None:
        state_path, state = self.fixture.build()
        state["candidates"][-1]["history_overlap_reason"] = "UNRELATED_CODE"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "history_overlap_reason is unsupported")

    def test_rejects_duplicate_selected_url(self) -> None:
        state_path, state = self.fixture.build()
        duplicate = state["candidates"][0]["selected_source_url"]
        state["candidates"][1]["selected_source_url"] = duplicate
        state["candidates"][1]["sources"] = copy.deepcopy(state["candidates"][0]["sources"])
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "source URLs")

    def test_selected_candidates_must_be_score_ranked(self) -> None:
        state_path, state = self.fixture.build()
        state["candidates"][0]["scores"] = {
            "impact": 0,
            "source_quality": 0,
            "freshness": 0,
            "influence": 0,
            "novelty": 0,
            "total": 0,
        }
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "not ranked by descending score")

    def test_lower_score_rejection_cannot_outrank_selection(self) -> None:
        state_path, state = self.fixture.build()
        state["candidates"][9]["scores"] = {
            "impact": 0,
            "source_quality": 0,
            "freshness": 0,
            "influence": 0,
            "novelty": 0,
            "total": 0,
        }
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "rejection outranks")

    def test_rejects_recent_theme_overlap(self) -> None:
        state_path, state = self.fixture.build()
        state["candidates"][0]["theme"] = state["history"]["themes"][0]
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "repeats a recent theme")

    def test_rejects_recent_source_url_overlap(self) -> None:
        state_path, state = self.fixture.build()
        recent_url = state["history"]["urls"][0]
        state["candidates"][0]["selected_source_url"] = recent_url
        state["candidates"][0]["sources"][0]["original_url"] = recent_url
        state["candidates"][0]["sources"][0]["canonical_url"] = recent_url
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "repeats a recent source URL")

    def test_repeated_person_requires_material_development_reason(self) -> None:
        state_path, state = self.fixture.build()
        state["candidates"][0]["person"] = state["history"]["people"][0]
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "without a material-development reason")

    def test_rejects_invalid_graph_transition(self) -> None:
        state_path, state = self.fixture.build()
        state["trace"][0]["route"] = "render"
        state["trace"][1]["node"] = "render"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "invalid graph transition")

    def test_rejects_publication_with_unverified_target(self) -> None:
        state_path, state = self.fixture.build()
        publish_index = next(
            index for index, event in enumerate(state["trace"]) if event["node"] == "publish_update"
        )
        state["trace"] = state["trace"][: publish_index + 1]
        state["trace"][-1]["route"] = ""
        state["trace"][-1]["outcome"] = "completed"
        state["revision"] = len(state["trace"])
        state["status"] = "running"
        state["current_node"] = "publish_update"
        state["finished_at"] = None
        state["node_status"] = {
            node: value
            for node, value in state["node_status"].items()
            if node in {event["node"] for event in state["trace"]}
        }
        state["node_status"]["publish_update"]["status"] = "running"
        state["publication"].update(
            {
                "target_verified": False,
                "target_id": None,
                "target_url": None,
                "delivery_status": "not_attempted",
                "live_status": "not_checked",
                "attempts": 1,
                "live_checks": 0,
                "receipt_fingerprint": None,
                "live_fingerprint": None,
                "live_date": None,
                "live_item_count": None,
                "archive_url": None,
                "archive_status": "not_checked",
                "archive_fingerprint": None,
                "archive_date": None,
                "archive_item_count": None,
            }
        )
        state["budgets"]["live_checks"]["used"] = 0
        state["persistence"]["run_log_status"] = "not_written"
        state["persistence"]["run_log_entry_sha256"] = None
        (self.workspace / state["persistence"]["run_log_path"]).write_text(
            self.fixture.prior_log(),
            encoding="utf-8",
        )
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "verified target")

    def test_rejects_publication_retry_overrun(self) -> None:
        state_path, _ = self.fixture.build(status="publish_failed", publish_attempts=4)
        self.assert_invalid(state_path, "exhausted beyond")

    def test_rejects_publication_retry_payload_change(self) -> None:
        state_path, state = self.fixture.build(publish_attempts=2)
        publish_events = [event for event in state["trace"] if event["node"] == "publish_update"]
        publish_events[1]["payload_fingerprint"] = "0" * 64
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "changed across publication attempts")

    def test_rejects_permanent_publication_retry_reason(self) -> None:
        state_path, state = self.fixture.build(publish_attempts=2)
        publish_events = [event for event in state["trace"] if event["node"] == "publish_update"]
        publish_events[0]["reason_code"] = "DELIVERY_PERMANENT"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "not retryable for this backedge")

    def test_rejects_permanent_live_retry_reason(self) -> None:
        state_path, state = self.fixture.build(live_check_attempts=2)
        live_events = [event for event in state["trace"] if event["node"] == "live_verify"]
        live_events[0]["reason_code"] = "LIVE_PERMANENT"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "not retryable for this backedge")

    def test_rejects_permanent_artifact_repair_reason(self) -> None:
        state_path, state = self.fixture.build(artifact_repairs=1)
        validate_events = [event for event in state["trace"] if event["node"] == "validate"]
        validate_events[0]["reason_code"] = "ARTIFACT_PERMANENT"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "not retryable for this backedge")

    def test_rejects_tampered_terminal_outcome(self) -> None:
        state_path, state = self.fixture.build()
        state["trace"][-1]["outcome"] = "failed"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "terminal trace outcome")

    def test_rejects_tampered_terminal_node_status(self) -> None:
        state_path, state = self.fixture.build()
        state["node_status"]["done"]["status"] = "failed"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "does not match graph state")

    def test_rejects_unvisited_node_status_extra_field(self) -> None:
        state_path, state = self.fixture.build()
        state["node_status"]["targeted_research"] = {
            "status": "pending",
            "attempts": 0,
            "last_error": "",
            "private_reasoning": "unsafe",
        }
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "unknown keys")

    def test_rejects_research_duration_budget_mismatch(self) -> None:
        state_path, state = self.fixture.build()
        state["budgets"]["research_seconds"]["used"] += 1
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "research_seconds.used does not match")

    def test_rejects_targeted_search_budget_mismatch(self) -> None:
        state_path, state = self.fixture.build(selected_count=8, targeted_rounds=2)
        state["budgets"]["targeted_searches"]["used"] += 1
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "targeted_searches.used does not match")

    def test_rejects_confirmation_search_count_mismatch(self) -> None:
        state_path, state = self.fixture.build()
        state["candidates"][0]["confirmation_attempts"] = 1
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "confirmation search counts")

    def test_rejects_content_fingerprint_missing_displayed_field_change(self) -> None:
        state_path, state = self.fixture.build()
        old_role = state["candidates"][0]["role_org"]
        new_role = "Changed role, Changed organization"
        state["candidates"][0]["role_org"] = new_role
        artifact_path = self.workspace / state["artifact"]["path"]
        artifact_html = artifact_path.read_text(encoding="utf-8").replace(old_role, new_role)
        self.fixture.write_artifact(state, artifact_html)
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "content fingerprint")

    def test_rejects_untracked_public_article_text(self) -> None:
        state_path, state = self.fixture.build()
        artifact_path = self.workspace / state["artifact"]["path"]
        artifact_html = artifact_path.read_text(encoding="utf-8").replace(
            "</article></li>",
            "<p>Untracked public claim.</p></article></li>",
            1,
        )
        self.fixture.write_artifact(state, artifact_html)
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "public text does not exactly match")

    def test_rejects_noncanonical_stored_url(self) -> None:
        state_path, state = self.fixture.build()
        state["candidates"][0]["sources"][0]["canonical_url"] += "?utm_source=test"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "is not normalized")

    def test_malformed_url_is_reported_as_validation_error(self) -> None:
        state_path, state = self.fixture.build()
        state["history"]["urls"][0] = "https://example.com:bad/story"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "not a valid URL")

    def test_rejects_invalid_unverified_publication_url(self) -> None:
        state_path, state = self.fixture.build(status="blocked")
        state["publication"]["target_url"] = "not a URL"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "must use HTTPS")

    def test_rejects_schema_drift(self) -> None:
        state_path, _ = self.fixture.build()
        schema = json.loads((SKILL_ROOT / "references" / "run-state.schema.json").read_text())
        schema["required"].append("unexpected")
        schema["properties"]["unexpected"] = {"type": "string"}
        schema_path = self.workspace / "drifted-schema.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "schema root drifted"):
            validate_run(state_path, self.workspace, schema_path=schema_path)

    def test_rejects_graph_budget_drift_without_version_bump(self) -> None:
        state_path, _ = self.fixture.build()
        graph = json.loads((SKILL_ROOT / "references" / "workflow-graph.json").read_text())
        graph["budgets"]["publish_retries"] = 3
        next(loop for loop in graph["loops"] if loop["name"] == "publication_retry")[
            "maximum"
        ] = 3
        graph_path = self.workspace / "drifted-graph.json"
        graph_path.write_text(json.dumps(graph), encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "budget contract drifted"):
            validate_run(state_path, self.workspace, graph_path=graph_path)

    def test_full_deployment_requires_separate_approval(self) -> None:
        state_path, state = self.fixture.build()
        state["publication"]["mode"] = "full_deployment"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "must stop blocked")

    def test_blocked_full_deployment_classification_is_valid(self) -> None:
        state_path, state = self.fixture.build(status="blocked")
        state["publication"]["mode"] = "full_deployment"
        state["publication"]["authorization_status"] = "required"
        self.fixture.write_state(state_path, state)
        self.assert_valid(state_path)

    def test_verified_target_full_deployment_waits_for_approval(self) -> None:
        state_path, state = self.fixture.build(status="blocked")
        state["publication"].update(
            {
                "mode": "full_deployment",
                "authorization_status": "required",
                "target_verified": True,
                "target_id": "existing-daily-brief",
                "target_url": "https://daily.example.test/",
                "failure_reason": "DEPLOYMENT_APPROVAL_REQUIRED",
            }
        )
        state["errors"][0]["reason_code"] = "DEPLOYMENT_APPROVAL_REQUIRED"
        state["errors"][0]["message"] = "DEPLOYMENT_APPROVAL_REQUIRED"
        state["trace"][-1]["reason_code"] = "DEPLOYMENT_APPROVAL_REQUIRED"
        state["node_status"]["blocked"]["last_error"] = "DEPLOYMENT_APPROVAL_REQUIRED"
        self.fixture.write_state(state_path, state)
        self.assert_valid(state_path)

    def test_success_requires_live_verification(self) -> None:
        state_path, state = self.fixture.build()
        state["publication"].update(
            {
                "live_status": "not_checked",
                "live_fingerprint": None,
                "live_date": None,
                "live_item_count": None,
            }
        )
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "live verification")

    def test_success_requires_archive_verification(self) -> None:
        state_path, state = self.fixture.build()
        state["publication"].update(
            {
                "archive_url": None,
                "archive_status": "not_checked",
                "archive_fingerprint": None,
                "archive_date": None,
                "archive_item_count": None,
            }
        )
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "archive verification")

    def test_archive_url_must_be_distinct_from_live_target(self) -> None:
        state_path, state = self.fixture.build()
        state["publication"]["archive_url"] = state["publication"]["target_url"]
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "must be distinct")

    def test_publish_failed_retains_artifact_without_success_log(self) -> None:
        state_path, state = self.fixture.build(status="publish_failed", publish_attempts=3)
        result = self.assert_valid(state_path)
        self.assertEqual(result["status"], "publish_failed")
        self.assertTrue((self.workspace / state["artifact"]["path"]).exists())
        self.assertNotIn(
            state["run_id"],
            (self.workspace / state["persistence"]["run_log_path"]).read_text(encoding="utf-8"),
        )

    def test_archive_mismatch_routes_to_publish_failed(self) -> None:
        state_path, state = self.fixture.build(
            status="publish_failed",
            publish_failure_stage="archive",
        )
        result = self.assert_valid(state_path)
        self.assertEqual(result["status"], "publish_failed")
        self.assertEqual(state["publication"]["archive_status"], "mismatch")

    def test_publication_failure_cannot_use_generic_failed_terminal(self) -> None:
        state_path, state = self.fixture.build(status="publish_failed")
        state["status"] = "failed"
        state["current_node"] = "failed"
        state["trace"][-2]["route"] = "failed"
        state["trace"][-1]["node"] = "failed"
        state["trace"][-1]["reason_code"] = "RUN_FAILED"
        state["node_status"]["failed"] = state["node_status"].pop("publish_failed")
        state["node_status"]["failed"]["last_error"] = "RUN_FAILED"
        state["errors"][0]["node"] = "failed"
        state["errors"][0]["reason_code"] = "RUN_FAILED"
        state["errors"][0]["message"] = "RUN_FAILED"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "invalid graph transition")

    def test_generic_failed_terminal_has_coherent_reason(self) -> None:
        state_path, _ = self.fixture.build(status="failed")
        result = self.assert_valid(state_path)
        self.assertEqual(result["status"], "failed")

    def test_blocked_stops_before_publication(self) -> None:
        state_path, state = self.fixture.build(status="blocked")
        result = self.assert_valid(state_path)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(state["publication"]["attempts"], 0)

    def test_unsuccessful_run_cannot_appear_in_success_log(self) -> None:
        state_path, state = self.fixture.build(status="publish_failed", publish_attempts=3)
        selected = state["candidates"][: state["selection"]["item_count"]]
        block = self.fixture.log_block(state, selected)
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        run_log_path.write_text(self.fixture.prior_log() + block, encoding="utf-8")
        self.assert_invalid(state_path, "must not appear")

    def test_rejects_forbidden_trace_field(self) -> None:
        state_path, state = self.fixture.build()
        state["trace"][0]["prompt"] = "hidden prompt"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "forbidden field")

    def test_rejects_prose_in_trace_reason_code(self) -> None:
        state_path, state = self.fixture.build()
        state["trace"][0]["reason_code"] = "private reasoning text"
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "not a reason code")

    def test_new_run_log_entry_requires_url_history(self) -> None:
        state_path, state = self.fixture.build()
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        text = run_log_path.read_text(encoding="utf-8")
        heading = f"## {RUN_DATE} 09:00 CEST"
        prior, current = text.split(heading, 1)
        run_log_path.write_text(
            prior + re_sub_line(heading + current, "Source URLs"),
            encoding="utf-8",
        )
        self.fixture.refresh_log_hash(state)
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "missing Source URLs")

    def test_run_log_url_history_must_exactly_match_selection(self) -> None:
        state_path, state = self.fixture.build()
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        heading = f"## {RUN_DATE} 09:00 CEST"
        prior, current = run_log_path.read_text(encoding="utf-8").split(heading, 1)
        current = (heading + current).replace(
            "]\n- Source-quality notes:",
            ", \"https://example.com/extra\"]\n- Source-quality notes:",
        )
        run_log_path.write_text(prior + current, encoding="utf-8")
        self.fixture.refresh_log_hash(state)
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "do not match selection")

    def test_run_log_people_must_exactly_match_selection(self) -> None:
        state_path, state = self.fixture.build()
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        text = run_log_path.read_text(encoding="utf-8").replace(
            "- Selected people: Person 1,",
            "- Selected people: Extra Person, Person 1,",
        )
        run_log_path.write_text(text, encoding="utf-8")
        self.fixture.refresh_log_hash(state)
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "Selected people mismatches")

    def test_run_log_resolved_clock_must_match_state(self) -> None:
        state_path, state = self.fixture.build()
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        text = run_log_path.read_text(encoding="utf-8").replace(
            f"- Resolved date/timezone: {RUN_DATE}, Europe/Stockholm, 09:00 CEST",
            "- Resolved date/timezone: 1999-01-01, UTC, 00:00 UTC",
        )
        run_log_path.write_text(text, encoding="utf-8")
        self.fixture.refresh_log_hash(state)
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "resolved date/timezone mismatches")

    def test_rejects_duplicate_run_id_log_entries(self) -> None:
        state_path, state = self.fixture.build()
        run_log_path = self.workspace / state["persistence"]["run_log_path"]
        text = run_log_path.read_text(encoding="utf-8")
        current = text.split(f"## {RUN_DATE} 09:00 CEST", 1)[1]
        run_log_path.write_text(text + f"\n## {RUN_DATE} 09:00 CEST" + current, encoding="utf-8")
        self.fixture.write_state(state_path, state)
        self.assert_invalid(state_path, "exactly one")


def re_sub_line(text: str, label: str) -> str:
    lines = [line for line in text.splitlines() if not line.startswith(f"- {label}:")]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    unittest.main()
