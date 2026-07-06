from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pddl_dataset.cli import _find_generators_dir
from pddl_dataset.loader import load_registry
from pddl_dataset.runner import GenerationError, generate_batch

from pddl_generator.batch import BATCH_SPECS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pddl-cli generate batch", description="Generate curated PDDL batches.")
    parser.add_argument("domain", nargs="?", help="Batch domain name.")
    parser.add_argument("--out", type=Path, required=False, default=Path("./out"), help="Output directory.")
    parser.add_argument("--count", type=int, help="Number of instances to generate.")
    parser.add_argument("--seed-base", type=int, default=1, help="Starting seed; instance i uses seed_base+i.")
    parser.add_argument("--list", action="store_true", help="List available batch domains and exit.")
    parser.add_argument(
        "-p", "--param", action="append", default=[], metavar="NAME=VALUE", help="Override a derived domain parameter."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list:
        for name in sorted(BATCH_SPECS):
            print(name)
        return 0

    if args.domain is None:
        parser.error("the following arguments are required: domain (or pass --list)")

    if args.domain not in BATCH_SPECS:
        print(f"unknown batch domain: {args.domain}; try `pddl-cli generate batch --list`", file=sys.stderr)
        return 2

    registry = load_registry()
    if args.domain not in registry:
        print(f"batch domain is not registered as a generator: {args.domain}", file=sys.stderr)
        return 2

    spec = BATCH_SPECS[args.domain]
    gen = registry[args.domain]
    count = spec.default_count if args.count is None else args.count
    if count < 0:
        print("--count must be non-negative", file=sys.stderr)
        return 2

    user_args: dict[str, str] = {}
    for kv in args.param:
        if "=" not in kv:
            print(f"--param expects NAME=VALUE, got: {kv}", file=sys.stderr)
            return 2
        name, value = kv.split("=", 1)
        user_args[name] = value

    if gen.python_module is not None:
        gen_dir = Path("/tmp")
    else:
        gen_dir = _find_generators_dir() / gen.name

    try:
        instances = []
        for index in range(count):
            if spec.derive_with_params is not None:
                instance = spec.derive_with_params(index, count, args.seed_base, dict(user_args))
            else:
                instance = spec.derive(index, count, args.seed_base)
                instance.params.update(user_args)
            instances.append(instance)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    try:
        result = generate_batch(gen, gen_dir, args.out, instances, plan=spec.plan)
    except GenerationError as e:
        print(str(e), file=sys.stderr)
        return 1

    print(f"wrote {len(result.instances)} batch instance(s) + domain.pddl to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
