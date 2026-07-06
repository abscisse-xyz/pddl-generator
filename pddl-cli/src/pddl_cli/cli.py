from __future__ import annotations

import sys

USAGE = """\
usage: pddl-cli <subcommand> [args...]

Subcommands:
  dataset     Generate PDDL benchmark instances from the registry.
  generate    Generate higher-level datasets, including curated batches.
  simulate    Replay a plan against the simulator and persist the trace.
  plan        Solve a PDDL problem. (not yet implemented)

Run `pddl-cli <subcommand> --help` for subcommand-specific options.
"""


def _run_dataset(rest: list[str]) -> int:
    from pddl_dataset.cli import main as dataset_main

    return dataset_main(rest)


def _run_simulate(rest: list[str]) -> int:
    from simulator.simulate_cli import main as simulate_main

    return simulate_main(rest)


def _run_generate(rest: list[str]) -> int:
    if not rest or rest[0] in ("-h", "--help"):
        print(
            """\
usage: pddl-cli generate <mode> [args...]

Modes:
  batch      Generate a curated batch for a supported domain.

Run `pddl-cli generate <mode> --help` for mode-specific options.
"""
        )
        return 0 if rest else 2

    mode, *mode_args = rest
    match mode:
        case "batch":
            from pddl_generator.batch.cli import main as batch_main

            return batch_main(mode_args)
        case _:
            print(f"unknown generate mode: {mode!r}", file=sys.stderr)
            return 2


def _run_not_implemented(name: str) -> int:
    print(f"`pddl-cli {name}` is not implemented yet.", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args or args[0] in ("-h", "--help"):
        print(USAGE)
        return 0 if args else 2

    cmd, *rest = args
    match cmd:
        case "dataset":
            return _run_dataset(rest)
        case "generate":
            return _run_generate(rest)
        case "simulate":
            return _run_simulate(rest)
        case "plan":
            return _run_not_implemented(cmd)
        case _:
            print(f"unknown subcommand: {cmd!r}\n", file=sys.stderr)
            print(USAGE, file=sys.stderr)
            return 2


if __name__ == "__main__":
    sys.exit(main())
