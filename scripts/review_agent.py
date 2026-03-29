#!/usr/bin/env python3
"""Minimal PR review agent for GitHub Actions.

This MVP intentionally uses only stdlib to keep setup simple.

Supports a local dry-run mode with fixtures for predictable testing.

"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable


GITHUB_API = "https://api.github.com"


@dataclass
class Finding:
    severity: str
    file: str
    issue: str
    recommendation: str



def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _require_env(name: str) -> str:
    value = _env(name)
    if value is None:

        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _github_request(url: str, token: str, method: str = "GET", data: dict | None = None) -> dict | list:
    payload = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ai-code-review-mvp",
    }
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, data=payload, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))



def _load_json(path: str) -> dict | list:

    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _iter_pr_files(owner_repo: str, pr_number: int, token: str) -> Iterable[dict]:
    page = 1
    while True:
        params = urllib.parse.urlencode({"per_page": 100, "page": page})
        url = f"{GITHUB_API}/repos/{owner_repo}/pulls/{pr_number}/files?{params}"
        batch = _github_request(url, token)
        if not isinstance(batch, list) or not batch:
            break
        for item in batch:
            yield item
        page += 1


def _analyze_patch(filename: str, patch: str | None) -> list[Finding]:
    if not patch:
        return []

    findings: list[Finding] = []
    checks = [
        (r"(?i)password\s*=\s*['\"]", "blocker", "Possible hardcoded password", "Move secret to secure vault/env vars."),
        (r"(?i)api[_-]?key\s*=\s*['\"]", "blocker", "Possible hardcoded API key", "Use secret manager or CI secret store."),
        (r"\beval\(", "blocker", "Use of eval detected", "Replace with safe parser/explicit mapping."),
        (r"\bexec\(", "blocker", "Use of exec detected", "Avoid dynamic code execution on runtime input."),
        (r"TODO", "low", "TODO marker left in patch", "Resolve TODO or create an issue reference."),
    ]

    for pattern, severity, issue, recommendation in checks:
        if re.search(pattern, patch):
            findings.append(Finding(severity=severity, file=filename, issue=issue, recommendation=recommendation))

    return findings

def _format_comment(findings: list[Finding], files_changed: int, mode: str) -> str:
    header = [
        f"## 🤖 AI Code Review (MVP, {mode})",
        f"Reviewed files: **{files_changed}**",
        "",
    ]
    if not findings:
        return "\n".join(
            header
            + [
                "✅ No high-signal issues detected by MVP heuristics.",
                "",
                "_Note: this is a baseline rule-based pass. Add LLM + repository context for deeper review._",
            ]
        )

    rows = ["| severity | file | issue | recommendation |", "|---|---|---|---|"]
    for finding in findings:
        rows.append(f"| {finding.severity} | `{finding.file}` | {finding.issue} | {finding.recommendation} |")

    return "\n".join(header + rows)


def _review_files(files: Iterable[dict]) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    files_changed = 0
    for changed_file in files:
        files_changed += 1
        filename = changed_file.get("filename", "unknown")
        patch = changed_file.get("patch")
        findings.extend(_analyze_patch(filename, patch))
    return findings, files_changed


def _run_fixture_mode(fixtures_path: str) -> int:
    payload = _load_json(fixtures_path)
    if not isinstance(payload, list):
        raise RuntimeError("Fixture file must contain a JSON array of changed files.")

    findings, files_changed = _review_files(payload)
    comment = _format_comment(findings, files_changed, "fixture")

    output_path = _env("DRY_RUN_OUTPUT", "review-output.md")
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(comment)

    print(f"Fixture dry-run completed. Findings: {len(findings)}. Output: {output_path}")
    return 0


def _run_github_mode() -> int:
    token = _require_env("GITHUB_TOKEN")
    owner_repo = _require_env("GITHUB_REPOSITORY")
    event_path = _require_env("GITHUB_EVENT_PATH")

    event = _load_json(event_path)
    if not isinstance(event, dict):
        raise RuntimeError("Invalid GitHub event payload.")

    pr = event.get("pull_request")
    if not isinstance(pr, dict):
        print("No pull_request payload found. Exiting.")
        return 0

    pr_number = int(pr["number"])
    findings, files_changed = _review_files(_iter_pr_files(owner_repo, pr_number, token))
    body = _format_comment(findings, files_changed, "github")

    comments_url = pr["comments_url"]
    if not isinstance(comments_url, str):
        raise RuntimeError("Missing comments_url in event payload.")

    if _env("DRY_RUN", "0") == "1":
        print(body)
        return 0

    _github_request(comments_url, token, method="POST", data={"body": body})
    print(f"Posted AI review summary for PR #{pr_number} with {len(findings)} finding(s).")
    return 0


def main() -> int:
    try:
        fixtures_path = _env("REVIEW_FILES_PATH")
        if fixtures_path:
            return _run_fixture_mode(fixtures_path)
        return _run_github_mode()
    except urllib.error.HTTPError as exc:
        print(f"GitHub API HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
