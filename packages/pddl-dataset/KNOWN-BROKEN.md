# Known-broken upstream generators

These domains from `pddl-generators` cannot be wrapped reliably by `pddl-dataset`.

## storage

The compiled binary hangs indefinitely whenever it is given the trailing
positional output-file argument that its own Makefile prescribes:

    ./storage -o 1 -c 1 -n 1 -s 1 -d 1 -e 1 /tmp/p.pddl   # never terminates

Reproduced inside the Docker builder image. The hang is independent of
parameter values (verified with `-n 3 -s 9 -c 5`, the documented defaults).

The Makefile recipe `./storage -o 1 -c 1 -n 1 -s 1 -d 1 -e 1 $${PDDL_TEST_DIR}/problem.pddl`
also hangs in our environment.

Until upstream is fixed, storage is excluded from the registry. To re-enable,
debug `main.cpp` (likely an infinite loop somewhere in the placement code).

## tpp

Same shape as storage — trailing positional output-file argument, same hang
pattern. Excluded from the registry pending an upstream fix.
