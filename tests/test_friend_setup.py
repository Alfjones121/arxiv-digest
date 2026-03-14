from pathlib import Path
import os
import time

from scripts.friend_setup import pick_downloaded_config, prepare_config_text, rewrite_top_level_scalar


def test_pick_downloaded_config_chooses_latest_recent_yaml(tmp_path):
    started_at = time.time()
    old_file = tmp_path / "config-old.yaml"
    old_file.write_text("old: true\n")
    os.utime(old_file, (started_at - 30, started_at - 30))

    first = tmp_path / "config.yaml"
    first.write_text("first: true\n")
    os.utime(first, (started_at + 1, started_at + 1))

    latest = tmp_path / "config (1).yaml"
    latest.write_text("latest: true\n")
    os.utime(latest, (started_at + 2, started_at + 2))

    assert pick_downloaded_config(tmp_path, started_at) == latest


def test_rewrite_top_level_scalar_replaces_existing_value():
    text = 'digest_name: "Demo"\ngithub_repo: "wrong/repo"\n'

    rewritten = rewrite_top_level_scalar(text, "github_repo", "friend/arxiv-digest")

    assert 'github_repo: "friend/arxiv-digest"' in rewritten
    assert 'github_repo: "wrong/repo"' not in rewritten


def test_prepare_config_text_appends_missing_github_repo(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text('digest_name: "Demo"\nrecipient_email: "a@example.com"\n')

    prepared = prepare_config_text(config_path, "friend/arxiv-digest")

    assert prepared.endswith('github_repo: "friend/arxiv-digest"\n')
    assert 'recipient_email: "a@example.com"' in prepared
