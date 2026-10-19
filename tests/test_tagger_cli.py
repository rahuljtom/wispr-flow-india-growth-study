import subprocess
import sys


def run(*args, env=None):
    return subprocess.run([sys.executable, "-m", "src.tagging.tagger", *args],
                          check=False, capture_output=True, text=True, env=env)


def test_default_is_dry_run_even_with_key(tmp_path, monkeypatch):
    import os
    csv = tmp_path / "r.csv"
    csv.write_text("review_key,text_clean\nk1,hello\n")
    env = {**os.environ, "GEMINI_API_KEY": "SECRET-KEY-123"}
    r = run("--input", str(csv), env=env)
    assert "DRY RUN" in r.stdout and "SECRET-KEY-123" not in r.stdout + r.stderr


def test_run_without_approval_flag_refuses(tmp_path):
    import os
    csv = tmp_path / "r.csv"
    csv.write_text("review_key,text_clean\nk1,hello\n")
    env = {**os.environ, "GEMINI_API_KEY": "SECRET-KEY-123"}
    r = run("--input", str(csv), "--run", env=env)
    assert "DRY RUN" in r.stdout and "approve" in (r.stdout + r.stderr).lower()
