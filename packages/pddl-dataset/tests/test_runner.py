import json
import sys
from pathlib import Path

import pytest

from pddl_dataset.runner import GenerationError, generate
from pddl_dataset.schema import Generator

FIXTURES = Path(__file__).parent / "fixtures"


def _make_gen_dir(tmp_path: Path, fixture_name: str, binary_name: str = "gen") -> Path:
    """Stage a fixture script + a fake domain.pddl into a generator directory."""
    gen_dir = tmp_path / "gen_dir"
    gen_dir.mkdir()
    target = gen_dir / binary_name
    target.write_text((FIXTURES / fixture_name).read_text())
    target.chmod(0o755)
    (gen_dir / "domain.pddl").write_text("(define (domain fake))\n")
    return gen_dir


def test_stdout_generator_with_flag_param(tmp_path):
    gen_dir = _make_gen_dir(tmp_path, "fake_stdout_gen.py", "gen")
    out_dir = tmp_path / "out"

    gen = Generator.model_validate(
        {
            "name": "fake-gripper",
            "binary": f"{sys.executable}",
            "fixed_args": [str(gen_dir / "gen")],
            "domain_file": {"source": "static", "path": "domain.pddl"},
            "output": {"mode": "stdout"},
            "parameters": [{"name": "balls", "type": "int", "flag": "-n", "default_test": 3}],
        }
    )

    result = generate(gen, gen_dir, out_dir, count=2, seed_base=10)

    assert (out_dir / "domain.pddl").exists()
    assert (out_dir / "p01.pddl").exists()
    assert (out_dir / "p02.pddl").exists()
    manifest = json.loads((out_dir / "manifest.json").read_text())
    assert manifest["domain"] == "fake-gripper"
    assert [i["seed"] for i in manifest["instances"]] == [10, 11]
    assert manifest["instances"][0]["params"] == {"balls": 3}
    assert "-n" in manifest["instances"][0]["command"]


def test_positional_params_with_copy_domain(tmp_path):
    gen_dir = tmp_path / "bw"
    gen_dir.mkdir()
    (gen_dir / "gen").write_text((FIXTURES / "fake_stdout_gen.py").read_text())
    (gen_dir / "gen").chmod(0o755)
    sub = gen_dir / "3ops"
    sub.mkdir()
    (sub / "domain.pddl").write_text("(define (domain bw-3ops))\n")
    out_dir = tmp_path / "out"

    gen = Generator.model_validate(
        {
            "name": "fake-bw",
            "binary": sys.executable,
            "fixed_args": [str(gen_dir / "gen")],
            "domain_file": {"source": "copy", "path": "3ops/domain.pddl"},
            "output": {"mode": "stdout"},
            "parameters": [
                {"name": "ops", "type": "int", "positional": 0, "default_test": 3},
                {"name": "blocks", "type": "int", "positional": 1, "default_test": 5},
                {"name": "seed", "type": "int", "positional": 2, "default_test": 1},
            ],
        }
    )

    result = generate(gen, gen_dir, out_dir, user_args={"blocks": "9"}, count=1, seed_base=42)

    assert "bw-3ops" in (out_dir / "domain.pddl").read_text()
    cmd = result.instances[0].command
    assert cmd[-3:] == ["3", "9", "42"]  # ops, blocks, seed (from seed_base auto-injection)


def test_file_arg_output(tmp_path):
    gen_dir = _make_gen_dir(tmp_path, "fake_filearg_gen.py", "gen.py")
    out_dir = tmp_path / "out"

    gen = Generator.model_validate(
        {
            "name": "fake-cavediving",
            "binary": sys.executable,
            "fixed_args": [str(gen_dir / "gen.py")],
            "domain_file": {"source": "static", "path": "domain.pddl"},
            "output": {"mode": "file_arg", "flag": "-problem_file"},
            "parameters": [{"name": "neg_link_prob", "type": "float", "flag": "-neg_link_prob", "default_test": 0.5}],
        }
    )

    generate(gen, gen_dir, out_dir, count=1)

    body = (out_dir / "p01.pddl").read_text()
    assert "fake" in body
    assert "-neg_link_prob" in body and "0.5" in body
    assert "-problem_file" in body


def test_domain_only_static_skips_generator_run(tmp_path):
    gen_dir = _make_gen_dir(tmp_path, "fake_stdout_gen.py", "gen")
    out_dir = tmp_path / "out"

    gen = Generator.model_validate(
        {
            "name": "fake-static",
            "binary": sys.executable,
            "fixed_args": [str(gen_dir / "gen")],
            "domain_file": {"source": "static", "path": "domain.pddl"},
            "output": {"mode": "stdout"},
            "parameters": [{"name": "balls", "type": "int", "flag": "-n", "default_test": 3}],
        }
    )

    result = generate(gen, gen_dir, out_dir, domain_only=True)

    assert (out_dir / "domain.pddl").exists()
    assert not (out_dir / "p01.pddl").exists()
    assert result.instances == []
    manifest = json.loads((out_dir / "manifest.json").read_text())
    assert manifest["instances"] == []
    assert manifest["domain_file"] == "domain.pddl"


def test_domain_only_emitted_runs_once_and_discards_problem(tmp_path):
    # Set up a generator that has no static domain.pddl; it emits one.
    gen_dir = tmp_path / "emitted_gen"
    gen_dir.mkdir()
    target = gen_dir / "gen.py"
    target.write_text((FIXTURES / "fake_emitted_domain_gen.py").read_text())
    target.chmod(0o755)
    out_dir = tmp_path / "out"

    gen = Generator.model_validate(
        {
            "name": "fake-emitted",
            "binary": sys.executable,
            "fixed_args": [str(gen_dir / "gen.py")],
            "domain_file": {"source": "emitted_by_generator", "filename": "domain.pddl"},
            "output": {"mode": "file_arg", "flag": "-problem_file"},
            "parameters": [],
        }
    )

    result = generate(gen, gen_dir, out_dir, domain_only=True)

    assert (out_dir / "domain.pddl").read_text().startswith("(define (domain emitted)")
    assert not (out_dir / "p01.pddl").exists()
    assert result.instances == []
    # generator's working-copy domain.pddl was moved out of gen_dir
    assert not (gen_dir / "domain.pddl").exists()


def test_emitted_domain_via_flag_writes_directly_and_skips_post_run_move(tmp_path):
    """When EmittedDomain has a `flag`, the runner should pass the absolute
    domain path on argv and NOT try to move a sibling file from gen_dir."""
    gen_dir = tmp_path / "fakegen"
    gen_dir.mkdir()
    target = gen_dir / "gen.py"
    target.write_text((FIXTURES / "fake_filearg_with_domain_flag.py").read_text())
    target.chmod(0o755)
    out_dir = tmp_path / "out"

    gen = Generator.model_validate(
        {
            "name": "fake-flag-domain",
            "binary": sys.executable,
            "fixed_args": [str(gen_dir / "gen.py")],
            "domain_file": {"source": "emitted_by_generator", "flag": "-domain_file"},
            "output": {"mode": "file_arg", "flag": "-problem_file"},
            "parameters": [],
        }
    )

    result = generate(gen, gen_dir, out_dir, count=1)

    assert (out_dir / "domain.pddl").read_text().startswith("(define (domain emitted_via_flag)")
    assert "fake" in (out_dir / "p01.pddl").read_text()
    cmd = result.instances[0].command
    # Both flags carry absolute paths and the domain flag was emitted by the runner.
    assert "-problem_file" in cmd and "-domain_file" in cmd
    domain_arg_idx = cmd.index("-domain_file") + 1
    assert cmd[domain_arg_idx] == str((out_dir / "domain.pddl").resolve())


def test_custom_recipe_renders_placeholders_and_writes_files(tmp_path):
    gen_dir = tmp_path / "outlier"
    gen_dir.mkdir()
    (gen_dir / "domain.pddl").write_text("(define (domain outlier))\n")
    out_dir = tmp_path / "out"

    gen = Generator.model_validate(
        {
            "name": "fake-outlier",
            "domain_file": {"source": "static", "path": "domain.pddl"},
            "parameters": [{"name": "size", "type": "int", "flag": "-s", "default_test": 7}],
            "custom_recipe": {
                "commands": [
                    "echo '(problem fake size={param_size} seed={seed})' > {problem_path}",
                ],
            },
        }
    )

    result = generate(gen, gen_dir, out_dir, count=1, seed_base=99)

    assert (out_dir / "domain.pddl").exists()
    assert "size=7" in (out_dir / "p01.pddl").read_text()
    assert result.instances[0].params == {"size": 7}
    assert "size=7 seed=99" in result.instances[0].command[0]


def test_missing_required_param_raises(tmp_path):
    gen_dir = _make_gen_dir(tmp_path, "fake_stdout_gen.py", "gen")
    out_dir = tmp_path / "out"

    gen = Generator.model_validate(
        {
            "name": "needs-param",
            "binary": sys.executable,
            "fixed_args": [str(gen_dir / "gen")],
            "domain_file": {"source": "static"},
            "output": {"mode": "stdout"},
            "parameters": [{"name": "size", "type": "int", "flag": "-s", "required": True}],
        }
    )

    with pytest.raises(GenerationError, match="missing required"):
        generate(gen, gen_dir, out_dir)
