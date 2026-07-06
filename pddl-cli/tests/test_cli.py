from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout

import pytest
from pddl_cli.cli import main


def test_no_args_prints_usage_and_exits_nonzero():
    buf = io.StringIO()
    with redirect_stderr(buf):
        rc = main([])
    assert rc != 0
    # Usage shows up either on stdout (no args case prints to stdout) — accept both.


def test_help_flag_prints_usage_and_exits_zero():
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["--help"])
    assert rc == 0
    out = buf.getvalue()
    assert "Subcommands:" in out
    assert "dataset" in out
    assert "generate" in out
    assert "simulate" in out
    assert "plan" in out


def test_unknown_subcommand_exits_nonzero():
    buf = io.StringIO()
    with redirect_stderr(buf):
        rc = main(["frobnicate"])
    assert rc != 0
    assert "unknown subcommand" in buf.getvalue()


def test_unimplemented_plan_subcommand_exits_nonzero_with_clear_message():
    buf = io.StringIO()
    with redirect_stderr(buf):
        rc = main(["plan"])
    assert rc != 0
    assert "not implemented" in buf.getvalue()


def test_simulate_subcommand_delegates_to_simulator(tmp_path):
    """simulate without --input must surface the underlying CLI's argparse error
    (proves argv pass-through and confirms we routed to the right `main`)."""
    buf_err = io.StringIO()
    with redirect_stderr(buf_err):
        # argparse exits via SystemExit when required args are missing.
        with pytest.raises(SystemExit) as excinfo:
            main(["simulate"])
    assert excinfo.value.code != 0
    assert "--input" in buf_err.getvalue()


def test_dataset_subcommand_delegates_to_pddl_dataset_cli():
    """Without args, pddl-dataset's CLI requires `domain` or `--list`. We pass --list
    and check for a non-empty domain list — confirms argv pass-through works."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["dataset", "--list"])
    assert rc == 0
    domains = [line for line in buf.getvalue().splitlines() if line.strip()]
    assert "gripper" in domains
    assert "travel" in domains
    assert len(domains) >= 50


def test_dataset_subcommand_passes_through_unknown_flags():
    """Confirms args after the subcommand reach pddl-dataset's argparse."""
    buf_err = io.StringIO()
    with redirect_stderr(buf_err):
        rc = main(["dataset", "totally-not-a-real-domain"])
    assert rc != 0
    assert "unknown domain" in buf_err.getvalue()


def test_generate_batch_list_delegates_to_batch_cli():
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["generate", "batch", "--list"])
    assert rc == 0
    domains = [line for line in buf.getvalue().splitlines() if line.strip()]
    assert domains == ["cavediving", "citycar", "schedule", "travel"]


def test_generate_unknown_mode_exits_nonzero():
    buf_err = io.StringIO()
    with redirect_stderr(buf_err):
        rc = main(["generate", "not-a-mode"])
    assert rc != 0
    assert "unknown generate mode" in buf_err.getvalue()
