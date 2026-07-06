from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from pddl_dataset.loader import load_registry
from pddl_dataset.runner import GenerationError, generate


def _find_generators_dir() -> Path:
    env = os.environ.get("PDDL_GENERATORS_DIR")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "pddl-generators"
        if candidate.is_dir():
            return candidate
    raise SystemExit("could not locate pddl-generators dir; set PDDL_GENERATORS_DIR")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pddl-dataset", description="Generate PDDL benchmark instances.")
    parser.add_argument("domain", nargs="?", help="Domain name as registered in the YAML registry.")
    parser.add_argument("--out", type=Path, default=Path("./out"), help="Output directory (default: ./out)")
    parser.add_argument("--count", type=int, default=1, help="Number of instances to generate (default: 1)")
    parser.add_argument(
        "--seed-base", type=int, default=1, help="Starting seed; instance i uses seed_base+i (default: 1)"
    )
    parser.add_argument("--list", action="store_true", help="List registered domains and exit.")
    parser.add_argument("--describe", action="store_true", help="Describe parameters of <domain> and exit.")
    parser.add_argument("--domain-only", action="store_true", help="Emit only domain.pddl (no problem instances).")
    parser.add_argument(
        "-p", "--param", action="append", default=[], metavar="NAME=VALUE", help="Set a domain parameter (repeatable)."
    )

    args = parser.parse_args(argv)

    registry = load_registry()

    if args.list:
        for name in sorted(registry):
            print(name)
        return 0

    if args.domain is None:
        parser.error("the following arguments are required: domain (or pass --list)")

    if args.domain not in registry:
        print(f"unknown domain: {args.domain}; try `pddl-dataset --list`", file=sys.stderr)
        return 2

    gen = registry[args.domain]

    if args.describe:
        print(f"{gen.name} ({gen.binary})")
        for p in gen.parameters:
            shape = f"--{p.flag}" if p.flag else f"<positional #{p.positional}>"
            default = p.default_test if p.default_test is not None else p.default
            print(f"  {p.name:<24} {p.type:<8} {shape:<20} default={default!r:<10} {p.description}")
        return 0

    user_args: dict[str, str] = {}
    for kv in args.param:
        if "=" not in kv:
            print(f"--param expects NAME=VALUE, got: {kv}", file=sys.stderr)
            return 2
        name, value = kv.split("=", 1)
        user_args[name] = value

    if gen.python_module is not None:
        # In-package generator: cwd is irrelevant (the module is on sys.path) and
        # there is no upstream `pddl-generators/<name>/` directory to point at.
        gen_dir = Path("/tmp")
    else:
        gen_dir = _find_generators_dir() / gen.name

    try:
        result = generate(
            gen,
            gen_dir,
            args.out,
            user_args,
            count=args.count,
            seed_base=args.seed_base,
            domain_only=args.domain_only,
        )
    except GenerationError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.domain_only:
        print(f"wrote domain.pddl to {args.out}")
    else:
        print(f"wrote {len(result.instances)} instance(s) + domain.pddl to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
