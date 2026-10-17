import json
import os
import subprocess
import sys
from pathlib import Path

from eval_score_bounds.cli import main


def test_private_argv_valid_files(tmp_path, capsys):
    rows = tmp_path / "rows.jsonl"
    policy = tmp_path / "policy.json"
    rows.write_text('{"id":"secret-id","score":"100"}', encoding="utf-8")
    policy.write_text('{"min":"0","max":"1"}', encoding="utf-8")
    assert main([str(rows), str(policy)]) == 1
    out, err = capsys.readouterr()
    assert json.loads(out)["above_lines"] == [1]
    assert "secret-id" not in out and "100" not in out and err == ""


def test_invalid_cli_has_fixed_output_and_no_partial(tmp_path, capsys):
    assert main(["one"]) == 2
    out, err = capsys.readouterr()
    assert out == '{"status":"invalid_input"}\n' and err == ""


def test_installed_entrypoint_exit_matrix(tmp_path):
    rows = tmp_path / "rows"
    pol = tmp_path / "policy"
    rows.write_text('{"id":"private","score":"0"}', encoding="utf-8")
    pol.write_text('{"min":"0","max":"1"}', encoding="utf-8")
    env = dict(os.environ)
    executable = str(Path(sys.executable).with_name("eval-score-bounds.exe" if os.name == "nt" else "eval-score-bounds"))
    help_run = subprocess.run([executable, "--help"], capture_output=True, text=True, env=env)
    assert help_run.returncode == 0 and not help_run.stderr
    okay = subprocess.run([executable, str(rows), str(pol)], capture_output=True, text=True, env=env)
    assert okay.returncode == 0 and json.loads(okay.stdout)["status"] == "within_bounds"
    rows.write_text('{"id":"private","score":"2"}', encoding="utf-8")
    outside = subprocess.run([executable, str(rows), str(pol)], capture_output=True, text=True, env=env)
    assert outside.returncode == 1 and json.loads(outside.stdout)["status"] == "out_of_bounds"
    rows.write_text("invalid private fixture", encoding="utf-8")
    invalid = subprocess.run([executable, str(rows), str(pol)], capture_output=True, text=True, env=env)
    assert invalid.returncode == 2 and invalid.stdout == '{"status":"invalid_input"}\n'
    assert not invalid.stderr and "private" not in invalid.stdout
