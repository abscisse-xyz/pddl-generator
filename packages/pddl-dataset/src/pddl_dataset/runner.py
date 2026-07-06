from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pddl_dataset.schema import (
    CopyDomain,
    CustomRecipe,
    CwdFileOutput,
    EmittedDomain,
    FileArgOutput,
    Generator,
    Parameter,
    StaticDomain,
    StdoutOutput,
)


class GenerationError(RuntimeError):
    pass


@dataclass
class InstanceRecord:
    file: str
    seed: int | None
    params: dict[str, Any]
    command: list[str]
    family: str | None = None


@dataclass
class GenerationResult:
    domain: str
    domain_file: str
    instances: list[InstanceRecord] = field(default_factory=list)
    plan: dict[str, Any] | None = None


@dataclass
class BatchInstanceSpec:
    params: dict[str, Any]
    family: str | None = None
    seed: int | None = None


def _coerce(value: str, ptype: str) -> Any:
    match ptype:
        case "int":
            return int(value)
        case "float":
            return float(value)
        case "bool":
            return value.lower() in {"1", "true", "yes"}
        case "int_seq":
            return [int(x) for x in value.split(":")]
        case "float_seq":
            return [float(x) for x in value.split(":")]
        case _:
            return value


def _format(value: Any, ptype: str) -> str:
    if ptype in ("int_seq", "float_seq"):
        return ":".join(str(x) for x in value)
    return str(value)  # bool → "True"/"False" (Python-native, accepted by most argparse-style generators)


def _resolve_param(param: Parameter, user_args: dict[str, Any], seed: int | None) -> Any:
    if param.name == "seed" and seed is not None and param.name not in user_args:
        return seed
    if param.name in user_args:
        return (
            _coerce(user_args[param.name], param.type)
            if isinstance(user_args[param.name], str)
            else user_args[param.name]
        )
    if param.default_test is not None:
        return param.default_test
    if param.default is not None:
        return param.default
    if param.required:
        raise GenerationError(f"missing required parameter {param.name!r}")
    return None


def _build_argv(
    gen: Generator,
    user_args: dict[str, Any],
    seed: int | None,
    out_path: Path,
    domain_path: Path,
) -> tuple[list[str], dict[str, Any]]:
    flag_args: list[str] = []
    positional_args: list[tuple[int, str]] = []
    used: dict[str, Any] = {}

    for param in gen.parameters:
        value = _resolve_param(param, user_args, seed)
        if value is None:
            continue
        rendered = _format(value, param.type)
        used[param.name] = value
        if param.flag is not None:
            flag_args.extend([param.flag, rendered])
        else:
            assert param.positional is not None
            positional_args.append((param.positional, rendered))

    positional_args.sort()
    # Positionals before flags: some upstream scripts read sys.argv[1] directly
    # (bypassing argparse), so they need positionals at the start of argv.
    head = [sys.executable, "-m", gen.python_module] if gen.python_module else [gen.binary]
    argv = [*head, *gen.fixed_args, *(v for _, v in positional_args), *flag_args]

    if isinstance(gen.output, FileArgOutput):
        argv.extend([gen.output.flag, str(out_path)])
    if isinstance(gen.domain_file, EmittedDomain) and gen.domain_file.flag:
        argv.extend([gen.domain_file.flag, str(domain_path)])

    return argv, used


def _run_recipe(
    recipe: CustomRecipe,
    gen: Generator,
    gen_dir: Path,
    out_dir: Path,
    domain_path: Path,
    problem_path: Path,
    user_args: dict[str, Any],
    seed: int,
    instance_name: str,
) -> tuple[dict[str, Any], list[str]]:
    used: dict[str, Any] = {}
    placeholders: dict[str, str] = {
        "gen_dir": str(gen_dir),
        "out_dir": str(out_dir),
        "domain_path": str(domain_path),
        "problem_path": str(problem_path),
        "seed": str(seed),
        "instance_name": instance_name,
    }
    for param in gen.parameters:
        value = _resolve_param(param, user_args, seed)
        if value is None:
            continue
        used[param.name] = value
        placeholders[f"param_{param.name}"] = _format(value, param.type)

    rendered_commands: list[str] = []
    for cmd_template in recipe.commands:
        cmd = cmd_template.format(**placeholders)
        rendered_commands.append(cmd)
        proc = subprocess.run(cmd, cwd=gen_dir, shell=True, capture_output=True, text=True)
        if proc.returncode != 0:
            raise GenerationError(f"{gen.name}: recipe step failed: {cmd}\nstderr: {proc.stderr}")
    return used, rendered_commands


def _resolve_domain(gen: Generator, gen_dir: Path, out_dir: Path) -> Path:
    target = out_dir / "domain.pddl"
    match gen.domain_file:
        case StaticDomain(path=path):
            shutil.copy2(gen_dir / path, target)
        case CopyDomain(path=path):
            shutil.copy2(gen_dir / path, target)
        case EmittedDomain():
            pass  # generator writes it; we'll move it after the run
    return target


def generate(
    gen: Generator,
    gen_dir: Path,
    out_dir: Path,
    user_args: dict[str, Any] | None = None,
    count: int = 1,
    seed_base: int = 1,
    domain_only: bool = False,
) -> GenerationResult:
    user_args = user_args or {}
    out_dir.mkdir(parents=True, exist_ok=True)
    # Subprocess runs with cwd=gen_dir, so out paths must be absolute or they'd be resolved
    # relative to gen_dir instead of to where the CLI was invoked.
    gen_dir = gen_dir.resolve()
    out_dir = out_dir.resolve()
    domain_path = _resolve_domain(gen, gen_dir, out_dir)

    result = GenerationResult(domain=gen.name, domain_file=str(domain_path.relative_to(out_dir)))

    # When the domain is emitted by the generator (or produced by a custom recipe),
    # we must run it once even in domain_only mode.
    if domain_only:
        needs_run = isinstance(gen.domain_file, EmittedDomain) or gen.custom_recipe is not None
        iterations = 1 if needs_run else 0
    else:
        iterations = count

    for i in range(iterations):
        seed = seed_base + i
        instance_name = f"p{i + 1:02d}.pddl"
        record = _generate_instance(
            gen=gen,
            gen_dir=gen_dir,
            out_dir=out_dir,
            domain_path=domain_path,
            user_args=user_args,
            seed=seed,
            instance_name=instance_name,
        )

        if domain_only:
            (out_dir / instance_name).unlink(missing_ok=True)
        else:
            result.instances.append(record)

    _write_manifest(result, out_dir)
    return result


def generate_batch(
    gen: Generator,
    gen_dir: Path,
    out_dir: Path,
    instances: list[BatchInstanceSpec],
    plan: dict[str, Any] | None = None,
) -> GenerationResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    gen_dir = gen_dir.resolve()
    out_dir = out_dir.resolve()
    domain_path = _resolve_domain(gen, gen_dir, out_dir)
    result = GenerationResult(domain=gen.name, domain_file=str(domain_path.relative_to(out_dir)), plan=plan)
    width = max(2, len(str(len(instances))))

    for index, instance in enumerate(instances):
        instance_name = f"p{index + 1:0{width}d}.pddl"
        seed = instance.seed
        if seed is None:
            raw_seed = instance.params.get("seed")
            seed = raw_seed if isinstance(raw_seed, int) else None
        record = _generate_instance(
            gen=gen,
            gen_dir=gen_dir,
            out_dir=out_dir,
            domain_path=domain_path,
            user_args=instance.params,
            seed=seed,
            instance_name=instance_name,
            family=instance.family,
        )
        result.instances.append(record)

    _write_manifest(result, out_dir)
    return result


def _generate_instance(
    *,
    gen: Generator,
    gen_dir: Path,
    out_dir: Path,
    domain_path: Path,
    user_args: dict[str, Any],
    seed: int | None,
    instance_name: str,
    family: str | None = None,
) -> InstanceRecord:
    out_path = out_dir / instance_name

    if gen.custom_recipe is not None:
        if seed is None:
            raise GenerationError(f"{gen.name}: custom recipe batch instance missing seed")
        used, command = _run_recipe(
            gen.custom_recipe, gen, gen_dir, out_dir, domain_path, out_path, user_args, seed, instance_name
        )
    else:
        argv, used = _build_argv(gen, user_args, seed, out_path, domain_path)
        command = argv

        if isinstance(gen.output, StdoutOutput):
            with out_path.open("w") as fh:
                proc = subprocess.run(argv, cwd=gen_dir, stdout=fh, stderr=subprocess.PIPE, text=True)
        else:
            proc = subprocess.run(argv, cwd=gen_dir, capture_output=True, text=True)

        if proc.returncode != 0:
            raise GenerationError(f"{gen.name}: generator failed (exit {proc.returncode}): {proc.stderr}")

        if isinstance(gen.output, CwdFileOutput):
            shutil.move(str(gen_dir / gen.output.filename), out_path)

    # If the generator writes domain.pddl as a side-effect (no flag), move it
    # from gen_dir into out_dir. With `flag` set, it already wrote to domain_path.
    if isinstance(gen.domain_file, EmittedDomain) and not gen.domain_file.flag:
        emitted = gen_dir / gen.domain_file.filename
        if emitted.exists():
            shutil.move(str(emitted), domain_path)

    return InstanceRecord(file=instance_name, seed=seed, params=used, command=command, family=family)


def _write_manifest(result: GenerationResult, out_dir: Path) -> None:
    payload = {
        "domain": result.domain,
        "domain_file": result.domain_file,
        "instances": [
            {
                **({"family": inst.family} if inst.family is not None else {}),
                "file": inst.file,
                "seed": inst.seed,
                "params": inst.params,
                "command": inst.command,
            }
            for inst in result.instances
        ],
    }
    if result.plan is not None:
        payload["plan"] = result.plan
    (out_dir / "manifest.json").write_text(json.dumps(payload, indent=2))
