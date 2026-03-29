#!/usr/bin/env python3
"""Minimal PR review agent for GitHub Actions.

This MVP intentionally uses only stdlib to keep setup simple.
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


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
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


def _load_event(path: str) -> dict:
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


def _format_comment(findings: list[Finding], files_changed: int) -> str:
    header = [
        "## 🤖 AI Code Review (MVP)",
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
    for f in findings:
        rows.append(f"| {f.severity} | `{f.file}` | {f.issue} | {f.recommendation} |")

    return "\n".join(header + rows)


def main() -> int:
    try:
        token = _require_env("GITHUB_TOKEN")
        owner_repo = _require_env("GITHUB_REPOSITORY")
        event_path = _require_env("GITHUB_EVENT_PATH")

        event = _load_event(event_path)
        pr = event.get("pull_request")
        if not pr:
            print("No pull_request payload found. Exiting.")
            return 0

        pr_number = int(pr["number"])

        findings: list[Finding] = []
        files_changed = 0
        for changed_file in _iter_pr_files(owner_repo, pr_number, token):
            files_changed += 1
            filename = changed_file.get("filename", "unknown")
            patch = changed_file.get("patch")
            findings.extend(_analyze_patch(filename, patch))

        body = _format_comment(findings, files_changed)
        comments_url = pr["comments_url"]
        _github_request(comments_url, token, method="POST", data={"body": body})

        print(f"Posted AI review summary for PR #{pr_number} with {len(findings)} finding(s).")
        return 0

    except urllib.error.HTTPError as exc:
        print(f"GitHub API HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
