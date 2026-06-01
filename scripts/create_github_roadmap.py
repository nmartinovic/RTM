#!/usr/bin/env python3
"""Create GitHub labels, milestones, and issues from docs/github-roadmap.json.

The script uses only the Python standard library so it can run in minimal CI
containers without the GitHub CLI installed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs" / "github-roadmap.json"
API_ROOT = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str, repo: str, dry_run: bool = False) -> None:
        self.token = token
        self.repo = repo
        self.dry_run = dry_run

    def request(self, method: str, path: str, data: dict[str, Any] | None = None) -> Any:
        url = f"{API_ROOT}{path}"
        body = None if data is None else json.dumps(data).encode("utf-8")
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "rtm-roadmap-bootstrapper",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload) if payload else None
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {method} {path} failed: {exc.code} {payload}") from exc

    def paginated_get(self, path: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        separator = "&" if "?" in path else "?"
        page = 1
        while True:
            batch = self.request("GET", f"{path}{separator}per_page=100&page={page}")
            if not batch:
                return results
            results.extend(batch)
            if len(batch) < 100:
                return results
            page += 1

    def upsert_label(self, label: dict[str, str]) -> None:
        name = label["name"]
        encoded = urllib.parse.quote(name, safe="")
        payload = {
            "name": name,
            "color": label["color"],
            "description": label.get("description", ""),
        }
        if self.dry_run:
            print(f"DRY RUN label: {name}")
            return
        try:
            self.request("PATCH", f"/repos/{self.repo}/labels/{encoded}", payload)
            print(f"Updated label: {name}")
        except RuntimeError as exc:
            if " 404 " not in str(exc):
                raise
            self.request("POST", f"/repos/{self.repo}/labels", payload)
            print(f"Created label: {name}")

    def get_milestones_by_title(self) -> dict[str, dict[str, Any]]:
        milestones = self.paginated_get(f"/repos/{self.repo}/milestones?state=all")
        return {milestone["title"]: milestone for milestone in milestones}

    def upsert_milestone(self, milestone: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
        payload = {
            "title": milestone["title"],
            "description": milestone.get("description", ""),
            "state": milestone.get("state", "open"),
        }
        if milestone.get("due_on"):
            payload["due_on"] = milestone["due_on"]
        if self.dry_run:
            print(f"DRY RUN milestone: {milestone['title']}")
            return {"number": 0, "title": milestone["title"]}
        if existing:
            updated = self.request("PATCH", f"/repos/{self.repo}/milestones/{existing['number']}", payload)
            print(f"Updated milestone: {milestone['title']}")
            return updated
        created = self.request("POST", f"/repos/{self.repo}/milestones", payload)
        print(f"Created milestone: {milestone['title']}")
        return created

    def get_issues_by_title(self) -> dict[str, dict[str, Any]]:
        issues = self.paginated_get(f"/repos/{self.repo}/issues?state=all")
        issue_items = [issue for issue in issues if "pull_request" not in issue]
        return {issue["title"]: issue for issue in issue_items}

    def upsert_issue(
        self,
        issue: dict[str, Any],
        milestone_number: int,
        existing: dict[str, Any] | None,
    ) -> None:
        payload = {
            "title": issue["title"],
            "body": issue["body"],
            "labels": issue.get("labels", []),
            "milestone": milestone_number,
        }
        if self.dry_run:
            print(f"DRY RUN issue: {issue['title']}")
            return
        if existing:
            self.request("PATCH", f"/repos/{self.repo}/issues/{existing['number']}", payload)
            print(f"Updated issue #{existing['number']}: {issue['title']}")
            return
        created = self.request("POST", f"/repos/{self.repo}/issues", payload)
        print(f"Created issue #{created['number']}: {issue['title']}")
        time.sleep(0.25)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="Repository in owner/name format. Defaults to GITHUB_REPOSITORY.",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"),
        help="GitHub token. Defaults to GITHUB_TOKEN or GH_TOKEN.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without calling GitHub.")
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    args = parse_args()
    if not args.repo:
        print("error: --repo or GITHUB_REPOSITORY is required", file=sys.stderr)
        return 2
    if "/" not in args.repo:
        print("error: repo must be in owner/name format", file=sys.stderr)
        return 2
    if not args.token and not args.dry_run:
        print("error: --token, GITHUB_TOKEN, or GH_TOKEN is required unless --dry-run is used", file=sys.stderr)
        return 2

    manifest = load_manifest(args.manifest)
    client = GitHubClient(token=args.token or "dry-run", repo=args.repo, dry_run=args.dry_run)

    for label in manifest["labels"]:
        client.upsert_label(label)

    existing_milestones = client.get_milestones_by_title() if not args.dry_run else {}
    milestone_numbers: dict[str, int] = {}
    for milestone in manifest["milestones"]:
        updated = client.upsert_milestone(milestone, existing_milestones.get(milestone["title"]))
        milestone_numbers[milestone["title"]] = int(updated["number"])

    existing_issues = client.get_issues_by_title() if not args.dry_run else {}
    for milestone in manifest["milestones"]:
        milestone_number = milestone_numbers[milestone["title"]]
        for issue in milestone["issues"]:
            client.upsert_issue(issue, milestone_number, existing_issues.get(issue["title"]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
