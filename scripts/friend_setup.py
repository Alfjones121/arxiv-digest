#!/usr/bin/env python3
"""Terminal bootstrap for friends setting up their own arXiv Digest fork."""

from __future__ import annotations

import argparse
import getpass
import json
import re
import subprocess
import sys
import tempfile
import time
import webbrowser
from pathlib import Path


DEFAULT_SOURCE_REPO = "SilkeDainese/arxiv-digest"
DEFAULT_SETUP_URL = "https://arxiv-digest-setup.streamlit.app"
DOWNLOAD_PATTERNS = (
    "config.yaml",
    "config.yml",
    "config*.yaml",
    "config*.yml",
)
DOWNLOAD_STABLE_AGE_SECONDS = 1.0


class SetupError(RuntimeError):
    """Raised when a terminal-setup step fails."""


def run_command(
    args: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command and return its completed process."""
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        input=input_text,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise SetupError(f"{' '.join(args)}: {detail}")
    return result


def gh_json(args: list[str]) -> dict | list:
    """Run a gh command that returns JSON."""
    result = run_command(["gh", *args])
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SetupError(f"Could not parse JSON from {' '.join(args)}") from exc


def prompt(text: str, *, default: str | None = None, required: bool = True) -> str:
    """Prompt for a normal terminal input."""
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"{text}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ""
        print("Please enter a value.")


def prompt_secret(text: str, *, required: bool = True) -> str:
    """Prompt for a secret value without echoing it."""
    while True:
        value = getpass.getpass(f"{text}: ").strip()
        if value or not required:
            return value
        print("Please enter a value.")


def prompt_yes_no(text: str, *, default: bool = True) -> bool:
    """Prompt for a yes/no answer."""
    hint = "Y/n" if default else "y/N"
    while True:
        value = input(f"{text} [{hint}]: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def pick_downloaded_config(downloads_dir: Path, started_at: float) -> Path | None:
    """Return the newest freshly-downloaded config file, if any."""
    candidates: list[Path] = []
    for pattern in DOWNLOAD_PATTERNS:
        for path in downloads_dir.glob(pattern):
            if not path.is_file():
                continue
            if path.suffix not in {".yaml", ".yml"}:
                continue
            if path.stat().st_size <= 0:
                continue
            if path.stat().st_mtime < started_at:
                continue
            if path.name.endswith(".crdownload"):
                continue
            candidates.append(path)
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.stat().st_mtime)


def wait_for_downloaded_config(
    downloads_dir: Path,
    *,
    started_at: float,
    timeout_seconds: int,
) -> Path:
    """Wait until a config file appears in Downloads and becomes stable."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        candidate = pick_downloaded_config(downloads_dir, started_at)
        if candidate:
            age = time.time() - candidate.stat().st_mtime
            if age >= DOWNLOAD_STABLE_AGE_SECONDS:
                return candidate
        time.sleep(2)
    raise SetupError(
        f"Timed out waiting for config.yaml in {downloads_dir}. "
        "Pass --config-path if the file is elsewhere."
    )


def rewrite_top_level_scalar(text: str, key: str, value: str) -> str:
    """Replace or append a top-level YAML scalar while preserving the rest."""
    replacement = f"{key}: {json.dumps(value)}"
    pattern = re.compile(rf"(?m)^{re.escape(key)}:\s*.*$")
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return text.rstrip() + f"\n{replacement}\n"


def prepare_config_text(config_path: Path, fork_repo: str) -> str:
    """Load the downloaded config and point github_repo at the new fork."""
    text = config_path.read_text()
    return rewrite_top_level_scalar(text, "github_repo", fork_repo)


def repo_exists(repo: str) -> bool:
    """Return True if the given repo already exists."""
    result = run_command(
        ["gh", "repo", "view", repo, "--json", "nameWithOwner"],
        check=False,
    )
    return result.returncode == 0


def wait_for_repo(repo: str, timeout_seconds: int = 180) -> None:
    """Poll until GitHub finishes creating the fork."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if repo_exists(repo):
            return
        time.sleep(2)
    raise SetupError(f"Timed out waiting for {repo} to appear on GitHub.")


def ensure_fork(source_repo: str, fork_repo: str) -> None:
    """Create the friend's fork if it doesn't exist yet."""
    if repo_exists(fork_repo):
        print(f"Using existing repo: {fork_repo}")
        return

    source_name = source_repo.split("/", 1)[1]
    fork_name = fork_repo.split("/", 1)[1]
    args = ["gh", "api", "-X", "POST", f"repos/{source_repo}/forks"]
    if fork_name != source_name:
        args.extend(["-f", f"name={fork_name}"])
    run_command(args)
    wait_for_repo(fork_repo)
    print(f"Fork created: {fork_repo}")


def get_default_branch(repo: str) -> str:
    """Return the repo's default branch name."""
    data = gh_json(["repo", "view", repo, "--json", "defaultBranchRef"])
    branch = data.get("defaultBranchRef", {}).get("name", "").strip()
    if not branch:
        raise SetupError(f"Could not determine the default branch for {repo}.")
    return branch


def clone_repo(repo: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    """Clone the repo into a temporary directory."""
    tmpdir = tempfile.TemporaryDirectory(prefix="arxiv-digest-friend-")
    target = Path(tmpdir.name) / repo.split("/", 1)[1]
    run_command(["gh", "repo", "clone", repo, str(target), "--", "--depth=1"])
    return tmpdir, target


def upload_config(repo: str, config_text: str, *, author_name: str) -> None:
    """Commit config.yaml into the fork."""
    branch = get_default_branch(repo)
    tmpdir, checkout = clone_repo(repo)
    try:
        (checkout / "config.yaml").write_text(config_text)
        run_command(["git", "config", "user.name", author_name], cwd=checkout)
        run_command(
            ["git", "config", "user.email", f"{author_name}@users.noreply.github.com"],
            cwd=checkout,
        )
        run_command(["git", "add", "config.yaml"], cwd=checkout)
        diff = run_command(["git", "diff", "--cached", "--quiet"], cwd=checkout, check=False)
        if diff.returncode == 0:
            print("config.yaml already matches the fork.")
            return
        run_command(["git", "commit", "-m", "Add config.yaml via terminal setup"], cwd=checkout)
        run_command(["git", "push", "origin", f"HEAD:{branch}"], cwd=checkout)
    finally:
        tmpdir.cleanup()


def set_actions_secret(repo: str, name: str, value: str) -> None:
    """Write one GitHub Actions secret."""
    run_command(
        [
            "gh",
            "secret",
            "set",
            name,
            "-R",
            repo,
            "-a",
            "actions",
            "--body",
            value,
        ]
    )


def configure_actions(repo: str) -> None:
    """Enable Actions and let the workflow write keyword stats back."""
    run_command(
        [
            "gh",
            "api",
            "-X",
            "PUT",
            f"repos/{repo}/actions/permissions",
            "-f",
            "enabled=true",
            "-f",
            "allowed_actions=all",
        ]
    )
    run_command(
        [
            "gh",
            "api",
            "-X",
            "PUT",
            f"repos/{repo}/actions/permissions/workflow",
            "-f",
            "default_workflow_permissions=write",
            "-F",
            "can_approve_pull_request_reviews=false",
        ]
    )
    run_command(["gh", "workflow", "enable", "digest.yml", "-R", repo], check=False)


def collect_secret_values() -> dict[str, str]:
    """Prompt for the secrets to install in the new fork."""
    secrets: dict[str, str] = {}
    secrets["RECIPIENT_EMAIL"] = prompt("Recipient email")

    if prompt_yes_no("Use a relay token from the setup wizard?", default=True):
        secrets["DIGEST_RELAY_TOKEN"] = prompt_secret("DIGEST_RELAY_TOKEN")
    else:
        secrets["SMTP_USER"] = prompt("SMTP_USER")
        secrets["SMTP_PASSWORD"] = prompt_secret("SMTP_PASSWORD")

    gemini = prompt_secret("GEMINI_API_KEY (optional)", required=False)
    if gemini:
        secrets["GEMINI_API_KEY"] = gemini
    anthropic = prompt_secret("ANTHROPIC_API_KEY (optional)", required=False)
    if anthropic:
        secrets["ANTHROPIC_API_KEY"] = anthropic

    return secrets


def verify_gh_ready() -> None:
    """Ensure gh is installed and authenticated before starting."""
    try:
        run_command(["gh", "auth", "status"])
    except FileNotFoundError as exc:
        raise SetupError("GitHub CLI (`gh`) is required but not installed.") from exc


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", default=DEFAULT_SOURCE_REPO)
    parser.add_argument("--setup-url", default=DEFAULT_SETUP_URL)
    parser.add_argument("--downloads-dir", type=Path, default=Path.home() / "Downloads")
    parser.add_argument("--config-path", type=Path)
    parser.add_argument("--fork-name")
    parser.add_argument("--repo", help="Use an existing OWNER/REPO instead of creating a fork.")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--no-run", action="store_true")
    return parser


def main() -> int:
    """Run the end-to-end terminal setup flow."""
    args = build_parser().parse_args()
    verify_gh_ready()

    user = gh_json(["api", "user"])
    login = str(user["login"]).strip()
    target_repo = args.repo or f"{login}/{args.fork_name or args.source_repo.split('/', 1)[1]}"

    ensure_fork(args.source_repo, target_repo)

    config_path = args.config_path
    if config_path is None:
        if not args.no_browser:
            print(f"Opening the setup wizard: {args.setup_url}")
            webbrowser.open(args.setup_url)
        print(f"Waiting for config.yaml in {args.downloads_dir} ...")
        started_at = time.time()
        config_path = wait_for_downloaded_config(
            args.downloads_dir,
            started_at=started_at,
            timeout_seconds=args.timeout,
        )
        print(f"Found config file: {config_path}")
    elif not config_path.exists():
        raise SetupError(f"Config file not found: {config_path}")

    config_text = prepare_config_text(config_path, target_repo)
    upload_config(target_repo, config_text, author_name=login)
    print(f"Uploaded config.yaml to {target_repo}")

    print("\nNow enter the secrets for your fork.")
    for name, value in collect_secret_values().items():
        set_actions_secret(target_repo, name, value)
        print(f"Set secret: {name}")

    configure_actions(target_repo)
    print("Enabled Actions and workflow write permissions.")

    if not args.no_run and prompt_yes_no("Run the first digest now?", default=True):
        run_command(["gh", "workflow", "run", "digest.yml", "-R", target_repo])
        print(f"Triggered the digest workflow: https://github.com/{target_repo}/actions")
    else:
        print(f"Setup complete. Open https://github.com/{target_repo}/actions to run it.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SetupError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        raise SystemExit(1)
